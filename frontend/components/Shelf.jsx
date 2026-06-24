'use client'

import { useCallback, useEffect, useRef, useState } from 'react'

// A horizontally-scrolling shelf with prev/next arrow buttons. Arrows hide at the
// start/end (and on rows that don't overflow). Used by RecRow and the inline For You
// shelves. Native swipe/trackpad scrolling still works.
export default function Shelf({ children }) {
  const ref = useRef(null)
  const [atStart, setAtStart] = useState(true)
  const [atEnd, setAtEnd] = useState(true)

  const update = useCallback(() => {
    const el = ref.current
    if (!el) return
    setAtStart(el.scrollLeft <= 2)
    setAtEnd(el.scrollLeft + el.clientWidth >= el.scrollWidth - 2)
  }, [])

  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.addEventListener('scroll', update, { passive: true })
    window.addEventListener('resize', update)
    return () => {
      el.removeEventListener('scroll', update)
      window.removeEventListener('resize', update)
    }
  }, [update])

  // Re-check after every render — e.g. when async items finish loading and widen the row.
  useEffect(() => { update() })

  const scroll = (dir) => {
    const el = ref.current
    if (el) el.scrollBy({ left: dir * el.clientWidth * 0.82, behavior: 'smooth' })
  }

  return (
    <div className="shelf">
      {!atStart && (
        <button type="button" className="shelf-arrow left" onClick={() => scroll(-1)} aria-label="Scroll left">‹</button>
      )}
      <div className="shelf-scroll" ref={ref}>{children}</div>
      {!atEnd && (
        <button type="button" className="shelf-arrow right" onClick={() => scroll(1)} aria-label="Scroll right">›</button>
      )}
    </div>
  )
}
