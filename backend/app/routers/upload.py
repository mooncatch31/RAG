# app/routers/upload.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from typing import List
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import settings
from app.db.session import get_db
from app.db import models
from app.deps import workspace_header, openai_key_header
from app.services.extract import extract_from_bytes
from app.services.chunker import chunk_text
from app.services.embedding import embedding_dimension
from app.services.pinecone_client import ensure_index
from app.services.vectorize import vectorize_and_upsert
from app.utils.files import ensure_dir, sha256_bytes

router = APIRouter()

DATA_DIR = Path("data/uploads")
ensure_dir(DATA_DIR)

@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    workspace: str = Depends(workspace_header),
    openai_key: str | None = Depends(openai_key_header),
    mode: str = Query("dedupe", regex="^(dedupe|version|reindex)$"),
):
    if not files:
        raise HTTPException(400, "No files provided.")
    if len(files) > settings.MAX_FILES:
        raise HTTPException(413, f"Too many files. Limit is {settings.MAX_FILES}.")

    provider = (settings.EMBEDDING_PROVIDER or "local").lower()
    can_vectorize = True
    if provider == "openai" and not openai_key:
        # Without a key, we cannot call OpenAI for embeddings.
        can_vectorize = False

    results: list[dict] = []
    total_chunks = 0

    # Only ensure the index if we are going to upsert vectors
    if can_vectorize:
        ensure_index(embedding_dimension())

    workspace_dir = DATA_DIR / workspace
    ensure_dir(workspace_dir)

    for f in files:
        # ---- 0) Read + size guard
        content = await f.read()
        size_mb = len(content) / (1024 * 1024)
        if size_mb > settings.MAX_UPLOAD_MB:
            results.append({
                "filename": f.filename,
                "status": "failed",
                "error": f"File too large ({size_mb:.1f} MB). Limit is {settings.MAX_UPLOAD_MB} MB."
            })
            continue

        file_hash = sha256_bytes(content)

        if mode in ("dedupe", "reindex"):
            existing = (
                db.query(models.Document)
                  .filter(models.Document.workspace_id == workspace,
                          models.Document.file_sha256 == file_hash)
                  .order_by(models.Document.created_at.desc())
                  .first()
            )
            if existing:
                if mode == "reindex":
                    chunks = (
                        db.query(models.Chunk)
                          .filter(models.Chunk.document_id == existing.id)
                          .order_by(models.Chunk.idx)
                          .all()
                    )
                    if not chunks:
                        results.append({
                            "id": str(existing.id),
                            "filename": existing.filename,
                            "status": "no_chunks",
                            "duplicate_of": str(existing.id)
                        })
                        continue

                    if can_vectorize:
                        written = vectorize_and_upsert(
                            workspace=workspace,
                            document_id=str(existing.id),
                            filename=existing.filename,
                            chunks=chunks,
                            openai_key=openai_key,  # only used when provider='openai'
                        )
                        existing.status = "processed"
                        db.add(existing); db.commit()
                        results.append({
                            "id": str(existing.id),
                            "filename": existing.filename,
                            "status": "reindexed",
                            "chunks": len(chunks),
                            "vectors": written,
                            "duplicate_of": str(existing.id)
                        })
                    else:
                        results.append({
                            "id": str(existing.id),
                            "filename": existing.filename,
                            "status": "skipped_no_key",
                            "duplicate_of": str(existing.id)
                        })
                else:
                    chunk_count = db.query(func.count(models.Chunk.id)) \
                                    .filter(models.Chunk.document_id == existing.id) \
                                    .scalar() or 0
                    results.append({
                        "id": str(existing.id),
                        "filename": existing.filename,
                        "status": "duplicate",
                        "chunks": int(chunk_count),
                        "duplicate_of": str(existing.id)
                    })
                continue

        dest_path = workspace_dir / f.filename
        dest_path.write_bytes(content)

        doc = models.Document(
            workspace_id=workspace,
            filename=f.filename,
            mime=f.content_type or "application/octet-stream",
            bytes=len(content),
            storage_uri=str(dest_path),
            file_sha256=file_hash,
            status="uploaded",
            meta={}
        )
        db.add(doc); db.commit(); db.refresh(doc)

        try:
            extracted = extract_from_bytes(content, f.filename, f.content_type)

            parts = chunk_text(
                extracted.text,
                size_tokens=settings.CHUNK_SIZE_TOKENS,
                overlap_tokens=settings.CHUNK_OVERLAP_TOKENS
            )

            chunk_rows: list[models.Chunk] = []
            for i, p in enumerate(parts):
                chunk_rows.append(models.Chunk(
                    document_id=doc.id,
                    idx=i,
                    text=p["text"],
                    token_count=p["token_count"],
                    sha256=p["sha256"],
                    page_start=None,
                    page_end=None,
                ))
            db.add_all(chunk_rows); db.commit()

            total_chunks += len(chunk_rows)

            if can_vectorize:
                written = vectorize_and_upsert(
                    workspace=workspace,
                    document_id=str(doc.id),
                    filename=doc.filename,
                    chunks=chunk_rows,
                    openai_key=openai_key,
                )
                doc.status = "processed"
                db.add(doc); db.commit()
                results.append({
                    "id": str(doc.id),
                    "filename": doc.filename,
                    "chunks": len(chunk_rows),
                    "vectors": written,
                    "status": doc.status
                })
            else:
                results.append({
                    "id": str(doc.id),
                    "filename": doc.filename,
                    "chunks": len(chunk_rows),
                    "vectors": 0,
                    "status": "uploaded"
                })

        except Exception as e:
            doc.status = "failed"
            db.add(doc); db.commit()
            results.append({
                "id": str(doc.id),
                "filename": doc.filename,
                "status": "failed",
                "error": str(e)
            })

    return {
        "documents": results,
        "total_chunks": total_chunks,
        "vectorized": can_vectorize,
        "workspace": workspace
    }
