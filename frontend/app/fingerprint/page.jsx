'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api'
import { useRatings } from '@/lib/ratings-context'
import RequireAuth from '@/components/RequireAuth'
import BookCover from '@/components/BookCover'
import FingerprintAura from '@/components/FingerprintAura'
import { getEmotionColor } from '@/components/emotionColors'
import { getMediaType, MEDIA_TYPES } from '@/components/mediaType'
import {
  buildTasteProfile, lovedAvoided, tasteAxes, archetype, personaLine,
  arcPreference, mediaSplit, resonanceStats, definingWorks, radarData,
  enjoymentByMedium, enjoymentByCreator, enjoymentByGenre, enjoymentStats,
} from '@/lib/taste'

const fmt = (s) => s.replace(/_/g, ' ')
const MIN_SHARP = 6

function BarList({ items, kind }) {
  const max = Math.max(0.0001, ...items.map(([, w]) => Math.abs(w)))
  return (
    <div className="fp-bars">
      {items.map(([k, w]) => (
        <div key={k} className="fp-bar-row">
          <span className="fp-bar-label">{fmt(k)}</span>
          <span className="fp-bar-track">
            <span
              className="fp-bar-fill"
              style={{
                width: `${(Math.abs(w) / max) * 100}%`,
                background: kind === 'loved' ? getEmotionColor(k).color : 'var(--text-muted)',
              }}
            />
          </span>
        </div>
      ))}
    </div>
  )
}

function Gauge({ value, left, right, label }) {
  return (
    <div className="fp-gauge">
      <div className="fp-gauge-track"><span className="fp-gauge-dot" style={{ left: `${value * 100}%` }} /></div>
      <div className="fp-gauge-ends">
        <span>{left}</span>
        <span className="fp-gauge-label">{label}</span>
        <span>{right}</span>
      </div>
    </div>
  )
}

function MediaBars({ counts }) {
  const total = Object.values(counts).reduce((a, b) => a + b, 0) || 1
  const order = Object.keys(MEDIA_TYPES).filter((m) => counts[m])
  return (
    <div className="fp-bars">
      {order.map((m) => {
        const t = getMediaType(m)
        return (
          <div key={m} className="fp-bar-row">
            <span className="fp-bar-label">{t.label}</span>
            <span className="fp-bar-track">
              <span className="fp-bar-fill" style={{ width: `${(counts[m] / total) * 100}%`, background: t.color }} />
            </span>
            <span className="fp-bar-num">{counts[m]}</span>
          </div>
        )
      })}
    </div>
  )
}

// Avg-enjoyment bars (0–5, in the star/warning hue) — for the "beyond emotion" section.
function EnjoyBars({ rows, label }) {
  return (
    <div className="fp-bars">
      {rows.map(({ key, avg }) => (
        <div key={key} className="fp-bar-row">
          <span className="fp-bar-label">{label ? label(key) : key}</span>
          <span className="fp-bar-track">
            <span className="fp-bar-fill" style={{ width: `${(avg / 5) * 100}%`, background: 'var(--warning)' }} />
          </span>
          <span className="fp-bar-num">{avg.toFixed(1)}★</span>
        </div>
      ))}
    </div>
  )
}

function Fingerprint() {
  const { ratings } = useRatings()
  const [byId, setById] = useState({})
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    api.getMedia()
      .then((list) => setById(Object.fromEntries(list.map((x) => [x.id, x]))))
      .catch(() => {})
      .finally(() => setLoaded(true))
  }, [])

  const ratedWorks = useMemo(
    () => ratings.map((r) => ({ ...r, book: byId[r.media_id] })).filter((x) => x.book),
    [ratings, byId]
  )
  const profile = useMemo(() => buildTasteProfile(ratings.map((r) => r.feedback)), [ratings])
  const { loved, avoided } = useMemo(() => lovedAvoided(profile, 6), [profile])
  const persona = useMemo(() => archetype(tasteAxes(profile)), [profile])
  const line = useMemo(() => personaLine(loved, avoided), [loved, avoided])
  const arc = useMemo(() => arcPreference(ratedWorks), [ratedWorks])
  const media = useMemo(() => mediaSplit(ratedWorks), [ratedWorks])
  const stats = useMemo(() => resonanceStats(ratings), [ratings])
  const defining = useMemo(() => definingWorks(ratedWorks, 5), [ratedWorks])
  const radar = useMemo(() => radarData(profile), [profile])
  const enjoyMedium = useMemo(() => enjoymentByMedium(ratedWorks), [ratedWorks])
  const enjoyCreator = useMemo(() => enjoymentByCreator(ratedWorks, 6), [ratedWorks])
  const enjoyGenre = useMemo(() => enjoymentByGenre(ratedWorks, 6), [ratedWorks])
  const enjoyStats = useMemo(() => enjoymentStats(ratings), [ratings])

  if (!loaded) return <div className="loading"><span className="spinner" /> Loading…</div>

  if (ratings.length === 0) {
    return (
      <div>
        <div className="page-header">
          <h1>Your emotional fingerprint</h1>
          <p>A portrait of your taste — once you’ve rated a few works.</p>
        </div>
        <div className="rec-coldstart">
          <p>Rate a few works and your fingerprint takes shape — the emotions you’re drawn to, how you like things to end, and more.</p>
          <Link href="/ratings" className="btn">Rate works →</Link>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="page-header">
        <h1>Your emotional fingerprint</h1>
        <p>What {ratings.length} {ratings.length === 1 ? 'rating' : 'ratings'} say about your taste.</p>
      </div>

      <div className="fp-hero">
        <span className="fp-wordmark">Timbre</span>
        <span className="fp-archetype">{persona.name}</span>
        <p className="fp-line">{line}</p>
        <FingerprintAura data={radar} />
        <div className="fp-chips">
          {loved[0] && (
            <span
              className="fp-chip"
              style={{ background: getEmotionColor(loved[0][0]).bg, color: getEmotionColor(loved[0][0]).color }}
            >
              most drawn to {fmt(loved[0][0])}
            </span>
          )}
          {arc && <span className="fp-chip ghost">endings {arc.ending}</span>}
        </div>
        {ratings.length < MIN_SHARP && (
          <p className="fp-note">Rate {MIN_SHARP - ratings.length} more to sharpen your fingerprint.</p>
        )}
      </div>

      <div className="fp-grid">
        <div className="fp-section">
          <h2 className="section-title">What you gravitate toward</h2>
          {loved.length ? <BarList items={loved} kind="loved" /> : <p className="fp-stat">No clear pulls yet.</p>}
          {avoided.length > 0 && (
            <>
              <h3 className="fp-subhead">…and steer clear of</h3>
              <BarList items={avoided} kind="avoided" />
            </>
          )}
        </div>

        {arc && (
          <div className="fp-section">
            <h2 className="section-title">How you like it to end</h2>
            <Gauge value={arc.endingValue} left="bleak" right="uplifting" label={arc.ending} />
            <Gauge value={arc.trajectoryValue} left="descends" right="rises" label={`${arc.arc} arcs`} />
          </div>
        )}

        <div className="fp-section">
          <h2 className="section-title">Across media</h2>
          <MediaBars counts={media} />
        </div>

        {enjoyStats.count > 0 && (
          <div className="fp-section">
            <h2 className="section-title">What you gravitate toward — beyond emotion</h2>
            <p className="fp-stat">
              Your enjoyment, separate from the feelings — across {enjoyStats.count} starred {enjoyStats.count === 1 ? 'work' : 'works'} (avg {enjoyStats.avg.toFixed(1)}★).
            </p>
            {enjoyMedium.length > 0 && (<><h3 className="fp-subhead">By medium</h3><EnjoyBars rows={enjoyMedium} label={(k) => getMediaType(k).label} /></>)}
            {enjoyCreator.length > 0 && (<><h3 className="fp-subhead">Top creators</h3><EnjoyBars rows={enjoyCreator} /></>)}
            {enjoyGenre.length > 0 && (<><h3 className="fp-subhead">By genre</h3><EnjoyBars rows={enjoyGenre} label={fmt} /></>)}
          </div>
        )}

        <div className="fp-section">
          <h2 className="section-title">By the numbers</h2>
          <p className="fp-stat">
            {stats.total} works rated · {stats.bands.loved} loved · {stats.bands.liked} liked · {stats.bands.notForMe} not for you
          </p>
          {defining.length > 0 && (
            <>
              <h3 className="fp-subhead">Works that define your taste</h3>
              <div className="fp-defining">
                {defining.map((r) => (
                  <Link key={r.media_id} href={`/book/${r.book.id}`} className="fp-def">
                    <BookCover url={r.book.cover_image_url} size="small" />
                    <span className="fp-def-title">{r.book.title}</span>
                  </Link>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default function FingerprintPage() {
  return (
    <RequireAuth>
      <Fingerprint />
    </RequireAuth>
  )
}
