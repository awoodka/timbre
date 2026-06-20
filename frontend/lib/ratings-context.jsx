'use client'

import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { api } from './api'
import { useAuth } from './auth-context'

const RatingsContext = createContext(null)

export function RatingsProvider({ children }) {
  const { user } = useAuth()
  const [ratings, setRatings] = useState([]) // [{ media_id, rating }]
  const [results, setResults] = useState(null)

  // Load the signed-in user's ratings from the server; clear them on logout.
  useEffect(() => {
    let active = true
    setResults(null)
    if (user) {
      api.getRatings()
        .then((rows) => {
          if (active) setRatings(rows.map((r) => ({ media_id: r.media_id, feedback: r.feedback || {}, resonance: r.resonance ?? 0.5 })))
        })
        .catch(() => {})
    } else {
      setRatings([])
    }
    return () => { active = false }
  }, [user])

  // Add or update a rating. Persists to the account when signed in; otherwise
  // stays in-memory (anonymous, as before).
  const rate = useCallback((mediaId, feedback) => {
    setRatings((prev) => {
      const exists = prev.some((r) => r.media_id === mediaId)
      return exists
        ? prev.map((r) => (r.media_id === mediaId ? { ...r, feedback } : r))
        : [...prev, { media_id: mediaId, feedback, resonance: 0.5 }]
    })
    setResults(null)
    if (user) {
      api.putRating(mediaId, feedback)
        .then((res) => setRatings((prev) => prev.map((r) => (r.media_id === mediaId ? { ...r, resonance: res.resonance } : r))))
        .catch(() => {})
    }
  }, [user])

  const removeRating = useCallback((mediaId) => {
    setRatings((prev) => prev.filter((r) => r.media_id !== mediaId))
    setResults(null)
    if (user) api.deleteRating(mediaId).catch(() => {})
  }, [user])

  return (
    <RatingsContext.Provider value={{ ratings, setRatings, results, setResults, rate, removeRating }}>
      {children}
    </RatingsContext.Provider>
  )
}

export function useRatings() {
  const ctx = useContext(RatingsContext)
  if (!ctx) throw new Error('useRatings must be used within RatingsProvider')
  return ctx
}
