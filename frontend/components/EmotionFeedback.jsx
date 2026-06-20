'use client'

import { getEmotionColor } from '@/components/emotionColors'

const fmt = (s) => s.replace(/_/g, ' ')
const SCALE = [-2, -1, 0, 1, 2]

// Per-emotion preference on a 5-point scale: not-for-me … neutral … loved.
// Emits a sparse map { emotion_key: -2|-1|1|2 } (neutral/0 is omitted).
export default function EmotionFeedback({ emotions, value = {}, onChange }) {
  const set = (key, v) => {
    const next = { ...value }
    if (v === 0) delete next[key]
    else next[key] = v
    onChange(next)
  }

  return (
    <div className="emotion-feedback">
      {emotions.map((key) => {
        const c = getEmotionColor(key)
        const cur = value[key] ?? 0
        return (
          <div key={key} className="ef-row">
            <span className="ef-label" style={{ background: c.bg, color: c.color }}>{fmt(key)}</span>
            <div className="ef-scale">
              <span className="ef-end">not for me</span>
              {SCALE.map((v) => (
                <button
                  key={v}
                  type="button"
                  className={`ef-dot${cur === v ? ' on' : ''}${v < 0 ? ' neg' : v > 0 ? ' pos' : ''}`}
                  onClick={() => set(key, v)}
                  aria-label={`${fmt(key)}: ${v > 0 ? `+${v}` : v}`}
                />
              ))}
              <span className="ef-end">loved</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
