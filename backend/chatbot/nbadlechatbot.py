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
from chatbot.config import (
    PROMPT_TEMPLATE, 
    REWRITE_PROMPT_TEMPLATE,
    CLASSIFICATION_PROMPT_TEMPLATE,
    DEFAULT_INDEX_PATH,
    DEFAULT_DOCS_PATH,
    DEFAULT_METAS_PATH,
    RE_SEASON_RANGE,
    RE_YEAR,
    RE_NON_ALNUM_SPACE,
    RE_MULTI_SPACE,
    RE_POS,
    RE_TEAM,
    TEAM_INDICATORS,
    TEAM_ABBREVIATIONS,
    MIN_JACCARD_NAME_MATCH,
    MAX_RETRIES
)

load_dotenv()

def detect_season(query: str) -> str | None:
    """Extract season from query (e.g., '2013-14' or '2013')."""
    q = query.lower()
    m = RE_SEASON_RANGE.search(q)
    if m:
        return m.group(0).replace(" ", "")
    
    m2 = RE_YEAR.search(q)
    if m2:
        yr = int(m2.group(0))
        return f"{yr}-{str((yr + 1) % 100).zfill(2)}"
    
    return None


def normalize_text(s: str) -> str:
    """Normalize text for matching."""
    s = s.lower().strip()
    s = RE_NON_ALNUM_SPACE.sub(" ", s)
    s = RE_MULTI_SPACE.sub(" ", s).strip()
    return s


def last_token(s: str) -> str:
    """Get last token from normalized text."""
    toks = normalize_text(s).split()
    return toks[-1] if toks else ""


def name_jaccard(a: str, b: str) -> float:
    """Calculate Jaccard similarity between two names."""
    a_set = set(normalize_text(a).split())
    b_set = set(normalize_text(b).split())
    if not a_set or not b_set:
        return 0.0
    return len(a_set & b_set) / len(a_set | b_set)


def is_exact_name_match(query: str, player_name: str) -> bool:
    """Check if query exactly matches player name."""
    return normalize_text(query) == normalize_text(player_name)


def strong_name_matches(query: str, results, min_jaccard: float = 0.6):
    """Find player profiles that strongly match the query name."""
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

        # Strong match: last name matches OR high token overlap
        p_last = last_token(pname)
        jac = name_jaccard(query, pname)

        if (q_last and p_last and q_last == p_last) or jac >= min_jaccard:
            out.append((score, text, meta, jac))

    return out

def levenshtein(a: str, b: str) -> int:
    # small, fast DP, OK for short strings and small lists
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            ins = cur[j - 1] + 1
            dele = prev[j] + 1
            sub = prev[j - 1] + (ca != cb)
            cur.append(min(ins, dele, sub))
        prev = cur
    return prev[-1]

def close_token_match(token: str, targets: list[str], max_dist: int = 1) -> bool:
    """
    token: single word like 'wizard'
    targets: list of canonical team tokens like 'wizards', 'lakers'
    max_dist: edit distance tolerance
    """
    t = normalize_text(token)
    if not t:
        return False

    # exact
    if t in targets:
        return True

    # plural heuristics
    plural_forms = {
        t + "s",
        t + "es",
        t[:-1] + "ies" if t.endswith("y") and len(t) > 2 else "",
    }
    if any(p and p in targets for p in plural_forms):
        return True

    # small typo tolerance (only for short single tokens, keep it conservative)
    for cand in targets:
        if abs(len(t) - len(cand)) > max_dist:
            continue
        if levenshtein(t, cand) <= max_dist:
            return True

    return False

def convert_to_close_token_match(token: str, targets: list[str], max_dist: int = 1) -> str | None:
    """
    token: single word like 'wizard'
    targets: list of canonical team tokens like 'wizards', 'lakers'
    max_dist: edit distance tolerance
    """
    t = normalize_text(token)
    if not t:
        return None

    # exact
    if t in targets:
        return t

    # plural heuristics
    plural_forms = {
        t + "s",
        t + "es",
        t[:-1] + "ies" if t.endswith("y") and len(t) > 2 else "",
    }
    for p in plural_forms:
        if p and p in targets:
            return p

    # small typo tolerance (only for short single tokens, keep it conservative)
    for cand in targets:
        if abs(len(t) - len(cand)) > max_dist:
            continue
        if levenshtein(t, cand) <= max_dist:
            return cand

    return None

def is_team_query(query: str) -> bool:
    q_norm = normalize_text(query)
    toks = q_norm.split()

    team_keywords = ["coach", "conference", "team", "roster", "located"]

    TEAM_TOKENS = [normalize_text(x) for x in TEAM_INDICATORS]
    TEAM_WORDS  = sorted({w for t in TEAM_TOKENS for w in t.split()})
    TEAM_ABBRS  = [normalize_text(x) for x in TEAM_ABBREVIATIONS]

    # exact indicators first (fast)
    has_team_name = any(ind in q_norm for ind in TEAM_TOKENS)
    has_team_abbr = any(abbr in toks or abbr in q_norm for abbr in TEAM_ABBRS)

    # fuzzy team word match for short queries like "wizard", "laker"
    fuzzy_team = False
    if 1 <= len(toks) <= 2:
        fuzzy_team = any(close_token_match(t, TEAM_WORDS, max_dist=1) for t in toks)

    print(f"[is_team_query] has_team_name={has_team_name}, has_team_abbr={has_team_abbr}, fuzzy_team={fuzzy_team}")

    has_team_keyword = any(kw in q_norm for kw in team_keywords)

    # if user typed a short thing that looks like a team, treat it as team intent
    if fuzzy_team and not any(x in q_norm for x in ["ppg", "rpg", "apg", "stats", "points", "rebounds", "assists"]):
        print(f"[is_team_query] Detected fuzzy team query: '{query}'")
        return True

    if (has_team_name or has_team_abbr) and has_team_keyword:
        print(f"[is_team_query] Detected team query: '{query}'")
        return True

    player_indicators = ["player", "stats", "ppg", "points", "reb", "rebound", "assist", "fg", "3p", "ft", "plus minus"]
    has_player_indicator = any(pi in q_norm for pi in player_indicators)

    if (has_team_name or has_team_abbr) and not has_player_indicator:
        print(f"[is_team_query] Detected team query (no player indicators): '{query}'")
        return True

    print(f"[is_team_query] Not a team query: '{query}'")
    return False

def repair_rewrite(original: str, rewritten: str) -> str:
    o_toks = normalize_text(original).split()
    r_toks = normalize_text(rewritten).split()
    r_set = set(r_toks)

    missing = [t for t in o_toks if t not in r_set]
    if not missing:
        return rewritten.strip()

    # append missing intent words to the end
    repaired = " ".join((r_toks + missing)).strip()
    return repaired

def rewrite_is_valid(original: str, rewritten: str) -> bool:
    o = normalize_text(original)
    r = normalize_text(rewritten)

    if not r:
        return False

    o_toks = o.split()
    r_toks = set(r.split())

    # must keep every original token
    return all(t in r_toks for t in o_toks)


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
    
    def classify_query_llm(self, query: str) -> list[str]:
        """Use LLM to classify ambiguous query intent."""
        prompt = CLASSIFICATION_PROMPT_TEMPLATE.format(query=query)
        
        try:
            res = self.chat_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={"max_output_tokens": 100, "temperature": 0.0}
            )
            print(f"[classify_llm] '{query}' → '{res.text.strip()}'")
            category = res.text.strip().lower()
            
            # Validate category
            valid_categories = [
                "player_profile", "player_season", "player_career",
                "team", "team_coach", "roster", "comparison", "other"
            ]
            
            if category in valid_categories:
                return [category]
            
            return ["other"]
            
        except Exception as e:
            print(f"Classification error: {e}")
            return ["other"]
    
    def is_simple_name_query(self, query: str) -> bool:
        """Check if query is just a player/team name (1-4 words, no stats/year keywords)."""
        q = normalize_text(query)
        
        # Has year/season = not simple name
        if RE_YEAR.search(q):
            return False
        
        # Has stat/intent keywords = not simple name
        intent_keywords = {
            "height", "weight", "born", "birth", "age", "position", "college", "school",
            "country", "coach", "conference", "roster", "season", "stats", "ppg", "rpg",
            "apg", "points", "rebounds", "assists", "career", "average", "totals", "you", "me"
        }
        
        toks = q.split()
        if any(t in intent_keywords for t in toks):
            return False
        
        # 1-4 words = likely just a name
        return 1 <= len(toks) <= 3
        
    def classify_query_hybrid(self, query: str) -> list[str]:
        """
        Smart hybrid classification:
        - Use fast keyword matching for 80% of obvious queries
        - Fall back to LLM for 20% of ambiguous queries
        """
        q = query.lower()
        
        # === FAST PATHS (80% of queries) ===
        
        # 1. Roster queries - very distinctive patterns
        roster_signals = [
            "roster", "who played", "players on", "team members", 
            "lineup", "squad", "who plays", "on the team",
            "who is on", "who are on", "members of"  # NEW
        ]
        if any(sig in q for sig in roster_signals):
            print(f"[classify] '{query}' → roster (fast path)")
            return ["roster", "roster_simple"]
        
        # 2. Career queries - distinctive keywords
        career_signals = ["career", "all-time", "overall", "lifetime", "all time"]
        if any(sig in q for sig in career_signals):
            print(f"[classify] '{query}' → player_career (fast path)")
            return ["player_career"]
        
        # 3. Team info - coach/conference questions without player stats context
        if is_team_query(query):
            print(f"[classify] '{query}' → team/team_coach (fast path)")
            return ["team", "team_coach"]
        
        # 4. Season stats - has year AND stat keywords
        has_season = detect_season(query) is not None
        if has_season:
            stat_keywords = ["stats", "stat", "ppg", "rpg", "apg", "points", "rebounds", 
                           "assists", "fg", "3p", "ft", "average"]
            if any(kw in q for kw in stat_keywords):
                print(f"[classify] '{query}' → player_season (fast path)")
                return ["player_season"]
        
        # 5. Simple name query - just a player/team name
        if self.is_simple_name_query(query):
            print(f"[classify] '{query}' → player_profile (fast path)")
            return ["player_profile", "player_career"]
        
        # 6. Profile queries - asking about player attributes
        profile_keywords = ["height", "weight", "born", "birth", "age", "position", 
                          "college", "school", "country", "from"]
        if any(kw in q for kw in profile_keywords):
            print(f"[classify] '{query}' → player_profile (fast path)")
            return ["player_profile"]
        
        # AMBIGUOUS - Use LLM (20% of queries)
        print(f"[classify] '{query}' → using LLM (ambiguous)")
        return self.classify_query_llm(query)
    
    def latest_team_season(self, team_id: int) -> str | None:
        seasons = []
        for meta in self.metas:
            if meta.get("doc_type") in ("roster", "roster_simple") and meta.get("team_id") == team_id:
                s = meta.get("season")
                if isinstance(s, str) and re.match(r"^\d{4}-\d{2}$", s):
                    seasons.append(s)
        return max(seasons) if seasons else None
    
    def check_close_team_name(self, query: str) -> bool:
        """Check if query contains a close match to a known team name."""
        q_norm = normalize_text(query)
        toks = q_norm.split()

        TEAM_TOKENS = [normalize_text(x) for x in TEAM_INDICATORS]
        TEAM_WORDS  = sorted({w for t in TEAM_TOKENS for w in t.split()})

        if 1 <= len(toks) <= 2:
            if any(close_token_match(t, TEAM_WORDS, max_dist=1) for t in toks):
                return True
        return False

    def retrieve(self, query: str, top_k: int = 5, prefetch_k: int = 50):
        """Retrieve relevant documents with smart filtering."""
        qv = self.embed_query(query)
        
        # Classify query to determine doc type preference
        doc_type_pref = self.classify_query_hybrid(query)
        
        # Adjust retrieval parameters based on query type
        is_roster = "roster" in doc_type_pref
        is_team = "team" in doc_type_pref or "team_coach" in doc_type_pref
        is_comparison = "comparison" in doc_type_pref
        is_name_only = self.is_simple_name_query(query)
        
        if is_comparison:
            prefetch_k = 80
            top_k = 10
        elif is_name_only:
            prefetch_k = 50
            top_k = 8
        
        D, I = self.index.search(qv, prefetch_k)
        season = detect_season(query)

        # Build candidates
        candidates = []
        for score, idx in zip(D[0], I[0]):
            if idx < 0 or idx >= len(self.docs):
                continue
            candidates.append((float(score), idx, self.docs[idx], self.metas[idx]))

        # Boost scores for preferred doc types
        if doc_type_pref and "other" not in doc_type_pref:
            boosted = []
            for score, idx, text, meta in candidates:
                doc_type = meta.get("doc_type", "")
                if doc_type in doc_type_pref:
                    # Give 40% boost to matching doc types
                    score = min(score * 1.4, 1.0)
                boosted.append((score, idx, text, meta))
            candidates = boosted

        # Filter by season if detected
        if season:
            season_filtered = [c for c in candidates if c[3].get("season") == season]
            if len(season_filtered) >= 2:
                candidates = season_filtered
                print(f"[filter] Filtered to season {season}: {len(season_filtered)} docs")

        if is_roster and season is None:
            roster_cands = [c for c in candidates if c[3].get("doc_type") in ("roster", "roster_simple")]
            if roster_cands:
                top_team_id = max(
                    (c[3].get("team_id") for c in roster_cands),
                    key=lambda tid: sum(1 for rc in roster_cands if rc[3].get("team_id") == tid)
                )
                latest = self.latest_team_season(int(top_team_id))
                print(f"[filter] Roster candidates for team_id={top_team_id}, latest_season={latest}")
                if latest:
                    candidates = [c for c in roster_cands if c[3].get("team_id") == top_team_id and c[3].get("season") == latest]
                    print(f"[filter] Defaulted roster season to latest: {latest}")

        # Filter by doc type if we have strong preference and enough results
        if doc_type_pref and "other" not in doc_type_pref:
            type_filtered = [c for c in candidates if c[3].get("doc_type") in doc_type_pref]
            
            # For name-only queries, be strict about doc type
            if is_name_only and len(type_filtered) >= 1:
                candidates = type_filtered
                print(f"[filter] Strict name-only filter: {len(type_filtered)} docs")
            elif is_team and len(type_filtered) >= 1:
                candidates = type_filtered
                print(f"[filter] Strict team filter: {len(type_filtered)} docs")
            # For roster queries, be strict too
            elif is_roster and len(type_filtered) >= 1:
                candidates = type_filtered
                print(f"[filter] Strict roster filter: {len(type_filtered)} docs")
            # For other queries, only filter if we have enough matches
            elif len(type_filtered) >= 3:
                candidates = type_filtered
                print(f"[filter] Doc type filter: {len(type_filtered)} docs")

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
        """Create disambiguation message for multiple player matches."""
        options = []
        seen = set()

        for _, text, meta, _jac in matches:
            pid = meta.get("player_id")
            name = meta.get("player_name", "Unknown")
            if pid in seen:
                continue
            seen.add(pid)

            # Extract position and team from profile text
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
        )

    def generate_prompt(self, context: str, question: str) -> str:
        return self.prompt_template.format(context=context, question=question)
    
    def ask_gemini(self, prompt: str, metadata: dict) -> tuple[str, dict]:
        """Generate answer using Gemini with retry logic."""
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
        Rewrite query to be standalone using conversation history.
        Falls back to original message if rewrite fails or history is empty.
        """
        if not history.strip():
            return message
        
        print(f"[rewrite] History context: {history[:300]}...")

        prompt = REWRITE_PROMPT_TEMPLATE.format(history=history, message=message)

        for attempt in range(MAX_RETRIES):
            try:
                res = self.chat_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={"max_output_tokens": 100, "temperature": 0.0}
                )
                rewritten = (res.text or "").strip()

                if not rewritten:
                    print("[rewrite] Empty rewrite result, using original message")
                    return message
                
                if rewrite_is_valid(message, rewritten):
                    print(f"[rewrite] Rewritten query: '{message}' → '{rewritten}'")
                    return rewritten
                
                # Attempt repair if invalid
                repaired = repair_rewrite(message, rewritten)
                if rewrite_is_valid(message, repaired):
                    print(f"[rewrite] Rewritten query: '{rewritten}' → Repaired: '{repaired}'")
                    return repaired

                return message

            except google_exceptions.ResourceExhausted:
                if attempt < MAX_RETRIES - 1:
                    time.sleep((2 ** attempt) * 1)
                    continue
                return message
            except Exception:
                return message

    def build_retrieval_query(self, message: str, history: str) -> str:
        """Build query for retrieval (rewrite if history exists)."""
        return self.rewrite_query(message, history) if history else message

    def answer_question(self, question: str, history: str = "") -> tuple[str, dict]:
        """Answer a question using RAG pipeline."""
        
        if is_team_query(question) and self.check_close_team_name(question):
            print("[answer_question] Detected close team name match in query")
            question = convert_to_close_token_match(question, TEAM_INDICATORS) or question

        # Build retrieval query (rewrite if history exists)
        retrieval_query = self.build_retrieval_query(question, history)
        print(f"[query] user='{question}' → retrieval='{retrieval_query}'")

        # Retrieve relevant documents
        results = self.retrieve(retrieval_query)
        
        if not results:
            return "Sorry, I could not find any relevant NBA stats information to answer your question.", {}
        
        is_team = is_team_query(question)
        
        # Handle name-only queries with disambiguation (BUT NOT FOR TEAM QUERIES)
        if self.is_simple_name_query(question) and not is_team:
            print("[name_only] Applying player disambiguation logic")
            matches = strong_name_matches(question, results, min_jaccard=MIN_JACCARD_NAME_MATCH)

            # Exact match - lock onto that player
            exact = [m for m in matches if is_exact_name_match(question, m[2].get("player_name", ""))]
            if exact:
                target_pid = exact[0][2].get("player_id")
                results = [r for r in results 
                        if r[2].get("player_id") == target_pid 
                        and r[2].get("doc_type") in ["player_profile", "player_career"]]
                print(f"[name_only] Exact match found: player_id={target_pid}")

            else:
                # Multiple strong matches - disambiguate
                unique_pids = list({m[2].get("player_id") for m in matches if m[2].get("player_id") is not None})
                if len(unique_pids) >= 2:
                    print(f"[name_only] Disambiguation needed: {len(unique_pids)} players")
                    return self.disambiguation_message(matches), {}

                # Single strong match - lock onto it
                if len(unique_pids) == 1:
                    target_pid = unique_pids[0]
                    results = [r for r in results 
                            if r[2].get("player_id") == target_pid 
                            and r[2].get("doc_type") in ["player_profile", "player_career"]]
                    print(f"[name_only] Single match: player_id={target_pid}")
        elif is_team:
            print("[team_query] Skipping player disambiguation, keeping team docs")

        # Extract metadata for response
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

        # Format context and generate answer
        context = self.format_context(results)
        print(f"[context] Using {len(results)} documents")
        print(f"[context] {context[:500]}...")
        
        prompt = self.generate_prompt(context, retrieval_query)
        answer, answer_metadata = self.ask_gemini(prompt, metadata)
        
        return answer, answer_metadata

    def format_context(self, results) -> str:
        """Format retrieved documents into context string."""
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