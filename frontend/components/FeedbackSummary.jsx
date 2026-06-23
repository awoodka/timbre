'use client'

const fmt = (s) => s.replace(/_/g, ' ')
const SENTIMENT = { 2: 'loved', 1: 'liked', '-1': 'disliked', '-2': 'not for me' }

// Read-only summary of a work's per-emotion marks (loved/liked/disliked/not-for-me).
export default function FeedbackSummary({ feedback }) {
  const entries = Object.entries(feedback || {}).filter(([, v]) => v !== 0).sort((a, b) => b[1] - a[1])
  if (!entries.length) return <span className="fb-summary muted">no marks yet</span>
  return (
    <span className="fb-summary">
      {entries.map(([k, v]) => (
        <span key={k} className={`fb-chip ${v > 0 ? 'up' : 'down'}`}>{SENTIMENT[v]} {fmt(k)}</span>
      ))}
    </span>
  )
}
