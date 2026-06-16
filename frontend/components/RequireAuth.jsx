'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth-context'

// Client-side route guard. Auth lives in an httpOnly cookie resolved via /api/auth/me,
// so protection happens here on the client: wait for the check to finish, then send
// anyone who isn't signed in to the public home (which carries the sign-up CTAs).
// RequireAuth and the logout handlers both target '/', so there's no redirect race.
export default function RequireAuth({ children }) {
  const { user, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && !user) router.replace('/')
  }, [loading, user, router])

  if (loading || !user) {
    return <div className="loading"><span className="spinner" /> Loading…</div>
  }
  return children
}
