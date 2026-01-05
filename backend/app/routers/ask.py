from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Tuple

from app.db.session import get_db
from app.db import crud
from app.deps import workspace_header, openai_key_header
from app.config import settings

from app.services.rag import retrieve_topk, build_context_block, map_confidence
from app.services.answer_fallback import extractive_answer
from app.services.enrich import auto_enrich
from app.services.rag import origin_summary

router = APIRouter()


def _call_llm_json(
    *,
    standalone: str,
    context_block: str,
    openai_key: str | None,
) -> Dict[str, Any] | None:
    key = openai_key or settings.OPENAI_API_KEY
    if not key:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=key)
        system = (
            "You are a retrieval-augmented assistant. Use ONLY the provided context to answer. "
            "If insufficient, say what is missing. Cite as [1],[2],… referring to the Context."
        )
        user = (
            f"Standalone question:\n{standalone}\n\nContext:\n{context_block}\n\n"
            "Return a JSON object with keys: answer, confidence (high|medium|low), "
            "missing_info (array of strings), suggested_enrichment (array of strings)."
        )
        resp = client.chat.completions.create(
            model=settings.CHAT_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        import json

        return json.loads(resp.choices[0].message.content)
    except Exception:
        return None


def _make_out(
    *,
    query_id: str,
    answer: str,
    confidence: str,
    missing_info: List[str],
    suggested_enrichment: List[str],
    citations: List[Dict[str, Any]],
    enrichment_meta: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    out = {
        "query_id": query_id,
        "answer": answer,
        "confidence": confidence,
        "missing_info": missing_info,
        "suggested_enrichment": suggested_enrichment,
        "citations": citations,
        "origin": origin_summary(citations)
    }
    if enrichment_meta:
        out["enrichment"] = enrichment_meta
    return out


def _persist_query(db: Session, qrow, out: Dict[str, Any]) -> None:
    conf_map = {"low": 0.2, "medium": 0.6, "high": 0.9}
    used_chunk_ids = [
        c["chunk_id"] for c in out.get("citations", []) if "chunk_id" in c
    ]
    crud.update_query(
        db,
        qrow.id,
        answer=out.get("answer", ""),
        confidence=conf_map.get(out.get("confidence", "medium"), 0.5),
        missing_info=out.get("missing_info") or [],
        suggested_enrichment=out.get("suggested_enrichment") or [],
        used_chunk_ids=used_chunk_ids,
    )

def _first_pass_answer(
    *,
    db: Session,
    workspace: str,
    standalone: str,
    openai_key: str | None,
) -> Tuple[List[Dict[str, Any]], str, Dict[str, Any]]:
    matches, rows, avg_score = retrieve_topk(
        db, query_text=standalone, workspace=workspace, api_key=None
    )

    if not rows:
        data = {
            "answer": "I couldn’t find relevant information in your uploaded documents.",
            "confidence": "low",
            "missing_info": ["Documents that cover this topic", standalone],
            "suggested_enrichment": ["Upload more domain-relevant files"],
        }
        citations: List[Dict[str, Any]] = []
        return citations, "low", data, avg_score

    ctx_rows = rows[: settings.MAX_CONTEXT_CHUNKS]  # (you decided to skip MMR)
    context_block, citations = build_context_block(ctx_rows, db=db)

    data = _call_llm_json(
        standalone=standalone, context_block=context_block, openai_key=openai_key
    )
    if not data:
        data = {
            "answer": extractive_answer(standalone, ctx_rows),
            "confidence": map_confidence(avg_score, len(ctx_rows)),
            "missing_info": ["More comprehensive sources may be required", standalone],
            "suggested_enrichment": [
                "Enable auto-enrichment or upload additional documents"
            ],
        }

    conf = data.get("confidence")
    if conf not in {"high", "medium", "low"}:
        data["confidence"] = map_confidence(avg_score, len(ctx_rows))

    return citations, data["confidence"], data, avg_score

def _maybe_enrich_and_retry(
    *,
    db: Session,
    workspace: str,
    standalone: str,
    data: Dict[str, Any],
    citations: List[Dict[str, Any]],
    openai_key: str | None,
    auto_enrich_flag: bool,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], Dict[str, Any] | None]:
    if not auto_enrich_flag:
        return data, citations, None

    topics = data.get("missing_info") or []
    if not topics:
        topics = [standalone]

    added_ids = auto_enrich(
        db=db,
        workspace=workspace,
        topics=topics,
        openai_key=openai_key or settings.OPENAI_API_KEY,
        max_docs=settings.AUTO_ENRICH_MAX_DOCS,
        max_per_topic=settings.AUTO_ENRICH_MAX_PER_TOPIC,
    )
    if not added_ids:
        return data, citations, {"added_docs": 0}

    matches2, rows2, avg2 = retrieve_topk(
        db, query_text=standalone, workspace=workspace, api_key=None
    )
    if not rows2:
        return data, citations, {"added_docs": len(added_ids)}
    ctx_rows2 = rows2[: settings.MAX_CONTEXT_CHUNKS]
    context_block2, citations2 = build_context_block(ctx_rows2, db=db)
    print("topics:", topics)
    data2 = _call_llm_json(
        standalone=standalone, context_block=context_block2, openai_key=openai_key
    )
    if not data2:
        data2 = {
            "answer": extractive_answer(standalone, ctx_rows2),
            "confidence": map_confidence(avg2, len(ctx_rows2)),
            "missing_info": data.get("missing_info", []),
            "suggested_enrichment": data.get("suggested_enrichment", []),
        }
    conf2 = data2.get("confidence")
    if conf2 not in {"high", "medium", "low"}:
        data2["confidence"] = map_confidence(avg2, len(ctx_rows2))

    return data2, citations2, {"added_docs": len(added_ids)}

@router.post("/ask")
def ask(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    workspace: str = Depends(workspace_header),
    openai_key: str | None = Depends(openai_key_header),
):
    query_raw: str = (payload.get("query") or "").strip()
    history: List[Dict[str, str]] = payload.get("history") or []
    if not query_raw:
        raise HTTPException(400, "Query is required.")

    standalone = crud.create_query(db, workspace_id=workspace, question=query_raw)
    citations, conf_str, data, avg_score = _first_pass_answer(
        db=db, workspace=workspace, standalone=standalone, openai_key=openai_key
    )

    auto_enrich_requested = bool(
        (payload.get("auto_enrich") or False) and settings.AUTO_ENRICH_ENABLED
    )

    distinct_docs = len(
        {c.get("document_id") for c in citations if c.get("document_id")}
    )
    has_missing_info = bool(data.get("missing_info"))

    should_enrich = auto_enrich_requested and (
        conf_str == "low"
        or (avg_score is not None and avg_score < settings.AUTO_ENRICH_MIN_CONF)
        or distinct_docs < 1
        or has_missing_info
    )

    if should_enrich:
        print("Auto-enriching...", auto_enrich_requested, conf_str, avg_score, distinct_docs, has_missing_info)
        data, citations, enrich_meta = _maybe_enrich_and_retry(
            db=db,
            workspace=workspace,
            standalone=standalone,
            data=data,
            citations=citations,
            openai_key=openai_key,
            auto_enrich_flag=True,
        )
    else:
        enrich_meta = None

    out = _make_out(
        query_id=str(qrow.id),
        answer=data.get("answer", ""),
        confidence=data.get("confidence", "medium"),
        missing_info=data.get("missing_info", []) or [],
        suggested_enrichment=data.get("suggested_enrichment", []) or [],
        citations=citations,
        enrichment_meta=enrich_meta
    )

    _persist_query(db, qrow, out)
    return JSONResponse(out)
