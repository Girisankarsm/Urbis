import { Link, Outlet } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'

export function Layout() {
  const { user, loading, login, logout, googleEnabled } = useAuth()

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-civic-900 text-white shadow-lg">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-3 hover:opacity-90 shrink-0">
            <span className="text-2xl">🏛️</span>
            <div>
              <h1 className="text-xl font-bold tracking-tight">Urbis</h1>
              <p className="text-xs text-civic-100">Metro City Municipal Corp</p>
            </div>
          </Link>
          <nav className="flex items-center gap-2 flex-wrap justify-end">
            <NavLink to="/">Dashboard</NavLink>
            <NavLink to="/new">Report Issue</NavLink>
            <NavLink to="/approvals">Approvals</NavLink>
            {!loading && googleEnabled && (
              user ? (
                <div className="flex items-center gap-2 ml-2 pl-2 border-l border-civic-700">
                  {user.picture ? (
                    <img src={user.picture} alt="" className="w-7 h-7 rounded-full" />
                  ) : null}
                  <span className="text-xs text-civic-100 hidden sm:inline max-w-[140px] truncate">{user.email}</span>
                  <button type="button" onClick={() => logout()} className="text-xs px-2 py-1 rounded hover:bg-civic-700">
                    Sign out
                  </button>
                </div>
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
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-8">
        <Outlet />
      </main>
      <footer className="border-t bg-white py-4 text-center text-sm text-slate-500">
        Urbis · Gappy AI Hackathon · Powered by Lemma SDK
      </footer>
    </div>
  )
}

function NavLink({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <Link
      to={to}
      className="px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-civic-700 transition-colors"
    >
      {children}
    </Link>
  )
}
