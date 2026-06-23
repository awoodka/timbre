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

  useEffect(() => {
    let active = true
    if (user) {
      api.getSaves()
        .then((rows) => { if (active) setSaved(rows.map((r) => r.media_id)) })
        .catch(() => {})
    } else {
      setSaved([])
    }
    return () => { active = false }
  }, [user])

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
    <SavesContext.Provider value={{ saved, addSave, removeSave, isSaved }}>
      {children}
    </SavesContext.Provider>
  )
}

export function useSaves() {
  const ctx = useContext(SavesContext)
  if (!ctx) throw new Error('useSaves must be used within SavesProvider')
  return ctx
}
