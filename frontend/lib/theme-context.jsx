'use client'

import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { useAuth } from './auth-context'

const ThemeContext = createContext(null)
const STORAGE_KEY = 'timbre.theme'
const THEMES = ['system', 'light', 'dark']

// Resolve a preference to the concrete palette to apply ('light' | 'dark').
function resolve(pref) {
  if (pref === 'dark' || pref === 'light') return pref
  if (typeof window !== 'undefined' && window.matchMedia) {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }
  return 'light'
}

function applyTheme(pref) {
  if (typeof document !== 'undefined') {
    document.documentElement.setAttribute('data-theme', resolve(pref))
  }
}

export function ThemeProvider({ children }) {
  const { user, updateProfile } = useAuth()
  // The *preference* ('system' | 'light' | 'dark'). Starts 'system' for SSR; the
  // inline pre-paint script in layout.jsx already set the correct data-theme, and the
  // init effect below syncs React state to the stored value without a flash.
  const [theme, setTheme] = useState('system')
  const [resolved, setResolved] = useState('light')

  // Sync state from localStorage on mount (never read storage during render → no SSR drift).
  useEffect(() => {
    let pref = 'system'
    try { pref = localStorage.getItem(STORAGE_KEY) || 'system' } catch {}
    if (!THEMES.includes(pref)) pref = 'system'
    setTheme(pref)
    setResolved(resolve(pref))
  }, [])

  // While following the system, track live OS light/dark switches.
  useEffect(() => {
    if (theme !== 'system' || typeof window === 'undefined' || !window.matchMedia) return
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const onChange = () => { applyTheme('system'); setResolved(resolve('system')) }
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [theme])

  // Adopt a logged-in user's saved theme (the account is source of truth across devices).
  useEffect(() => {
    const saved = user?.settings?.theme
    if (saved && THEMES.includes(saved) && saved !== theme) {
      setTheme(saved)
      setResolved(resolve(saved))
      applyTheme(saved)
      try { localStorage.setItem(STORAGE_KEY, saved) } catch {}
    }
  }, [user]) // eslint-disable-line react-hooks/exhaustive-deps

  const setThemePref = useCallback((pref) => {
    if (!THEMES.includes(pref)) return
    setTheme(pref)
    setResolved(resolve(pref))
    applyTheme(pref)
    try { localStorage.setItem(STORAGE_KEY, pref) } catch {}
    if (user) updateProfile({ settings: { theme: pref } }).catch(() => {})
  }, [user, updateProfile])

  return (
    <ThemeContext.Provider value={{ theme, resolved, setThemePref, THEMES }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}
