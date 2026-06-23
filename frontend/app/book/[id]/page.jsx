'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { api } from '@/lib/api'
import BookCover from '@/components/BookCover'
import EmotionRadar from '@/components/EmotionRadar'
import EmotionBar from '@/components/EmotionBar'
import SaveButton from '@/components/SaveButton'

export default function BookDetail() {
  const { id } = useParams()
  const router = useRouter()
  const [book, setBook] = useState(null)
  const [similar, setSimilar] = useState([])
  const [loading, setLoading] = useState(true)
  const [showBars, setShowBars] = useState(false)

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
          </div>
        </div>
      </div>

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
