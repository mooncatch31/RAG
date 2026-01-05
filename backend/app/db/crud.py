from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db import models

def create_document(db: Session, **kwargs) -> models.Document:
    obj = models.Document(**kwargs)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

def create_query(db: Session, *, workspace_id: str, question: str) -> models.Query:
    obj = models.Query(workspace_id=workspace_id, question=question)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

def update_query(db: Session, query_id, **fields):
    q = db.get(models.Query, query_id)
    if not q: return None
    for k, v in fields.items():
        setattr(q, k, v)
    db.add(q); db.commit(); db.refresh(q); return q

def get_chunks_by_ids(db: Session, ids: list) -> list[models.Chunk]:
    if not ids: return []
    return db.query(models.Chunk).filter(models.Chunk.id.in_(ids)).all()

def upsert_document_reputation(db: Session, workspace_id: str, document_id):
    rep = db.execute(
        select(models.DocumentReputation).where(
            models.DocumentReputation.workspace_id == workspace_id,
            models.DocumentReputation.document_id == document_id
        )
    ).scalar_one_or_none()
    if not rep:
        rep = models.DocumentReputation(workspace_id=workspace_id, document_id=document_id, up_count=0, down_count=0, score=0.0)
        db.add(rep)
    return rep

def add_feedback(db: Session, query_id, rating: int, comment: str | None = None):
    fb = models.Feedback(query_id=query_id, rating=rating, comment=comment)
    db.add(fb); db.commit(); db.refresh(fb); return fb