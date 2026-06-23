'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api'
import { useRatings } from '@/lib/ratings-context'
import { useSaves } from '@/lib/saves-context'
import RequireAuth from '@/components/RequireAuth'
import RecRow from '@/components/RecRow'
import ShelfCard from '@/components/ShelfCard'
import MoodComposer from '@/components/MoodComposer'
import { buildRows } from '@/lib/recommendationRows'

const MIN_LOGGED = 4

function Recommendations() {
  const { ratings, results } = useRatings()
  const { saved } = useSaves()
  const [mediaById, setMediaById] = useState({})
  const [mediaLoaded, setMediaLoaded] = useState(false)

  // Fetch the corpus once to label "Because you loved {title}" rows.
  useEffect(() => {
    api.getMedia()
      .then((list) => setMediaById(Object.fromEntries(list.map((x) => [x.id, x]))))
      .catch(() => {})
      .finally(() => setMediaLoaded(true))
  }, [])

  const n = ratings.length
  const rows = useMemo(
    () => (mediaLoaded ? buildRows({ ratings, mediaById }) : []),
    [ratings, mediaById, mediaLoaded]
  )
  // Saved works (newest-first), resolved against the loaded corpus — the "On your list" shelf.
  const savedItems = useMemo(
    () => saved.map((id) => mediaById[id]).filter(Boolean),
    [saved, mediaById]
  )

  return (
    <div>
      <div className="page-header">
        <h1>For you</h1>
        <p>Recommendations by the emotions a work evokes — not its genre.</p>
      </div>

      {n === 0 && (
        <div className="rec-coldstart">
          <p>Rate a few works and we’ll learn your taste — then personalized picks unlock here.</p>
          <Link href="/ratings" className="btn">Rate works →</Link>
        </div>
      )}

      <MoodComposer />

      {results && results.length > 0 && (
        <section className="rec-row" aria-label="From your search">
          <div className="rec-row-head">
            <h2>From your search</h2>
            <span className="rec-row-sub">What you just composed</span>
          </div>
          <div className="shelf-scroll">
            {results.map((r) => <ShelfCard key={r.item.id} item={r.item} reasons={r.reasons} />)}
          </div>
        </section>
      )}

      {savedItems.length > 0 && (
        <section className="rec-row" aria-label="On your list">
          <div className="rec-row-head">
            <h2>On your list</h2>
            <span className="rec-row-sub">Saved to experience later</span>
          </div>
          <div className="shelf-scroll">
            {savedItems.map((item) => <ShelfCard key={item.id} item={item} />)}
          </div>
        </section>
      )}

      {n > 0 && n < MIN_LOGGED && (
        <p className="gate-msg">
          Rate {MIN_LOGGED - n} more {MIN_LOGGED - n === 1 ? 'work' : 'works'} to unlock your Top Picks.
        </p>
      )}

      {!mediaLoaded ? (
        <div className="loading"><span className="spinner" /> Loading…</div>
      ) : (
        rows.map((row) => (
          <RecRow key={row.id} title={row.title} subtitle={row.subtitle} fetcher={row.fetcher} />
        ))
      )}
    </div>
  )
}

export default function RecommendationsPage() {
  return (
    <RequireAuth>
      <Recommendations />
    </RequireAuth>
  )
}
