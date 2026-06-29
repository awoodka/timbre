'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/lib/auth-context'

// Auth-aware top nav. Home, Catalogue, and Explore are public; recommendations,
// ratings, and the account menu are for signed-in users. Collapses to a hamburger
// dropdown ≤720px — the open state + close-on-navigate live here.
export default function NavLinks() {
  const { user, loading, logout } = useAuth()
  const router = useRouter()
  const pathname = usePathname()
  const [open, setOpen] = useState(false)

  // Close the mobile menu whenever the route changes (tapping a link navigates).
  useEffect(() => { setOpen(false) }, [pathname])

  const doLogout = async () => { setOpen(false); await logout(); router.push('/') }

  // Until the cookie check resolves, show only the always-public links so we never
  // flash the wrong state (e.g. "Sign in" for someone who's actually logged in).
  const links = (loading || !user)
    ? [['/', 'Home'], ['/catalogue', 'Catalogue'], ['/explore', 'Explore']]
    : [
        ['/recommendations', 'For You'],
        ['/watchlist', 'My List'],
        ['/ratings', 'My Ratings'],
        ['/fingerprint', 'Your Taste'],
        ['/catalogue', 'Catalogue'],
        ['/explore', 'Explore'],
      ]

  return (
    <>
      <button
        type="button"
        className="nav-toggle"
        aria-label="Menu"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
      >
        <span /><span /><span />
      </button>
      <div className={`nav-links${open ? ' open' : ''}`}>
        {links.map(([href, label]) => (
          <Link key={href} href={href}>{label}</Link>
        ))}
        {!loading && !user && <Link href="/login" className="nav-signin">Sign in</Link>}
        {!loading && user && (
          <div className="nav-user">
            <Link href="/settings" className="nav-user-name">{user.display_name || user.username}</Link>
            <button className="nav-logout" onClick={doLogout}>Log out</button>
          </div>
        )}
      </div>
    </>
  )
}
