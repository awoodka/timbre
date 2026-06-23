'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

// /discover was split into /ratings (log + manage) and /recommendations (For You).
// Keep this route as a redirect so old links / bookmarks / history still resolve.
export default function DiscoverRedirect() {
  const router = useRouter()
  useEffect(() => { router.replace('/recommendations') }, [router])
  return <div className="loading"><span className="spinner" /> Redirecting…</div>
}
