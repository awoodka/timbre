'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api'
import { useRatings } from '@/lib/ratings-context'
import { useSaves } from '@/lib/saves-context'
import RequireAuth from '@/components/RequireAuth'
import RecRow from '@/components/RecRow'
import ShelfCard from '@/components/ShelfCard'
import Shelf from '@/components/Shelf'
import FindControls from '@/components/FindControls'
import { buildRows } from '@/lib/recommendationRows'
import LoadError from '@/components/LoadError'

const MIN_LOGGED = 4

function Recommendations() {
  const { ratings, results } = useRatings()
  const { saved, error: savesError, reload: reloadSaves } = useSaves()
  const [mediaById, setMediaById] = useState({})
  const [mediaLoaded, setMediaLoaded] = useState(false)
  const [modes, setModes] = useState(null)
  const [error, setError] = useState(false)
  const [reloadKey, setReloadKey] = useState(0)

  // Fetch the corpus once (resolves the saved-items shelf; powers the secondary rows).
  useEffect(() => {
    setError(false)
    api.getMedia()
      .then((list) => setMediaById(Object.fromEntries(list.map((x) => [x.id, x]))))
      .catch(() => setError(true))
      .finally(() => setMediaLoaded(true))
  }, [reloadKey])

  const n = ratings.length

  // Multi-modal taste rows: cluster the user's loved works into emotional "modes."
  // Re-fetch when the rating count changes (a new rating can reshape the modes).
  useEffect(() => {
    if (n >= MIN_LOGGED) {
      api.recommendModes().then((r) => setModes(r.modes || [])).catch(() => { setModes([]); setError(true) })
    } else {
      setModes([])
    }
  }, [n, reloadKey])

  const retry = () => { reloadSaves(); setError(false); setReloadKey((k) => k + 1) }

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

      <FindControls />

      {results && results.length > 0 && (
        <section className="rec-row" aria-label="From your search">
          <div className="rec-row-head">
            <h2>From your search</h2>
            <span className="rec-row-sub">Matched to your search</span>
          </div>
          <Shelf>
            {results.map((r) => <ShelfCard key={r.item.id} item={r.item} reasons={r.reasons} />)}
          </Shelf>
        </section>
      )}

      {savedItems.length > 0 && (
        <section className="rec-row" aria-label="On your list">
          <div className="rec-row-head">
            <h2>On your list</h2>
            <span className="rec-row-sub">Saved to experience later</span>
          </div>
          <Shelf>
            {savedItems.map((item) => <ShelfCard key={item.id} item={item} />)}
          </Shelf>
        </section>
      )}

      {n > 0 && n < MIN_LOGGED && (
        <p className="gate-msg">
          Rate {MIN_LOGGED - n} more {MIN_LOGGED - n === 1 ? 'work' : 'works'} to unlock your personalized picks.
        </p>
      )}

      {(error || savesError) ? (
        <LoadError onRetry={retry} />
      ) : (
        <>
          {modes?.map((m) => (
            <RecRow
              key={m.id}
              title={`Because you loved ${m.anchor_title}`}
              subtitle="More with the same feeling"
              emotions={m.emotions}
              fetcher={() => Promise.resolve(m.recommendations)}
            />
          ))}

          {!mediaLoaded ? (
            <div className="loading"><span className="spinner" /> Loading…</div>
          ) : (
            rows.map((row) => (
              <RecRow key={row.id} title={row.title} subtitle={row.subtitle} tuned={row.tuned} fetcher={row.fetcher} />
            ))
          )}
        </>
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
