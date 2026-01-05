import React, { useEffect, useState } from 'react'
import { listDocumentChunks, getDocument } from '../utils/api'
import { notify } from '../utils/notify'

export default function ChunkViewerModal({ open, docId, onClose }) {
  const [doc, setDoc] = useState(null)
  const [chunks, setChunks] = useState([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [limit] = useState(20)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    async function loadHead() {
      if (!open || !docId) return
      try { setDoc(await getDocument(docId)) } catch { setDoc(null) }
    }
    loadHead()
  }, [open, docId])

  useEffect(() => {
    async function loadPage() {
      if (!open || !docId) return
      setLoading(true)
      try {
        const data = await listDocumentChunks(docId, { limit, offset, include_text: false })
        setChunks(data.chunks || [])
        setTotal(data.total || 0)
      } catch (e) {
        notify.error(e?.message || 'Failed to load chunks')
      } finally {
        setLoading(false)
      }
    }
    loadPage()
  }, [open, docId, limit, offset])

  if (!open) return null

  const pages = Math.ceil((total || 0) / limit) || 1
  const page = Math.floor(offset / limit) + 1

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white w-full max-w-3xl rounded-2xl shadow-xl p-5 max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Chunks — {doc?.filename || docId}</h2>
            <p className="text-xs text-gray-500">{total} chunks</p>
          </div>
          <button onClick={onClose} className="px-2 py-1 rounded-lg border hover:bg-gray-50">Close</button>
        </div>

        <div className="mt-3 flex-1 overflow-y-auto border rounded-xl">
          {chunks.length === 0 && !loading && (
            <div className="p-6 text-center text-sm text-gray-500">No chunks</div>
          )}
          {chunks.map((c) => (
            <div key={c.chunk_id} className="border-b p-3">
              <div className="text-xs text-gray-500">#{c.idx}{(Number.isFinite(c.page_start) && Number.isFinite(c.page_end)) ? ` • p.${c.page_start}-${c.page_end}` : ''} • {c.token_count} tok</div>
              <div className="mt-1 text-sm text-gray-800">{c.preview}</div>
            </div>
          ))}
          {loading && <div className="p-4 text-sm text-gray-500">Loading…</div>}
        </div>

        <div className="mt-3 flex items-center justify-between">
          <div className="text-xs text-gray-500">Page {page} / {pages}</div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setOffset(Math.max(0, offset - limit))}
              disabled={page <= 1}
              className="px-2 py-1 rounded border text-sm disabled:opacity-50"
            >Prev</button>
            <button
              onClick={() => setOffset(Math.min((pages - 1) * limit, offset + limit))}
              disabled={page >= pages}
              className="px-2 py-1 rounded border text-sm disabled:opacity-50"
            >Next</button>
          </div>
        </div>
      </div>
    </div>
  )
}
