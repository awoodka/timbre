import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

export default function AddBook() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ title: '', author: '', isbn: '' })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.title.trim() || !form.author.trim()) return
    setSubmitting(true)
    setError(null)
    try {
      const book = await api.createBook({
        title: form.title.trim(),
        author: form.author.trim(),
        isbn: form.isbn.trim() || null,
      })
      navigate(`/book/${book.id}`)
    } catch (e) {
      setError(e.message)
      setSubmitting(false)
    }
  }

  return (
    <div style={{ maxWidth: 500 }}>
      <div className="page-header">
        <h1>Add a Book</h1>
        <p>The emotional analysis will run automatically after submission</p>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Title *</label>
          <input
            type="text"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            placeholder="e.g. The Great Gatsby"
            required
          />
        </div>
        <div className="form-group">
          <label>Author *</label>
          <input
            type="text"
            value={form.author}
            onChange={(e) => setForm({ ...form, author: e.target.value })}
            placeholder="e.g. F. Scott Fitzgerald"
            required
          />
        </div>
        <div className="form-group">
          <label>ISBN (optional)</label>
          <input
            type="text"
            value={form.isbn}
            onChange={(e) => setForm({ ...form, isbn: e.target.value })}
            placeholder="e.g. 978-0743273565"
          />
        </div>

        {error && <p style={{ color: 'var(--error)', marginBottom: '1rem' }}>{error}</p>}

        <button type="submit" disabled={submitting || !form.title.trim() || !form.author.trim()}>
          {submitting ? <><span className="spinner" /> Adding...</> : 'Add Book & Analyze'}
        </button>
      </form>
    </div>
  )
}
