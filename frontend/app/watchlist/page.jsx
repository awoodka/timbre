'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api'
import { useSaves } from '@/lib/saves-context'
import RequireAuth from '@/components/RequireAuth'
import ShelfCard from '@/components/ShelfCard'

function Watchlist() {
  const { saved } = useSaves()
  const [mediaById, setMediaById] = useState({})
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    api.getMedia()
      .then((list) => setMediaById(Object.fromEntries(list.map((x) => [x.id, x]))))
      .catch(() => {})
      .finally(() => setLoaded(true))
  }, [])

  // `saved` is newest-first; keep that order and drop any unresolved ids.
  const items = useMemo(
    () => saved.map((id) => mediaById[id]).filter(Boolean),
    [saved, mediaById]
  )

  return (
    <div>
      <div className="page-header">
        <h1>My list</h1>
        <p>Works you’ve saved to experience later. Rate one and it moves to your ratings.</p>
      </div>

      {!loaded ? (
        <div className="loading"><span className="spinner" /> Loading…</div>
      ) : items.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
          <p style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Your list is empty</p>
          <p style={{ fontSize: '0.85rem', marginBottom: '1.25rem' }}>
            Save works you want to experience — tap the bookmark on any title.
          </p>
          <Link href="/recommendations" className="btn">Find something →</Link>
        </div>
      ) : (
        <div className="shelf-grid">
          {items.map((item) => <ShelfCard key={item.id} item={item} />)}
        </div>
      )}
    </div>
  )
}

export default function WatchlistPage() {
  return (
    <RequireAuth>
      <Watchlist />
    </RequireAuth>
  )
}
