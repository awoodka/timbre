'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'
import BookCover from '@/components/BookCover'
import { getEmotionColor } from '@/components/emotionColors'
import { getMediaType } from '@/components/mediaType'
import SaveButton from '@/components/SaveButton'
import AddMediaFlow from '@/components/AddMediaFlow'

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

// The 7 shelf "books" (All + each medium). Heights vary for a real-shelf look.
const SHELF = [
  { key: 'all', label: 'All', height: 338 },
  { key: 'book', label: 'Books', height: 320 },
  { key: 'film', label: 'Films', height: 334 },
  { key: 'show', label: 'Shows', height: 308 },
  { key: 'anime', label: 'Anime', height: 338 },
  { key: 'manga', label: 'Manga', height: 324 },
  { key: 'game', label: 'Games', height: 314 },
]

// The 6 media types as toggle pills (used to narrow the All view to a few categories).
const MEDIA_PILLS = SHELF.filter((s) => s.key !== 'all')

export default function Catalogue() {
  const { user } = useAuth()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null) // null => shelf view
  const [search, setSearch] = useState('')
  const [mood, setMood] = useState(null)
  const [sort, setSort] = useState('recent')
  const [types, setTypes] = useState([]) // multi-select media subset, only used on the All view
  const [adding, setAdding] = useState(false)

  useEffect(() => {
    api.getMedia().then(setItems).finally(() => setLoading(false))
  }, [])

  // A freshly-added work (post-analysis) → fold it into the catalogue so it just appears.
  const handleAddComplete = (item) => {
    setAdding(false)
    setSearch(''); setMood(null)
    setItems((prev) => (prev.some((b) => b.id === item.id) ? prev : [item, ...prev]))
  }

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

  const totals = SHELF.reduce((acc, s) => {
    acc[s.key] = s.key === 'all' ? items.length : items.filter((i) => i.medium === s.key).length
    return acc
  }, {})

  // ---- Shelf view -------------------------------------------------------
  if (selected === null) {
    return (
      <div className="shelf-view">
        <div className="page-header">
          <h1>The Shelf</h1>
          <p>{items.length} works · by feeling, not genre</p>
          {user ? (
            <button className="catalogue-add-btn" style={{ marginTop: '0.6rem' }} onClick={() => { setSelected('all'); setAdding(true) }}>+ Add a work</button>
          ) : (
            <Link href="/login" className="catalogue-add-signin" style={{ marginTop: '0.6rem' }}>Sign in to add a work →</Link>
          )}
        </div>
        {user && adding && (
          <div className="add-panel add-panel-floating">
            <AddMediaFlow existing={items} onComplete={handleAddComplete} onCancel={() => setAdding(false)} />
          </div>
        )}
        <div className="shelf-stage">
          <div className="shelf-books">
            {SHELF.map((s) => (
              <button
                key={s.key}
                className="shelf-book"
                style={{ height: s.height, '--spine': s.key === 'all' ? '#262220' : getMediaType(s.key).color }}
                onClick={() => setSelected(s.key)}
                title={`${s.label} (${totals[s.key]})`}
              >
                <span className="shelf-book-title">{s.label}</span>
                <span className="shelf-book-count">{totals[s.key]}</span>
              </button>
            ))}
          </div>
          <div className="shelf-board" />
        </div>
      </div>
    )
  }

  // ---- Grid view (a shelf was chosen) -----------------------------------
  const type = selected === 'all'
    ? { label: 'All', color: 'var(--accent)' }
    : getMediaType(selected)

  const q = search.trim().toLowerCase()
  // search + mood applied first (ignoring the type subset) so the pill counts stay stable
  const searchMoodFiltered = items.filter((i) => {
    if (selected !== 'all' && i.medium !== selected) return false
    if (q && !(`${i.title} ${i.creator}`.toLowerCase().includes(q))) return false
    if (mood && !(i.emotion_breakdown && (i.emotion_breakdown[mood] ?? 0) >= MOOD_THRESHOLD)) return false
    return true
  })
  const typeCounts = MEDIA_PILLS.reduce((acc, p) => {
    acc[p.key] = searchMoodFiltered.filter((i) => i.medium === p.key).length
    return acc
  }, {})
  // on the All view, narrow to the chosen media subset (empty => all categories)
  const base = (selected === 'all' && types.length)
    ? searchMoodFiltered.filter((i) => types.includes(i.medium))
    : searchMoodFiltered
  let visible = base
  if (sort === 'title') {
    visible = [...visible].sort((a, b) => a.title.localeCompare(b.title))
  } else if (sort === 'mood' && mood) {
    visible = [...visible].sort((a, b) => (b.emotion_breakdown?.[mood] ?? 0) - (a.emotion_breakdown?.[mood] ?? 0))
  }

  return (
    <div>
      <div className="catalogue-gridhead">
        <button className="shelf-back" onClick={() => { setSelected(null); setSearch(''); setMood(null); setTypes([]) }}>← Shelf</button>
        <h1 style={{ borderLeft: `5px solid ${type.color}`, paddingLeft: '0.6rem', margin: 0, fontSize: '1.6rem' }}>{type.label}</h1>
        <span className="gridhead-count">{visible.length} works</span>
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
        {mood && (
          <button className="mood-chip" onClick={() => setMood(null)} title="Clear mood filter">
            mood: {mood.replace(/_/g, ' ')} ✕
          </button>
        )}
        {user ? (
          <button className="catalogue-add-btn" style={{ marginLeft: 'auto' }} onClick={() => setAdding(true)}>+ Add a work</button>
        ) : (
          <Link href="/login" className="catalogue-add-signin" style={{ marginLeft: 'auto' }}>Sign in to add a work →</Link>
        )}
      </div>

      {user && adding && (
        <div className="add-panel add-panel-floating">
          <AddMediaFlow existing={items} onComplete={handleAddComplete} onCancel={() => setAdding(false)} />
        </div>
      )}

      {selected === 'all' && (
        <div className="catalogue-filters">
          <button
            className={`filter-pill${types.length === 0 ? ' active' : ''}`}
            onClick={() => setTypes([])}
            style={types.length === 0
              ? { background: 'var(--accent)', borderColor: 'var(--accent)', color: '#fff' }
              : { borderColor: 'var(--accent)', color: 'var(--accent)' }}
          >
            All types <span className="filter-count">{searchMoodFiltered.length}</span>
          </button>
          {MEDIA_PILLS.map((p) => {
            const color = getMediaType(p.key).color
            const active = types.includes(p.key)
            return (
              <button
                key={p.key}
                className={`filter-pill${active ? ' active' : ''}`}
                onClick={() => setTypes((prev) => prev.includes(p.key) ? prev.filter((x) => x !== p.key) : [...prev, p.key])}
                style={active
                  ? { background: color, borderColor: color, color: '#fff' }
                  : { borderColor: color, color }}
              >
                {p.label} <span className="filter-count">{typeCounts[p.key]}</span>
              </button>
            )
          })}
        </div>
      )}

      {visible.length === 0 ? (
        <p style={{ color: 'var(--text-muted)' }}>No matches — try clearing a filter or the search.</p>
      ) : (
        <div className="book-grid">
          {visible.map((item) => {
            const t = getMediaType(item.medium)
            const meta = item.metadata || {}
            const metaBits = [meta.year, Array.isArray(meta.genre) ? meta.genre.join(', ') : null].filter(Boolean)
            return (
              <Link
                key={item.id}
                href={`/book/${item.id}`}
                className="book-card"
                style={{ borderLeft: `4px solid ${t.color}` }}
              >
                <SaveButton mediaId={item.id} className="card-save" />
                <BookCover url={item.cover_image_url} />
                <div className="book-card-info">
                  <div className="card-top">
                    <h3>{item.title}</h3>
                    <span className="media-badge" style={{ color: t.color, borderColor: t.color }}>{t.label}</span>
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
