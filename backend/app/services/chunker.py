import hashlib, tiktoken

def _enc():
    try: return tiktoken.get_encoding("o200k_base")
    except Exception: return tiktoken.get_encoding("cl100k_base")

def chunk_text(text: str, size_tokens: int, overlap_tokens: int):
    enc = _enc()
    toks = enc.encode(text)
    n, i, out = len(toks), 0, []
    while i < n:
        j = min(n, i + size_tokens)
        piece = enc.decode(toks[i:j])
        sha = hashlib.sha256(piece.encode("utf-8")).hexdigest()
        out.append({"text": piece, "token_count": j - i, "sha256": sha})
        if j == n: break
        i = max(0, j - overlap_tokens)
    return out
