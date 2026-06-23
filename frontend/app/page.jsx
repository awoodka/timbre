'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'
import { getEmotionColor } from '@/components/emotionColors'
import { getMediaType } from '@/components/mediaType'

const TAGLINE =
  'Discover books, films, games, and more by how they make you feel — not by genre.'

// Evocative moods shown first; only those actually present in the corpus are used.
const PREFERRED_MOODS = [
  'wonder', 'melancholy', 'warmth', 'dread', 'nostalgia',
  'tension', 'joy', 'hope', 'isolation', 'serenity', 'grief', 'intimacy', 'vastness',
]

// Fisher–Yates; runs client-side only (after the data fetch), so no SSR/hydration drift.
function shuffle(arr) {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

export default function Home() {
  // The home page is public and viewable by everyone (the logo brings signed-in
  // users back here); login/signup is what lands them on /recommendations, not a redirect.
  const { user } = useAuth()
  const [items, setItems] = useState([])
  const [loaded, setLoaded] = useState(false)
  const [mood, setMood] = useState(null)

  useEffect(() => {
    api.getMedia()
      .then((all) => setItems(all.filter((i) => i.analysis_status === 'completed')))
      .catch(() => {})
      .finally(() => setLoaded(true))
  }, [])

  // Band covers: only items that actually have a cover, across all media, freshly
  // shuffled each load so it's a different collection every visit.
  const bandCovers = useMemo(
    () => shuffle(items.filter((i) => i.cover_image_url)).slice(0, 24),
    [items]
  )

  // Moods to offer: preferred order intersected with dimensions present in the data.
  const moods = useMemo(() => {
    const present = new Set()
    items.forEach((i) =>
      i.emotion_breakdown && Object.keys(i.emotion_breakdown).forEach((k) => present.add(k))
    )
    const ordered = PREFERRED_MOODS.filter((m) => present.has(m))
    return (ordered.length ? ordered : [...present].sort()).slice(0, 10)
  }, [items])

  const activeMood = mood || moods[0] || null

  // A handful of works (with covers) that strongly evoke the active mood, across media.
  const moodMatches = useMemo(() => {
    if (!activeMood) return []
    const hits = items.filter(
      (i) => i.cover_image_url && (i.emotion_breakdown?.[activeMood] ?? 0) >= 0.5
    )
    return shuffle(hits).slice(0, 6)
  }, [items, activeMood])

  return (
    <div className="landing">
      <section className="hero">
        <h1 className="hero-title">Timbre</h1>
        <p className="hero-tagline">{TAGLINE}</p>
        <div className="hero-cta">
          {user
            ? <Link href="/ratings" className="btn">Start rating →</Link>
            : <Link href="/login" className="btn">Get started →</Link>}
          <Link href="/catalogue" className="btn-ghost">Browse the catalogue</Link>
        </div>
      </section>

      {/* Full-bleed band of slightly overlapping covers, drifting slowly. */}
      <section className="hero-band full-bleed" aria-hidden="true">
        {bandCovers.length > 0 ? (
          <div className="band-track">
            {[...bandCovers, ...bandCovers].map((item, idx) => (
              <img
                key={`${item.id}-${idx}`}
                src={item.cover_image_url}
                alt=""
                className="band-cover"
                loading="lazy"
              />
            ))}
          </div>
        ) : (
          <div className="band-placeholder" />
        )}
      </section>

      <section className="how">
        <h2 className="landing-h2">How it works</h2>
        <div className="how-steps">
          <div className="how-step">
            <span className="how-num">1</span>
            <h3>Rate what's moved you</h3>
            <p>Books, films, shows, anime, manga, games — anything that left a mark.</p>
          </div>
          <div className="how-step">
            <span className="how-num">2</span>
            <h3>Timbre reads the feeling</h3>
            <p>Every title is scored across 29 emotional dimensions — the texture of how it feels, not its genre.</p>
          </div>
          <div className="how-step">
            <span className="how-num">3</span>
            <h3>Get matches across media</h3>
            <p>Discover works that evoke the same feeling — a game that feels like your favorite novel.</p>
          </div>
        </div>
      </section>

      <section className="mood-explore">
        <h2 className="landing-h2">Explore by feeling</h2>
        <p className="mood-sub">Pick a mood — see what evokes it, across every medium.</p>
        <div className="mood-chips">
          {moods.map((m) => {
            const c = getEmotionColor(m)
            const on = m === activeMood
            return (
              <button
                key={m}
                className={`mood-chip-btn${on ? ' on' : ''}`}
                onClick={() => setMood(m)}
                style={on
                  ? { background: c.color, borderColor: c.color, color: '#fff' }
                  : { borderColor: c.color, color: c.color }}
              >
                {m.replace(/_/g, ' ')}
              </button>
            )
          })}
        </div>
        <div className="mood-results">
          {moodMatches.map((item) => {
            const t = getMediaType(item.medium)
            return (
              <Link
                key={item.id}
                href={`/book/${item.id}`}
                className="mood-card"
                title={`${item.title} — ${item.creator}`}
              >
                <img
                  src={item.cover_image_url}
                  alt=""
                  className="mood-card-cover"
                  loading="lazy"
                  style={{ borderColor: t.color }}
                />
                <span className="mood-card-title">{item.title}</span>
                <span className="mood-card-medium" style={{ color: t.color }}>{t.label}</span>
              </Link>
            )
          })}
          {loaded && activeMood && moodMatches.length === 0 && (
            <p className="mood-empty">Nothing loaded for this mood yet.</p>
          )}
        </div>
      </section>

      <section className="landing-cta">
        <h2>Ready to find your next favorite?</h2>
        {user
          ? <Link href="/recommendations" className="btn">Go to your recommendations →</Link>
          : <Link href="/login" className="btn">Create your free account →</Link>}
      </section>
    </div>
  )
}
