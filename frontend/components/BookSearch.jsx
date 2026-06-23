'use client'

import { useEffect, useRef, useState } from 'react'
import BookCover from '@/components/BookCover'
import EmotionFeedback from '@/components/EmotionFeedback'
import { topFeltEmotions } from '@/lib/emotions'

// Search the corpus, pick a work, mark how each of its top feelings landed, and log
// it. Extracted from the old /discover tool so it can power the ratings page.
export default function BookSearch({ books, onSelect }) {
  const [query, setQuery] = useState('')
  const [selectedBook, setSelectedBook] = useState(null)
  const [feedback, setFeedback] = useState({})
  const [showSuggestions, setShowSuggestions] = useState(false)
  const wrapperRef = useRef(null)

  const filtered = query.trim().length > 0
    ? books.filter((b) =>
        b.title.toLowerCase().includes(query.toLowerCase()) ||
        b.creator.toLowerCase().includes(query.toLowerCase())
      ).slice(0, 8)
    : []

  useEffect(() => {
    const handleClick = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) setShowSuggestions(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const pickBook = (book) => { setSelectedBook(book); setFeedback({}); setQuery(book.title); setShowSuggestions(false) }

  const handleSubmit = () => {
    if (!selectedBook) return
    onSelect(selectedBook.id, feedback)
    setSelectedBook(null); setQuery(''); setFeedback({})
  }

  const handleQueryChange = (e) => {
    setQuery(e.target.value)
    setShowSuggestions(true)
    if (selectedBook && e.target.value !== selectedBook.title) setSelectedBook(null)
  }

  return (
    <div className="add-book-form" ref={wrapperRef}>
      <div className="search-wrapper">
        <input
          type="text"
          value={query}
          onChange={handleQueryChange}
          onFocus={() => { if (!selectedBook && query.trim()) setShowSuggestions(true) }}
          placeholder="Search for a title or creator…"
          className="search-input"
        />
        {showSuggestions && filtered.length > 0 && (
          <div className="suggestions">
            {filtered.map((b) => (
              <button key={b.id} className="suggestion-item" onClick={() => pickBook(b)}>
                <span className="suggestion-title">{b.title}</span>
                <span className="suggestion-author">{b.creator}</span>
              </button>
            ))}
          </div>
        )}
        {showSuggestions && query.trim().length > 0 && filtered.length === 0 && (
          <div className="suggestions"><div className="suggestion-empty">No matches found</div></div>
        )}
      </div>

      {selectedBook && (
        <div className="log-panel">
          <div className="log-panel-head">
            <BookCover url={selectedBook.cover_image_url} size="small" />
            <div className="log-panel-meta">
              <span className="rated-title">{selectedBook.title}</span>
              <span className="rated-author">{selectedBook.creator}</span>
            </div>
          </div>
          <p className="log-hint">How did each feeling sit with you? Mark what you wanted more of — or less of — and skip the neutral ones.</p>
          <EmotionFeedback
            emotions={topFeltEmotions(selectedBook.emotion_breakdown)}
            value={feedback}
            onChange={setFeedback}
          />
          <button onClick={handleSubmit} className="add-btn" style={{ marginTop: '0.75rem' }}>Log this</button>
        </div>
      )}
    </div>
  )
}
