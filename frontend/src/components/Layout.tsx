import { Link, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import { UserMenu } from './UserMenu'

export function Layout() {
  const { user, loading, login, logout, googleEnabled } = useAuth()
  const location = useLocation()

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
            <NavLink to="/" active={location.pathname === '/'}>Dashboard</NavLink>
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
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
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
      className={`px-2.5 sm:px-3 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
        active ? 'bg-civic-700 text-white' : 'text-civic-100 hover:bg-civic-800 hover:text-white'
      }`}
    >
      {children}
    </Link>
  )
}
