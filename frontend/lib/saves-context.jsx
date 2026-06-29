'use client'

import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { api } from './api'
import { useAuth } from './auth-context'

const SavesContext = createContext(null)

// The signed-in user's watchlist ("My List") — a set of saved media_ids. Mirrors
// RatingsProvider: loads on login, clears on logout, optimistic add/remove.
export function SavesProvider({ children }) {
  const { user } = useAuth()
  const [saved, setSaved] = useState([]) // [media_id, ...], newest first
  const [error, setError] = useState(false)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let active = true
    setError(false)
    if (user) {
      api.getSaves()
        .then((rows) => { if (active) setSaved(rows.map((r) => r.media_id)) })
        .catch(() => { if (active) setError(true) })
    } else {
      setSaved([])
    }
    return () => { active = false }
  }, [user, reloadKey])

  const reload = useCallback(() => setReloadKey((k) => k + 1), [])

  const addSave = useCallback((mediaId) => {
    setSaved((prev) => (prev.includes(mediaId) ? prev : [mediaId, ...prev]))
    if (user) api.postSave(mediaId).catch(() => {})
  }, [user])

  const removeSave = useCallback((mediaId) => {
    setSaved((prev) => prev.filter((id) => id !== mediaId))
    if (user) api.deleteSave(mediaId).catch(() => {})
  }, [user])

  const isSaved = useCallback((mediaId) => saved.includes(mediaId), [saved])

  return (
    <SavesContext.Provider value={{ saved, addSave, removeSave, isSaved, error, reload }}>
      {children}
    </SavesContext.Provider>
  )
}

export function useSaves() {
  const ctx = useContext(SavesContext)
  if (!ctx) throw new Error('useSaves must be used within SavesProvider')
  return ctx
}
