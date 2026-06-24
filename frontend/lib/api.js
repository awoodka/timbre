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
  recommend: (limit = 10, medium = null) =>
    request('/recommend', { method: 'POST', body: JSON.stringify({ limit, ...(medium ? { medium } : {}) }) }),
  // Experience search: compose a mood (seek/avoid feelings), an ending tone, and
  // how much to lean on it vs. your usual taste. Ungated (works with no ratings).
  recommendExperience: ({ mood = {}, ending = 'any', alpha = 0.6, limit = 12, medium = null } = {}) =>
    request('/recommend', {
      method: 'POST',
      body: JSON.stringify({ mood, ending, alpha, limit, ...(medium ? { medium } : {}) }),
    }),
  // Natural-language search: a free-text description parsed (Gemini) into the same
  // mood/ending/medium query server-side. One round-trip → ranked recs.
  recommendNL: ({ description, limit = 12 } = {}) =>
    request('/recommend', { method: 'POST', body: JSON.stringify({ description, limit }) }),
  getDimensions: () => request('/dimensions'),
  getProjection: (method = 'umap') => request(`/projection?method=${method}`),

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
  putRating: (media_id, feedback) =>
    request(`/ratings/${media_id}`, { method: 'PUT', body: JSON.stringify({ feedback }) }),
  deleteRating: (media_id) => request(`/ratings/${media_id}`, { method: 'DELETE' }),

  // ---- watchlist / saved-for-later ----
  getSaves: () => request('/saves'),
  postSave: (media_id) => request(`/saves/${media_id}`, { method: 'POST' }),
  deleteSave: (media_id) => request(`/saves/${media_id}`, { method: 'DELETE' }),
}
