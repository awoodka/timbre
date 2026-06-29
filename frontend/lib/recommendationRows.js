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

// The user's loved work that best fits a mood's sought feelings — named in the row so
// the personalization is concrete ("leaning on your love of X"). Returns a work only
// when it genuinely fits, so we never name a weak match.
function topLovedFor(ratings, mediaById, seek) {
  let best = null
  let bestScore = 0.45 // floor: don't name a work that barely fits the mood
  for (const r of ratings) {
    const bd = mediaById[r.media_id]?.emotion_breakdown
    if (!bd) continue
    const fit = seek.reduce((s, k) => s + (bd[k] || 0), 0) / seek.length
    const score = fit * (r.resonance ?? 0.5) // fits the mood AND is loved
    if (score > bestScore) { bestScore = score; best = mediaById[r.media_id] }
  }
  return best
}

// Build the secondary row descriptors for the recommendations page (mood + arc +
// cross-media). The personalized taste rows ("Because you loved X — feelings") are the
// multi-modal taste modes from /recommend/modes, rendered separately by the page. These
// rows blend your taste too (via alpha); when they do, we flag it + name a loved work.
export function buildRows({ ratings = [], mediaById = {} }) {
  const n = ratings.length
  const hasTaste = n > 0
  const rows = []

  // Mood rows — experience search blends your taste (alpha) once you've rated. When it
  // does, flag it ("tuned to you") + name the loved work that most fits the mood.
  Object.entries(PRESETS).forEach(([key, p]) => {
    const anchor = hasTaste ? topLovedFor(ratings, mediaById, p.seek) : null
    rows.push({
      id: `mood-${key}`,
      title: p.title,
      subtitle: anchor ? `Leaning on your love of ${anchor.title}` : hasTaste ? 'Blended with your taste' : p.sub,
      tuned: hasTaste,
      fetcher: () =>
        api.recommendExperience({ mood: toMoodMap(p), alpha: hasTaste ? 0.6 : 1.0, limit: 18 }).then(recs),
    })
  })

  // Arc rows — leverage the ending/arc signal.
  rows.push({
    id: 'arc-uplifting',
    title: 'Uplifting endings',
    subtitle: hasTaste ? 'Hopeful landings, tuned to your taste' : 'Works that land on hope',
    tuned: hasTaste,
    fetcher: () => api.recommendExperience({ ending: 'uplifting', alpha: hasTaste ? 0.6 : 0.0, limit: 18 }).then(recs),
  })
  rows.push({
    id: 'arc-bleak',
    title: 'For a good cry',
    subtitle: hasTaste ? 'Devastating endings, tuned to your taste' : 'Bleak, devastating endings',
    tuned: hasTaste,
    fetcher: () => api.recommendExperience({ ending: 'bleak', alpha: hasTaste ? 0.6 : 0.0, limit: 18 }).then(recs),
  })

  if (n >= 4) {
    rows.push({
      id: 'beyond-books',
      title: 'Beyond books',
      subtitle: 'Your taste, in film',
      tuned: true,
      fetcher: () => api.recommend(18, 'film').then(recs),
    })
  }

  return rows
}
