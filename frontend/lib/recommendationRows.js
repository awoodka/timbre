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

// Build the ordered, tier-filtered row descriptors for the recommendations page.
// Rows that need taste (Top picks, Beyond books) only appear at >= 4 ratings;
// "Because you loved X" needs >= 1; mood/arc rows are ungated (work at 0 ratings).
export function buildRows({ ratings = [], mediaById = {} }) {
  const n = ratings.length
  const hasTaste = n > 0
  const rows = []

  if (n >= 4) {
    rows.push({
      id: 'top-picks',
      title: 'Top picks for you',
      subtitle: 'Matched to your emotional taste',
      fetcher: () => api.recommend(18).then(recs),
    })
  }

  // Because you loved {title} — highest resonance, distinct, up to 3.
  ;[...ratings]
    .filter((r) => mediaById[r.media_id])
    .sort((a, b) => (b.resonance ?? 0.5) - (a.resonance ?? 0.5))
    .slice(0, 3)
    .forEach((r) => {
      rows.push({
        id: `loved-${r.media_id}`,
        title: `Because you loved ${mediaById[r.media_id].title}`,
        subtitle: 'More with the same feeling',
        fetcher: () => api.getSimilar(r.media_id, 18),
      })
    })

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
