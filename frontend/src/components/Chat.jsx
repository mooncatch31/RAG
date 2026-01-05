import React, { useEffect, useRef, useState } from 'react'
import MessageBubble from './MessageBubble.jsx'
import TypingDots from './TypingDots.jsx'
import { askOnce } from '../utils/api.js'
import { useSettings } from '../context/SettingsContext.jsx'

export default function Chat() {
  const { apiKey } = useSettings()
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        'Hi! Upload documents and ask me anything.'
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const listRef = useRef(null)
  const autoEnrich = JSON.parse(localStorage.getItem('auto_enrich') || 'false')

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, isLoading])

  async function send() {
    const query = input.trim()
    if (!query) return
    setInput('')

    const next = [
      ...messages,
      { role: 'user', content: query },
      { role: 'assistant', content: '', meta: null }
    ]
    setMessages(next)
    setIsLoading(true)

    const history = next
      .slice(0, -1)
      .map(({ role, content }) => ({ role, content }))

    try {
      const data = await askOnce({ query, history, auto_enrich: autoEnrich }, { apiKey })
      const answerText = data?.answer || 'No answer.'
      const meta = {
        confidence: data?.confidence || 'medium',
        enrichment: data?.enrichment || {},
        missing_info: data?.missing_info || [],
        suggested_enrichment: data?.suggested_enrichment || [],
        citations: data?.citations || [],
        origin: data?.origin || {},
        query_id: data?.query_id || null
      }

      setMessages(prev => {
        const copy = [...prev]
        const i = copy.length - 1
        copy[i] = { ...copy[i], meta }
        return copy
      })
      await typeOut(answerText)
    } catch (e) {
      await typeOut(`⚠️ ${e?.message || 'Something went wrong.'}`)
    } finally {
      setIsLoading(false)
    }
  }

  async function typeOut(text) {
    const speed = 8
    let i = 0
    function step() {
      i += speed
      setMessages(prev => {
        const copy = [...prev]
        const idx = copy.length - 1
        const prevMeta = copy[idx]?.meta || null
        copy[idx] = { role: 'assistant', content: text.slice(0, i), meta: prevMeta }
        return copy
      })
      if (i < text.length) requestAnimationFrame(step)
    }
    step()
  }

  function onKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div className="bg-white border border-gray-200 rounded-2xl h-[75vh] flex flex-col shadow-sm">
      <div className="px-4 py-3 border-b">
        <h3 className="font-semibold text-gray-800">Chat</h3>
      </div>

      <div ref={listRef} className="flex-1 overflow-y-auto p-4">
        {messages.map((m, idx) => (
          <MessageBubble key={idx} role={m.role} content={m.content} meta={m.meta} />
        ))}
        {isLoading && (
          <div className="w-full flex justify-start mb-3">
            <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 shadow-sm">
              <TypingDots />
            </div>
          </div>
        )}
      </div>

      <div className="p-3 border-t">
        {!apiKey && (
          <div className="mb-2 text-xs bg-yellow-50 border border-yellow-200 text-yellow-800 rounded-lg px-3 py-2">
            No OpenAI API key set. The backend will still try an extractive fallback if configured.
          </div>
        )}
        <div className="flex items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Ask something…"
            rows={2}
            className="flex-1 resize-none rounded-xl border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-600"
          />
          <button
            onClick={send}
            disabled={!input.trim() || isLoading}
            className="px-4 py-2 rounded-xl bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-50">
            Send
          </button>
        </div>
      </div>
    </div>
  )
}
