from statistics import mean
from uuid import UUID
from sqlalchemy.orm import Session
from app.config import settings
from app.db import crud, models
from app.services.embedding import embed_batch
from app.services.pinecone_client import get_index
from urllib.parse import urlparse

def retrieve_topk(db: Session, *, query_text: str, workspace: str, api_key: str | None, topk: int | None = None, boost: float = 0.1):
    topk = topk or settings.TOPK
    q_vec = embed_batch([query_text], model=settings.EMBEDDING_MODEL, api_key=api_key)[0]
    idx = get_index()
    res = idx.query(namespace=workspace, vector=q_vec, top_k=topk, include_metadata=True)
    matches = getattr(res, "matches", None) or res.get("matches", []) or []

    chunk_ids, scores, doc_ids = [], [], []
    for m in matches:
        meta = m["metadata"] if isinstance(m, dict) else m.metadata
        cid = meta.get("chunk_id"); did = meta.get("document_id")
        if cid and did:
            chunk_ids.append(UUID(cid)); doc_ids.append(UUID(did))
            scores.append(float(m.get("score", getattr(m, "score", 0.0))))

    rows = crud.get_chunks_by_ids(db, chunk_ids)
    by_id = {str(r.id): r for r in rows}

    reps = db.query(models.DocumentReputation).filter(
        models.DocumentReputation.workspace_id == workspace,
        models.DocumentReputation.document_id.in_(set(doc_ids))
    ).all()
    rep_map = {str(r.document_id): float(r.score or 0.0) for r in reps}

    ordered = []
    for m in matches:
        meta = m["metadata"] if isinstance(m, dict) else m.metadata
        cid = meta.get("chunk_id"); did = meta.get("document_id")
        row = by_id.get(str(cid))
        if not row: continue
        base = float(m.get("score", getattr(m, "score", 0.0)))
        prior = rep_map.get(str(did), 0.0)
        final = base + boost * prior
        ordered.append((final, row))

    ordered.sort(key=lambda x: x[0], reverse=True)
    ranked_rows = [r for _, r in ordered]
    avg_score = sum(scores[:5]) / max(1, min(5, len(scores)))
    return matches, ranked_rows, avg_score

def select_context(rows, max_chunks: int):
    if not rows: return []
    picked, seen = [], set()
    for r in rows:
        if len(picked) >= max_chunks: break
        if r.document_id not in seen:
            picked.append(r); seen.add(r.document_id)
    if len(picked) < max_chunks:
        for r in rows:
            if len(picked) >= max_chunks: break
            if r not in picked: picked.append(r)
    return picked

def build_context_block(rows, db=None, filename_by_chunk: dict[str, str] | None = None):
    names_by_doc, meta_by_doc = {}, {}

    if db and rows:
        from app.db import models as db_models
        doc_ids = list({r.document_id for r in rows})
        pairs = (
            db.query(db_models.Document.id, db_models.Document.filename, db_models.Document.meta)
              .filter(db_models.Document.id.in_(doc_ids))
              .all()
        )
        for did, fname, meta in pairs:
            names_by_doc[str(did)] = fname
            meta_by_doc[str(did)] = meta or {}

    blocks, citations = [], []
    filename_by_chunk = filename_by_chunk or {}

    for i, ch in enumerate(rows, start=1):
        did = str(ch.document_id)
        fname = (
            names_by_doc.get(did)
            or filename_by_chunk.get(str(ch.id))
            or getattr(getattr(ch, "document", None), "filename", None)
            or "source"
        )
        meta = meta_by_doc.get(did, {})
        source = (meta.get("source") or "local").lower()
        url = meta.get("url")
        dom = urlparse(url).netloc if (url and source == "web") else None

        page_str = ""
        if isinstance(ch.page_start, int) and isinstance(ch.page_end, int):
            page_str = f", p.{ch.page_start}-{ch.page_end}"

        header = f"[{i}] ({fname}{page_str})"
        blocks.append(f"{header}\n{(ch.text or '').strip()}")

        citations.append({
            "n": i,
            "filename": fname,
            "document_id": did,
            "chunk_id": str(ch.id),
            "page_start": ch.page_start,
            "page_end": ch.page_end,
            "origin": "web" if source == "web" else "local",
            "domain": dom,
            "url": url if source == "web" else None,
        })

    return "\n\n".join(blocks), citations

def map_confidence(avg_score: float, used_count: int) -> str:   
    if avg_score >= 0.35 and used_count >= 3: return "high"
    if avg_score >= 0.25 and used_count >= 2: return "medium"
    return "low"

def doc_name_map(db, rows):
    from app.db import models
    ids = list({r.document_id for r in rows})
    if not ids: return {}
    pairs = db.query(models.Document.id, models.Document.filename).filter(models.Document.id.in_(ids)).all()
    return {str(doc_id): fname for (doc_id, fname) in pairs}

def origin_summary(citations: list[dict]) -> dict:
    local = sum(1 for c in citations if c.get("origin") == "local")
    web = sum(1 for c in citations if c.get("origin") == "web")
    web_domains = sorted({c.get("domain") for c in citations if c.get("domain")})
    mode = "enriched" if web > 0 else "local"
    return {"mode": mode, "local": local, "web": web, "web_domains": web_domains}