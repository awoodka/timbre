const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export const api = {
  getBooks: () => request('/books'),
  getBook: (id) => request(`/books/${id}`),
  getSimilar: (id, limit = 5) => request(`/books/${id}/similar?limit=${limit}`),
  createBook: (data) => request('/books', { method: 'POST', body: JSON.stringify(data) }),
  reanalyze: (id) => request(`/books/${id}/reanalyze`, { method: 'POST' }),
  recommend: (ratings, limit = 10) =>
    request('/recommend', { method: 'POST', body: JSON.stringify({ ratings, limit }) }),
  getDimensions: () => request('/dimensions'),
}
