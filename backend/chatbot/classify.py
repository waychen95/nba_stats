# chatbot/classify.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence

from chatbot.config import TEAM_INDICATORS, TEAM_ABBREVIATIONS, RE_YEAR
from chatbot.utils import normalize_text, tokens, levenshtein

STAT_WORDS = {"ppg", "rpg", "apg", "stats", "points", "rebounds", "assists"}

def _team_vocab():
    team_tokens = [normalize_text(x) for x in TEAM_INDICATORS]
    team_words = sorted({w for t in team_tokens for w in t.split()})
    team_abbrs = [normalize_text(x) for x in TEAM_ABBREVIATIONS]
    return team_tokens, team_words, team_abbrs

TEAM_TOKENS, TEAM_WORDS, TEAM_ABBRS = _team_vocab()

def close_token_match(token: str, targets: Sequence[str], max_dist: int = 1) -> bool:
    t = normalize_text(token)
    if not t:
        return False
    if t in targets:
        return True

    plural_forms = {
        t + "s",
        t + "es",
        (t[:-1] + "ies") if t.endswith("y") and len(t) > 2 else "",
    }
    if any(p and p in targets for p in plural_forms):
        return True

    for cand in targets:
        if abs(len(t) - len(cand)) > max_dist:
            continue
        if levenshtein(t, cand) <= max_dist:
            return True

    return False

def convert_to_close_token_match(token: str, targets: Sequence[str], max_dist: int = 1) -> str | None:
    t = normalize_text(token)
    if not t:
        return None
    if t in targets:
        return t

    plural_forms = {
        t + "s",
        t + "es",
        (t[:-1] + "ies") if t.endswith("y") and len(t) > 2 else "",
    }
    for p in plural_forms:
        if p and p in targets:
            return p

    for cand in targets:
        if abs(len(t) - len(cand)) > max_dist:
            continue
        if levenshtein(t, cand) <= max_dist:
            return cand
    return None

def is_simple_name_query(query: str) -> bool:
    q = normalize_text(query)

    if RE_YEAR.search(q):
        return False

    intent_keywords = {
        "height", "weight", "born", "birth", "age", "position", "college", "school",
        "country", "coach", "conference", "roster", "season", "stats", "ppg", "rpg",
        "apg", "points", "rebounds", "assists", "career", "average", "totals", "you", "me"
    }

    toks = q.split()
    if any(t in intent_keywords for t in toks):
        return False

    return 1 <= len(toks) <= 3

def is_team_query(query: str, debug: bool = False) -> bool:
    q_norm = normalize_text(query)
    toks = q_norm.split()
    team_keywords = {"coach", "conference", "team", "located"}

    has_team_name = any(ind in q_norm for ind in TEAM_TOKENS)
    has_team_abbr = any(abbr in toks or abbr in q_norm for abbr in TEAM_ABBRS)

    fuzzy_team = False
    if 1 <= len(toks) <= 2:
        fuzzy_team = any(close_token_match(t, TEAM_WORDS, max_dist=1) for t in toks)

    if debug:
        print(f"[is_team_query] has_team_name={has_team_name}, has_team_abbr={has_team_abbr}, fuzzy_team={fuzzy_team}")

    has_team_keyword = any(kw in q_norm for kw in team_keywords)

    if fuzzy_team and not any(w in q_norm for w in STAT_WORDS):
        if debug:
            print(f"[is_team_query] Detected fuzzy team query: '{query}'")
        return True

    player_indicators = {"player", "stats", "ppg", "points", "reb", "rebound", "assist", "fg", "3p", "ft", "plus minus"}
    has_player_indicator = any(pi in q_norm for pi in player_indicators)

    if (has_team_name or has_team_abbr) and (has_team_keyword or not has_player_indicator):
        if debug:
            print(f"[is_team_query] Detected team query: '{query}'")
        return True

    if debug:
        print(f"[is_team_query] Not a team query: '{query}'")
    return False

def check_close_team_name(query: str) -> bool:
    q_norm = normalize_text(query)
    toks = q_norm.split()
    if 1 <= len(toks) <= 2:
        return any(close_token_match(t, TEAM_WORDS, max_dist=1) for t in toks)
    return False
