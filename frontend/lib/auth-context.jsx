'use client'

import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { api } from './api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    try {
      setUser(await api.me()) // returns null (200) when not signed in
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  const login = useCallback(async (username, password) => {
    const u = await api.login(username, password)
    setUser(u)
    return u
  }, [])

  const signup = useCallback(async (username, password, displayName) => {
    const u = await api.signup(username, password, displayName || null)
    setUser(u)
    return u
  }, [])

  const logout = useCallback(async () => {
    await api.logout()
    setUser(null)
  }, [])

  const updateProfile = useCallback(async (data) => {
    const u = await api.updateProfile(data)
    setUser(u)
    return u
  }, [])

  const changePassword = useCallback((currentPassword, newPassword) =>
    api.changePassword(currentPassword, newPassword), [])

  const deleteAccount = useCallback(async (password) => {
    await api.deleteAccount(password)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout, updateProfile, changePassword, deleteAccount, refresh }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
