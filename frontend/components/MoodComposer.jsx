'use client'

import { useState } from 'react'
import { api } from '@/lib/api'
import { useRatings } from '@/lib/ratings-context'
import { getEmotionColor } from '@/components/emotionColors'
import { getMediaType } from '@/components/mediaType'

const fmt = (s) => s.replace(/_/g, ' ')

// Headline feelings shown by default; the rest live behind "more feelings".
const HEADLINE = [
  'warmth', 'joy', 'hope', 'serenity', 'wonder', 'nostalgia',
  'melancholy', 'grief', 'dread', 'tension', 'isolation', 'intimacy',
  'anger', 'vulnerability', 'frenetic_energy', 'vastness',
]
const MORE = [
  'confusion', 'empowerment', 'absurdity', 'alienation', 'obsession',
  'claustrophobia', 'sensuality', 'moral_ambiguity', 'stillness',
]

// Quick presets — seed seek/avoid from the explore-page region archetypes.
const PRESETS = [
  { name: 'cozy · warm', seek: ['warmth', 'serenity', 'hope', 'intimacy'], avoid: ['dread', 'tension', 'grief'] },
  { name: 'bleak · melancholy', seek: ['melancholy', 'grief', 'isolation', 'alienation'], avoid: ['warmth', 'joy', 'hope'] },
  { name: 'tense · harrowing', seek: ['tension', 'dread', 'frenetic_energy'], avoid: ['serenity', 'warmth', 'stillness'] },
  { name: 'awe · wonder', seek: ['wonder', 'vastness', 'hope'], avoid: ['claustrophobia'] },
  { name: 'joyful · lively', seek: ['joy', 'warmth', 'frenetic_energy', 'empowerment'], avoid: ['grief', 'melancholy', 'dread'] },
  { name: 'intimate · tender', seek: ['intimacy', 'vulnerability', 'sensuality', 'warmth'], avoid: ['vastness', 'frenetic_energy'] },
]

const ENDINGS = [
  { key: 'any', label: 'Any' },
  { key: 'bleak', label: 'Bleak' },
  { key: 'bittersweet', label: 'Bittersweet' },
  { key: 'uplifting', label: 'Uplifting' },
]

const MEDIA = ['book', 'film', 'show', 'anime', 'manga', 'game']

export default function MoodComposer({ open = false }) {
  const { ratings, setResults } = useRatings()
  const [mode, setMode] = useState('simple')    // 'simple' | 'advanced'
  const [picks, setPicks] = useState({})        // { emotion_key: 1 (seek) | -1 (avoid) }
  const [selectedPreset, setSelectedPreset] = useState(null)
  const [ending, setEnding] = useState('any')
  const [medium, setMedium] = useState('any')
  const [alpha, setAlpha] = useState(0.6)
  const [showMore, setShowMore] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const hasRatings = ratings.length > 0
  const canSearch = Object.keys(picks).length > 0 || ending !== 'any'
  const isDirty = Object.keys(picks).length > 0 || ending !== 'any' || medium !== 'any'

  // neutral → seek → avoid → neutral
  const cycle = (key) => {
    setSelectedPreset(null)
    setPicks((p) => {
      const cur = p[key] || 0
      const next = { ...p }
      if (cur === 0) next[key] = 1
      else if (cur === 1) next[key] = -1
      else delete next[key]
      return next
    })
  }

  const applyPreset = (preset) => {
    const next = {}
    preset.seek.forEach((k) => { next[k] = 1 })
    preset.avoid.forEach((k) => { next[k] = -1 })
    setPicks(next)
    setSelectedPreset(preset.name)
    if ([...preset.seek, ...preset.avoid].some((k) => MORE.includes(k))) setShowMore(true)
  }

  const clear = () => { setPicks({}); setEnding('any'); setMedium('any'); setSelectedPreset(null) }

  const search = async () => {
    if (!canSearch) return
    setLoading(true)
    setError(null)
    try {
      const advanced = mode === 'advanced'
      const res = await api.recommendExperience({
        mood: picks,
        ending,
        alpha: advanced ? alpha : 0.6,
        medium: advanced && medium !== 'any' ? medium : null,
        limit: 12,
      })
      setResults(res.recommendations || [])
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const Chip = ({ k }) => {
    const v = picks[k] || 0
    const c = getEmotionColor(k)
    const style = v === 1 ? { background: c.bg, color: c.color, borderColor: c.color } : undefined
    return (
      <button
        type="button"
        className={`mc-chip${v === 1 ? ' seek' : v === -1 ? ' avoid' : ''}`}
        style={style}
        onClick={() => cycle(k)}
      >
        {v !== 0 && <span className="mc-mark">{v === 1 ? '+' : '–'}</span>}
        {fmt(k)}
      </button>
    )
  }

  if (!open) return null

  return (
    <div className="find-panel">
          <div className="mc-modes">
            <div className="view-toggle">
              <button type="button" className={mode === 'simple' ? 'on' : ''} onClick={() => setMode('simple')}>Simple</button>
              <button type="button" className={mode === 'advanced' ? 'on' : ''} onClick={() => setMode('advanced')}>Advanced</button>
            </div>
          </div>

          <div className="mc-section">
            {mode === 'simple' && <div className="mc-label">Pick a vibe</div>}
            <div className="mc-presets">
              {PRESETS.map((p) => (
                <button
                  key={p.name}
                  type="button"
                  className={`mc-preset${selectedPreset === p.name ? ' on' : ''}`}
                  onClick={() => applyPreset(p)}
                >
                  {p.name}
                </button>
              ))}
            </div>
          </div>

          {mode === 'advanced' && (
          <div className="mc-section">
            <div className="mc-label">
              Feelings <span className="mc-hint">tap to seek, tap again to avoid</span>
            </div>
            <div className="mc-chips">
              {HEADLINE.map((k) => <Chip key={k} k={k} />)}
              {showMore && MORE.map((k) => <Chip key={k} k={k} />)}
            </div>
            {!showMore && (
              <button type="button" className="mc-more" onClick={() => setShowMore(true)}>
                more feelings…
              </button>
            )}
          </div>
          )}

          <div className="mc-section">
            <div className="mc-label">How it lands</div>
            <div className="mc-seg">
              {ENDINGS.map((e) => (
                <button
                  key={e.key}
                  type="button"
                  className={`mc-seg-btn${ending === e.key ? ' on' : ''}`}
                  onClick={() => setEnding(e.key)}
                >
                  {e.label}
                </button>
              ))}
            </div>
          </div>

          {mode === 'advanced' && (
          <div className="mc-section">
            <div className="mc-label">Media type</div>
            <div className="mc-chips">
              <button
                type="button"
                className={`filter-pill${medium === 'any' ? ' active' : ''}`}
                onClick={() => setMedium('any')}
                style={medium === 'any'
                  ? { background: 'var(--accent)', borderColor: 'var(--accent)', color: '#fff' }
                  : { borderColor: 'var(--accent)', color: 'var(--accent)' }}
              >
                Any
              </button>
              {MEDIA.map((m) => {
                const t = getMediaType(m)
                const on = medium === m
                return (
                  <button
                    key={m}
                    type="button"
                    className={`filter-pill${on ? ' active' : ''}`}
                    onClick={() => setMedium(on ? 'any' : m)}
                    style={on
                      ? { background: t.color, borderColor: t.color, color: '#fff' }
                      : { borderColor: t.color, color: t.color }}
                  >
                    {t.label}
                  </button>
                )
              })}
            </div>
          </div>
          )}

          {mode === 'advanced' && hasRatings && (
            <div className="mc-section">
              <div className="mc-label">Balance</div>
              <input
                type="range" min="0" max="1" step="0.05" value={alpha}
                onChange={(e) => setAlpha(parseFloat(e.target.value))}
                className="mc-slider"
              />
              <div className="mc-slider-ends">
                <span>my usual taste</span>
                <span>this mood</span>
              </div>
            </div>
          )}

          {error && <p className="mc-error">{error}</p>}

          <div className="mc-actions">
            <button className="mc-find" onClick={search} disabled={!canSearch || loading}>
              {loading ? <><span className="spinner" /> Finding…</> : 'Find it'}
            </button>
            {isDirty && (
              <button type="button" className="mc-clear" onClick={clear}>Clear</button>
            )}
          </div>
    </div>
  )
}
