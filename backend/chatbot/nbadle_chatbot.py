# chatbot/nbadle_chatbot.py
from __future__ import annotations
from dataclasses import dataclass
import time
from google.api_core import exceptions as google_exceptions

from chatbot.config import (
    PROMPT_TEMPLATE,
    CLASSIFICATION_PROMPT_TEMPLATE,
    DEFAULT_INDEX_PATH,
    DEFAULT_DOCS_PATH,
    DEFAULT_METAS_PATH,
    MAX_RETRIES,
    MIN_JACCARD_NAME_MATCH,
    TEAM_INDICATORS,
)
from chatbot.clients import Embedder, GeminiChat
from chatbot.retrieval import FaissStore
from chatbot.rewrite import QueryRewriter
from chatbot.classify import (
    is_team_query,
    is_simple_name_query,
    check_close_team_name,
    convert_to_close_token_match,
)
from chatbot.name_match import strong_name_matches, is_exact_name_match, disambiguation_message

class NBAdleChatbot:
    def __init__(self):
        self.prompt_template = PROMPT_TEMPLATE
        self.embedder = Embedder()
        self.gemini = GeminiChat().client
        self.rewriter = QueryRewriter(self.gemini)
        self.store = FaissStore(DEFAULT_INDEX_PATH, DEFAULT_DOCS_PATH, DEFAULT_METAS_PATH)
        print(f"Models loaded. FAISS docs={len(self.store.docs)}")

    def classify_query_llm(self, query: str) -> list[str]:
        prompt = CLASSIFICATION_PROMPT_TEMPLATE.format(query=query)
        try:
            res = self.gemini.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={"max_output_tokens": 100, "temperature": 0.0},
            )
            category = (res.text or "").strip().lower()
            valid = {
                "player_profile", "player_season", "player_career",
                "team", "team_coach", "roster", "comparison", "other",
                "roster_simple",
            }
            return [category] if category in valid else ["other"]
        except Exception as e:
            print(f"Classification error: {e}")
            return ["other"]

    def classify_query_hybrid(self, query: str) -> list[str]:
        q = (query or "").lower()

        roster_signals = [
            "roster", "who played", "players on", "team members",
            "lineup", "squad", "who plays", "on the team",
            "who is on", "who are on", "members of", "team mates", "teammates",
            "teammate", "playing for", "played for", "team roster"
        ]
        if any(sig in q for sig in roster_signals):
            print(f"[classify] '{query}' → roster (fast path)")
            return ["roster", "roster_simple"]

        career_signals = ["career", "all-time", "all time", "overall", "lifetime", "life time"]
        if any(sig in q for sig in career_signals):
            print(f"[classify] '{query}' → player_career (fast path)")
            return ["player_career"]

        if is_team_query(query, debug=True):
            print(f"[classify] '{query}' → team/team_coach (fast path)")
            return ["team", "team_coach"]

        if is_simple_name_query(query):
            print(f"[classify] '{query}' → player_profile (fast path)")
            return ["player_profile", "player_career"]

        profile_keywords = ["height", "weight", "born", "birth", "age", "position", "college", "school", "country", "from"]
        if any(kw in q for kw in profile_keywords):
            return ["player_profile"]

        print(f"[classify] '{query}' → using LLM (ambiguous)")
        return self.classify_query_llm(query)

    def generate_prompt(self, context: str, question: str) -> str:
        return self.prompt_template.format(context=context, question=question)

    def ask_gemini(self, prompt: str, metadata: dict) -> tuple[str, dict]:
        for attempt in range(MAX_RETRIES):
            try:
                res = self.gemini.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={"max_output_tokens": 2000, "temperature": 0.2},
                )
                text = (res.text or "").strip()
                return text, metadata if text else ({}, {})
            except google_exceptions.ResourceExhausted:
                if attempt < MAX_RETRIES - 1:
                    time.sleep((2 ** attempt) * 1)
                    continue
                return "I'm experiencing high demand right now. Please try again in a minute.", {}
            except Exception as e:
                print(f"Error during answer generation: {e}")
                return "Sorry, I encountered an error while generating the answer.", {}

    def format_context(self, docs) -> str:
        parts = []
        for d in docs:
            meta = d.meta
            label_bits = [meta.get("doc_type", "doc")]
            if meta.get("player_name"):
                label_bits.append(meta["player_name"])
            if meta.get("season"):
                label_bits.append(meta["season"])
            if meta.get("team_abbr"):
                label_bits.append(meta["team_abbr"])
            label = " | ".join(label_bits)
            parts.append(f"[{label}]\n{d.text}")
        return "\n\n".join(parts)

    def answer_question(self, question: str, history: str = "") -> tuple[str, dict]:
        q = question or ""

        if is_team_query(q) and check_close_team_name(q):
            fixed = convert_to_close_token_match(q, TEAM_INDICATORS)
            if fixed:
                q = fixed

        retrieval_query = self.rewriter.rewrite(q, history) if history else q
        print(f"[query] user='{question}' → retrieval='{retrieval_query}'")

        qv = self.embedder.embed(retrieval_query)
        doc_type_pref = self.classify_query_hybrid(retrieval_query)

        docs = self.store.search(qv, retrieval_query, doc_type_pref)
        if not docs:
            return "Sorry, I could not find any relevant NBA stats information to answer your question.", {}

        team_intent = is_team_query(q)

        if is_simple_name_query(q) and not team_intent:
            matches = strong_name_matches(q, docs, min_jaccard=MIN_JACCARD_NAME_MATCH)

            exact = [m for m in matches if is_exact_name_match(q, m[0].meta.get("player_name", ""))]
            if exact:
                target_pid = exact[0][0].meta.get("player_id")
                docs = [d for d in docs if d.meta.get("player_id") == target_pid and d.meta.get("doc_type") in {"player_profile", "player_career"}]
            else:
                unique_pids = list({m[0].meta.get("player_id") for m in matches if m[0].meta.get("player_id") is not None})
                if len(unique_pids) >= 2:
                    return disambiguation_message(matches), {}
                if len(unique_pids) == 1:
                    target_pid = unique_pids[0]
                    docs = [d for d in docs if d.meta.get("player_id") == target_pid and d.meta.get("doc_type") in {"player_profile", "player_career"}]

        metadata: dict = {}
        first_meta = docs[0].meta
        if first_meta.get("player_id"):
            metadata.update({
                "player_id": first_meta["player_id"],
                "player_name": first_meta.get("player_name", ""),
                "player_image_url": first_meta.get("player_image_url", ""),
            })
        elif first_meta.get("team_id"):
            metadata.update({
                "team_id": first_meta["team_id"],
                "team_name": first_meta.get("team_name", ""),
                "team_abbr": first_meta.get("team_abbr", ""),
                "team_url": first_meta.get("team_url", ""),
                "team_image_url": first_meta.get("team_image_url", ""),
            })

        context = self.format_context(docs)
        print(f"[context] {context[:200]}... (len={len(context)})")
        prompt = self.generate_prompt(context, retrieval_query)
        answer, meta = self.ask_gemini(prompt, metadata)
        return answer, meta
