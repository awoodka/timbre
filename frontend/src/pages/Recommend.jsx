import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'

export default function Recommend() {
  const [books, setBooks] = useState([])
  const [ratings, setRatings] = useState([])
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.getBooks().then((b) => setBooks(b.filter((x) => x.analysis_status === 'completed')))
  }, [])

  const addRating = () => {
    const available = books.filter((b) => !ratings.find((r) => r.book_id === b.id))
    if (available.length === 0) return
    setRatings([...ratings, { book_id: available[0].id, rating: 4 }])
  }

  const updateRating = (idx, field, value) => {
    const updated = [...ratings]
    updated[idx] = { ...updated[idx], [field]: value }
    setRatings(updated)
  }

  const removeRating = (idx) => {
    setRatings(ratings.filter((_, i) => i !== idx))
  }

  const getRecommendations = async () => {
    if (ratings.length === 0) return
    setLoading(true)
    setError(null)
    try {
      const res = await api.recommend(ratings)
      setResults(res)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const available = books.filter((b) => !ratings.find((r) => r.book_id === b.id))

  // Find matching emotion keys between a rec'd book and rated books
  const getMatchReasons = (recBook) => {
    if (!recBook.emotion_breakdown) return []
    return Object.entries(recBook.emotion_breakdown)
      .filter(([, v]) => v >= 0.5)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 4)
      .map(([k]) => k.replace(/_/g, ' '))
  }

  return (
    <div>
      <div className="page-header">
        <h1>Get Recommendations</h1>
        <p>Rate books you've read and discover emotionally similar ones</p>
      </div>

      <div className="rating-list">
        {ratings.map((r, idx) => {
          const book = books.find((b) => b.id === r.book_id)
          return (
            <div key={idx} className="rating-row">
              <select
                value={r.book_id}
                onChange={(e) => updateRating(idx, 'book_id', e.target.value)}
                style={{ flex: 1, background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--text)', padding: '0.5rem', borderRadius: 6, fontSize: '0.9rem' }}
              >
                {book && <option value={book.id}>{book.title} — {book.author}</option>}
                {available.map((b) => (
                  <option key={b.id} value={b.id}>{b.title} — {b.author}</option>
                ))}
              </select>
              <select
                className="star-select"
                value={r.rating}
                onChange={(e) => updateRating(idx, 'rating', Number(e.target.value))}
              >
                {[1, 2, 3, 4, 5].map((n) => (
                  <option key={n} value={n}>{'★'.repeat(n)}{'☆'.repeat(5 - n)}</option>
                ))}
              </select>
              <button className="remove-btn" onClick={() => removeRating(idx)}>&times;</button>
            </div>
          )
        })}
      </div>

      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '2rem' }}>
        <button onClick={addRating} disabled={available.length === 0}
          style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
          + Add Book
        </button>
        <button onClick={getRecommendations} disabled={ratings.length === 0 || loading}>
          {loading ? <><span className="spinner" /> Finding...</> : 'Get Recommendations'}
        </button>
      </div>

      {error && <p style={{ color: 'var(--error)', marginBottom: '1rem' }}>{error}</p>}

      {results && (
        <>
          <h2 className="section-title">Recommended For You</h2>
          <div className="similar-list">
            {results.map(({ book, similarity }) => (
              <Link key={book.id} to={`/book/${book.id}`} className="similar-item">
                <div className="info">
                  <h4>{book.title}</h4>
                  <div className="author">{book.author}</div>
                  <div className="reason-tags">
                    {getMatchReasons(book).map((r) => (
                      <span key={r} className="reason-tag">{r}</span>
                    ))}
                  </div>
                </div>
                <span className="similarity-badge">{(similarity * 100).toFixed(1)}% match</span>
              </Link>
            ))}
            {results.length === 0 && (
              <p style={{ color: 'var(--text-muted)' }}>No recommendations found. Try adding more books to the library first.</p>
            )}
          </div>
        </>
      )}
    </div>
  )
}
