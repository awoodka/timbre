// Client-side taste derivations for the "Your emotional fingerprint" page. Mirrors
// backend/app/services/feedback.py so it stays consistent with the recommender, and
// reuses the explore-page valence/energy/scope axes. All pure; guards empties.

// The 25 felt emotions in EMOTIONAL_DIMENSIONS order (fixed → a stable radar shape).
export const FELT = [
  'isolation', 'wonder', 'dread', 'melancholy', 'warmth', 'tension', 'joy', 'nostalgia',
  'anger', 'serenity', 'confusion', 'empowerment', 'vulnerability', 'absurdity', 'intimacy',
  'alienation', 'obsession', 'grief', 'hope', 'claustrophobia', 'vastness', 'sensuality',
  'moral_ambiguity', 'frenetic_energy', 'stillness',
]

// Curated feeling axes (signed sums), copied from app/explore/page.jsx AXES.
const AXES = {
  valence: {
    pos: ['warmth', 'joy', 'hope', 'serenity', 'nostalgia', 'intimacy', 'empowerment', 'catharsis', 'ending_valence', 'sensuality', 'wonder'],
    neg: ['dread', 'grief', 'melancholy', 'isolation', 'alienation', 'anger', 'claustrophobia', 'obsession', 'confusion', 'vulnerability'],
  },
  energy: {
    pos: ['frenetic_energy', 'tension', 'pacing', 'anger', 'obsession', 'empowerment'],
    neg: ['stillness', 'serenity', 'melancholy', 'nostalgia', 'intimacy'],
  },
  scope: {
    pos: ['vastness', 'wonder', 'emotional_complexity', 'moral_ambiguity'],
    neg: ['intimacy', 'vulnerability', 'sensuality', 'claustrophobia'],
  },
}

const fmt = (s) => s.replace(/_/g, ' ')

// w_e = Σ marks / (count + 1) over felt emotions (matches build_taste_profile).
export function buildTasteProfile(feedbackMaps) {
  const sums = {}, counts = {}
  for (const k of FELT) { sums[k] = 0; counts[k] = 0 }
  for (const fb of feedbackMaps || []) {
    for (const [k, mark] of Object.entries(fb || {})) {
      if (k in sums && mark) { sums[k] += mark; counts[k] += 1 }
    }
  }
  const profile = {}
  for (const k of FELT) profile[k] = counts[k] ? sums[k] / (counts[k] + 1) : 0
  return profile
}

export function lovedAvoided(profile, n = 6) {
  const entries = Object.entries(profile)
  const loved = entries.filter(([, w]) => w > 0).sort((a, b) => b[1] - a[1]).slice(0, n)
  const avoided = entries.filter(([, w]) => w < 0).sort((a, b) => a[1] - b[1]).slice(0, n)
  return { loved, avoided } // arrays of [key, weight]
}

export function tasteAxes(profile) {
  const axis = (spec) => {
    let s = 0
    for (const k of spec.pos) s += profile[k] || 0
    for (const k of spec.neg) s -= profile[k] || 0
    return s
  }
  return { valence: axis(AXES.valence), energy: axis(AXES.energy), scope: axis(AXES.scope) }
}

// Playful persona from the axis signature. Heuristic thresholds (tune by eye); a
// neutral fallback catches anyone without a clear lean.
export function archetype(axes) {
  const { valence: v, energy: e, scope: s } = axes
  if (s > 0.6) return { name: 'The Stargazer', blurb: 'You chase the vast and the sublime — wonder over comfort.' }
  if (v < -0.4 && e > 0.4) return { name: 'The Thrill-Seeker', blurb: 'You run toward tension and dread — the harrowing thrill.' }
  if (v < -0.4) return { name: 'The Melancholy Wanderer', blurb: 'You sit with sorrow and longing; you find the beauty in the bleak.' }
  if (v > 0.4 && e > 0.4) return { name: 'The Bright Spark', blurb: 'You want joy with a pulse — lively, warm, and alive.' }
  if (v > 0.4 && e <= 0) return { name: 'The Hearthkeeper', blurb: 'You seek comfort, warmth, and a soft place to land.' }
  if (s < -0.4 && v > -0.1) return { name: 'The Tender Heart', blurb: 'You live for intimacy and the quiet, close, human moments.' }
  return { name: 'The Omnivore', blurb: 'Your taste roams widely — no single mood owns you.' }
}

export function personaLine(loved, avoided) {
  const top = loved.slice(0, 2).map(([k]) => fmt(k))
  const av = avoided.slice(0, 1).map(([k]) => fmt(k))
  if (!top.length && !av.length) return 'Rate a few works and your taste will take shape here.'
  const love = top.length ? `drawn to ${top.join(' + ')}` : 'still finding your pull'
  const avoid = av.length ? `, and you steer clear of ${av[0]}` : ''
  return `You're ${love}${avoid}.`
}

// Resonance-weighted ending/arc lean from the works' breakdowns (the arc dims the
// taste weights ignore). Weighting by resonance → "the endings of works that landed."
export function arcPreference(ratedWorks) {
  let wsum = 0, ev = 0, tr = 0, n = 0
  for (const r of ratedWorks || []) {
    const bd = r.book?.emotion_breakdown
    if (!bd || bd.ending_valence == null) continue
    const w = r.resonance ?? 0.5
    ev += bd.ending_valence * w
    tr += (bd.emotional_trajectory ?? 0.5) * w
    wsum += w; n += 1
  }
  if (!n || wsum === 0) return null
  const e = ev / wsum, t = tr / wsum
  return {
    endingValue: e,
    trajectoryValue: t,
    ending: e < 0.4 ? 'bleak' : e < 0.6 ? 'bittersweet' : 'uplifting',
    arc: t < 0.4 ? 'descending' : t < 0.6 ? 'steady' : 'rising',
  }
}

export function mediaSplit(ratedWorks) {
  const counts = {}
  for (const r of ratedWorks || []) {
    const m = r.book?.medium
    if (m) counts[m] = (counts[m] || 0) + 1
  }
  return counts
}

export function resonanceStats(ratings) {
  const bands = { loved: 0, liked: 0, neutral: 0, notForMe: 0 }
  for (const r of ratings || []) {
    const v = r.resonance ?? 0.5
    if (v >= 0.75) bands.loved++
    else if (v >= 0.55) bands.liked++
    else if (v >= 0.45) bands.neutral++
    else bands.notForMe++
  }
  return { total: (ratings || []).length, bands }
}

export function definingWorks(ratedWorks, n = 5) {
  return [...(ratedWorks || [])]
    .sort((a, b) => (b.resonance ?? 0.5) - (a.resonance ?? 0.5))
    .slice(0, n)
}

// Radar reach per spoke = positive taste weight normalized to the strongest love.
export function radarData(profile) {
  const max = Math.max(0.0001, ...FELT.map((k) => Math.max(0, profile[k] || 0)))
  return FELT.map((k) => ({ key: k, label: fmt(k), value: Math.max(0, profile[k] || 0) / max }))
}
