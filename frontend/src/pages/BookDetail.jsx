import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '../api/client'
import EmotionRadar from '../components/EmotionRadar'
import EmotionBar from '../components/EmotionBar'

export default function BookDetail() {
  const { id } = useParams()
  const [book, setBook] = useState(null)
  const [similar, setSimilar] = useState([])
  const [loading, setLoading] = useState(true)
  const [showBars, setShowBars] = useState(false)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      api.getBook(id),
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
      <Link to="/" style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textDecoration: 'none' }}>
        &larr; Back
      </Link>

      <h1 style={{ marginTop: '1rem' }}>{book.title}</h1>
      <div className="author">{book.author}</div>

      {book.metadata && (
        <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: '0.25rem 0 1rem' }}>
          {book.metadata.year && <span>{book.metadata.year}</span>}
          {book.metadata.genre && (
            <span> &middot; {book.metadata.genre.join(', ')}</span>
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
            {similar.map(({ book: sim, similarity }) => (
              <Link key={sim.id} to={`/book/${sim.id}`} className="similar-item">
                <div className="info">
                  <h4>{sim.title}</h4>
                  <div className="author">{sim.author}</div>
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
