import React from 'react'

export default function PillWithTooltip({ label, count, tone = 'gray', tooltip }) {
  const tones = {
    green:  'bg-green-100 text-green-800 border-green-200',
    yellow: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    blue:   'bg-blue-100 text-blue-800 border-blue-200',
    red:    'bg-red-100 text-red-800 border-red-200',
    gray:   'bg-gray-100 text-gray-800 border-gray-200',
  }

  return (
    <div className="relative inline-flex items-center group" tabIndex={0}>
      <span
        className={`inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full border ${tones[tone]} whitespace-nowrap`}
        aria-describedby="pill-tooltip"
      >
        {label}
        {typeof count === 'number' && (
          <span className="inline-flex items-center justify-center min-w-5 h-5 px-1 rounded-full bg-white/60 text-[11px] border border-black/10">
            {count}
          </span>
        )}
      </span>

      {tooltip && (
        <div
          role="tooltip"
          className="pointer-events-none opacity-0 group-hover:opacity-100 group-focus:opacity-100 transition-opacity
                     absolute z-50 -top-2 left-1/2 -translate-x-1/2 -translate-y-full
                     bg-white border border-gray-200 shadow-xl rounded-xl px-3 py-2 text-xs text-gray-700 w-72"
          id="pill-tooltip"
        >
          {tooltip}

          <div className="absolute left-1/2 -bottom-2 -translate-x-1/2 w-3 h-3 rotate-45 bg-white border-l border-t border-gray-200"></div>
        </div>
      )}
    </div>
  )
}
