import os
import re
import faiss
import numpy as np
import pickle
import time
from google.api_core import exceptions as google_exceptions
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from google import genai
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage

from chatbot.config import PROMPT_TEMPLATE, REWRITE_PROMPT_TEMPLATE

load_dotenv()

# Default paths for FAISS assets
BASE_DIR = Path(__file__).resolve().parent  # backend/chatbot
DEFAULT_INDEX_PATH = str(BASE_DIR / "nbadle.index")
DEFAULT_DOCS_PATH  = str(BASE_DIR / "docs.pkl")
DEFAULT_METAS_PATH = str(BASE_DIR / "metas.pkl")

# Precompiled regex
RE_SEASON_RANGE = re.compile(r"(19|20)\d{2}\s*-\s*\d{2}")
RE_YEAR = re.compile(r"(19|20)\d{2}")
RE_NON_ALNUM_SPACE = re.compile(r"[^a-z0-9\s]+")
RE_MULTI_SPACE = re.compile(r"\s+")

RE_POS = re.compile(r"Position:\s*([^\.]+)\.")
RE_TEAM = re.compile(r"Current team:\s*([^\.]+)\.")

# Keywords indicating user intent
INTENT_WORDS = {
    "height","weight","born","birth","age","position","college","school","country",
    "coach","conference","team","city",
    "season","year","stats","stat","career","overall","all","time","average","averages","totals",
    "ppg","rpg","apg","mpg","points","rebounds","rebound","assists","assist","minutes","min",
    "fg","fg%","3p","3p%","ft","ft%","+/-","plus","minus"
}

# Minimum Jaccard similarity for strong name match
MIN_JACCARD_NAME_MATCH = 0.6
MAX_RETRIES = 3


def detect_season(query: str) -> str | None:
    q = query.lower()

    m = RE_SEASON_RANGE.search(q)
    if m:
        return m.group(0).replace(" ", "")

    m2 = RE_YEAR.search(q)
    if m2:
        yr = int(m2.group(0))
        return f"{yr}-{str((yr + 1) % 100).zfill(2)}"

    return None


def preferred_doc_types(query: str, name_only: bool) -> list[str] | None:
    q = query.lower()

    # Highest priority, name-only query
    if name_only:
        return ["player_profile", "player_career"]

    profile_words = ["height", "weight", "born", "birth", "age", "position", "college", "school", "country"]
    team_words = ["coach", "conference", "team info", "city"]
    season_words = ["season", "year", "stats", "ppg", "points", "reb", "rebound", "assist", "fg", "3p", "ft", "plus minus", "+/-"]
    career_words = ["career", "overall", "all time", "average", "totals"]

    if any(w in q for w in career_words):
        return ["player_career"]
    if any(w in q for w in profile_words):
        return ["player_profile"]
    if any(w in q for w in team_words):
        return ["team"]
    if any(w in q for w in season_words):
        return ["player_season"]

    return None


def normalize_text(s: str) -> str:
    s = s.lower().strip()
    s = RE_NON_ALNUM_SPACE.sub(" ", s)
    s = RE_MULTI_SPACE.sub(" ", s).strip()
    return s


def is_name_only_query(query: str) -> bool:
    q = normalize_text(query)

    # If it has any year, not name-only
    if RE_YEAR.search(q):
        return False

    toks = q.split()
    if any(t in INTENT_WORDS for t in toks):
        return False

    return 1 <= len(toks) <= 4


def last_token(s: str) -> str:
    toks = normalize_text(s).split()
    return toks[-1] if toks else ""


def name_jaccard(a: str, b: str) -> float:
    a_set = set(normalize_text(a).split())
    b_set = set(normalize_text(b).split())
    if not a_set or not b_set:
        return 0.0
    return len(a_set & b_set) / len(a_set | b_set)


def is_exact_name_match(query: str, player_name: str) -> bool:
    return normalize_text(query) == normalize_text(player_name)


def strong_name_matches(query: str, results, min_jaccard: float = 0.6):
    q_last = last_token(query)
    out = []
    for score, text, meta in results:
        if meta.get("doc_type") != "player_profile":
            continue
        pname = meta.get("player_name", "")
        if not pname:
            continue

        # Exact match always counts
        if is_exact_name_match(query, pname):
            out.append((score, text, meta, 1.0))
            continue

        # Strong match heuristic:
        # - last name matches OR
        # - token overlap similarity is high
        p_last = last_token(pname)
        jac = name_jaccard(query, pname)

        if (q_last and p_last and q_last == p_last) or jac >= min_jaccard:
            out.append((score, text, meta, jac))

    return out


class NBAdleChatbot:
    def __init__(self):
        self.prompt_template = PROMPT_TEMPLATE
        self.load_models()
        self.load_faiss_assets()

    def load_models(self):
        self.embedder = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.chat_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        print("Models loaded.")

    def load_faiss_assets(
        self,
        index_path: str = DEFAULT_INDEX_PATH,
        docs_path: str = DEFAULT_DOCS_PATH,
        metas_path: str = DEFAULT_METAS_PATH
    ):
        try:
            self.index = faiss.read_index(index_path)
            with open(docs_path, "rb") as f:
                self.docs = pickle.load(f)
            with open(metas_path, "rb") as f:
                self.metas = pickle.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load FAISS assets: {e}")

        if len(self.docs) != len(self.metas):
            raise RuntimeError("docs.pkl and metas.pkl length mismatch")

        print(f"FAISS loaded. docs={len(self.docs)}")

    def embed_query(self, query: str) -> np.ndarray:
        try:
            res = self.embedder.embeddings.create(
                model="text-embedding-3-small",
                input=[query]
            )
            v = np.array(res.data[0].embedding, dtype="float32").reshape(1, -1)
            faiss.normalize_L2(v)
        except Exception as e:
            raise RuntimeError(f"Failed to embed query: {e}")
        
        return v

    def retrieve(self, query: str, top_k: int = 5, prefetch_k: int = 50):
        qv = self.embed_query(query)
        D, I = self.index.search(qv, prefetch_k)

        season = detect_season(query)
        name_only = is_name_only_query(query)
        type_pref = preferred_doc_types(query, name_only)

        candidates = []
        for score, idx in zip(D[0], I[0]):
            if idx < 0 or idx >= len(self.docs):
                continue
            candidates.append((float(score), idx, self.docs[idx], self.metas[idx]))

        # Filter by season if user implies one
        if season:
            season_filtered = [c for c in candidates if c[3].get("season") == season]
            if len(season_filtered) >= 3:
                candidates = season_filtered

        # Filter by doc type preference
        if type_pref:
            type_filtered = [c for c in candidates if c[3].get("doc_type") in type_pref]

            if name_only:
                # For name-only, be strict: do not allow season/team docs into context
                if len(type_filtered) >= 1:
                    candidates = type_filtered
            else:
                # For other queries, only filter if we have enough options
                if len(type_filtered) >= 3:
                    candidates = type_filtered

        # Deduplicate by meta id
        seen = set()
        final = []
        for score, idx, text, meta in sorted(candidates, key=lambda x: x[0], reverse=True):
            key = meta.get("id") or text[:120]
            if key in seen:
                continue
            seen.add(key)
            final.append((score, text, meta))
            if len(final) >= top_k:
                break

        return final
    
    def disambiguation_message(self, matches, limit: int = 5) -> str:
        # Show top profile matches with a little identifying info
        options = []
        seen = set()

        for _, text, meta, _jac in matches:
            pid = meta.get("player_id")
            name = meta.get("player_name", "Unknown")
            if pid in seen:
                continue
            seen.add(pid)

            # Try to extract a tiny bit of info from the profile text
            position = ""
            team = ""
            m_pos = RE_POS.search(text)
            if m_pos:
                position = m_pos.group(1).strip()

            m_team = RE_TEAM.search(text)
            if m_team:
                team = m_team.group(1).strip()

            extra = []
            if position:
                extra.append(position)
            if team:
                extra.append(team)

            if extra:
                options.append(f"- {name} [{', '.join(extra)}]")
            else:
                options.append(f"- {name}")

            if len(options) >= limit:
                break

        if not options:
            return "Sorry, I need more information to identify the player. Please provide the full name or team."

        return (
            "Which one did you mean?\n"
            + "\n".join(options)
            + "\n\nReply with the full name, or add a hint like team, position, or season."
        ), {}

    def generate_prompt(self, context: str, question: str) -> str:
        return self.prompt_template.format(context=context, question=question)
    
    def ask_gemini(self, prompt: str, metadata: dict) -> tuple[str, dict]:
        for attempt in range(MAX_RETRIES):
            try:
                res = self.chat_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={"max_output_tokens": 2000, "temperature": 0.2}
                )
                if res.text == "Sorry, I can only answer NBA stats questions. Please ask another question.":
                    return res.text, {}
                return res.text.strip(), metadata

            except google_exceptions.ResourceExhausted as e:
                if attempt < MAX_RETRIES - 1:
                    wait_time = (2 ** attempt) * 1
                    print(f"Rate limit hit. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    error_msg = "I'm experiencing high demand right now. Please try again in a minute."
                    return error_msg, {}
            
            except Exception as e:
                print(f"Error during answer generation: {e}")
                return "Sorry, I encountered an error while generating the answer.", {}
            
    def rewrite_query(self, message: str, history: str) -> str:
        """
        Returns a standalone query for embedding + retrieval.
        Falls back to original message if rewrite fails or history is empty.
        """
        if not history.strip():
            return message

        prompt = REWRITE_PROMPT_TEMPLATE.format(history=history, message=message)

        for attempt in range(MAX_RETRIES):
            try:
                res = self.chat_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={"max_output_tokens": 80, "temperature": 0.0}
                )
                rewritten = (res.text or "").strip()

                # Safety: avoid empty rewrites
                if rewritten:
                    return rewritten

                return message

            except google_exceptions.ResourceExhausted:
                if attempt < MAX_RETRIES - 1:
                    time.sleep((2 ** attempt) * 1)
                    continue
                return message
            except Exception:
                return message

    def build_retrieval_query(self, message: str, history: str) -> str:
        """
        If history exists, use Gemini to rewrite.
        Otherwise use message as-is.
        """
        return self.rewrite_query(message, history) if history else message

    def answer_question(self, question: str, history: str = "") -> str:
    
        name_only = is_name_only_query(question)

        top_k = 8 if name_only else 5
        prefetch_k = 50 if name_only else 60
        
        retrieval_query = self.build_retrieval_query(question, history)

        print(f"[rewrite] user='{question}' -> retrieval='{retrieval_query}'")

        results = self.retrieve(retrieval_query, top_k=top_k, prefetch_k=prefetch_k)

        if not results:
            return "Sorry, I could not find any relevant NBA stats information to answer your question."
        
        if name_only:
            matches = strong_name_matches(question, results, min_jaccard=MIN_JACCARD_NAME_MATCH)

            # If any exact match exists, lock onto that player
            exact = [m for m in matches if is_exact_name_match(question, m[2].get("player_name", ""))]
            if exact:
                target_pid = exact[0][2].get("player_id")
                # Keep only docs for that player (profile + career are ideal for name-only)
                results = [r for r in results if r[2].get("player_id") == target_pid and r[2].get("doc_type") in ["player_profile", "player_career"]]

            else:
                # If multiple strong matches, then disambiguate
                unique_pids = list({m[2].get("player_id") for m in matches if m[2].get("player_id") is not None})
                if len(unique_pids) >= 2:
                    print(f"Disambiguation needed for query '{question}': {[m[2].get('player_name') for m in matches]}")
                    return self.disambiguation_message(matches)

                # If only one strong match, lock onto it
                if len(unique_pids) == 1:
                    target_pid = unique_pids[0]
                    results = [r for r in results if r[2].get("player_id") == target_pid and r[2].get("doc_type") in ["player_profile", "player_career"]]

        # Extract metadata for links
        metadata = {}
        if results:
            first_meta = results[0][2]
            if first_meta.get("player_id"):
                metadata["player_id"] = first_meta["player_id"]
                metadata["player_name"] = first_meta.get("player_name", "")
                metadata["player_image_url"] = first_meta.get("player_image_url", "")
            elif first_meta.get("team_id"):
                metadata["team_id"] = first_meta["team_id"]
                metadata["team_name"] = first_meta.get("team_name", "")
                metadata["team_abbr"] = first_meta.get("team_abbr", "")
                metadata["team_url"] = first_meta.get("team_url", "")
                metadata["team_image_url"] = first_meta.get("team_image_url", "")

        context = self.format_context(results)
        print(context)
        prompt = self.generate_prompt(context, retrieval_query)

        answer, answer_metadata = self.ask_gemini(prompt, metadata)
        return answer, answer_metadata

    def format_context(self, results) -> str:
        context_parts = []
        for score, text, meta in results:
            label_bits = [meta.get("doc_type", "doc")]
            if meta.get("player_name"):
                label_bits.append(meta["player_name"])
            if meta.get("season"):
                label_bits.append(meta["season"])
            if meta.get("team_abbr"):
                label_bits.append(meta["team_abbr"])

            label = " | ".join(label_bits)
            context_parts.append(f"[{label}]\n{text}")

        return "\n\n".join(context_parts)

    def chat(self):
        print("Welcome to the NBAdle Chatbot! Type 'exit' to quit.")
        while True:
            q = input("You: ").strip()
            if q.lower() in ["exit", "quit"]:
                print("Goodbye!")
                return
            answer = self.answer_question(q)
            print("NBAdle:")
            print(answer)


if __name__ == "__main__":

    NBAdleChatbot().chat()
