'use client'

import { useEffect, useRef, useState } from 'react'
import { api } from '@/lib/api'
import BookCover from '@/components/BookCover'
import { MEDIA_TYPES, getMediaType } from '@/components/mediaType'

const MEDIA = Object.keys(MEDIA_TYPES) // book, film, show, anime, manga, game

// Cosmetic rotating copy — the backend only exposes pending→completed, so these
// communicate activity rather than true step progress.
const PROGRESS_COPY = [
  'Gathering reviews and discussion…',
  'Reading the emotional texture…',
  'Scoring the 31 emotional dimensions…',
  'Placing it in the emotional map…',
]
const POLL_MS = 2500
const POLL_CAP_MS = 90000
const norm = (s) => (s || '').trim().toLowerCase()

const creatorLabel = (m) =>
  m === 'book' ? 'Author (optional)'
  : m === 'film' || m === 'show' ? 'Director (optional)'
  : m === 'game' ? 'Studio (optional)'
  : 'Creator (optional)'

// Input → look up the medium's API → confirm the match → run the full analysis,
// polling until it lands. `onComplete(item)` fires when analysis_status==="completed".
export default function AddMediaFlow({
  title: initialTitle = '',
  medium: initialMedium = 'book',
  existing = [],
  onComplete,
  onCancel,
}) {
  const [stage, setStage] = useState('form') // form|looking|confirm|notfound|analyzing|slow|failed|dupe
  const [medium, setMedium] = useState(initialMedium)
  const [title, setTitle] = useState(initialTitle)
  const [creator, setCreator] = useState('')
  const [match, setMatch] = useState(null)
  const [dupe, setDupe] = useState(null)
  const [error, setError] = useState(null)
  const [progressIdx, setProgressIdx] = useState(0)
  const itemIdRef = useRef(null)

  const sourceLabel = getMediaType(medium)?.label || medium

  const findDupe = () => {
    const t = norm(title), c = norm(creator)
    return existing.find((b) => b.medium === medium && norm(b.title) === t && (!c || norm(b.creator) === c))
  }

  const lookup = async () => {
    if (!title.trim()) return
    const d = findDupe()
    if (d) { setDupe(d); setStage('dupe'); return }
    setError(null); setStage('looking')
    try {
      const res = await api.lookupMedia({ medium, title: title.trim(), creator: creator.trim() })
      if (res.found) { setMatch(res); setStage('confirm') }
      else setStage('notfound')
    } catch (e) { setError(e.message); setStage('form') }
  }

  const create = async (payload) => {
    setError(null); itemIdRef.current = null; setStage('analyzing')
    try {
      const item = await api.createItem(payload)
      itemIdRef.current = item.id
    } catch (e) { setError(e.message); setStage('failed') }
  }

  const confirmCreate = () => create({
    medium,
    title: match.title || title.trim(),
    creator: match.creator || creator.trim(),
    cover_image_url: match.cover_image_url || null,
    metadata: match.year ? { year: match.year } : null,
  })

  const createAsTyped = () => create({
    medium, title: title.trim(), creator: creator.trim(), cover_image_url: null, metadata: null,
  })

  const retry = () => {
    if (!itemIdRef.current) { setStage(match ? 'confirm' : 'form'); return }
    setError(null); setStage('analyzing')
    api.reanalyze(itemIdRef.current).catch((e) => { setError(e.message); setStage('failed') })
  }

  // Poll for completion while analyzing.
  useEffect(() => {
    if (stage !== 'analyzing') return
    let cancelled = false
    let timer
    const started = Date.now()
    const tick = async () => {
      if (cancelled) return
      if (!itemIdRef.current) { timer = setTimeout(tick, POLL_MS); return }
      try {
        const item = await api.getItem(itemIdRef.current)
        if (cancelled) return
        if (item.analysis_status === 'completed') { onComplete?.(item); return }
        if (item.analysis_status === 'failed') { setError('We couldn’t analyze that one.'); setStage('failed'); return }
      } catch { /* transient — keep polling */ }
      if (cancelled) return
      if (Date.now() - started > POLL_CAP_MS) { setStage('slow'); return }
      timer = setTimeout(tick, POLL_MS)
    }
    timer = setTimeout(tick, POLL_MS)
    return () => { cancelled = true; clearTimeout(timer) }
  }, [stage]) // eslint-disable-line react-hooks/exhaustive-deps

  // Rotate the progress copy while analyzing.
  useEffect(() => {
    if (stage !== 'analyzing') { setProgressIdx(0); return }
    const id = setInterval(() => setProgressIdx((i) => (i + 1) % PROGRESS_COPY.length), 3000)
    return () => clearInterval(id)
  }, [stage])

  if (stage === 'dupe') {
    return (
      <div className="add-flow">
        <p className="add-msg">“{dupe.title}” is already in Timbre.</p>
        <div className="add-actions">
          <button className="btn" onClick={() => onComplete?.(dupe)}>Use it</button>
          <button type="button" className="add-link" onClick={() => { setDupe(null); setStage('form') }}>Add something else</button>
        </div>
      </div>
    )
  }

  if (stage === 'looking') {
    return <div className="add-flow"><p className="add-msg"><span className="spinner" /> Looking up “{title}”…</p></div>
  }

  if (stage === 'confirm') {
    return (
      <div className="add-flow">
        <div className="add-confirm">
          <BookCover url={match.cover_image_url} size="small" />
          <div className="add-confirm-meta">
            <span className="rated-title">{match.title}</span>
            <span className="rated-author">{[match.creator, match.year].filter(Boolean).join(' · ')}</span>
            {match.description && <p className="add-desc">{match.description}</p>}
          </div>
        </div>
        <p className="add-hint">Is this the one? Analysis takes up to a minute.</p>
        <div className="add-actions">
          <button className="btn" onClick={confirmCreate}>Confirm &amp; analyze</button>
          <button type="button" className="add-link" onClick={() => setStage('form')}>Not it — edit</button>
        </div>
      </div>
    )
  }

  if (stage === 'notfound') {
    return (
      <div className="add-flow">
        <p className="add-msg">Couldn’t find “{title}” in {sourceLabel} sources.</p>
        <div className="add-actions">
          <button className="btn" onClick={createAsTyped}>Add as typed &amp; analyze</button>
          <button type="button" className="add-link" onClick={() => setStage('form')}>Edit</button>
        </div>
      </div>
    )
  }

  if (stage === 'analyzing' || stage === 'slow') {
    return (
      <div className="add-flow">
        <div className="add-analyzing">
          <span className="spinner" />
          <div className="add-analyzing-text">
            <p className="add-msg">
              {stage === 'slow' ? 'Still analyzing — it’ll appear in your library shortly.' : `Analyzing “${match?.title || title}”…`}
            </p>
            {stage === 'analyzing' && <p className="add-sub">{PROGRESS_COPY[progressIdx]}</p>}
          </div>
        </div>
        {stage === 'analyzing' && <div className="add-progress"><span className="add-progress-bar" /></div>}
        {stage === 'slow' && <div className="add-actions"><button type="button" className="add-link" onClick={() => onCancel?.()}>Close</button></div>}
      </div>
    )
  }

  if (stage === 'failed') {
    return (
      <div className="add-flow">
        <p className="add-msg add-error">{error || 'Something went wrong.'}</p>
        <div className="add-actions">
          <button className="btn" onClick={retry}>Try again</button>
          <button type="button" className="add-link" onClick={() => onCancel?.()}>Cancel</button>
        </div>
      </div>
    )
  }

  // stage === 'form'
  return (
    <div className="add-flow">
      <div className="add-media-pills">
        {MEDIA.map((m) => {
          const t = getMediaType(m), on = medium === m
          return (
            <button
              key={m}
              type="button"
              className={`filter-pill${on ? ' active' : ''}`}
              onClick={() => setMedium(m)}
              style={on ? { background: t.color, borderColor: t.color, color: '#fff' } : { borderColor: t.color, color: t.color }}
            >
              {t.label}
            </button>
          )
        })}
      </div>
      <input
        className="search-input add-input"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        onKeyDown={(e) => { if (e.key === 'Enter') lookup() }}
        placeholder="Title"
        aria-label="Title"
        autoFocus
      />
      <input
        className="search-input add-input"
        value={creator}
        onChange={(e) => setCreator(e.target.value)}
        onKeyDown={(e) => { if (e.key === 'Enter') lookup() }}
        placeholder={creatorLabel(medium)}
        aria-label="Creator"
      />
      {error && <p className="add-msg add-error">{error}</p>}
      <div className="add-actions">
        <button className="btn" onClick={lookup} disabled={!title.trim()}>Look it up</button>
        {onCancel && <button type="button" className="add-link" onClick={() => onCancel()}>Cancel</button>}
      </div>
    </div>
  )
}
