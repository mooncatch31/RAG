from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from typing import List, Optional

from app.db.session import get_db
from app.db import models
from app.deps import workspace_header, openai_key_header
from app.config import settings
from app.services.embedding import embedding_dimension
from app.services.pinecone_client import ensure_index, get_index
from app.services.vectorize import vectorize_and_upsert

router = APIRouter()

def _doc_or_404(db: Session, workspace: str, doc_id: UUID) -> models.Document:
    doc = db.get(models.Document, doc_id)
    if not doc or doc.workspace_id != workspace:
        raise HTTPException(404, "Document not found")
    return doc

@router.get("/documents")
def list_documents(
    db: Session = Depends(get_db),
    workspace: str = Depends(workspace_header),
    status: Optional[str] = Query(None, regex="^(uploaded|processed|failed)$"),
    q: Optional[str] = Query(None, description="Search by filename (ILIKE)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    base = (
        db.query(
            models.Document.id,
            models.Document.filename,
            models.Document.status,
            models.Document.bytes,
            models.Document.created_at,
            models.Document.updated_at,
            func.count(models.Chunk.id).label("chunks"),
        )
        .outerjoin(models.Chunk, models.Chunk.document_id == models.Document.id)
        .filter(models.Document.workspace_id == workspace)
        .group_by(
            models.Document.id,
            models.Document.filename,
            models.Document.status,
            models.Document.bytes,
            models.Document.created_at,
            models.Document.updated_at,
        )
        .order_by(models.Document.created_at.desc())
    )
    if status:
        base = base.filter(models.Document.status == status)
    if q:
        base = base.filter(models.Document.filename.ilike(f"%{q}%"))

    total = base.count()
    rows = base.offset(offset).limit(limit).all()
    docs = [
        {
            "id": str(r.id),
            "filename": r.filename,
            "status": r.status,
            "bytes": r.bytes,
            "chunks": int(r.chunks or 0),
            "created_at": r.created_at,
            "updated_at": r.updated_at,
        }
        for r in rows
    ]
    return {"total": total, "limit": limit, "offset": offset, "documents": docs}

@router.get("/documents/{doc_id}")
def get_document(
    doc_id: UUID = Path(...),
    db: Session = Depends(get_db),
    workspace: str = Depends(workspace_header),
):
    doc = _doc_or_404(db, workspace, doc_id)
    chunk_count = db.query(func.count(models.Chunk.id)).filter(models.Chunk.document_id == doc.id).scalar() or 0
    return {
        "id": str(doc.id),
        "filename": doc.filename,
        "status": doc.status,
        "bytes": doc.bytes,
        "chunks": int(chunk_count),
        "created_at": doc.created_at,
        "updated_at": doc.updated_at,
        "meta": doc.meta or {},
    }

@router.get("/documents/{doc_id}/chunks")
def list_document_chunks(
    doc_id: UUID = Path(...),
    db: Session = Depends(get_db),
    workspace: str = Depends(workspace_header),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    include_text: bool = Query(False),
):
    _ = _doc_or_404(db, workspace, doc_id)
    q = (
        db.query(models.Chunk)
        .filter(models.Chunk.document_id == doc_id)
        .order_by(models.Chunk.idx)
    )
    total = q.count()
    items = q.offset(offset).limit(limit).all()
    out = []
    for ch in items:
        item = {
            "chunk_id": str(ch.id),
            "idx": ch.idx,
            "page_start": ch.page_start,
            "page_end": ch.page_end,
            "token_count": ch.token_count,
        }
        if include_text:
            item["text"] = ch.text
        else:
            prev = (ch.text or "").strip().replace("\n", " ")
            item["preview"] = (prev[:200] + "…") if len(prev) > 200 else prev
        out.append(item)
    return {"total": total, "limit": limit, "offset": offset, "chunks": out}

@router.post("/documents/{doc_id}/reindex")
def reindex_document(
    doc_id: UUID = Path(...),
    db: Session = Depends(get_db),
    workspace: str = Depends(workspace_header),
    openai_key: str | None = Depends(openai_key_header),
    clear_first: bool = Query(False, description="Delete vectors for this doc before upsert"),
    force: bool = Query(True, description="Re-embed even if already processed"),
):
    doc = _doc_or_404(db, workspace, doc_id)
    ensure_index(embedding_dimension())
    idx = get_index()

    if clear_first:
        idx.delete(filter={"document_id": str(doc.id)}, namespace=workspace)

    chunks = (
        db.query(models.Chunk)
        .filter(models.Chunk.document_id == doc.id)
        .order_by(models.Chunk.idx)
        .all()
    )
    if not chunks:
        raise HTTPException(400, "No chunks to index for this document.")

    vectorize_and_upsert(
        workspace=workspace,
        document_id=str(doc.id),
        filename=doc.filename,
        chunks=chunks,
        openai_key=openai_key,  # used only if provider='openai'
    )
    if force or doc.status != "processed":
        doc.status = "processed"
        db.add(doc); db.commit()
    return {"id": str(doc.id), "filename": doc.filename, "status": doc.status, "chunks": len(chunks)}

@router.post("/reindex")
def reindex_documents(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    workspace: str = Depends(workspace_header),
    openai_key: str | None = Depends(openai_key_header),
):
    ids: List[str] = payload.get("document_ids") or []
    all_pending: bool = bool(payload.get("all_pending"))
    force: bool = bool(payload.get("force"))
    clear_first: bool = bool(payload.get("clear_first"))

    ensure_index(embedding_dimension())
    idx = get_index()

    qy = db.query(models.Document).filter(models.Document.workspace_id == workspace)
    if ids:
        uuids = [UUID(x) for x in ids]
        qy = qy.filter(models.Document.id.in_(uuids))
    elif all_pending:
        qy = qy.filter(models.Document.status.in_(["uploaded", "failed"]))
    else:
        raise HTTPException(400, "Provide 'document_ids' or set 'all_pending': true")

    docs = qy.order_by(models.Document.created_at.desc()).all()
    results, updated = [], 0
    for doc in docs:
        try:
            if clear_first:
                idx.delete(filter={"document_id": str(doc.id)}, namespace=workspace)

            chunks = (
                db.query(models.Chunk)
                .filter(models.Chunk.document_id == doc.id)
                .order_by(models.Chunk.idx)
                .all()
            )
            if not chunks:
                results.append({"id": str(doc.id), "filename": doc.filename, "status": "no_chunks"})
                continue

            if not force and doc.status == "processed":
                results.append({"id": str(doc.id), "filename": doc.filename, "status": "skipped_already_processed"})
                continue

            vectorize_and_upsert(
                workspace=workspace,
                document_id=str(doc.id),
                filename=doc.filename,
                chunks=chunks,
                openai_key=openai_key,
            )
            doc.status = "processed"
            db.add(doc); db.commit()
            updated += 1
            results.append({"id": str(doc.id), "filename": doc.filename, "status": "processed", "chunks": len(chunks)})
        except Exception as e:
            doc.status = "failed"
            db.add(doc); db.commit()
            results.append({"id": str(doc.id), "filename": doc.filename, "status": "failed", "error": str(e)})

    return {"updated": updated, "results": results}

@router.delete("/documents/{doc_id}")
def delete_document(
    doc_id: UUID = Path(...),
    db: Session = Depends(get_db),
    workspace: str = Depends(workspace_header),
    clear_vectors: bool = Query(True, description="Delete Pinecone vectors for this doc"),
):
    doc = _doc_or_404(db, workspace, doc_id)

    if clear_vectors:
        idx = get_index()
        idx.delete(filter={"document_id": str(doc.id)}, namespace=workspace)

    db.delete(doc); db.commit()
    return {"id": str(doc_id), "status": "deleted", "cleared_vectors": clear_vectors}
