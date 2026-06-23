'use client'

import { useEffect, useState } from 'react'
import ShelfCard from '@/components/ShelfCard'

// One Netflix-style row. Owns its own fetch so rows load independently and pop in
// as they resolve. `fetcher` returns a normalized array of { item, reasons? }.
// A row that resolves to empty (or errors, or is gated) renders nothing.
export default function RecRow({ title, subtitle, fetcher }) {
  const [items, setItems] = useState(null) // null = loading, [] = empty/hidden, [...] = loaded

  useEffect(() => {
    let active = true
    Promise.resolve()
      .then(fetcher)
      .then((r) => { if (active) setItems(Array.isArray(r) ? r : []) })
      .catch(() => { if (active) setItems([]) })
    return () => { active = false }
    // Rows are stable for the life of the page; fetch once on mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (items && items.length === 0) return null

  return (
    <section className="rec-row" aria-label={title}>
      <div className="rec-row-head">
        <h2>{title}</h2>
        {subtitle && <span className="rec-row-sub">{subtitle}</span>}
      </div>
      <div className="shelf-scroll">
        {items === null
          ? Array.from({ length: 6 }).map((_, i) => <div key={i} className="shelf-card skeleton" />)
          : items.map((r) => <ShelfCard key={r.item.id} item={r.item} reasons={r.reasons} />)}
      </div>
    </section>
  )
}
