'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api'
import { useRatings } from '@/lib/ratings-context'
import { useSaves } from '@/lib/saves-context'
import RequireAuth from '@/components/RequireAuth'
import BookSearch from '@/components/BookSearch'
import RatingItem from '@/components/RatingItem'
import { getMediaType } from '@/components/mediaType'

const MOOD_THRESHOLD = 0.5
const RESONANCE_BANDS = {
  loved: [0.75, 1.01],
  liked: [0.55, 0.75],
  neutral: [0.45, 0.55],
  'not-for-me': [-0.01, 0.45],
}
const BAND_LABEL = { loved: 'Loved', liked: 'Liked', neutral: 'Neutral', 'not-for-me': 'Not for me' }

function RatingsManager() {
  const { ratings, rate, removeRating } = useRatings()
  const { removeSave } = useSaves()
  const [books, setBooks] = useState([])
  const [booksLoading, setBooksLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [types, setTypes] = useState([])
  const [mood, setMood] = useState('')
  const [band, setBand] = useState('')
  const [sort, setSort] = useState('recent')
  const [view, setView] = useState('grid')
  const [editingId, setEditingId] = useState(null)
  const [confirmingDelete, setConfirmingDelete] = useState(null)

  useEffect(() => { api.getMedia().then(setBooks).finally(() => setBooksLoading(false)) }, [])
  // Hydrate the saved view in an effect (never read localStorage during render → no SSR mismatch).
  useEffect(() => {
    const v = localStorage.getItem('timbre.ratingsView')
    if (v === 'grid' || v === 'list') setView(v)
  }, [])
  const chooseView = (v) => { setView(v); try { localStorage.setItem('timbre.ratingsView', v) } catch {} }

  const byId = useMemo(() => Object.fromEntries(books.map((b) => [b.id, b])), [books])
  const available = useMemo(
    () => books.filter((b) => b.analysis_status === 'completed' && !ratings.some((r) => r.media_id === b.id)),
    [books, ratings]
  )
  const ratedMediums = useMemo(() => {
    const s = new Set()
    ratings.forEach((r) => { const m = byId[r.media_id]?.medium; if (m) s.add(m) })
    return [...s]
  }, [ratings, byId])
  const allDims = useMemo(() => {
    const s = new Set()
    ratings.forEach((r) => { const bd = byId[r.media_id]?.emotion_breakdown; if (bd) Object.keys(bd).forEach((k) => s.add(k)) })
    return [...s].sort()
  }, [ratings, byId])

  const rated = useMemo(() => {
    let list = ratings.map((r) => ({ ...r, book: byId[r.media_id] })).filter((x) => x.book)
    const q = search.trim().toLowerCase()
    if (q) list = list.filter((x) => `${x.book.title} ${x.book.creator}`.toLowerCase().includes(q))
    if (types.length) list = list.filter((x) => types.includes(x.book.medium))
    if (mood) list = list.filter((x) => (x.book.emotion_breakdown?.[mood] ?? 0) >= MOOD_THRESHOLD)
    if (band && RESONANCE_BANDS[band]) {
      const [lo, hi] = RESONANCE_BANDS[band]
      list = list.filter((x) => { const v = x.resonance ?? 0.5; return v >= lo && v < hi })
    }
    if (sort === 'title') list = [...list].sort((a, b) => a.book.title.localeCompare(b.book.title))
    else if (sort === 'resonance') list = [...list].sort((a, b) => (b.resonance ?? 0.5) - (a.resonance ?? 0.5))
    return list
  }, [ratings, byId, search, types, mood, band, sort])

  if (booksLoading) return <div className="loading"><span className="spinner" /> Loading…</div>

  const itemProps = (x) => ({
    rating: x,
    book: x.book,
    editing: editingId === x.media_id,
    confirming: confirmingDelete === x.media_id,
    onEdit: setEditingId,
    onRate: rate,
    onAskRemove: setConfirmingDelete,
    onConfirmRemove: (id) => { removeRating(id); setConfirmingDelete(null) },
    onCancelRemove: () => setConfirmingDelete(null),
  })

  return (
    <div>
      <div className="page-header">
        <h1>My ratings</h1>
        <p>
          Everything you’ve logged — search, filter, and tune how each work landed.{' '}
          <Link href="/fingerprint" className="link-btn" style={{ padding: 0 }}>See your emotional fingerprint →</Link>
        </p>
      </div>

      <BookSearch books={available} onSelect={(id, fb) => { rate(id, fb); removeSave(id) }} />

      {ratings.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
          <p style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>You haven’t rated anything yet</p>
          <p style={{ fontSize: '0.85rem' }}>Search for a work above and mark how its emotions landed.</p>
        </div>
      ) : (
        <>
          <div className="catalogue-controls" style={{ marginTop: '1.5rem' }}>
            <input
              className="catalogue-search"
              placeholder="Search your ratings…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <label className="control">
              <span className="control-label">Mood</span>
              <select className="sort-select" value={mood} onChange={(e) => setMood(e.target.value)}>
                <option value="">Any mood</option>
                {allDims.map((d) => <option key={d} value={d}>{d.replace(/_/g, ' ')}</option>)}
              </select>
            </label>
            <label className="control">
              <span className="control-label">Resonance</span>
              <select className="sort-select" value={band} onChange={(e) => setBand(e.target.value)}>
                <option value="">Any</option>
                {Object.keys(RESONANCE_BANDS).map((b) => <option key={b} value={b}>{BAND_LABEL[b]}</option>)}
              </select>
            </label>
            <label className="control">
              <span className="control-label">Sort</span>
              <select className="sort-select" value={sort} onChange={(e) => setSort(e.target.value)}>
                <option value="recent">Recently added</option>
                <option value="resonance">Resonance</option>
                <option value="title">Title (A–Z)</option>
              </select>
            </label>
            <div className="view-toggle" style={{ marginLeft: 'auto' }}>
              <button className={view === 'grid' ? 'on' : ''} onClick={() => chooseView('grid')}>Grid</button>
              <button className={view === 'list' ? 'on' : ''} onClick={() => chooseView('list')}>List</button>
            </div>
          </div>

          {ratedMediums.length > 1 && (
            <div className="catalogue-filters">
              <button
                className={`filter-pill${types.length === 0 ? ' active' : ''}`}
                onClick={() => setTypes([])}
                style={types.length === 0
                  ? { background: 'var(--accent)', borderColor: 'var(--accent)', color: '#fff' }
                  : { borderColor: 'var(--accent)', color: 'var(--accent)' }}
              >
                All types
              </button>
              {ratedMediums.map((m) => {
                const color = getMediaType(m).color
                const active = types.includes(m)
                return (
                  <button
                    key={m}
                    className={`filter-pill${active ? ' active' : ''}`}
                    onClick={() => setTypes((prev) => prev.includes(m) ? prev.filter((x) => x !== m) : [...prev, m])}
                    style={active ? { background: color, borderColor: color, color: '#fff' } : { borderColor: color, color }}
                  >
                    {getMediaType(m).label}
                  </button>
                )
              })}
            </div>
          )}

          {rated.length === 0 ? (
            <p style={{ color: 'var(--text-muted)' }}>No ratings match — try clearing a filter.</p>
          ) : view === 'grid' ? (
            <div className="ratings-grid">
              {rated.map((x) => <RatingItem key={x.media_id} view="grid" {...itemProps(x)} />)}
            </div>
          ) : (
            <div className="rating-list">
              {rated.map((x) => <RatingItem key={x.media_id} view="list" {...itemProps(x)} />)}
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default function RatingsPage() {
  return (
    <RequireAuth>
      <RatingsManager />
    </RequireAuth>
  )
}
