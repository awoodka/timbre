'use client'

import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth-context'
import { useSaves } from '@/lib/saves-context'

// Bookmark toggle to add/remove a work from the watchlist ("My List"). Designed to
// live inside <Link> cards — it stops the click from navigating. Logged-out users
// are routed to /login (saves require an account). `label` renders an icon+text pill.
export default function SaveButton({ mediaId, className = '', label = false }) {
  const { user } = useAuth()
  const { isSaved, addSave, removeSave } = useSaves()
  const router = useRouter()
  const saved = isSaved(mediaId)

  const onClick = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (!user) { router.push('/login'); return }
    if (saved) removeSave(mediaId)
    else addSave(mediaId)
  }

  return (
    <button
      type="button"
      className={`save-btn${saved ? ' saved' : ''}${label ? ' labeled' : ''} ${className}`}
      onClick={onClick}
      aria-pressed={saved}
      aria-label={saved ? 'Remove from My List' : 'Save to My List'}
      title={saved ? 'Saved — remove from My List' : 'Save to My List'}
    >
      <svg
        width="16" height="16" viewBox="0 0 16 16"
        fill={saved ? 'currentColor' : 'none'}
        stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"
      >
        <path d="M4 2h8v12l-4-3-4 3V2z" />
      </svg>
      {label && <span>{saved ? 'Saved' : 'Save'}</span>}
    </button>
  )
}
