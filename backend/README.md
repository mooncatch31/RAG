
# Backend — WandAI RAG + Auto-Enrichment

This backend powers the WandAI RAG + Auto-Enrichment platform, providing document ingestion, semantic search, conversational Q&A, auto-enrichment, and feedback APIs. It is built with FastAPI, PostgreSQL, Pinecone, and supports both local transformer and OpenAI models.

---

## Features

- **Document Ingestion:** Extract, chunk, embed, and upsert documents for semantic retrieval
- **Semantic Search:** Pinecone vector DB, local transformer embeddings (default), OpenAI optional
- **Conversational Q&A:** Context-aware answers via OpenAI LLM (non-stream)
- **Auto-Enrichment:** Google Custom Search for trusted web content on low-confidence answers
- **Feedback:** Per-document reputation, atomic upsert, influences retrieval
- **RESTful API:** All endpoints under `/api/*`

---

## Technology Stack

- **Framework:** Python 3.10+ with FastAPI
- **Database:** PostgreSQL (SQLAlchemy ORM)
- **Vector Store:** Pinecone
- **Embeddings:** Local transformer (default), OpenAI, or other providers
- **LLM:** OpenAI (non-stream completions)
- **Enrichment:** Google Custom Search (CSE)

---

## Setup & Installation

### Prerequisites
- Python 3.10–3.12
- PostgreSQL 13+
- Pinecone account & index (auto-created if needed)
- (Optional) OpenAI API key
- (Optional) Google CSE API key + CX

### Installation

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/Scripts/activate
pip install -U pip
pip install -r requirements.txt
cp .env.example .env  # Edit .env with your settings
```

### Database
- Ensure PostgreSQL is running and the user/database in `.env` exists.
- Run migrations if needed (see Alembic setup).

### Running the API

```bash
uvicorn app.main:app --reload --port 8000
```

---

## API Endpoints (Selected)

- `GET /api/health` — Health summary
- `POST /api/upload` — Upload & ingest documents
- `POST /api/ask` — Ask a question (non-stream)
- `GET /api/documents` — List/search/filter documents
- `GET /api/documents/{doc_id}` — Document details
- `GET /api/documents/{doc_id}/chunks` — Chunk previews
- `POST /api/documents/{doc_id}/reindex` — Reindex document
- `DELETE /api/documents/{doc_id}` — Delete document
- `POST /api/feedback` — Submit feedback

---

## Database Schema (Core Tables)

- **documents:** id, workspace_id, filename, mime, bytes, storage_uri, file_sha256, status, meta(jsonb), created/updated
- **chunks:** id, document_id, idx, text, token_count, sha256, page_start, page_end
- **queries:** id, workspace_id, question, answer, confidence, missing_info[], suggested_enrichment[], used_chunk_ids[]
- **feedback:** id, query_id, rating(-1|0|1), comment
- **document_reputation:** (workspace_id, document_id), up_count, down_count, score

---

## Typical Workflow

1. **Upload:** Validate, dedupe, extract, chunk, embed, upsert to Pinecone
2. **Ask:** Embed query, retrieve top-K, build context, call LLM, auto-enrich if needed
3. **Feedback:** Update feedback and document reputation

---

## Extensibility

- Add new embedding providers (Ollama, etc.)
- Add new enrichment sources (docs.python.org, *.gov, etc.)
- Reranker/cross-encoder for improved retrieval
- Alembic migrations for schema evolution
