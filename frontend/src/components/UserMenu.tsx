import { useEffect, useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import type { AuthUser } from '../context/AuthContext'
import { usePwaInstall } from '../hooks/usePwaInstall'

function ProfileIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path strokeLinecap="round" strokeLinejoin="round" d="M20 21a8 8 0 10-16 0" />
      <circle cx="12" cy="8" r="4" />
    </svg>
  )
}

export function UserMenu({ user, onLogout }: { user: AuthUser; onLogout: () => void }) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()
  const location = useLocation()
  const onProfile = location.pathname === '/profile'
  const { install, showInstall } = usePwaInstall()

  useEffect(() => {
    const onClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  const handleLogout = async () => {
    setOpen(false)
    await onLogout()
    navigate('/')
  }

  const handleInstall = async () => {
    setOpen(false)
    await install()
  }

  return (
    <div
      className="relative ml-2 pl-2 border-l border-civic-700/80 flex items-center gap-1 shrink-0"
      ref={ref}
    >
      <Link
        to="/profile"
        title="My profile"
        className={`inline-flex items-center gap-1.5 px-2.5 py-2 rounded-lg text-sm font-medium transition-colors ${
          onProfile
            ? 'bg-civic-700 text-white'
            : 'text-civic-100 hover:bg-civic-800 hover:text-white'
        }`}
      >
        <ProfileIcon className="w-4 h-4" />
        Profile
      </Link>

      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="p-2 rounded-lg text-civic-200 hover:bg-civic-800 hover:text-white transition-colors"
        aria-label="Account menu"
        aria-expanded={open}
      >
        <svg className={`w-4 h-4 transition-transform ${open ? 'rotate-180' : ''}`} viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 10.94l3.71-3.71a.75.75 0 111.06 1.06l-4.24 4.25a.75.75 0 01-1.06 0L5.21 8.29a.75.75 0 01.02-1.08z" clipRule="evenodd" />
        </svg>
      </button>

      {open && (
        <div
          className="absolute right-0 top-full mt-2 w-52 rounded-xl bg-white text-slate-800 shadow-xl border border-slate-100 py-1 z-50"
          role="menu"
        >
          <div className="px-4 py-3 border-b border-slate-100">
            <p className="font-semibold text-sm truncate">{user.name || 'Citizen'}</p>
            <p className="text-xs text-slate-500 truncate">{user.email}</p>
          </div>
          {showInstall && (
            <button
              type="button"
              onClick={handleInstall}
              className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-civic-700 hover:bg-civic-50 border-b border-slate-100"
              role="menuitem"
            >
              Install app
            </button>
          )}
          <button
            type="button"
            onClick={handleLogout}
            className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50"
            role="menuitem"
          >
            Sign out
          </button>
        </div>
      )}
    </div>
  )
}
