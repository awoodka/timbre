'use client'

import { useState } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api'
import { useRatings } from '@/lib/ratings-context'

// A few starter phrases — clicking one fills the box and runs it (teaches the feature).
const EXAMPLES = [
  'cozy but a little melancholy',
  'tense and sleepless',
  'a warm hug with a happy ending',
  'for a rainy Sunday',
]

export default function NlSearch({ open = false }) {
  const { setResults } = useRatings()
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [empty, setEmpty] = useState(false)
  const [signupRequired, setSignupRequired] = useState(false)

  const run = async (q) => {
    const description = (q ?? text).trim()
    if (!description || loading) return
    setLoading(true)
    setError(null)
    setEmpty(false)
    setSignupRequired(false)
    try {
      const res = await api.recommendNL({ description, limit: 12 })
      // Anonymous visitors get a few free Gemini searches per day, then a sign-up wall.
      if (res.signup_required) {
        setSignupRequired(true)
        setResults([])
        return
      }
      const recs = res.recommendations || []
      setResults(recs)
      setEmpty(recs.length === 0)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  if (!open) return null

  return (
    <div className="find-panel">
      <div className="nl-search-bar">
        <input
          className="search-input nl-search-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') run() }}
          placeholder="“cozy but a little melancholy, with a hopeful ending”"
          aria-label="Describe a feeling or a moment"
          autoFocus
        />
        <button className="btn nl-search-btn" onClick={() => run()} disabled={!text.trim() || loading}>
          {loading ? <><span className="spinner" /> Finding…</> : 'Find it'}
        </button>
      </div>
      <div className="nl-examples">
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            type="button"
            className="nl-example"
            onClick={() => { setText(ex); run(ex) }}
            disabled={loading}
          >
            {ex}
          </button>
        ))}
      </div>
      {error && <p className="mc-error nl-search-msg">{error}</p>}
      {signupRequired && (
        <p className="nl-search-wall nl-search-msg">
          That’s your free look for today.{' '}
          <Link href="/login">Sign up to keep exploring — it’s free →</Link>
        </p>
      )}
      {empty && !loading && (
        <p className="nl-search-empty nl-search-msg">
          Couldn’t read a feeling in that — try describing the mood or the moment.
        </p>
      )}
    </div>
  )
}
