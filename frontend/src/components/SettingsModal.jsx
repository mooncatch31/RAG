import React, { useState, useEffect } from 'react'
import { useSettings } from '../context/SettingsContext.jsx'

export default function SettingsModal({ open, onClose }) {
  const { apiKey, setApiKey, apiBase, setApiBase } = useSettings()
  const [localKey, setLocalKey] = useState(apiKey)
  const [localBase, setLocalBase] = useState(apiBase)
  const [autoEnrich, setAutoEnrich] = useState(JSON.parse(localStorage.getItem('auto_enrich') || 'false'))

  useEffect(() => {
    setLocalKey(apiKey)
    setLocalBase(apiBase)
  }, [apiKey, apiBase, open])

  if (!open) return null

  function save() {
    setApiKey(localKey.trim())
    setApiBase(localBase.trim() || 'http://localhost:8000')
    localStorage.setItem('auto_enrich', JSON.stringify(autoEnrich))
    onClose?.()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white w-full max-w-lg rounded-2xl shadow-xl p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Settings</h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100"
            aria-label="Close">
            ✕
          </button>
        </div>

        <div className="mt-4 space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700">OpenAI API Key</label>
            <input
              type="password"
              placeholder="sk-..."
              value={localKey}
              onChange={(e) => setLocalKey(e.target.value)}
              className="mt-1 w-full rounded-xl border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-600"
            />
            <p className="text-xs text-gray-500 mt-1">Stored securely in your browser via localStorage.</p>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700">Backend Base URL</label>
            <input
              type="text"
              placeholder="http://localhost:8000"
              value={localBase}
              onChange={(e) => setLocalBase(e.target.value)}
              className="mt-1 w-full rounded-xl border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-600"
            />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={autoEnrich} onChange={(e)=>setAutoEnrich(e.target.checked)} />
            Auto-enrich on low confidence
          </label>
        </div>

        <div className="mt-6 flex justify-end gap-2">
          <button onClick={onClose} className="px-4 py-2 rounded-xl border">
            Cancel
          </button>
          <button
            onClick={save}
            className="px-4 py-2 rounded-xl bg-brand-600 text-white hover:bg-brand-700">
            Save
          </button>
        </div>
      </div>
    </div>
  )
}
