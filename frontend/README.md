# WandAI RAG + Auto-Enrichment — Frontend

This is the frontend for the WandAI RAG + Auto-Enrichment platform. It provides a modern, user-friendly interface for uploading documents, managing knowledge, and chatting with an AI assistant powered by your own data and trusted web sources.

---

## Features

- **File Uploading:** Drag & drop or file picker, multi-file support, upload progress, and notifications
- **Document Management:** List, search, filter, preview chunks, reindex, and delete documents
- **Chat Interface:** ChatGPT-style UI, markdown answers, citations, confidence/origin pills, and feedback (thumbs up/down)
- **Settings Modal:** Configure API base URL, OpenAI API key (stored locally), and auto-enrichment toggle
- **Persistence:** API base, key, and enrichment setting are stored in localStorage

---

## Getting Started

### Prerequisites
- Node.js 18+
- npm

### Installation & Running

```bash
cd frontend
npm install
# Set API base URL (default: http://localhost:8000)
echo "REACT_APP_API_BASE_URL=http://localhost:8000" > .env
npm start
# App: http://localhost:3000
```

---

## Environment Variables

- `REACT_APP_API_BASE_URL` — Backend API URL (default: http://localhost:8000)

---

## Usage Notes

- **API Key:** The OpenAI API key is stored in your browser and sent as `X-OpenAI-Key` only to your backend.
- **Auto-Enrichment:** Enable in settings to allow the backend to fetch and ingest trusted web content for low-confidence answers.
- **Feedback:** Use thumbs up/down to help improve document reputation and answer quality.