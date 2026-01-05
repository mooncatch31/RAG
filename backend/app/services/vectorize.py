import time, logging
from typing import Iterable
from app.config import settings
from app.services.embedding import embed_batch
from app.services.pinecone_client import get_index
from app.services.embed_gate import embed_gate

log = logging.getLogger("app.vectorize")

def make_vector_id(workspace: str, document_id: str, chunk_id: str) -> str:
    return f"{workspace}:{document_id}:{chunk_id}"

def vectorize_and_upsert(
    *,
    workspace: str,
    document_id: str,
    filename: str,
    chunks: Iterable,   # list of ORM Chunk rows
    openai_key: str | None,          # only used if provider='openai'
) -> int:
    texts = [c.text for c in chunks]
    if not texts: return 0

    idx = get_index()
    vectors: list[dict] = []
    B = settings.EMBEDDING_BATCH
    delay = max(0.0, settings.EMBED_REQUEST_DELAY_S)

    for start in range(0, len(texts), B):
        batch_txt = texts[start:start+B]
        with embed_gate():
            embs = embed_batch(batch_txt, model=settings.EMBEDDING_MODEL, api_key=openai_key)
        for row, vec in zip(chunks[start:start+B], embs):
            vectors.append({
                "id": make_vector_id(workspace, document_id, str(row.id)),
                "values": vec,
                "metadata": {
                    "workspace_id": workspace,
                    "document_id": document_id,
                    "chunk_id": str(row.id),
                    "idx": row.idx,
                    "filename": filename,
                }
            })
        if delay: time.sleep(delay)

    U = 100
    for s in range(0, len(vectors), U):
        idx.upsert(vectors=vectors[s:s+U], namespace=workspace)

    log.info("upserted %d vectors for doc %s", len(vectors), document_id)
    return len(vectors)
