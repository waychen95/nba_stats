# chatbot/retrieval.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

import re
import faiss
import pickle

from chatbot.utils import detect_season
from chatbot.classify import is_team_query, is_simple_name_query

@dataclass(frozen=True)
class Doc:
    score: float
    text: str
    meta: dict

class FaissStore:
    def __init__(self, index_path: str, docs_path: str, metas_path: str):
        self.index = faiss.read_index(index_path)
        with open(docs_path, "rb") as f:
            self.docs = pickle.load(f)
        with open(metas_path, "rb") as f:
            self.metas = pickle.load(f)

        if len(self.docs) != len(self.metas):
            raise RuntimeError("docs.pkl and metas.pkl length mismatch")

    def latest_team_season(self, team_id: int) -> str | None:
        seasons = []
        for meta in self.metas:
            if meta.get("doc_type") in ("roster", "roster_simple") and meta.get("team_id") == team_id:
                s = meta.get("season")
                if isinstance(s, str) and re.match(r"^\d{4}-\d{2}$", s):
                    seasons.append(s)
        return max(seasons) if seasons else None

    def search(
        self,
        qv,
        query: str,
        doc_type_pref: list[str],
        top_k: int = 5,
        prefetch_k: int = 50,
    ) -> list[Doc]:
        is_roster = "roster" in doc_type_pref
        is_team = ("team" in doc_type_pref) or ("team_coach" in doc_type_pref)
        is_name_only = is_simple_name_query(query)

        if is_name_only:
            prefetch_k = max(prefetch_k, 50)
            top_k = max(top_k, 8)

        D, I = self.index.search(qv, prefetch_k)
        season = detect_season(query)

        candidates: list[tuple[float, int, str, dict]] = []
        for score, idx in zip(D[0], I[0]):
            if idx < 0 or idx >= len(self.docs):
                continue
            candidates.append((float(score), int(idx), self.docs[idx], self.metas[idx]))

        if doc_type_pref and "other" not in doc_type_pref:
            boosted = []
            for score, idx, text, meta in candidates:
                if meta.get("doc_type", "") in doc_type_pref:
                    score = min(score * 1.4, 1.0)
                boosted.append((score, idx, text, meta))
            candidates = boosted

        if season:
            season_filtered = [c for c in candidates if c[3].get("season") == season]
            if len(season_filtered) >= 2:
                candidates = season_filtered
                print(f"[filter] season={season}: {len(season_filtered)} docs")

        if is_roster and season is None:
            roster_cands = [c for c in candidates if c[3].get("doc_type") in ("roster", "roster_simple")]
            if roster_cands:
                top_team_id = max(
                    (c[3].get("team_id") for c in roster_cands),
                    key=lambda tid: sum(1 for rc in roster_cands if rc[3].get("team_id") == tid),
                )
                latest = self.latest_team_season(int(top_team_id))
                if latest:
                    candidates = [c for c in roster_cands if c[3].get("team_id") == top_team_id and c[3].get("season") == latest]
                    print(f"[filter] roster default season={latest}")

        if doc_type_pref and "other" not in doc_type_pref:
            type_filtered = [c for c in candidates if c[3].get("doc_type") in doc_type_pref]
            if (is_name_only or is_team or is_roster) and len(type_filtered) >= 1:
                candidates = type_filtered
            elif len(type_filtered) >= 3:
                candidates = type_filtered

        seen: set[str] = set()
        final: list[Doc] = []
        for score, _idx, text, meta in sorted(candidates, key=lambda x: x[0], reverse=True):
            key = str(meta.get("id") or text[:120])
            if key in seen:
                continue
            seen.add(key)
            final.append(Doc(score=score, text=text, meta=meta))
            if len(final) >= top_k:
                break

        return final
