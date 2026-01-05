import axios from 'axios'

const DEFAULT_BASE = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000'

function getBase() {
  try {
    return localStorage.getItem('api_base') || DEFAULT_BASE
  } catch {
    return DEFAULT_BASE
  }
}

export async function uploadFiles(files, { apiKey } = {}, onProgress) {
  const url = `${getBase()}/api/upload`
  const form = new FormData()
  for (const f of files) form.append('files', f)

  const res = await axios.post(url, form, {
    headers: {
      'Content-Type': 'multipart/form-data',
      ...(apiKey ? { 'X-OpenAI-Key': apiKey } : {})
    },
    onUploadProgress: (e) => {
      if (typeof onProgress === 'function' && e.total) onProgress(e.loaded / e.total)
    },
    transformResponse: (r) => r
  })

  try { return typeof res.data === 'string' ? JSON.parse(res.data) : res.data }
  catch { return res.data }
}

export async function askOnce({ query, history, auto_enrich }, { apiKey } = {}) {
  const url = `${getBase()}/api/ask`
  const res = await axios.post(url, { query, history, auto_enrich }, {
    headers: {
      'Content-Type': 'application/json',
      ...(apiKey ? { 'X-OpenAI-Key': apiKey } : {})
    }
  })
  return res.data
}

export async function listDocuments({ q = '', status = '', limit = 50, offset = 0 } = {}) {
  const base = getBase()
  const params = new URLSearchParams()
  if (q) params.set('q', q)
  if (status) params.set('status', status)
  params.set('limit', String(limit))
  params.set('offset', String(offset))
  const res = await axios.get(`${base}/api/documents?${params.toString()}`)
  return res.data
}

export async function getDocument(docId) {
  const res = await axios.get(`${getBase()}/api/documents/${docId}`)
  return res.data
}

export async function listDocumentChunks(docId, { limit = 50, offset = 0, include_text = false } = {}) {
  const params = new URLSearchParams()
  params.set('limit', String(limit))
  params.set('offset', String(offset))
  if (include_text) params.set('include_text', 'true')
  const res = await axios.get(`${getBase()}/api/documents/${docId}/chunks?${params.toString()}`)
  return res.data
}

export async function reindexDocuments(payload = {}, { apiKey } = {}) {
  const res = await axios.post(`${getBase()}/api/reindex`, payload, {
    headers: {
      'Content-Type': 'application/json',
      ...(apiKey ? { 'X-OpenAI-Key': apiKey } : {})
    }
  })
  return res.data
}

export async function reindexOneDocument(docId, { clearFirst = true, force = true } = {}, { apiKey } = {}) {
  const params = new URLSearchParams()
  if (clearFirst) params.set('clear_first', 'true')
  if (force) params.set('force', 'true')
  const res = await axios.post(`${getBase()}/api/documents/${docId}/reindex?${params.toString()}`, {}, {
    headers: {
      'Content-Type': 'application/json',
      ...(apiKey ? { 'X-OpenAI-Key': apiKey } : {})
    }
  })
  return res.data
}

export async function deleteDocument(docId, { clearVectors = true } = {}) {
  const params = new URLSearchParams()
  if (clearVectors) params.set('clear_vectors', 'true')
  const res = await axios.delete(`${getBase()}/api/documents/${docId}?${params.toString()}`)
  return res.data
}

export async function sendFeedback({ query_id, rating, comment = '' }) {
  const res = await axios.post(`${getBase()}/api/feedback`, { query_id, rating, comment }, {
    headers: { 'Content-Type': 'application/json' }
  })
  return res.data
}