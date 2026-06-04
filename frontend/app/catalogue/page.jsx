'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api'
import BookCover from '@/components/BookCover'
import { getEmotionColor } from '@/components/emotionColors'
import { getMediaType } from '@/components/mediaType'

const MOOD_THRESHOLD = 0.5

function cosine(a, b) {
  let dot = 0, na = 0, nb = 0
  for (let i = 0; i < a.length; i++) { dot += a[i] * b[i]; na += a[i] * a[i]; nb += b[i] * b[i] }
  return na && nb ? dot / (Math.sqrt(na) * Math.sqrt(nb)) : 0
}

function TopEmotions({ breakdown, activeMood, onMood }) {
  if (!breakdown) return null
  const top = Object.entries(breakdown).sort((a, b) => b[1] - a[1]).slice(0, 3)
  return (
    <div className="emotion-dots">
      {top.map(([key, val]) => {
        const colors = getEmotionColor(key)
        return (
          <span
            key={key}
            className={`emotion-dot clickable${activeMood === key ? ' selected' : ''}`}
            style={{ background: colors.bg, color: colors.color }}
            title={`Filter by ${key.replace(/_/g, ' ')}`}
            onClick={(e) => { e.preventDefault(); e.stopPropagation(); onMood(key) }}
          >
            {key.replace(/_/g, ' ')} {val.toFixed(1)}
          </span>
        )
      })}
    </div>
  )
}

export default function Catalogue() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [mediaFilter, setMediaFilter] = useState('all')
  const [search, setSearch] = useState('')
  const [mood, setMood] = useState(null)
  const [sort, setSort] = useState('recent')

  useEffect(() => {
    api.getMedia().then(setItems).finally(() => setLoading(false))
  }, [])

  // Nearest item of a DIFFERENT medium for each item (the cross-media "feels like").
  const feelsLike = useMemo(() => {
    const withVec = items.filter((i) => i.emotion_vector)
    const map = {}
    for (const a of withVec) {
      let best = null, bestSim = -2
      for (const b of withVec) {
        if (b.id === a.id || b.medium === a.medium) continue
        const s = cosine(a.emotion_vector, b.emotion_vector)
        if (s > bestSim) { bestSim = s; best = b }
      }
      if (best) map[a.id] = best.title
    }
    return map
  }, [items])

  const allDims = useMemo(() => {
    const s = new Set()
    items.forEach((i) => i.emotion_breakdown && Object.keys(i.emotion_breakdown).forEach((k) => s.add(k)))
    return [...s].sort()
  }, [items])

  if (loading) return <div className="loading"><span className="spinner" /> Loading catalogue...</div>

  const q = search.trim().toLowerCase()
  // Apply search + mood (but NOT the media filter) so the pill counts stay meaningful.
  const base = items.filter((i) => {
    if (q && !(`${i.title} ${i.creator}`.toLowerCase().includes(q))) return false
    if (mood && !(i.emotion_breakdown && (i.emotion_breakdown[mood] ?? 0) >= MOOD_THRESHOLD)) return false
    return true
  })
  const counts = {
    all: base.length,
    book: base.filter((i) => i.medium === 'book').length,
    film: base.filter((i) => i.medium === 'film').length,
    show: base.filter((i) => i.medium === 'show').length,
    anime: base.filter((i) => i.medium === 'anime').length,
    manga: base.filter((i) => i.medium === 'manga').length,
    game: base.filter((i) => i.medium === 'game').length,
  }

  let visible = mediaFilter === 'all' ? base : base.filter((i) => i.medium === mediaFilter)
  if (sort === 'title') {
    visible = [...visible].sort((a, b) => a.title.localeCompare(b.title))
  } else if (sort === 'mood' && mood) {
    visible = [...visible].sort((a, b) => (b.emotion_breakdown?.[mood] ?? 0) - (a.emotion_breakdown?.[mood] ?? 0))
  } // 'recent' keeps the API order (created_at desc)

  const FILTERS = [
    { key: 'all', label: 'All' },
    { key: 'book', label: 'Books' },
    { key: 'film', label: 'Movies' },
    { key: 'show', label: 'Shows' },
    { key: 'anime', label: 'Anime' },
    { key: 'manga', label: 'Manga' },
    { key: 'game', label: 'Games' },
  ]

  return (
    <div>
      <div className="page-header">
        <h1>Catalogue</h1>
        <p>{items.length} works across books, films, shows, anime &amp; manga — and their emotional fingerprints</p>
      </div>

      <div className="catalogue-controls">
        <input
          type="text"
          className="catalogue-search"
          placeholder="Search title or creator..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <label className="control">
          <span className="control-label">Sort</span>
          <select
            className="sort-select"
            value={sort === 'mood' && !mood ? 'recent' : sort}
            onChange={(e) => setSort(e.target.value)}
          >
            <option value="recent">Recently added</option>
            <option value="title">Title (A–Z)</option>
            {mood && <option value="mood">Most {mood.replace(/_/g, ' ')}</option>}
          </select>
        </label>
        <label className="control">
          <span className="control-label">Mood</span>
          <select
            className="sort-select"
            value={mood || ''}
            onChange={(e) => setMood(e.target.value || null)}
          >
            <option value="">Any mood</option>
            {allDims.map((d) => (
              <option key={d} value={d}>{d.replace(/_/g, ' ')}</option>
            ))}
          </select>
        </label>
      </div>

      <div className="catalogue-filters">
        {FILTERS.map((f) => {
          const color = f.key === 'all' ? 'var(--accent)' : getMediaType(f.key).color
          const active = mediaFilter === f.key
          return (
            <button
              key={f.key}
              className={`filter-pill${active ? ' active' : ''}`}
              onClick={() => setMediaFilter(f.key)}
              style={active ? { background: color, borderColor: color, color: '#fff' } : { borderColor: color, color }}
            >
              {f.label} <span className="filter-count">{counts[f.key]}</span>
            </button>
          )
        })}
        {mood && (
          <button className="mood-chip" onClick={() => setMood(null)} title="Clear mood filter">
            mood: {mood.replace(/_/g, ' ')} ✕
          </button>
        )}
      </div>

      {visible.length === 0 ? (
        <p style={{ color: 'var(--text-muted)' }}>No matches — try clearing a filter.</p>
      ) : (
        <div className="book-grid">
          {visible.map((item) => {
            const type = getMediaType(item.medium)
            const meta = item.metadata || {}
            const metaBits = [meta.year, Array.isArray(meta.genre) ? meta.genre.join(', ') : null].filter(Boolean)
            return (
              <Link
                key={item.id}
                href={`/book/${item.id}`}
                className="book-card"
                style={{ borderLeft: `4px solid ${type.color}` }}
              >
                <BookCover url={item.cover_image_url} />
                <div className="book-card-info">
                  <div className="card-top">
                    <h3>{item.title}</h3>
                    <span className="media-badge" style={{ color: type.color, borderColor: type.color }}>{type.label}</span>
                  </div>
                  <div className="author">{item.creator}</div>
                  {metaBits.length > 0 && <div className="card-meta">{metaBits.join(' · ')}</div>}
                  <TopEmotions breakdown={item.emotion_breakdown} activeMood={mood} onMood={setMood} />
                  {feelsLike[item.id] && (
                    <div className="card-feels">✦ feels like <span>{feelsLike[item.id]}</span></div>
                  )}
                </div>
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}
