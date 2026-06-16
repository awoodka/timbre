'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth-context'
import RequireAuth from '@/components/RequireAuth'

function AccountInner() {
  const router = useRouter()
  const { user, updateProfile, logout } = useAuth()
  const [displayName, setDisplayName] = useState(user.display_name || '')
  const [saved, setSaved] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const save = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setSaved(false)
    try {
      await updateProfile({ display_name: displayName.trim() || null })
      setSaved(true)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Your account</h1>
        <p>@{user.username}</p>
      </div>
      <div className="account-card">
        <form onSubmit={save} className="auth-form">
          <label className="auth-field">
            <span>Display name</span>
            <input value={displayName} onChange={(e) => { setDisplayName(e.target.value); setSaved(false) }} />
          </label>
          {error && <p className="auth-error">{error}</p>}
          <div className="account-actions">
            <button type="submit" disabled={busy} className="auth-submit">{busy ? 'Saving…' : 'Save'}</button>
            {saved && <span className="account-saved">Saved ✓</span>}
          </div>
        </form>
        <hr className="account-divider" />
        <button className="nav-logout" onClick={async () => { await logout(); router.push('/') }}>Log out</button>
      </div>
    </div>
  )
}

export default function AccountPage() {
  return (
    <RequireAuth>
      <AccountInner />
    </RequireAuth>
  )
}
