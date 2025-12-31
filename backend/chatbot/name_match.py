# chatbot/name_match.py
from __future__ import annotations
from chatbot.utils import last_token, name_jaccard, normalize_text
from chatbot.config import RE_POS, RE_TEAM

def is_exact_name_match(query: str, player_name: str) -> bool:
    return normalize_text(query) == normalize_text(player_name)

def strong_name_matches(query: str, docs, min_jaccard: float = 0.6):
    q_last = last_token(query)
    out = []
    for d in docs:
        meta = d.meta
        if meta.get("doc_type") != "player_profile":
            continue
        pname = meta.get("player_name", "")
        if not pname:
            continue

        if is_exact_name_match(query, pname):
            out.append((d, 1.0))
            continue

        p_last = last_token(pname)
        jac = name_jaccard(query, pname)
        if (q_last and p_last and q_last == p_last) or jac >= min_jaccard:
            out.append((d, jac))
    return out

def disambiguation_message(matches, limit: int = 5) -> str:
    options = []
    seen = set()

    for d, _jac in matches:
        meta = d.meta
        text = d.text
        pid = meta.get("player_id")
        name = meta.get("player_name", "Unknown")
        if pid in seen:
            continue
        seen.add(pid)

        position = ""
        team = ""
        
        m_pos = RE_POS.search(text or "")
        if m_pos:
            position = m_pos.group(1).strip()

        m_team = RE_TEAM.search(text or "")
        if m_team:
            team = m_team.group(1).strip()

        extra = [x for x in [position, team] if x]
        options.append(f"- {name}" + (f" [{', '.join(extra)}]" if extra else ""))

        if len(options) >= limit:
            break

    if not options:
        return "Sorry, I need more information to identify the player. Please provide the full name or team."

    return (
        "Which one did you mean?\n"
        + "\n".join(options)
        + "\n\nReply with the full name, or add a hint like team, position, or season."
    )
