import React, { useEffect, useMemo, useState } from 'react'
import {
  listDocuments,
  reindexDocuments,
  reindexOneDocument,
  deleteDocument
} from '../utils/api'
import { useSettings } from '../context/SettingsContext'
import ConfirmDialog from './ConfirmDialog'
import ChunkViewerModal from './ChunkViewerModal'
import { notify } from '../utils/notify'

function StatusPill({ status }) {
  const s = (status || '').toLowerCase()
  const map = {
    processed: 'bg-green-100 text-green-800 border-green-200',
    uploaded: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    failed: 'bg-red-100 text-red-800 border-red-200',
    reindexed: 'bg-blue-100 text-blue-800 border-blue-200',
    duplicate: 'bg-gray-100 text-gray-700 border-gray-200',
    'no_chunks': 'bg-gray-100 text-gray-700 border-gray-200',
    'skipped_already_processed': 'bg-gray-100 text-gray-700 border-gray-200'
  }
  return <span className={`text-xs px-2 py-1 rounded-full border ${map[s] || 'bg-gray-100 text-gray-700 border-gray-200'}`}>{status}</span>
}

function bytesToMB(b) { return (b / (1024 * 1024)).toFixed(2) }

export default function DocumentsManager() {
  const { apiKey } = useSettings()
  const [rows, setRows] = useState([])
  const [total, setTotal] = useState(0)
  const [q, setQ] = useState('')
  const [status, setStatus] = useState('')
  const [offset, setOffset] = useState(0)
  const [limit] = useState(50)
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState({})

  const [viewDocId, setViewDocId] = useState(null)
  const [confirm, setConfirm] = useState({ open: false, ids: [] })

  async function fetchDocs() {
    setLoading(true)
    try {
      const data = await listDocuments({ q, status, limit, offset })
      setRows(data.documents || [])
      setTotal(data.total || 0)
      setSelected({})
    } catch (e) {
      notify.error(e?.message || 'Failed to load documents')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchDocs() }, [q, status, offset, limit])

  const allSelected = useMemo(() => rows.length > 0 && rows.every(r => selected[r.id]), [rows, selected])
  function toggleAll() { setSelected(allSelected ? {} : Object.fromEntries(rows.map(r => [r.id, true]))) }
  function toggleOne(id) { setSelected(prev => ({ ...prev, [id]: !prev[id] })) }

  async function doReindexPending() {
    notify.promise(
      reindexDocuments({ all_pending: true, clear_first: true }, { apiKey })
        .then(res => { fetchDocs(); return `Reindexed ${res.updated} document(s)` }),
      { loading: 'Reindexing pending…' }
    )
  }

  async function doReindexSelected() {
    const ids = Object.keys(selected).filter(k => selected[k])
    if (ids.length === 0) return notify.info('Select at least one document')
    notify.promise(
      reindexDocuments({ document_ids: ids, force: true, clear_first: true }, { apiKey })
        .then(res => { fetchDocs(); return `Reindexed ${res.updated} document(s)` }),
      { loading: 'Reindexing selected…' }
    )
  }

  async function doReindexOne(id) {
    notify.promise(
      reindexOneDocument(id, { clearFirst: true, force: true }, { apiKey })
        .then(() => { fetchDocs(); return 'Reindexed' }),
      { loading: 'Reindexing…' }
    )
  }

  function askDeleteSelected() {
    const ids = Object.keys(selected).filter(k => selected[k])
    if (ids.length === 0) return notify.info('Select at least one document')
    setConfirm({ open: true, ids })
  }

  async function doDeleteSelected(clearVectors = true) {
    const ids = confirm.ids
    setConfirm({ open: false, ids: [] })
    notify.promise(
      Promise.allSettled(ids.map(id => deleteDocument(id, { clearVectors }))).then(results => {
        const ok = results.filter(r => r.status === 'fulfilled').length
        const fail = results.length - ok
        fetchDocs()
        return `Deleted ${ok} • Failed ${fail}`
      }),
      { loading: 'Deleting…', success: (msg) => msg }
    )
  }

  const pages = Math.ceil(total / limit) || 1
  const page = Math.floor(offset / limit) + 1

  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <h3 className="font-semibold text-gray-800">Documents</h3>
        <div className="flex items-center gap-2">
          <input
            value={q}
            onChange={(e) => { setOffset(0); setQ(e.target.value) }}
            placeholder="Search by filename…"
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
          />
          <select
            value={status}
            onChange={(e) => { setOffset(0); setStatus(e.target.value) }}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="">All statuses</option>
            <option value="processed">Processed</option>
            <option value="uploaded">Uploaded</option>
            <option value="failed">Failed</option>
          </select>
          <button onClick={fetchDocs} className="px-3 py-2 rounded-lg border hover:bg-gray-50 text-sm">Refresh</button>
          <button onClick={doReindexPending} className="px-3 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 text-sm">Reindex Pending</button>
          <button onClick={doReindexSelected} className="px-3 py-2 rounded-lg bg-green-600 text-white hover:bg-green-700 text-sm">Reindex Selected</button>
          <button onClick={askDeleteSelected} className="px-3 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700 text-sm">Delete Selected</button>
        </div>
      </div>

      <div className="mt-3 border rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr className="text-left text-gray-600">
              <th className="px-3 py-2 w-8">
                <input type="checkbox" checked={allSelected} onChange={toggleAll} />
              </th>
              <th className="px-3 py-2">Filename</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Chunks</th>
              <th className="px-3 py-2">Size (MB)</th>
              <th className="px-3 py-2">Created</th>
              <th className="px-3 py-2">Updated</th>
              <th className="px-3 py-2 w-56">Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && !loading && (
              <tr><td className="px-3 py-6 text-center text-gray-500" colSpan={8}>No documents</td></tr>
            )}
            {rows.map((r) => (
              <tr key={r.id} className="border-t">
                <td className="px-3 py-2 align-top">
                  <input type="checkbox" checked={!!selected[r.id]} onChange={() => toggleOne(r.id)} />
                </td>
                <td className="px-3 py-2 align-top font-medium text-gray-900">{r.filename}</td>
                <td className="px-3 py-2 align-top"><StatusPill status={r.status} /></td>
                <td className="px-3 py-2 align-top">{r.chunks ?? '-'}</td>
                <td className="px-3 py-2 align-top">{bytesToMB(r.bytes)}</td>
                <td className="px-3 py-2 align-top">{new Date(r.created_at).toLocaleString()}</td>
                <td className="px-3 py-2 align-top">{new Date(r.updated_at).toLocaleString()}</td>
                <td className="px-3 py-2 align-top">
                  <div className="flex items-center gap-2 flex-wrap">
                    <button
                      onClick={() => setViewDocId(r.id)}
                      className="px-2 py-1 rounded border hover:bg-gray-50 text-xs"
                    >
                      View
                    </button>
                    <button
                      onClick={() => doReindexOne(r.id)}
                      className="px-2 py-1 rounded border hover:bg-gray-50 text-xs"
                    >
                      Reindex
                    </button>
                    <button
                      onClick={() => setConfirm({ open: true, ids: [r.id] })}
                      className="px-2 py-1 rounded border hover:bg-gray-50 text-xs text-red-700"
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="mt-3 flex items-center justify-between">
        <div className="text-xs text-gray-500">Total: {total}</div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setOffset(Math.max(0, offset - limit))}
            disabled={page <= 1}
            className="px-2 py-1 rounded border text-sm disabled:opacity-50"
          >Prev</button>
          <div className="text-sm text-gray-600">Page {page} / {pages}</div>
          <button
            onClick={() => setOffset(Math.min((pages - 1) * limit, offset + limit))}
            disabled={page >= pages}
            className="px-2 py-1 rounded border text-sm disabled:opacity-50"
          >Next</button>
        </div>
      </div>

      {/* Modals */}
      <ChunkViewerModal open={!!viewDocId} docId={viewDocId} onClose={() => setViewDocId(null)} />
      <ConfirmDialog
        open={confirm.open}
        title="Delete selected documents?"
        message="This will remove the documents and (by default) their vectors from Pinecone. This action cannot be undone."
        confirmLabel="Delete"
        danger
        onCancel={() => setConfirm({ open: false, ids: [] })}
        onConfirm={() => doDeleteSelected(true)}
      />
    </div>
  )
}
