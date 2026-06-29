import { api } from '@/lib/api'

// 4 mood presets drawn from the explore-page REGIONS (same seed/avoid feelings the
// MoodComposer uses). Each becomes a "When you want …" row via experience search.
const PRESETS = {
  comfort: {
    title: 'When you want comfort', sub: 'A mood, not a genre',
    seek: ['warmth', 'serenity', 'hope', 'intimacy'], avoid: ['dread', 'tension', 'grief'],
  },
  awe: {
    title: 'When you want awe', sub: 'Vast, wondrous, sublime',
    seek: ['wonder', 'vastness', 'hope'], avoid: ['claustrophobia'],
  },
  tension: {
    title: 'When you want a thrill', sub: 'Tense, harrowing, edge-of-seat',
    seek: ['tension', 'dread', 'frenetic_energy'], avoid: ['serenity', 'warmth', 'stillness'],
  },
  intimacy: {
    title: 'When you want something tender', sub: 'Close, vulnerable, human',
    seek: ['intimacy', 'vulnerability', 'sensuality', 'warmth'], avoid: ['vastness', 'frenetic_energy'],
  },
}

// seek/avoid → the experience-search mood map { key: +1 | -1 } (NOT the ±2 rating scale).
const toMoodMap = ({ seek = [], avoid = [] }) => ({
  ...Object.fromEntries(seek.map((k) => [k, 1])),
  ...Object.fromEntries(avoid.map((k) => [k, -1])),
})

const recs = (p) => p.recommendations || []

// Build the secondary row descriptors for the recommendations page (mood + arc +
// cross-media). The personalized taste rows ("Because you loved X — feelings") are the
// multi-modal taste modes from /recommend/modes, rendered separately by the page.
export function buildRows({ ratings = [] }) {
  const n = ratings.length
  const hasTaste = n > 0
  const rows = []

  // Mood rows — experience search (blends taste once available via alpha).
  Object.entries(PRESETS).forEach(([key, p]) => {
    rows.push({
      id: `mood-${key}`,
      title: p.title,
      subtitle: p.sub,
      fetcher: () =>
        api.recommendExperience({ mood: toMoodMap(p), alpha: hasTaste ? 0.6 : 1.0, limit: 18 }).then(recs),
    })
  })

  // Arc rows — leverage the ending/arc signal.
  rows.push({
    id: 'arc-uplifting',
    title: 'Uplifting endings',
    subtitle: 'Works that land on hope',
    fetcher: () => api.recommendExperience({ ending: 'uplifting', alpha: hasTaste ? 0.6 : 0.0, limit: 18 }).then(recs),
  })
  rows.push({
    id: 'arc-bleak',
    title: 'For a good cry',
    subtitle: 'Bleak, devastating endings',
    fetcher: () => api.recommendExperience({ ending: 'bleak', alpha: hasTaste ? 0.6 : 0.0, limit: 18 }).then(recs),
  })

  if (n >= 4) {
    rows.push({
      id: 'beyond-books',
      title: 'Beyond books',
      subtitle: 'Your taste, in film',
      fetcher: () => api.recommend(18, 'film').then(recs),
    })
  }

  return rows
}
