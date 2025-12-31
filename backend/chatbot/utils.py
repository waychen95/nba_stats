# chatbot/text_utils.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

from chatbot.config import RE_SEASON_RANGE, RE_YEAR, RE_NON_ALNUM_SPACE, RE_MULTI_SPACE

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

def normalize_text(s: str) -> str:
    s = (s or "").lower().strip()
    s = RE_NON_ALNUM_SPACE.sub(" ", s)
    s = RE_MULTI_SPACE.sub(" ", s).strip()
    return s

def tokens(s: str) -> list[str]:
    return normalize_text(s).split()

def last_token(s: str) -> str:
    toks = tokens(s)
    return toks[-1] if toks else ""

def name_jaccard(a: str, b: str) -> float:
    a_set = set(tokens(a))
    b_set = set(tokens(b))
    if not a_set or not b_set:
        return 0.0
    return len(a_set & b_set) / len(a_set | b_set)

def levenshtein(a: str, b: str) -> int:
    a = a or ""
    b = b or ""
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
