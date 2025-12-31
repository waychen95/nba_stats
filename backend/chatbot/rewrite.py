# chatbot/rewrite.py
from __future__ import annotations
from chatbot.utils import normalize_text
from chatbot.config import REWRITE_PROMPT_TEMPLATE, MAX_RETRIES
from google.api_core import exceptions as google_exceptions
import time

def rewrite_is_valid(original: str, rewritten: str) -> bool:
    o = normalize_text(original)
    r = normalize_text(rewritten)
    if not r:
        return False
    o_toks = o.split()
    r_toks = set(r.split())
    return all(t in r_toks for t in o_toks)

def repair_rewrite(original: str, rewritten: str) -> str:
    o_toks = normalize_text(original).split()
    r_toks = normalize_text(rewritten).split()
    r_set = set(r_toks)

    missing = [t for t in o_toks if t not in r_set]
    if not missing:
        return rewritten.strip()

    return " ".join((r_toks + missing)).strip()

class QueryRewriter:
    def __init__(self, gemini_client):
        self.client = gemini_client

    def rewrite(self, message: str, history: str) -> str:
        if not (history or "").strip():
            return message

        prompt = REWRITE_PROMPT_TEMPLATE.format(history=history, message=message)

        for attempt in range(MAX_RETRIES):
            try:
                res = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={"max_output_tokens": 100, "temperature": 0.0},
                )
                rewritten = (res.text or "").strip()
                print(f"[original message] '{message}'")
                if not rewritten:
                    return message

                if rewrite_is_valid(message, rewritten):
                    print(f"[rewrite] '{message}' → '{rewritten}'")
                    return rewritten

                repaired = repair_rewrite(message, rewritten)
                if rewrite_is_valid(message, repaired):
                    print(f"[rewrite] repaired '{rewritten}' → '{repaired}'")
                    return repaired

                return message

            except google_exceptions.ResourceExhausted:
                if attempt < MAX_RETRIES - 1:
                    time.sleep((2 ** attempt) * 1)
                    continue
                return message
            except Exception:
                return message
