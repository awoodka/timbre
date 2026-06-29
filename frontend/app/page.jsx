'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'
import { useRatings } from '@/lib/ratings-context'
import FindControls from '@/components/FindControls'
import Shelf from '@/components/Shelf'
import ShelfCard from '@/components/ShelfCard'

const TAGLINE =
  'Discover books, films, games, and more by how they make you feel — not by genre.'

// Fisher–Yates; runs client-side only (after the data fetch), so no SSR/hydration drift.
function shuffle(arr) {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

export default function Home() {
  // The home page is public. Anyone can describe a feeling and see real matches
  // before signing up; login is what lands them on /recommendations, not a redirect.
  const { user } = useAuth()
  const { results } = useRatings()
  const [items, setItems] = useState([])

  useEffect(() => {
    api.getMedia()
      .then((all) => setItems(all.filter((i) => i.analysis_status === 'completed')))
      .catch(() => {})
  }, [])

  // Band covers: only items that actually have a cover, freshly shuffled each load.
  const bandCovers = useMemo(
    () => shuffle(items.filter((i) => i.cover_image_url)).slice(0, 24),
    [items]
  )

  return (
    <div className="landing">
      <section className="hero">
        <h1 className="hero-title">Timbre</h1>
        <p className="hero-tagline">{TAGLINE}</p>
        <div className="hero-cta">
          <a href="#discover" className="btn">Describe a feeling →</a>
          <Link href="/explore" className="btn-ghost">Explore the map</Link>
          {!user && <Link href="/login" className="btn-ghost">Sign in</Link>}
        </div>
      </section>

      {/* Full-bleed band of slightly overlapping covers, drifting slowly. */}
      <section className="hero-band full-bleed" aria-hidden="true">
        {bandCovers.length > 0 ? (
          <div className="band-track">
            {[...bandCovers, ...bandCovers].map((item, idx) => (
              <img
                key={`${item.id}-${idx}`}
                src={item.cover_image_url}
                alt=""
                className="band-cover"
                loading="lazy"
                onError={(e) => { e.currentTarget.style.visibility = 'hidden' }}
              />
            ))}
          </div>
        ) : (
          <div className="band-placeholder" />
        )}
      </section>

      {/* The core magic, open to anyone: describe a feeling → real matches. */}
      <section id="discover" className="discover">
        <h2 className="landing-h2">Find something by how it feels</h2>
        <p className="discover-sub">
          Describe a mood or a moment — Timbre reads the feeling and finds works
          that evoke it, across every medium.
        </p>
        <FindControls defaultActive="describe" />

        {results && results.length > 0 && (
          <section className="rec-row discover-results" aria-label="From your search">
            <div className="rec-row-head">
              <h3>What that feels like</h3>
              <span className="rec-row-sub">Matched to your search</span>
            </div>
            <Shelf>
              {results.map((r) => <ShelfCard key={r.item.id} item={r.item} reasons={r.reasons} />)}
            </Shelf>
            {!user && (
              <p className="discover-convert">
                <Link href="/login">Sign up to save these + unlock personalized picks →</Link>
              </p>
            )}
          </section>
        )}

        <p className="discover-explore">
          Or wander the whole emotional map — <Link href="/explore">explore in 3D →</Link>
        </p>
      </section>

      <section className="how">
        <h2 className="landing-h2">How it works</h2>
        <div className="how-steps">
          <div className="how-step">
            <span className="how-num">1</span>
            <h3>Rate what's moved you</h3>
            <p>Books, films, shows, anime, manga, games — anything that left a mark.</p>
          </div>
          <div className="how-step">
            <span className="how-num">2</span>
            <h3>Timbre reads the feeling</h3>
            <p>Every title is scored across 29 emotional dimensions — the texture of how it feels, not its genre.</p>
          </div>
          <div className="how-step">
            <span className="how-num">3</span>
            <h3>Get matches across media</h3>
            <p>Discover works that evoke the same feeling — a game that feels like your favorite novel.</p>
          </div>
        </div>
      </section>

      <section className="landing-cta">
        <h2>Ready to find your next favorite?</h2>
        {user
          ? <Link href="/recommendations" className="btn">Go to your recommendations →</Link>
          : <Link href="/login" className="btn">Create your free account →</Link>}
      </section>
    </div>
  )
}
