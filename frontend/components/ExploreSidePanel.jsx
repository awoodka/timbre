'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import BookCover from '@/components/BookCover'
import { getMediaType } from '@/components/mediaType'

const fmt = (s) => s.replace(/_/g, ' ')

function topEmotions(bd, n = 6) {
  if (!bd) return []
  return Object.entries(bd).sort((a, b) => b[1] - a[1]).slice(0, n)
}

// Click-preview panel that slides in from the right over the map. Kept mounted so
// it can animate OUT with its content intact: we snapshot the last selection and
// keep rendering it while `point` is null during the close transition.
export default function ExploreSidePanel({ point, neighbors, onClose }) {
  const [snap, setSnap] = useState({ point: null, neighbors: [] })
  useEffect(() => { if (point) setSnap({ point, neighbors }) }, [point, neighbors])

  const open = !!point
  const p = point || snap.point
  const nb = (point ? neighbors : snap.neighbors) || []
  if (!p) return <aside className="xp-sidepanel" aria-hidden="true" />

  const t = getMediaType(p.medium)
  return (
    <aside className={`xp-sidepanel${open ? ' open' : ''}`} aria-hidden={!open}>
      <button className="xp-sp-close" onClick={onClose} aria-label="Close">×</button>

      <div className="xp-sp-head">
        <BookCover url={p.cover_image_url} size="large" />
        <div className="sp-meta">
          <span className="xp-sp-title">{p.title}</span>
          <span className="xp-sp-creator">{p.creator}</span>
          <span className="xp-medium-badge" style={{ color: t.color, borderColor: t.color }}>{t.label}</span>
        </div>
      </div>

      <div className="xp-sp-section-title">Emotional profile</div>
      <div className="xp-bars">
        {topEmotions(p.emotion_breakdown).map(([k, v]) => (
          <div key={k} className="xp-bar-row">
            <span className="xp-bar-label">{fmt(k)}</span>
            <span className="xp-bar-track">
              <span className="xp-bar-fill" style={{ width: `${Math.round(v * 100)}%` }} />
            </span>
          </div>
        ))}
      </div>

      {nb.length > 0 && (
        <>
          <div className="xp-sp-section-title">Feels like</div>
          <div className="xp-feels">
            {nb.map((n) => {
              const nt = getMediaType(n.medium)
              return (
                <Link key={n.id} href={`/book/${n.id}`} className="xp-feels-item">
                  <BookCover url={n.cover_image_url} size="small" />
                  <div className="xp-feels-info">
                    <span className="xp-feels-title">{n.title}</span>
                    <span className="xp-feels-medium" style={{ color: nt.color }}>{nt.label}</span>
                  </div>
                </Link>
              )
            })}
          </div>
        </>
      )}

      <Link href={`/book/${p.id}`} className="xp-sp-link">View full page →</Link>
    </aside>
  )
}
