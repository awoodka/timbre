'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth-context'

// Auth-aware top nav. Home, Catalogue, and Explore are public; the Discover tool
// and account menu are for signed-in users.
export default function NavLinks() {
  const { user, loading, logout } = useAuth()
  const router = useRouter()

  const doLogout = async () => {
    await logout()
    router.push('/')
  }

  // Until the cookie check resolves, show only the always-public links so we never
  // flash the wrong state (e.g. "Sign in" for someone who's actually logged in).
  if (loading) {
    return (
      <div className="nav-links">
        <Link href="/">Home</Link>
        <Link href="/catalogue">Catalogue</Link>
        <Link href="/explore">Explore</Link>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="nav-links">
        <Link href="/">Home</Link>
        <Link href="/catalogue">Catalogue</Link>
        <Link href="/explore">Explore</Link>
        <Link href="/login" className="nav-signin">Sign in</Link>
      </div>
    )
  }

  return (
    <div className="nav-links">
      <Link href="/discover">Discover</Link>
      <Link href="/catalogue">Catalogue</Link>
      <Link href="/explore">Explore</Link>
      <div className="nav-user">
        <Link href="/account" className="nav-user-name">{user.display_name || user.username}</Link>
        <button className="nav-logout" onClick={doLogout}>Log out</button>
      </div>
    </div>
  )
}
