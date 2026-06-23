'use client'

import Link from 'next/link'
import BookCover from '@/components/BookCover'
import { getMediaType } from '@/components/mediaType'
import { getEmotionColor } from '@/components/emotionColors'

const fmt = (s) => s.replace(/_/g, ' ')

// One poster card used in the recommendation shelves (and the ratings grid).
// `item` is a full MediaResponse; `reasons` are optional ReasonOut chips; `badge`
// is an optional corner label (e.g. "92% match" or a resonance mark).
export default function ShelfCard({ item, reasons, badge }) {
  const t = getMediaType(item.medium)
  return (
    <Link href={`/book/${item.id}`} className="shelf-card" style={{ borderLeftColor: t.color }}>
      <BookCover url={item.cover_image_url} size="large" />
      <div className="shelf-card-title">{item.title}</div>
      <div className="shelf-card-author">{item.creator}</div>
      {badge && <span className="shelf-card-badge">{badge}</span>}
      {reasons?.length > 0 && (
        <div className="reason-tags">
          {reasons.slice(0, 2).map((rr) =>
            rr.kind === 'ending' ? (
              <span key={rr.key} className="reason-tag ending-tag">{rr.name}</span>
            ) : (
              <span
                key={rr.key}
                className="reason-tag"
                style={{ background: getEmotionColor(rr.key).bg, color: getEmotionColor(rr.key).color }}
              >
                {fmt(rr.key)}
              </span>
            )
          )}
        </div>
      )}
    </Link>
  )
}
