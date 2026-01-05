import React, { useCallback, useRef, useState } from 'react'
import { uploadFiles } from '../utils/api.js'
import { useSettings } from '../context/SettingsContext.jsx'
import { notify } from '../utils/notify'

export default function FileUploader() {
  const { apiKey } = useSettings()
  const [files, setFiles] = useState([])
  const [isDragging, setIsDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const inputRef = useRef(null)

  const onDrop = useCallback((ev) => {
    ev.preventDefault()
    setIsDragging(false)
    const dropped = Array.from(ev.dataTransfer.files || [])
    if (dropped.length) {
      setFiles((prev) => [...prev, ...dropped])
    }
  }, [])

  const onChoose = useCallback((ev) => {
    const selected = Array.from(ev.target.files || [])
    if (selected.length) setFiles((p) => [...p, ...selected])
    ev.target.value = ''
  }, [])

  function removeAt(idx) {
    setFiles((prev) => prev.filter((_, i) => i !== idx))
  }

  async function startUpload() {
    if (!files.length) return
    setUploading(true)
    setProgress(0)
    try {
      await uploadFiles(files, { apiKey }, (pct) => setProgress(pct))
      setFiles([])
      setProgress(1)
    } catch (e) {
      notify.error(e?.message || 'Upload failed')
    } finally {
      setUploading(false)
      setTimeout(() => setProgress(0), 800)
    }
  }

  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm">
      <h3 className="font-semibold text-gray-800">Upload Documents</h3>
      <p className="text-sm text-gray-500">PDF, DOCX, TXT. Multiple files supported.</p>

      <div
        onDragOver={(e) => {
          e.preventDefault()
          setIsDragging(true)
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
        className={`mt-3 border-2 border-dashed rounded-2xl p-6 text-center transition-colors ${isDragging ? 'border-brand-600 bg-brand-50' : 'border-gray-300'}`}>
        <div className="text-gray-600">
          Drag & drop files here, or{' '}
          <button
            onClick={() => inputRef.current?.click()}
            className="text-brand-700 underline">
            browse
          </button>
        </div>
        <input
          type="file"
          multiple
          ref={inputRef}
          onChange={onChoose}
          className="hidden"
          accept=".pdf,.txt,.doc,.docx,.md"
        />
      </div>

      {files.length > 0 && (
        <div className="mt-3">
          <ul className="divide-y bg-gray-50 rounded-xl border">
            {files.map((f, i) => (
              <li key={i} className="flex items-center justify-between px-3 py-2">
                <div className="min-w-0">
                  <p className="truncate font-medium text-gray-800">{f.name}</p>
                  <p className="text-xs text-gray-500">{(f.size / 1024 / 1024).toFixed(3)} MB</p>
                </div>
                <button
                  disabled={uploading}
                  onClick={() => removeAt(i)}
                  className="text-sm text-red-600 hover:underline">
                  remove
                </button>
              </li>
            ))}
          </ul>

          {uploading && (
            <div className="mt-2">
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-brand-600 transition-all"
                  style={{ width: `${Math.round(progress * 100)}%` }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Uploading… {Math.round(progress * 100)}%
              </p>
            </div>
          )}

          <div className="mt-3 flex justify-end">
            <button
              onClick={startUpload}
              disabled={uploading}
              className="px-4 py-2 rounded-xl bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-50">
              {uploading ? 'Uploading…' : 'Upload'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
