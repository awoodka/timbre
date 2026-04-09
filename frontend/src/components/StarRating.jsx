import { useState } from 'react'

export default function StarRating({ value, onChange }) {
  const [hover, setHover] = useState(0)

  return (
    <div className="star-rating" onMouseLeave={() => setHover(0)}>
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          type="button"
          className={`star ${n <= (hover || value) ? 'filled' : ''}`}
          onClick={() => onChange(n)}
          onMouseEnter={() => setHover(n)}
        >
          ★
        </button>
      ))}
    </div>
  )
}
