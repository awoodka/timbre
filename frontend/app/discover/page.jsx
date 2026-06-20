'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api'
import { useRatings } from '@/lib/ratings-context'
import EmotionFeedback from '@/components/EmotionFeedback'
import BookCover from '@/components/BookCover'
import { getEmotionColor } from '@/components/emotionColors'
import { topFeltEmotions } from '@/lib/emotions'
import RequireAuth from '@/components/RequireAuth'
import MoodComposer from '@/components/MoodComposer'

const MIN_LOGGED = 4
const fmt = (s) => s.replace(/_/g, ' ')

function BookSearch({ books, onSelect }) {
  const [query, setQuery] = useState('')
  const [selectedBook, setSelectedBook] = useState(null)
  const [feedback, setFeedback] = useState({})
  const [showSuggestions, setShowSuggestions] = useState(false)
  const wrapperRef = useRef(null)

  const filtered = query.trim().length > 0
    ? books.filter((b) =>
        b.title.toLowerCase().includes(query.toLowerCase()) ||
        b.creator.toLowerCase().includes(query.toLowerCase())
      ).slice(0, 8)
    : []

  useEffect(() => {
    const handleClick = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) setShowSuggestions(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const pickBook = (book) => { setSelectedBook(book); setFeedback({}); setQuery(book.title); setShowSuggestions(false) }

  const handleSubmit = () => {
    if (!selectedBook) return
    onSelect(selectedBook.id, feedback)
    setSelectedBook(null); setQuery(''); setFeedback({})
  }

  const handleQueryChange = (e) => {
    setQuery(e.target.value)
    setShowSuggestions(true)
    if (selectedBook && e.target.value !== selectedBook.title) setSelectedBook(null)
  }

  return (
    <div className="add-book-form" ref={wrapperRef}>
      <div className="search-wrapper">
        <input
          type="text"
          value={query}
          onChange={handleQueryChange}
          onFocus={() => { if (!selectedBook && query.trim()) setShowSuggestions(true) }}
          placeholder="Search for a title or creator…"
          className="search-input"
        />
        {showSuggestions && filtered.length > 0 && (
          <div className="suggestions">
            {filtered.map((b) => (
              <button key={b.id} className="suggestion-item" onClick={() => pickBook(b)}>
                <span className="suggestion-title">{b.title}</span>
                <span className="suggestion-author">{b.creator}</span>
              </button>
            ))}
          </div>
        )}
        {showSuggestions && query.trim().length > 0 && filtered.length === 0 && (
          <div className="suggestions"><div className="suggestion-empty">No matches found</div></div>
        )}
      </div>

      {selectedBook && (
        <div className="log-panel">
          <div className="log-panel-head">
            <BookCover url={selectedBook.cover_image_url} size="small" />
            <div className="log-panel-meta">
              <span className="rated-title">{selectedBook.title}</span>
              <span className="rated-author">{selectedBook.creator}</span>
            </div>
          </div>
          <p className="log-hint">How did each feeling sit with you? Mark what you wanted more of — or less of — and skip the neutral ones.</p>
          <EmotionFeedback
            emotions={topFeltEmotions(selectedBook.emotion_breakdown)}
            value={feedback}
            onChange={setFeedback}
          />
          <button onClick={handleSubmit} className="add-btn" style={{ marginTop: '0.75rem' }}>Log this</button>
        </div>
      )}
    </div>
  )
}

const SENTIMENT = { 2: 'loved', 1: 'liked', '-1': 'disliked', '-2': 'not for me' }

function FeedbackSummary({ feedback }) {
  const entries = Object.entries(feedback || {}).filter(([, v]) => v !== 0).sort((a, b) => b[1] - a[1])
  if (!entries.length) return <span className="fb-summary muted">no marks yet</span>
  return (
    <span className="fb-summary">
      {entries.map(([k, v]) => (
        <span key={k} className={`fb-chip ${v > 0 ? 'up' : 'down'}`}>{SENTIMENT[v]} {fmt(k)}</span>
      ))}
    </span>
  )
}

function DiscoverTool() {
  const { ratings, results, setResults, rate, removeRating } = useRatings()
  const [books, setBooks] = useState([])
  const [loading, setLoading] = useState(false)
  const [booksLoading, setBooksLoading] = useState(true)
  const [error, setError] = useState(null)
  const [confirmingDelete, setConfirmingDelete] = useState(null)
  const [editingId, setEditingId] = useState(null)

  useEffect(() => {
    api.getMedia()
      .then((b) => setBooks(b.filter((x) => x.analysis_status === 'completed')))
      .finally(() => setBooksLoading(false))
  }, [])

  const available = books.filter((b) => !ratings.find((r) => r.media_id === b.id))
  const remaining = Math.max(0, MIN_LOGGED - ratings.length)

  const getRecommendations = async () => {
    if (ratings.length < MIN_LOGGED) return
    setLoading(true)
    setError(null)
    try {
      const res = await api.recommend()
      setResults(res.recommendations || [])
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  if (booksLoading) return <div className="loading"><span className="spinner" /> Loading…</div>

  return (
    <div>
      <div className="page-header">
        <h1>What have you experienced?</h1>
        <p>Log works you know and mark how each emotion landed — we’ll learn your emotional taste.</p>
      </div>

      <MoodComposer />

      <BookSearch books={available} onSelect={(id, fb) => rate(id, fb)} />

      {ratings.length > 0 && (
        <div style={{ marginTop: '1.5rem' }}>
          <h2 className="section-title" style={{ marginTop: 0 }}>Your logged works</h2>
          <div className="rating-list">
            {ratings.map((r) => {
              const book = books.find((b) => b.id === r.media_id)
              if (!book) return null
              const editing = editingId === r.media_id
              return (
                <div key={r.media_id} className="rating-row logged">
                  <div className="logged-head">
                    <BookCover url={book.cover_image_url} size="small" />
                    <Link href={`/book/${book.id}`} className="rated-book-info">
                      <span className="rated-title">{book.title}</span>
                      <span className="rated-author">{book.creator}</span>
                    </Link>
                    <button className="link-btn" onClick={() => setEditingId(editing ? null : r.media_id)}>
                      {editing ? 'Done' : 'Edit'}
                    </button>
                    {confirmingDelete === r.media_id ? (
                      <div className="confirm-delete">
                        <span className="confirm-text">Remove?</span>
                        <button className="confirm-yes" onClick={() => { removeRating(r.media_id); setConfirmingDelete(null) }}>Yes</button>
                        <button className="confirm-no" onClick={() => setConfirmingDelete(null)}>No</button>
                      </div>
                    ) : (
                      <button className="remove-btn" onClick={() => setConfirmingDelete(r.media_id)} title="Remove">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                          <path d="M2 4h12M5.3 4V2.7a1 1 0 011-1h3.4a1 1 0 011 1V4M6.5 7v4.5M9.5 7v4.5M3.5 4l.7 9a1.5 1.5 0 001.5 1.4h4.6a1.5 1.5 0 001.5-1.4l.7-9" />
                        </svg>
                      </button>
                    )}
                  </div>
                  {!editing && <FeedbackSummary feedback={r.feedback} />}
                  {editing && (
                    <EmotionFeedback
                      emotions={topFeltEmotions(book.emotion_breakdown)}
                      value={r.feedback}
                      onChange={(fb) => rate(r.media_id, fb)}
                    />
                  )}
                </div>
              )
            })}
          </div>

          {remaining > 0 ? (
            <p className="gate-msg">Log {remaining} more {remaining === 1 ? 'work' : 'works'} to unlock recommendations.</p>
          ) : (
            <button onClick={getRecommendations} disabled={loading} style={{ marginTop: '0.75rem' }}>
              {loading ? <><span className="spinner" /> Finding matches…</> : 'Find recommendations'}
            </button>
          )}
        </div>
      )}

      {error && <p style={{ color: 'var(--error)', marginTop: '1rem' }}>{error}</p>}

      {results && (
        <div style={{ marginTop: '2rem' }}>
          <h2 className="section-title" style={{ marginTop: 0 }}>Your recommendations</h2>
          {results.length === 0 ? (
            <p style={{ color: 'var(--text-muted)' }}>No matches yet — mark a few more emotions and try again.</p>
          ) : (
            <div className="similar-list">
              {results.map((rec) => {
                const book = rec.item
                return (
                  <Link key={book.id} href={`/book/${book.id}`} className="similar-item">
                    <BookCover url={book.cover_image_url} size="small" />
                    <div className="info">
                      <h4>{book.title}</h4>
                      <div className="author">{book.creator}</div>
                      <div className="reason-tags">
                        {(rec.reasons || []).map((rr) => {
                          if (rr.kind === 'ending') {
                            return <span key={rr.key} className="reason-tag ending-tag">{rr.name}</span>
                          }
                          const colors = getEmotionColor(rr.key)
                          return (
                            <span key={rr.key} className="reason-tag" style={{ background: colors.bg, color: colors.color }}>
                              {fmt(rr.key)}
                            </span>
                          )
                        })}
                      </div>
                    </div>
                    <span className="similarity-badge">{(rec.similarity * 100).toFixed(1)}% match</span>
                  </Link>
                )
              })}
            </div>
          )}
        </div>
      )}

      {!results && ratings.length === 0 && (
        <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
          <p style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Search for a work above to get started</p>
          <p style={{ fontSize: '0.85rem' }}>
            Mark the emotions you loved (or didn’t) and we’ll match your taste — not just genre.
          </p>
        </div>
      )}
    </div>
  )
}

export default function DiscoverPage() {
  return (
    <RequireAuth>
      <DiscoverTool />
    </RequireAuth>
  )
}
