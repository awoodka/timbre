'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth-context'
import { useTheme } from '@/lib/theme-context'
import { useRatings } from '@/lib/ratings-context'
import { api } from '@/lib/api'
import RequireAuth from '@/components/RequireAuth'

const THEME_OPTIONS = [
  { key: 'system', label: 'System' },
  { key: 'light', label: 'Light' },
  { key: 'dark', label: 'Dark' },
]

function AppearanceSection() {
  const { theme, setThemePref } = useTheme()
  return (
    <section className="account-card settings-section">
      <h2 className="settings-h2">Appearance</h2>
      <p className="settings-hint">Theme follows your device by default.</p>
      <div className="seg settings-theme">
        {THEME_OPTIONS.map((o) => (
          <button
            key={o.key}
            type="button"
            className={`seg-btn${theme === o.key ? ' on' : ''}`}
            onClick={() => setThemePref(o.key)}
          >
            {o.label}
          </button>
        ))}
      </div>
    </section>
  )
}

function ProfileSection() {
  const { user, updateProfile } = useAuth()
  const [displayName, setDisplayName] = useState(user.display_name || '')
  const [username, setUsername] = useState(user.username)
  const [busy, setBusy] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState(null)

  const save = async (e) => {
    e.preventDefault()
    setBusy(true); setError(null); setSaved(false)
    const patch = {}
    if (displayName.trim() !== (user.display_name || '')) patch.display_name = displayName.trim() || null
    if (username.trim() !== user.username) patch.username = username.trim()
    if (Object.keys(patch).length === 0) { setBusy(false); setSaved(true); return }
    try {
      await updateProfile(patch)
      setSaved(true)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="account-card settings-section">
      <h2 className="settings-h2">Profile</h2>
      <form onSubmit={save} className="auth-form">
        <label className="auth-field">
          <span>Display name</span>
          <input value={displayName} onChange={(e) => { setDisplayName(e.target.value); setSaved(false) }} />
        </label>
        <label className="auth-field">
          <span>Username <em>used to sign in</em></span>
          <input value={username} minLength={3} maxLength={50} onChange={(e) => { setUsername(e.target.value); setSaved(false) }} />
        </label>
        {error && <p className="auth-error">{error}</p>}
        <div className="account-actions">
          <button type="submit" disabled={busy} className="auth-submit">{busy ? 'Saving…' : 'Save'}</button>
          {saved && <span className="account-saved">Saved ✓</span>}
        </div>
      </form>
    </section>
  )
}

function PasswordSection() {
  const { changePassword } = useAuth()
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [confirm, setConfirm] = useState('')
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)
  const [error, setError] = useState(null)

  const submit = async (e) => {
    e.preventDefault()
    setError(null); setDone(false)
    if (next.length < 6) { setError('New password must be at least 6 characters.'); return }
    if (next !== confirm) { setError('New passwords don’t match.'); return }
    setBusy(true)
    try {
      await changePassword(current, next)
      setDone(true)
      setCurrent(''); setNext(''); setConfirm('')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="account-card settings-section">
      <h2 className="settings-h2">Password</h2>
      <form onSubmit={submit} className="auth-form">
        <label className="auth-field">
          <span>Current password</span>
          <input type="password" value={current} autoComplete="current-password" onChange={(e) => setCurrent(e.target.value)} />
        </label>
        <label className="auth-field">
          <span>New password</span>
          <input type="password" value={next} autoComplete="new-password" onChange={(e) => setNext(e.target.value)} />
        </label>
        <label className="auth-field">
          <span>Confirm new password</span>
          <input type="password" value={confirm} autoComplete="new-password" onChange={(e) => setConfirm(e.target.value)} />
        </label>
        {error && <p className="auth-error">{error}</p>}
        <div className="account-actions">
          <button type="submit" disabled={busy || !current || !next} className="auth-submit">{busy ? 'Updating…' : 'Update password'}</button>
          {done && <span className="account-saved">Password updated ✓</span>}
        </div>
      </form>
    </section>
  )
}

function RecommendationsSection() {
  const { user, updateProfile } = useAuth()
  const [on, setOn] = useState(!!user.settings?.lean_enjoyment)
  const [error, setError] = useState(null)

  const toggle = async () => {
    const wanted = !on
    setOn(wanted) // optimistic
    setError(null)
    try {
      await updateProfile({ settings: { lean_enjoyment: wanted } })
    } catch (err) {
      setOn(!wanted) // revert
      setError(err.message)
    }
  }

  return (
    <section className="account-card settings-section">
      <h2 className="settings-h2">Recommendations</h2>
      <label className="settings-toggle">
        <input type="checkbox" checked={on} onChange={toggle} />
        <span>
          <strong>Lean toward what I enjoy</strong>
          <em>Let your ⭐ ratings gently nudge recommendations. Off by default — recs stay purely about the emotions a work evokes.</em>
        </span>
      </label>
      {error && <p className="auth-error">{error}</p>}
    </section>
  )
}

function DataSection() {
  const { clearRatings } = useRatings()
  const [busy, setBusy] = useState(null) // 'export' | 'reset'
  const [confirmReset, setConfirmReset] = useState(false)
  const [msg, setMsg] = useState(null)
  const [error, setError] = useState(null)

  const exportData = async () => {
    setBusy('export'); setError(null); setMsg(null)
    try {
      const data = await api.exportData()
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = 'timbre-data.json'
      document.body.appendChild(a); a.click(); a.remove()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(null)
    }
  }

  const reset = async () => {
    setBusy('reset'); setError(null); setMsg(null)
    try {
      await clearRatings()
      setMsg('Your taste profile has been reset.')
      setConfirmReset(false)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(null)
    }
  }

  return (
    <section className="account-card settings-section">
      <h2 className="settings-h2">Your data</h2>
      <div className="settings-row">
        <div className="settings-row-text">
          <strong>Export my data</strong>
          <em>Download your ratings and taste profile as JSON.</em>
        </div>
        <button className="btn-ghost" onClick={exportData} disabled={busy === 'export'}>{busy === 'export' ? 'Preparing…' : 'Export'}</button>
      </div>
      <hr className="account-divider" />
      <div className="settings-row">
        <div className="settings-row-text">
          <strong>Reset my taste profile</strong>
          <em>Delete all your ratings and start fresh. Your account stays.</em>
        </div>
        {confirmReset ? (
          <div className="confirm-delete">
            <span className="confirm-text">Delete all ratings?</span>
            <button className="confirm-yes" onClick={reset} disabled={busy === 'reset'}>{busy === 'reset' ? '…' : 'Yes'}</button>
            <button className="confirm-no" onClick={() => setConfirmReset(false)}>No</button>
          </div>
        ) : (
          <button className="btn-ghost" onClick={() => setConfirmReset(true)}>Reset</button>
        )}
      </div>
      {msg && <p className="account-saved">{msg}</p>}
      {error && <p className="auth-error">{error}</p>}
    </section>
  )
}

function DangerSection() {
  const router = useRouter()
  const { deleteAccount } = useAuth()
  const [open, setOpen] = useState(false)
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const remove = async () => {
    setBusy(true); setError(null)
    try {
      await deleteAccount(password)
      router.replace('/')
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  return (
    <section className="account-card settings-section settings-danger">
      <h2 className="settings-h2">Danger zone</h2>
      <div className="settings-row">
        <div className="settings-row-text">
          <strong>Delete account</strong>
          <em>Permanently remove your account, ratings, and saved list. This can’t be undone.</em>
        </div>
        {!open && <button className="confirm-yes" onClick={() => setOpen(true)}>Delete…</button>}
      </div>
      {open && (
        <div className="settings-delete-confirm">
          <label className="auth-field">
            <span>Confirm your password to delete</span>
            <input type="password" value={password} autoComplete="current-password" onChange={(e) => setPassword(e.target.value)} />
          </label>
          {error && <p className="auth-error">{error}</p>}
          <div className="account-actions">
            <button className="confirm-yes" onClick={remove} disabled={busy || !password}>{busy ? 'Deleting…' : 'Permanently delete'}</button>
            <button className="confirm-no" onClick={() => { setOpen(false); setPassword(''); setError(null) }}>Cancel</button>
          </div>
        </div>
      )}
    </section>
  )
}

const SECTIONS = [
  { key: 'appearance', label: 'Appearance', Component: AppearanceSection },
  { key: 'profile', label: 'Profile', Component: ProfileSection },
  { key: 'password', label: 'Password', Component: PasswordSection },
  { key: 'recommendations', label: 'Recommendations', Component: RecommendationsSection },
  { key: 'data', label: 'Your data', Component: DataSection },
  { key: 'danger', label: 'Danger zone', Component: DangerSection },
]

function SettingsInner() {
  const router = useRouter()
  const { user, logout } = useAuth()
  const [active, setActive] = useState('appearance')
  const Active = (SECTIONS.find((s) => s.key === active) || SECTIONS[0]).Component

  return (
    <div className="settings-page">
      <div className="page-header">
        <h1>Settings</h1>
        <p>@{user.username}</p>
      </div>
      <div className="settings-layout">
        <nav className="settings-nav">
          {SECTIONS.map((s) => (
            <button
              key={s.key}
              type="button"
              className={`settings-nav-item${active === s.key ? ' on' : ''}${s.key === 'danger' ? ' danger' : ''}`}
              onClick={() => setActive(s.key)}
            >
              {s.label}
            </button>
          ))}
          <button
            type="button"
            className="settings-nav-item settings-nav-logout"
            onClick={async () => { await logout(); router.push('/') }}
          >
            Log out
          </button>
        </nav>
        <div className="settings-content">
          <Active />
        </div>
      </div>
    </div>
  )
}

export default function SettingsPage() {
  return (
    <RequireAuth>
      <SettingsInner />
    </RequireAuth>
  )
}
