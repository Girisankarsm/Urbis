import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'

import { fetchAuthMe, fetchAuthStatus, loginUrl, logout as apiLogout } from '../api/client'

export interface AuthUser {
  id: string
  email: string
  name: string
  picture?: string
  can_send_gmail: boolean
}

interface AuthContextValue {
  user: AuthUser | null
  loading: boolean
  googleEnabled: boolean
  authError: string | null
  clearAuthError: () => void
  login: () => void
  logout: () => Promise<void>
  refresh: () => Promise<AuthUser | null>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate()
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)
  const [googleEnabled, setGoogleEnabled] = useState(false)
  const [authError, setAuthError] = useState<string | null>(null)

  const clearAuthError = useCallback(() => setAuthError(null), [])

  const refresh = useCallback(async (): Promise<AuthUser | null> => {
    try {
      const status = await fetchAuthStatus()
      setGoogleEnabled(status.google_auth_enabled)
      if (!status.google_auth_enabled) {
        setUser(null)
        return null
      }
      const me = await fetchAuthMe()
      setUser(me)
      return me
    } catch {
      setUser(null)
      return null
    }
  }, [])

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const justSignedIn = params.has('signed_in')
    const authError = params.get('auth_error')
    if (justSignedIn || authError) {
      window.history.replaceState({}, '', window.location.pathname)
    }
    refresh().then((me) => {
      setLoading(false)
      if (justSignedIn && me) {
        navigate('/dashboard', { replace: true })
      } else if (justSignedIn && !me) {
        setAuthError('session_failed')
      }
    })
  }, [refresh, navigate])

  const login = () => {
    window.location.href = loginUrl()
  }

  const logout = async () => {
    await apiLogout()
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{ user, loading, googleEnabled, authError, clearAuthError, login, logout, refresh }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
