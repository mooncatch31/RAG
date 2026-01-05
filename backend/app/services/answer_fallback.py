import re
from typing import List
from app.db.models import Chunk

def _sentences(text: str) -> List[str]:
    parts = re.split(r'(?<=[.!?])\s+|\n+', text.strip())
    return [p.strip() for p in parts if p.strip()]

def extractive_answer(query: str, ctx_rows: List[Chunk], max_chars: int = 1200) -> str:
    """
    Cheap, deterministic fallback: take top context chunks and return
    their most informative first sentences until we hit max_chars.
    """
    out: List[str] = []
    remaining = max_chars
    for ch in ctx_rows:
        sents = _sentences(ch.text)
        if not sents:
            continue
        # prefer first sentence; you can add naive keyword scoring here
        pick = sents[0]
        if len(pick) > remaining:
            pick = pick[:remaining]
        out.append(pick)
        remaining -= len(pick) + 1
        if remaining <= 0:
            break
    if not out:
        return "No relevant snippets found in your uploaded documents."

    return "Extractive answer (no LLM due to quota):\n\n" + "\n\n".join(out)
