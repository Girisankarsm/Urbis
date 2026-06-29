import { Link, Outlet, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'

import { useAuth } from '../context/AuthContext'
import { UserMenu } from './UserMenu'

const AUTH_ERROR_MESSAGES: Record<string, string> = {
  access_denied: 'Google sign-in was cancelled. Add your email as a test user in Google Cloud Console if the app is in Testing mode.',
  denied: 'Google sign-in was denied. Publish the OAuth consent screen or add yourself as a test user.',
}

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', match: (path: string) => path === '/dashboard' },
  { to: '/new', label: 'Report Issue', match: (path: string) => path === '/new' },
  { to: '/hub', label: 'Hub', match: (path: string) => path.startsWith('/hub') },
] as const

export function Layout() {
  const { user, loading, login, logout, googleEnabled } = useAuth()
  const location = useLocation()
  const [authError, setAuthError] = useState('')
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const code = params.get('auth_error')
    if (code) {
      setAuthError(AUTH_ERROR_MESSAGES[code] ?? 'Sign-in failed. Please try again.')
      window.history.replaceState({}, '', window.location.pathname)
    }
  }, [])

  useEffect(() => {
    setMobileNavOpen(false)
  }, [location.pathname])

  useEffect(() => {
    document.body.style.overflow = mobileNavOpen ? 'hidden' : ''
    return () => {
      document.body.style.overflow = ''
    }
  }, [mobileNavOpen])

  return (
    <div className="app-shell min-h-screen flex flex-col w-full">
      <header className="app-header bg-civic-900 text-white shadow-lg sticky top-0 z-40 w-full">
        <div className="app-header-inner max-w-6xl mx-auto px-4 sm:px-6 h-14 sm:h-16 flex items-center justify-between gap-3 min-w-0">
          <Link to="/" className="flex items-center gap-2.5 sm:gap-3 hover:opacity-90 min-w-0 shrink-0">
            <span className="text-xl sm:text-2xl shrink-0">🏛️</span>
            <div className="min-w-0">
              <h1 className="text-lg sm:text-xl font-bold tracking-tight truncate">Urbis</h1>
              <p className="hidden sm:block text-xs text-civic-100 truncate">
                Metro City Municipal Corp
              </p>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-0.5 shrink-0" aria-label="Main">
            {NAV_ITEMS.map((item) => (
              <NavLink key={item.to} to={item.to} active={item.match(location.pathname)}>
                {item.label}
              </NavLink>
            ))}
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

          <div className="flex md:hidden items-center gap-1 shrink-0">
            {!loading && googleEnabled && user && (
              <Link
                to="/profile"
                title="My profile"
                className={`p-2 rounded-lg transition-colors ${
                  location.pathname === '/profile'
                    ? 'bg-civic-700 text-white'
                    : 'text-civic-100 hover:bg-civic-800'
                }`}
              >
                <ProfileIcon className="w-5 h-5" />
              </Link>
            )}
            <button
              type="button"
              onClick={() => setMobileNavOpen((open) => !open)}
              className="p-2 rounded-lg text-civic-100 hover:bg-civic-800 hover:text-white transition-colors"
              aria-label={mobileNavOpen ? 'Close menu' : 'Open menu'}
              aria-expanded={mobileNavOpen}
            >
              {mobileNavOpen ? <CloseIcon className="w-6 h-6" /> : <MenuIcon className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {mobileNavOpen && (
          <nav
            className="md:hidden border-t border-civic-800/80 bg-civic-900 px-4 py-3 flex flex-col gap-1"
            aria-label="Mobile"
          >
            {NAV_ITEMS.map((item) => (
              <MobileNavLink
                key={item.to}
                to={item.to}
                active={item.match(location.pathname)}
                onNavigate={() => setMobileNavOpen(false)}
              >
                {item.label}
              </MobileNavLink>
            ))}
            {!loading && googleEnabled && (
              user ? (
                <button
                  type="button"
                  onClick={async () => {
                    setMobileNavOpen(false)
                    await logout()
                  }}
                  className="mt-2 w-full text-left px-4 py-3 rounded-xl text-sm font-medium text-red-200 hover:bg-civic-800"
                >
                  Sign out
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => {
                    setMobileNavOpen(false)
                    login()
                  }}
                  className="mt-2 w-full px-4 py-3 rounded-xl text-sm font-medium bg-white text-civic-900 text-center"
                >
                  Sign in with Google
                </button>
              )
            )}
          </nav>
        )}
      </header>

      <main className="flex-1 w-full min-w-0">
        <div className="max-w-6xl mx-auto w-full px-4 sm:px-6 py-6 sm:py-8 min-w-0">
          {authError && (
            <div className="mb-6 text-sm text-amber-900 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
              {authError}
            </div>
          )}
          <Outlet />
        </div>
      </main>

      <footer className="app-footer w-full border-t bg-white py-4 text-center text-xs sm:text-sm text-slate-500 px-4">
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

function MobileNavLink({
  to,
  children,
  active,
  onNavigate,
}: {
  to: string
  children: React.ReactNode
  active?: boolean
  onNavigate: () => void
}) {
  return (
    <Link
      to={to}
      onClick={onNavigate}
      className={`block px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
        active ? 'bg-civic-700 text-white' : 'text-civic-100 hover:bg-civic-800 hover:text-white'
      }`}
    >
      {children}
    </Link>
  )
}

function MenuIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path strokeLinecap="round" d="M4 7h16M4 12h16M4 17h16" />
    </svg>
  )
}

function CloseIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path strokeLinecap="round" d="M6 6l12 12M18 6L6 18" />
    </svg>
  )
}

function ProfileIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path strokeLinecap="round" strokeLinejoin="round" d="M20 21a8 8 0 10-16 0" />
      <circle cx="12" cy="8" r="4" />
    </svg>
  )
}
