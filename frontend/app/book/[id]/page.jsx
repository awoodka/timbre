'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { api } from '@/lib/api'
import BookCover from '@/components/BookCover'
import EmotionRadar from '@/components/EmotionRadar'
import EmotionBar from '@/components/EmotionBar'
import SaveButton from '@/components/SaveButton'
import EmotionFeedback from '@/components/EmotionFeedback'
import StarRating from '@/components/StarRating'
import { useAuth } from '@/lib/auth-context'
import { useRatings } from '@/lib/ratings-context'
import { useSaves } from '@/lib/saves-context'
import { topFeltEmotions } from '@/lib/emotions'

export default function BookDetail() {
  const { id } = useParams()
  const router = useRouter()
  const { user } = useAuth()
  const { ratings, rate, removeRating } = useRatings()
  const { isSaved, removeSave } = useSaves()
  const [book, setBook] = useState(null)
  const [similar, setSimilar] = useState([])
  const [loading, setLoading] = useState(true)
  const [showBars, setShowBars] = useState(false)
  const [rateOpen, setRateOpen] = useState(false)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      api.getItem(id),
      api.getSimilar(id, 5).catch(() => []),
    ]).then(([b, s]) => {
      setBook(b)
      setSimilar(s)
    }).finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="loading"><span className="spinner" /> Loading...</div>
  if (!book) return <div className="loading">Book not found</div>

  const myRating = ratings.find((r) => r.media_id === book.id)
  const emotions = topFeltEmotions(book.emotion_breakdown)
  const onRate = (fb) => { rate(book.id, fb, myRating?.enjoyment ?? null); if (isSaved(book.id)) removeSave(book.id) }
  const onEnjoy = (n) => { rate(book.id, myRating?.feedback || {}, n || null); if (isSaved(book.id)) removeSave(book.id) }

  return (
    <div className="book-detail">
      <button
        type="button"
        onClick={() => (window.history.length > 1 ? router.back() : router.push('/catalogue'))}
        style={{ background: 'none', border: 'none', padding: 0, color: 'var(--text-muted)', fontSize: '0.85rem', cursor: 'pointer' }}
      >
        &larr; Back
      </button>

      <div className="detail-header">
        <BookCover url={book.cover_image_url} size="large" />
        <div className="detail-header-info">
          <h1>{book.title}</h1>
          <div className="author">{book.creator}</div>
          {book.metadata && (
            <div className="detail-meta">
              {book.metadata.year && <span>{book.metadata.year}</span>}
              {book.metadata.genre && <span> &middot; {book.metadata.genre.join(', ')}</span>}
            </div>
          )}
          <div className="detail-actions">
            <SaveButton mediaId={book.id} label />
            <button
              type="button"
              className={`rate-toggle${myRating ? ' rated' : ''}`}
              onClick={() => { if (!user) { router.push('/login'); return } setRateOpen((o) => !o) }}
              aria-expanded={rateOpen}
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round">
                <circle cx="8" cy="8" r="6" />
                <path d="M5.4 9.4a3.2 3.2 0 0 0 5.2 0" />
                <circle cx="6" cy="6.6" r="0.55" fill="currentColor" stroke="none" />
                <circle cx="10" cy="6.6" r="0.55" fill="currentColor" stroke="none" />
              </svg>
              {myRating ? 'Edit rating' : 'Rate'}
            </button>
          </div>
        </div>
      </div>

      {rateOpen && user && (
        <div className="detail-rating">
          <div className="rate-enjoy">
            <span className="rate-enjoy-label">How much did you enjoy it?</span>
            <StarRating value={myRating?.enjoyment || 0} onChange={onEnjoy} />
          </div>
          <h2 className="section-title">How did it make you feel?</h2>
          {emotions.length > 0 ? (
            <EmotionFeedback emotions={emotions} value={myRating?.feedback || {}} onChange={onRate} />
          ) : (
            <p style={{ color: 'var(--text-muted)' }}>Not analyzed yet — rate it with a star above.</p>
          )}
          {myRating && (
            <button type="button" className="mc-clear" onClick={() => removeRating(book.id)} style={{ marginTop: '0.5rem' }}>
              Remove rating
            </button>
          )}
        </div>
      )}

      {book.description && (
        <>
          <h2 className="section-title">Emotional Profile</h2>
          <div className="description">{book.description}</div>
        </>
      )}

      {book.emotion_breakdown && (
        <>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginTop: '2rem' }}>
            <h2 className="section-title" style={{ margin: 0 }}>Emotional Breakdown</h2>
            <button
              onClick={() => setShowBars(!showBars)}
              style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem', background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text-muted)' }}
            >
              {showBars ? 'Radar View' : 'Bar View'}
            </button>
          </div>
          {showBars ? (
            <EmotionBar breakdown={book.emotion_breakdown} />
          ) : (
            <EmotionRadar breakdown={book.emotion_breakdown} size={450} />
          )}
        </>
      )}

      {similar.length > 0 && (
        <>
          <h2 className="section-title">Emotionally Similar Books</h2>
          <div className="similar-list">
            {similar.map(({ item: sim, similarity }) => (
              <Link key={sim.id} href={`/book/${sim.id}`} className="similar-item">
                <BookCover url={sim.cover_image_url} size="small" />
                <div className="info">
                  <h4>{sim.title}</h4>
                  <div className="author">{sim.creator}</div>
                </div>
                <span className="similarity-badge">{(similarity * 100).toFixed(1)}% match</span>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
