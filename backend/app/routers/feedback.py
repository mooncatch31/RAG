# app/routers/feedback.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import cast, Float, literal

from app.db.session import get_db
from app.db import models
from app.deps import workspace_header

router = APIRouter()


class FeedbackIn(BaseModel):
    query_id: UUID
    rating: int = Field(..., ge=-1, le=1)
    comment: Optional[str] = None


@router.post("/feedback")
def submit_feedback(
    payload: FeedbackIn,
    db: Session = Depends(get_db),
    workspace: str = Depends(workspace_header),
):
    q = db.get(models.Query, payload.query_id)
    if not q or q.workspace_id != workspace:
        raise HTTPException(404, "Query not found")

    fb = models.Feedback(
        query_id=payload.query_id,
        rating=payload.rating,
        comment=payload.comment or None,
    )
    db.add(fb)

    used_chunks: List[UUID] = list(set(q.used_chunk_ids or []))  # dedupe
    if not used_chunks:
        db.commit()
        return {"ok": True, "updated": 0, "feedback_id": str(fb.id)}

    rows = (
        db.query(models.Chunk.document_id)
        .filter(models.Chunk.id.in_(used_chunks))
        .all()
    )
    doc_ids = list({r.document_id for r in rows})
    if not doc_ids:
        db.commit()
        return {"ok": True, "updated": 0, "feedback_id": str(fb.id)}

    up = 1 if payload.rating > 0 else 0
    down = 1 if payload.rating < 0 else 0

    table = models.DocumentReputation.__table__
    values = [
        {
            "workspace_id": workspace,
            "document_id": did,
            "up_count": up,
            "down_count": down,
            "score": 0.0,
        }
        for did in doc_ids
    ]

    if up or down:
        stmt = pg_insert(table).values(values)

        new_up = table.c.up_count + stmt.excluded.up_count
        new_down = table.c.down_count + stmt.excluded.down_count

        score_expr = cast(new_up - new_down, Float) / cast(
            new_up + new_down + literal(3), Float
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=[table.c.workspace_id, table.c.document_id],
            set_={
                "up_count": new_up,
                "down_count": new_down,
                "score": score_expr,
            },
        )

        db.execute(stmt)

    db.commit()

    return {
        "ok": True,
        "updated": len(doc_ids) if (up or down) else 0,
        "feedback_id": str(fb.id),
    }
