import os
from typing import List
from app.config import settings

_PROVIDER = os.getenv("EMBEDDING_PROVIDER", settings.EMBEDDING_PROVIDER).lower()

_LOCAL_MODEL = None
_LOCAL_DIM   = None

def _load_local_model():
    global _LOCAL_MODEL, _LOCAL_DIM
    if _LOCAL_MODEL is not None: return _LOCAL_MODEL, _LOCAL_DIM
    from sentence_transformers import SentenceTransformer
    name = settings.EMBEDDING_MODEL
    device = settings.EMBEDDING_DEVICE
    _LOCAL_MODEL = SentenceTransformer(name, device=device)
    _LOCAL_DIM = _LOCAL_MODEL.get_sentence_embedding_dimension()
    return _LOCAL_MODEL, _LOCAL_DIM

def _embed_local(texts: List[str]) -> List[List[float]]:
    model, _ = _load_local_model()
    embs = model.encode(texts,
                        batch_size=settings.EMBEDDING_BATCH,
                        normalize_embeddings=True,
                        convert_to_numpy=True,
                        show_progress_bar=False)
    return [e.tolist() for e in embs]

def embedding_dimension() -> int:
    if _PROVIDER == "local":
        _, dim = _load_local_model()
        return int(dim)
    return int(settings.EMBEDDING_DIM)

def embed_batch(texts: List[str], model: str | None = None, api_key: str | None = None) -> List[List[float]]:
    if not texts: return []
    if _PROVIDER == "local":
        return _embed_local(texts)
    elif _PROVIDER == "ollama":
        import requests
        base = settings.OLLAMA_BASE_URL
        name = settings.EMBEDDING_MODEL
        out = []
        for t in texts:
            r = requests.post(f"{base}/api/embeddings", json={"model": name, "prompt": t}, timeout=60)
            r.raise_for_status()
            out.append(r.json()["embedding"])
        return out
    else:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.embeddings.create(model=model or settings.EMBEDDING_MODEL, input=texts)
        return [d.embedding for d in resp.data]
