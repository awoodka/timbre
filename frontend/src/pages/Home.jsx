import { useEffect, useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import StarRating from '../components/StarRating'
import BookCover from '../components/BookCover'

function BookSearch({ books, onSelect }) {
  const [query, setQuery] = useState('')
  const [selectedBook, setSelectedBook] = useState(null)
  const [rating, setRating] = useState(0)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const wrapperRef = useRef(null)

  const filtered = query.trim().length > 0
    ? books.filter((b) =>
        b.title.toLowerCase().includes(query.toLowerCase()) ||
        b.author.toLowerCase().includes(query.toLowerCase())
      ).slice(0, 8)
    : []

  useEffect(() => {
    const handleClick = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setShowSuggestions(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const pickBook = (book) => {
    setSelectedBook(book)
    setQuery(book.title)
    setShowSuggestions(false)
  }

  const handleSubmit = () => {
    if (!selectedBook || rating === 0) return
    onSelect(selectedBook.id, rating)
    setSelectedBook(null)
    setQuery('')
    setRating(0)
  }

  const handleQueryChange = (e) => {
    setQuery(e.target.value)
    setShowSuggestions(true)
    if (selectedBook && e.target.value !== selectedBook.title) {
      setSelectedBook(null)
    }
  }

  return (
    <div className="add-book-form" ref={wrapperRef}>
      <div className="add-book-row">
        <div className="search-wrapper">
          <input
            type="text"
            value={query}
            onChange={handleQueryChange}
            onFocus={() => { if (!selectedBook && query.trim()) setShowSuggestions(true) }}
            placeholder="Search for a book title or author..."
            className="search-input"
          />
          {showSuggestions && filtered.length > 0 && (
            <div className="suggestions">
              {filtered.map((b) => (
                <button
                  key={b.id}
                  className="suggestion-item"
                  onClick={() => pickBook(b)}
                >
                  <span className="suggestion-title">{b.title}</span>
                  <span className="suggestion-author">{b.author}</span>
                </button>
              ))}
            </div>
          )}
          {showSuggestions && query.trim().length > 0 && filtered.length === 0 && (
            <div className="suggestions">
              <div className="suggestion-empty">No matching books found</div>
            </div>
          )}
        </div>
        <StarRating value={rating} onChange={setRating} />
        <button
          onClick={handleSubmit}
          disabled={!selectedBook || rating === 0}
          className="add-btn"
        >
          Add
        </button>
      </div>
    </div>
  )
}

export default function Home({ ratings, setRatings, results, setResults }) {
  const [books, setBooks] = useState([])
  const [loading, setLoading] = useState(false)
  const [booksLoading, setBooksLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.getBooks()
      .then((b) => setBooks(b.filter((x) => x.analysis_status === 'completed')))
      .finally(() => setBooksLoading(false))
  }, [])

  const available = books.filter((b) => !ratings.find((r) => r.book_id === b.id))

  const addRating = (bookId, rating) => {
    setRatings([...ratings, { book_id: bookId, rating }])
    setResults(null)
  }

  const updateRating = (idx, rating) => {
    const updated = [...ratings]
    updated[idx] = { ...updated[idx], rating }
    setRatings(updated)
    setResults(null)
  }

  const removeRating = (idx) => {
    setRatings(ratings.filter((_, i) => i !== idx))
    setResults(null)
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

  const getMatchReasons = (recBook) => {
    if (!recBook.emotion_breakdown) return []
    return Object.entries(recBook.emotion_breakdown)
      .filter(([, v]) => v >= 0.5)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 4)
      .map(([k]) => k.replace(/_/g, ' '))
  }

  if (booksLoading) return <div className="loading"><span className="spinner" /> Loading...</div>

  return (
    <div>
      <div className="page-header">
        <h1>What books have you read?</h1>
        <p>Rate books you've read and we'll find ones that feel the same</p>
      </div>

      {/* Add book form */}
      <BookSearch books={available} onSelect={addRating} />

      {/* Rated books */}
      {ratings.length > 0 && (
        <div style={{ marginTop: '1.5rem' }}>
          <h2 className="section-title" style={{ marginTop: 0 }}>Your Rated Books</h2>
          <div className="rating-list">
            {ratings.map((r, idx) => {
              const book = books.find((b) => b.id === r.book_id)
              if (!book) return null
              return (
                <div key={r.book_id} className="rating-row">
                  <BookCover url={book.cover_image_url} size="small" />
                  <Link to={`/book/${book.id}`} className="rated-book-info">
                    <span className="rated-title">{book.title}</span>
                    <span className="rated-author">{book.author}</span>
                  </Link>
                  <StarRating value={r.rating} onChange={(val) => updateRating(idx, val)} />
                  <button className="remove-btn" onClick={() => removeRating(idx)}>&times;</button>
                </div>
              )
            })}
          </div>

          <button
            onClick={getRecommendations}
            disabled={loading}
            style={{ marginTop: '0.75rem' }}
          >
            {loading ? <><span className="spinner" /> Finding matches...</> : 'Find Recommendations'}
          </button>
        </div>
      )}

      {error && <p style={{ color: 'var(--error)', marginTop: '1rem' }}>{error}</p>}

      {/* Recommendations */}
      {results && (
        <div style={{ marginTop: '2rem' }}>
          <h2 className="section-title" style={{ marginTop: 0 }}>Your Recommendations</h2>
          {results.length === 0 ? (
            <p style={{ color: 'var(--text-muted)' }}>No matches found — try rating more books.</p>
          ) : (
            <div className="similar-list">
              {results.map(({ book, similarity }) => (
                <Link key={book.id} to={`/book/${book.id}`} className="similar-item">
                  <BookCover url={book.cover_image_url} size="small" />
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
            </div>
          )}
        </div>
      )}

      {/* Empty state */}
      {!results && ratings.length === 0 && (
        <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
          <p style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>
            Search for a book above to get started
          </p>
          <p style={{ fontSize: '0.85rem' }}>
            We'll match you with books that evoke similar emotions — not just similar genres
          </p>
        </div>
      )}
    </div>
  )
}
