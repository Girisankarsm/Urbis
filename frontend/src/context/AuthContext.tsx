import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'

import { fetchAuthMe, fetchAuthStatus, loginUrl, logout as apiLogout, completeSignIn } from '../api/client'

export interface AuthUser {
  id: string
  email: string
  name: string
  picture?: string
  can_send_gmail: boolean
}

const PENDING_SIGN_IN_KEY = 'urbis_pending_sign_in'

function markPendingSignIn() {
  try {
    sessionStorage.setItem(PENDING_SIGN_IN_KEY, '1')
    localStorage.setItem(PENDING_SIGN_IN_KEY, '1')
  } catch {
    // Private mode / storage blocked — auth_code exchange still works.
  }
}

function consumePendingSignIn(): boolean {
  try {
    const pending =
      sessionStorage.getItem(PENDING_SIGN_IN_KEY) === '1' ||
      localStorage.getItem(PENDING_SIGN_IN_KEY) === '1'
    sessionStorage.removeItem(PENDING_SIGN_IN_KEY)
    localStorage.removeItem(PENDING_SIGN_IN_KEY)
    return pending
  } catch {
    return false
  }
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
  const bootstrapped = useRef(false)

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
    if (bootstrapped.current) return
    bootstrapped.current = true

    const params = new URLSearchParams(window.location.search)
    const urlAuthError = params.get('auth_error')
    const authCode = params.get('auth_code')

    if (params.has('signed_in')) {
      markPendingSignIn()
    }
    if (params.has('signed_in') || urlAuthError || authCode) {
      window.history.replaceState({}, '', window.location.pathname)
    }
    if (urlAuthError) {
      setAuthError(urlAuthError)
    }

    const pendingSignIn = consumePendingSignIn() || Boolean(authCode)

    async function bootstrap() {
      if (authCode) {
        try {
          await completeSignIn(authCode)
        } catch {
          setAuthError('session_failed')
        }
      }

      let me = await refresh()
      if (!me && pendingSignIn) {
        // Mobile Safari can lag applying Set-Cookie on the first request.
        await new Promise((resolve) => setTimeout(resolve, 400))
        me = await refresh()
      }

      setLoading(false)
      if (pendingSignIn) {
        if (me) {
          navigate('/dashboard', { replace: true })
        } else {
          setAuthError('session_failed')
        }
      }
    }

    void bootstrap()
  }, [refresh, navigate])

  const login = () => {
    window.location.href = loginUrl()
  }

  const logout = async () => {
    await apiLogout()
    setUser(null)
    try {
      sessionStorage.removeItem(PENDING_SIGN_IN_KEY)
      localStorage.removeItem(PENDING_SIGN_IN_KEY)
    } catch {
      // ignore
    }
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
