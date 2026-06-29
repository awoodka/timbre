'use client'

import { useState } from 'react'

// Plain <img> (not next/image) on purpose: it's immune to the remote-host allowlist
// and falls back to the placeholder on ANY load failure (404 / expired / odd host).
export default function BookCover({ url, size = 'medium' }) {
  const sizes = {
    small: { width: 40, height: 60 },
    medium: { width: 64, height: 96 },
    large: { width: 150, height: 225 },
  }
  const { width, height } = sizes[size] || sizes.medium
  const [failed, setFailed] = useState(false)

  if (url && !failed) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={url}
        alt=""
        width={width}
        height={height}
        className="book-cover-img"
        loading="lazy"
        onError={() => setFailed(true)}
      />
    )
  }

  return (
    <div className="book-cover-placeholder" style={{ width, height }}>
      <svg viewBox="0 0 24 32" fill="none" width={width * 0.4} height={height * 0.4}>
        <rect x="2" y="1" width="20" height="30" rx="2" stroke="currentColor" strokeWidth="1.5" fill="none" />
        <line x1="6" y1="8" x2="18" y2="8" stroke="currentColor" strokeWidth="1" />
        <line x1="6" y1="12" x2="15" y2="12" stroke="currentColor" strokeWidth="1" />
        <line x1="6" y1="16" x2="16" y2="16" stroke="currentColor" strokeWidth="1" />
      </svg>
    </div>
  )
}
