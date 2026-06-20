// The 6 structural/arc axes are bipolar (0.5 = neutral), not "felt emotions" you'd
// like or dislike. Mirrors backend app/dimensions.py STRUCTURAL_KEYS.
export const STRUCTURAL_KEYS = new Set([
  'pacing', 'emotional_complexity', 'predictability',
  'catharsis', 'emotional_trajectory', 'ending_valence',
])

// A work's top-N most-prevalent FELT emotions, by raw breakdown score.
export function topFeltEmotions(breakdown, n = 6) {
  if (!breakdown) return []
  return Object.entries(breakdown)
    .filter(([k]) => !STRUCTURAL_KEYS.has(k))
    .sort((a, b) => b[1] - a[1])
    .slice(0, n)
    .map(([k]) => k)
}
