'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

// /account merged into /settings — redirect for any old links or bookmarks.
export default function AccountPage() {
  const router = useRouter()
  useEffect(() => { router.replace('/settings') }, [router])
  return <div className="loading"><span className="spinner" /> Redirecting…</div>
}
