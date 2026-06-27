'use client'

import { useState } from 'react'

// 1–5 stars. Interactive by default (click the active star to clear it back to none);
// pass `readOnly` for a static display. `value` of 0/null/undefined = no rating.
export default function StarRating({ value = 0, onChange, readOnly = false, size }) {
  const [hover, setHover] = useState(0)
  const cls = `star-rating${readOnly ? ' readonly' : ''}${size ? ` ${size}` : ''}`

  if (readOnly) {
    return (
      <div className={cls} aria-label={`${value || 0} out of 5`}>
        {[1, 2, 3, 4, 5].map((n) => (
          <span key={n} className={`star ${n <= (value || 0) ? 'filled' : ''}`}>★</span>
        ))}
      </div>
    )
  }

  return (
    <div className={cls} onMouseLeave={() => setHover(0)}>
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          type="button"
          className={`star ${n <= (hover || value || 0) ? 'filled' : ''}`}
          onClick={() => onChange(n === value ? 0 : n)}
          onMouseEnter={() => setHover(n)}
        >
          ★
        </button>
      ))}
    </div>
  )
}
