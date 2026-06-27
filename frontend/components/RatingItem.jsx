'use client'

import Link from 'next/link'
import BookCover from '@/components/BookCover'
import EmotionFeedback from '@/components/EmotionFeedback'
import FeedbackSummary from '@/components/FeedbackSummary'
import StarRating from '@/components/StarRating'
import { getMediaType } from '@/components/mediaType'
import { topFeltEmotions } from '@/lib/emotions'

// One rated work, rendered as a poster card (grid) or a compact row (list). Edit /
// remove state lives in the parent so both layouts behave identically.
export default function RatingItem({
  view, rating, book, editing, confirming,
  onEdit, onRate, onAskRemove, onConfirmRemove, onCancelRemove,
}) {
  const t = getMediaType(book.medium)

  const Controls = () => (
    <div className="ri-controls">
      <button className="link-btn" onClick={() => onEdit(editing ? null : rating.media_id)}>
        {editing ? 'Done' : 'Edit'}
      </button>
      {confirming ? (
        <div className="confirm-delete">
          <span className="confirm-text">Remove?</span>
          <button className="confirm-yes" onClick={() => onConfirmRemove(rating.media_id)}>Yes</button>
          <button className="confirm-no" onClick={onCancelRemove}>No</button>
        </div>
      ) : (
        <button className="remove-btn" onClick={() => onAskRemove(rating.media_id)} title="Remove">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
            <path d="M2 4h12M5.3 4V2.7a1 1 0 011-1h3.4a1 1 0 011 1V4M6.5 7v4.5M9.5 7v4.5M3.5 4l.7 9a1.5 1.5 0 001.5 1.4h4.6a1.5 1.5 0 001.5-1.4l.7-9" />
          </svg>
        </button>
      )}
    </div>
  )

  const editor = (
    <div className="ri-editor">
      <div className="rate-enjoy">
        <span className="rate-enjoy-label">Enjoyment</span>
        <StarRating value={rating.enjoyment || 0} onChange={(n) => onRate(rating.media_id, rating.feedback, n || null)} />
      </div>
      <EmotionFeedback
        emotions={topFeltEmotions(book.emotion_breakdown)}
        value={rating.feedback}
        onChange={(fb) => onRate(rating.media_id, fb, rating.enjoyment ?? null)}
      />
    </div>
  )

  const summary = (
    <div className="ri-summary">
      {rating.enjoyment ? <StarRating value={rating.enjoyment} readOnly size="sm" /> : null}
      <FeedbackSummary feedback={rating.feedback} />
    </div>
  )

  if (view === 'grid') {
    return (
      <div className="rating-card" style={{ borderLeftColor: t.color }}>
        <Link href={`/book/${book.id}`} className="rating-card-link">
          <BookCover url={book.cover_image_url} size="large" />
          <div className="rating-card-title">{book.title}</div>
          <div className="rating-card-author">{book.creator}</div>
        </Link>
        {editing ? editor : summary}
        <Controls />
      </div>
    )
  }

  return (
    <div className="rating-row logged">
      <div className="logged-head">
        <BookCover url={book.cover_image_url} size="small" />
        <Link href={`/book/${book.id}`} className="rated-book-info">
          <span className="rated-title">{book.title}</span>
          <span className="rated-author">{book.creator}</span>
        </Link>
        <Controls />
      </div>
      {editing ? editor : summary}
    </div>
  )
}
