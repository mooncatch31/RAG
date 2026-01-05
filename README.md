#   RAG + Auto-Enrichment

**  RAG + Auto-Enrichment** is a modern, full-stack Retrieval-Augmented Generation (RAG) platform designed for practical, real-world document Q&A and enrichment workflows. This project combines a robust backend with a user-friendly frontend, enabling users to upload, manage, and chat with their documents, while leveraging both local and cloud AI capabilities.

---

## Project Overview

  RAG + Auto-Enrichment provides an end-to-end solution for knowledge retrieval and conversational AI over your own documents. The system is built to be:

- **Flexible:** Supports local transformer models for embeddings, with optional OpenAI integration for LLM answers.
- **Extensible:** Auto-enrichment via trusted web sources (Google Custom Search) when local knowledge is insufficient.
- **User-Centric:** Modern chat UI, document management, and feedback mechanisms to improve answer quality over time.

---
## Demo



https://github.com/user-attachments/assets/25673d06-0ca4-4510-8de1-90ecc2133d6f


---

## Key Capabilities

- **Document Upload & Management:** Ingest, chunk, and embed documents for semantic search and retrieval.
- **Conversational Q&A:** Chat interface for asking questions, with context-aware, cited answers.
- **Auto-Enrichment:** Optionally enhance answers with up-to-date web content when confidence is low.
- **Feedback Loop:** User feedback on answers improves document reputation and retrieval quality.

---

## Technology Stack

- **Frontend:** React, Tailwind CSS, Axios
- **Backend:** Python FastAPI, PostgreSQL, Pinecone (vector DB), local transformer models, OpenAI (optional)

> **Technical implementation details and setup instructions are provided in the respective `frontend/README.md` and `backend/README.md` files.**

---

## Typical Workflow

1. **Upload Documents:** Users add files via the web UI. Backend extracts, chunks, and embeds content, storing vectors in Pinecone.
2. **Ask Questions:** Users chat with the system. The backend retrieves relevant document chunks and generates answers using an LLM.
3. **Auto-Enrichment:** If enabled and confidence is low, the system fetches and ingests trusted web content to improve answers.
4. **Feedback:** Users rate answers, influencing future retrievals and document ranking.

---

## Getting Started

See the `frontend/README.md` and `backend/README.md` for environment setup, configuration, and usage instructions.
