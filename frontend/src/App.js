import React, { useState } from 'react'
import SettingsModal from './components/SettingsModal.jsx'
import FileUploader from './components/FileUploader.jsx'
import Chat from './components/Chat.jsx'
import DocumentsManager from './components/DocumentsManager.jsx'
import { useSettings } from './context/SettingsContext.jsx'

export default function App() {
  const [openSettings, setOpenSettings] = useState(false)
  const [view, setView] = useState('chat')
  const { apiBase } = useSettings()

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 bg-white/80 backdrop-blur border-b">
        <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-brand-600 text-white grid place-items-center font-bold">KB</div>
            <div>
              <h1 className="font-semibold text-gray-900 leading-tight">AI KB Search & Enrichment</h1>
              <p className="text-xs text-gray-500 -mt-0.5">Backend: {apiBase}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setView('chat')}
                className={`px-3 py-1.5 rounded-md text-sm ${view==='chat' ? 'bg-white shadow border' : ''}`}
              >Chat</button>
              <button
                onClick={() => setView('docs')}
                className={`px-3 py-1.5 rounded-md text-sm ${view==='docs' ? 'bg-white shadow border' : ''}`}
              >Documents</button>
            </div>
            <button
              onClick={() => setOpenSettings(true)}
              className="px-3 py-2 rounded-xl border hover:bg-gray-50"
              aria-label="Settings"
            >
              ⚙️ Settings
            </button>
          </div>
        </div>
      </header>

      {view === 'chat' ? (
        <main className="mx-auto max-w-6xl px-4 py-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
          <section className="lg:col-span-1 space-y-6">
            <FileUploader />
            <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm">
              <h3 className="font-semibold text-gray-800">Tips</h3>
              <ul className="list-disc ml-5 mt-2 text-sm text-gray-600 space-y-1">
                <li>Upload domain docs first (PDF/DOCX/TXT).</li>
                <li>Ask concise questions; I’ll cite sources and flag missing info.</li>
                <li>Use Settings to set your OpenAI API key and backend URL.</li>
              </ul>
            </div>
          </section>
          <section className="lg:col-span-2">
            <Chat />
          </section>
        </main>
      ) : (
        <main className="mx-auto max-w-6xl px-4 py-6">
          <DocumentsManager />
        </main>
      )}

      <SettingsModal open={openSettings} onClose={() => setOpenSettings(false)} />
    </div>
  )
}
