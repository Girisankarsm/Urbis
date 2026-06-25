import { Link, Outlet, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'

import { useAuth } from '../context/AuthContext'
import { UserMenu } from './UserMenu'

const AUTH_ERROR_MESSAGES: Record<string, string> = {
  access_denied: 'Google sign-in was cancelled. Add your email as a test user in Google Cloud Console if the app is in Testing mode.',
  denied: 'Google sign-in was denied. Publish the OAuth consent screen or add yourself as a test user.',
}

export function Layout() {
  const { user, loading, login, logout, googleEnabled } = useAuth()
  const location = useLocation()
  const [authError, setAuthError] = useState('')

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const code = params.get('auth_error')
    if (code) {
      setAuthError(AUTH_ERROR_MESSAGES[code] ?? 'Sign-in failed. Please try again.')
      window.history.replaceState({}, '', window.location.pathname)
    }
  }, [])

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-civic-900 text-white shadow-lg sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-3 hover:opacity-90 shrink-0">
            <span className="text-2xl">🏛️</span>
            <div>
              <h1 className="text-xl font-bold tracking-tight">Urbis</h1>
              <p className="text-xs text-civic-100">Metro City Municipal Corp</p>
            </div>
          </Link>
          <nav className="flex items-center gap-0.5 sm:gap-1">
            <NavLink to="/dashboard" active={location.pathname === '/dashboard'}>Dashboard</NavLink>
            <NavLink to="/new" active={location.pathname === '/new'}>Report Issue</NavLink>
            <NavLink to="/approvals" active={location.pathname.startsWith('/approvals')}>Approvals</NavLink>
            {!loading && googleEnabled && (
              user ? (
                <UserMenu user={user} onLogout={logout} />
              ) : (
                <button
                  type="button"
                  onClick={login}
                  className="ml-2 px-3 py-1.5 text-sm font-medium bg-white text-civic-900 rounded-lg hover:bg-civic-50"
                >
                  Sign in with Google
                </button>
              )
            )}
          </nav>
        </div>
      </header>
      <main className="flex-1 w-full">
        <div className="max-w-6xl mx-auto px-[clamp(1rem,3vw,1.5rem)] py-[clamp(1.75rem,4vw,2.5rem)]">
          {authError && (
            <div className="mb-6 text-sm text-amber-900 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
              {authError}
            </div>
          )}
          <Outlet />
        </div>
      </main>
      <footer className="border-t bg-white py-4 text-center text-sm text-slate-500">
        Urbis · Gappy AI Hackathon · Powered by Lemma SDK
      </footer>
    </div>
  )
}

function NavLink({ to, children, active }: { to: string; children: React.ReactNode; active?: boolean }) {
  return (
    <Link
      to={to}
      className={`nav-link relative px-2.5 sm:px-3 py-2 text-sm font-medium whitespace-nowrap transition-colors duration-200 ease-out ${
        active ? 'text-white' : 'text-civic-100/90 hover:text-white'
      }`}
    >
      {children}
      <span
        className={`nav-link-indicator ${active ? 'nav-link-indicator--active' : ''}`}
        aria-hidden
      />
    </Link>
  )
}
