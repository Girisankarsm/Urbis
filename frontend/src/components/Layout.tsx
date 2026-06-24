import { Link, Outlet } from 'react-router-dom'

export function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-civic-900 text-white shadow-lg">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 hover:opacity-90">
            <span className="text-2xl">🏛️</span>
            <div>
              <h1 className="text-xl font-bold tracking-tight">Urbis</h1>
              <p className="text-xs text-civic-100">Metro City Municipal Corp</p>
            </div>
          </Link>
          <nav className="flex gap-2">
            <NavLink to="/">Dashboard</NavLink>
            <NavLink to="/new">Report Issue</NavLink>
            <NavLink to="/approvals">Approvals</NavLink>
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
