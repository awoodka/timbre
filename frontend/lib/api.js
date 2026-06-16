const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    credentials: 'include',
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
  getMedia: () => request('/media'),
  getItem: (id) => request(`/media/${id}`),
  getSimilar: (id, limit = 5) => request(`/media/${id}/similar?limit=${limit}`),
  createItem: (data) => request('/media', { method: 'POST', body: JSON.stringify(data) }),
  reanalyze: (id) => request(`/media/${id}/reanalyze`, { method: 'POST' }),
  recommend: (ratings, limit = 10) =>
    request('/recommend', { method: 'POST', body: JSON.stringify({ ratings, limit }) }),
  getDimensions: () => request('/dimensions'),

  // ---- auth ----
  me: () => request('/auth/me'),
  signup: (username, password, display_name) =>
    request('/auth/signup', { method: 'POST', body: JSON.stringify({ username, password, display_name }) }),
  login: (username, password) =>
    request('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) }),
  logout: () => request('/auth/logout', { method: 'POST' }),
  updateProfile: (data) => request('/auth/me', { method: 'PATCH', body: JSON.stringify(data) }),

  // ---- per-user ratings ----
  getRatings: () => request('/ratings'),
  putRating: (media_id, rating) =>
    request(`/ratings/${media_id}`, { method: 'PUT', body: JSON.stringify({ rating }) }),
  deleteRating: (media_id) => request(`/ratings/${media_id}`, { method: 'DELETE' }),
}
