import hashlib, time, requests
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db import models
from app.utils.files import sha256_bytes
from app.services.vectorize import vectorize_and_upsert
from app.services.chunker import chunk_text
from app.config import settings
from urllib.parse import urlparse

def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def _google_cse_search(topic: str) -> List[dict]:
    if not settings.GOOGLE_CSE_API_KEY or not settings.GOOGLE_CSE_CX:
        return []
    params = {"key": settings.GOOGLE_CSE_API_KEY, "cx": settings.GOOGLE_CSE_CX, "q": topic, "num": 3}
    r = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    items = data.get("items", []) or []
    out = []
    for it in items:
        out.append({"title": it.get("title"), "url": it.get("link")})
    return out

def _fetch_url_text(url: str) -> Optional[str]:
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        txt = r.text
        import re
        text = re.sub(r"<[^>]+>", " ", txt)
        text = " ".join(text.split())
        return text if len(text) > 500 else None
    except Exception:
        return None

def _ingest_text_as_document(
    *,
    db: Session,
    workspace: str,
    title: str,
    url: str,
    text: str,
    openai_key: str | None
) -> Optional[models.Document]:
    h = _hash_text(text)
    existing = (
        db.query(models.Document)
          .filter(models.Document.workspace_id == workspace,
                  models.Document.file_sha256 == h)
          .first()
    )
    if existing:
        return existing

    doc = models.Document(
        workspace_id=workspace,
        filename=title or url,
        mime="text/plain",
        bytes=len(text.encode("utf-8")),
        storage_uri=url,
        file_sha256=h,
        status="uploaded",
        meta={"source": "web", "provider": "web", "url": url, "domain": urlparse(url).netloc}
    )
    db.add(doc); db.commit(); db.refresh(doc)

    parts = chunk_text(text, size_tokens=settings.CHUNK_SIZE_TOKENS, overlap_tokens=settings.CHUNK_OVERLAP_TOKENS)
    chunk_rows: List[models.Chunk] = []
    for i, p in enumerate(parts):
        chunk_rows.append(models.Chunk(
            document_id=doc.id,
            idx=i,
            text=p["text"],
            token_count=p["token_count"],
            sha256=p["sha"],
            page_start=None, page_end=None
        ) if "sha" in p else models.Chunk(
            document_id=doc.id,
            idx=i,
            text=p["text"],
            token_count=p["token_count"],
            sha256=_hash_text(p["text"]),
            page_start=None, page_end=None
        ))
    db.add_all(chunk_rows); db.commit()

    vectorize_and_upsert(
        workspace=workspace,
        document_id=str(doc.id),
        filename=doc.filename,
        chunks=chunk_rows,
        openai_key=openai_key
    )
    doc.status = "processed"
    db.add(doc); db.commit()
    return doc

def auto_enrich(
    *,
    db: Session,
    workspace: str,
    topics: List[str],
    openai_key: str | None,
    max_docs: int,
    max_per_topic: int
) -> List[str]:
    added: List[str] = []
    budget = max_docs
    for topic in topics:
        if budget <= 0:
            break
        per_topic = 0
        for it in _google_cse_search(topic):
            if budget <= 0 or per_topic >= max_per_topic:
                break
            txt = _fetch_url_text(it["url"])
            if not txt: continue
            doc = _ingest_text_as_document(
                db=db, workspace=workspace,
                title=it["title"], url=it["url"], text=txt, openai_key=openai_key
            )
            if doc:
                added.append(str(doc.id)); budget -= 1; per_topic += 1

    return added
