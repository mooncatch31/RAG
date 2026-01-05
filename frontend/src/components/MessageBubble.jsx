import React, { useMemo } from 'react'
import PillWithTooltip from './PillWithTooltip.jsx'
import { sendFeedback } from '../utils/api'
import { notify } from '../utils/notify'
import { useState } from 'react'

function ConfidencePill({ level = 'medium' }) {
  const map = {
    high: 'bg-green-100 text-green-800 border-green-200',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    low: 'bg-red-100 text-red-800 border-red-200'
  }
  const label = (level || 'medium').toLowerCase()
  return (
    <span className={`inline-block text-xs px-2 py-0.5 rounded-full border ${map[label] || map.medium}`}>
      confidence: {label}
    </span>
  )
}

function Thumbs({ queryId }) {
  const [sent, setSent] = useState(false)
  if (!queryId || sent) return null
  async function vote(v) {
    try {
      await sendFeedback({ query_id: queryId, rating: v, comment: '' })
      setSent(true)
      notify.success(v > 0 ? 'Thanks for the feedback!' : 'Got it — we’ll improve this.')
    } catch (e) {
      notify.error('Failed to send feedback')
    }
  }
  return (
    <div className="flex items-center gap-2 text-gray-500">
      <button onClick={() => vote(1)} className="px-2 py-1 rounded border hover:bg-gray-50 text-xs">👍</button>
      <button onClick={() => vote(-1)} className="px-2 py-1 rounded border hover:bg-gray-50 text-xs">👎</button>
    </div>
  )
}

export default function MessageBubble({ role = 'assistant', content = '', meta = null }) {
  const isUser = role === 'user'

  const { missingInfo, enrichment, sources, origin, originTone, originLabel, originTip } = useMemo(() => {
    const mi = Array.isArray(meta?.missing_info) ? meta.missing_info.filter(Boolean) : []
    const se = Array.isArray(meta?.suggested_enrichment) ? meta.suggested_enrichment.filter(Boolean) : []
    const files = Array.isArray(meta?.citations)
      ? Array.from(new Set(meta.citations.map(c => c.filename).filter(Boolean)))
      : []
    const or = meta?.origin || { mode: 'local', web: 0, local: 0, web_domains: [] }
    const orTone = or.mode === 'enriched' ? 'blue' : 'green'
    const orLabel = or.mode === 'enriched' ? 'Enriched' : 'Local'
    const orTip = or.mode === 'enriched'
      ? (<div>
        <div className="font-medium mb-1">Web domains</div>
        <ul className="list-disc ml-4 space-y-1">
          {(or.web_domains || []).map((d, i) => <li key={i}>{d}</li>)}
        </ul>
      </div>)
      : (<div>Answer uses only your uploaded documents.</div>)
    return { missingInfo: mi, enrichment: se, sources: files, origin: or, originTone: orTone, originLabel: orLabel, originTip: orTip }
  }, [meta])

  if (!content) return null

  return (
    <div className={`w-full flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
      <div
        className={`max-w-[80%] whitespace-pre-wrap ${isUser
          ? 'bg-brand-600 text-white'
          : 'bg-white text-gray-800 border border-gray-200'
          } rounded-2xl px-4 py-3 shadow-sm`}
      >
        <div className="prose-chat">{content}</div>

        {!isUser && meta && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <div className="flex flex-wrap items-center gap-2">
              <ConfidencePill level={meta.confidence} />
              <PillWithTooltip label={originLabel} count={origin.web || undefined} tone={originTone} tooltip={originTip} />

              {missingInfo.length > 0 && (
                <PillWithTooltip
                  label="Missing info"
                  count={missingInfo.length}
                  tone="yellow"
                  tooltip={
                    <ul className="list-disc ml-4 space-y-1">
                      {missingInfo.map((m, i) => <li key={i}>{m}</li>)}
                    </ul>
                  }
                />
              )}

              {enrichment.length > 0 && (
                <PillWithTooltip
                  label="Suggested enrichment"
                  count={enrichment.length}
                  tone="blue"
                  tooltip={
                    <ul className="list-disc ml-4 space-y-1">
                      {enrichment.map((m, i) => <li key={i}>{m}</li>)}
                    </ul>
                  }
                />
              )}

              {sources.length > 0 && (
                <PillWithTooltip
                  label="Sources"
                  count={sources.length}
                  tone="green"
                  tooltip={
                    <ol className="list-decimal ml-4 space-y-1">
                      {sources.map((f, i) => <li key={i}>{f}</li>)}
                    </ol>
                  }
                />
              )}

              {meta?.query_id && <Thumbs queryId={meta.query_id} />}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
