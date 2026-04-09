import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'

function TopEmotions({ breakdown }) {
  if (!breakdown) return null
  const top = Object.entries(breakdown)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
  return (
    <div className="emotion-dots">
      {top.map(([key, val]) => (
        <span key={key} className="emotion-dot">
          {key.replace(/_/g, ' ')} {val.toFixed(1)}
        </span>
      ))}
    </div>
  )
}

export default function Library() {
  const [books, setBooks] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getBooks().then(setBooks).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading"><span className="spinner" /> Loading books...</div>

  return (
    <div>
      <div className="page-header">
        <h1>Library</h1>
        <p>All {books.length} books and their emotional fingerprints</p>
      </div>
      <div className="book-grid">
        {books.map((book) => (
          <Link key={book.id} to={`/book/${book.id}`} className="book-card">
            {book.cover_image_url && (
              <img src={book.cover_image_url} alt="" className="book-cover" />
            )}
            <div className="book-card-info">
              <h3>{book.title}</h3>
              <div className="author">{book.author}</div>
              <TopEmotions breakdown={book.emotion_breakdown} />
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
