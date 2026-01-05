import React from 'react'

export default function ConfirmDialog({
  open,
  title = 'Are you sure?',
  message = '',
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  onConfirm,
  onCancel,
  danger = false
}) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white w-full max-w-md rounded-2xl shadow-xl p-5">
        <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
        {message && <p className="text-sm text-gray-600 mt-2">{message}</p>}

        <div className="mt-5 flex items-center justify-end gap-2">
          <button onClick={onCancel} className="px-3 py-2 rounded-lg border hover:bg-gray-50 text-sm">
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            className={`px-3 py-2 rounded-lg text-sm text-white ${
              danger ? 'bg-red-600 hover:bg-red-700' : 'bg-brand-600 hover:bg-brand-700'
            }`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
