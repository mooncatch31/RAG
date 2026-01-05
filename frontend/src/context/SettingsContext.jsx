import React, { createContext, useContext, useMemo, useState, useEffect } from 'react'

const SettingsContext = createContext(null)

export function SettingsProvider({ children }) {
  const [apiKey, setApiKey] = useState(localStorage.getItem('openai_api_key') || '')
  const [apiBase, setApiBase] = useState(
    localStorage.getItem('api_base') || process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000'
  )

  useEffect(() => {
    localStorage.setItem('openai_api_key', apiKey || '')
  }, [apiKey])

  useEffect(() => {
    localStorage.setItem('api_base', apiBase || '')
  }, [apiBase])

  const value = useMemo(() => ({ apiKey, setApiKey, apiBase, setApiBase }), [apiKey, apiBase])

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>
}

export function useSettings() {
  const ctx = useContext(SettingsContext)
  if (!ctx) throw new Error('useSettings must be used inside SettingsProvider')
  return ctx
}
