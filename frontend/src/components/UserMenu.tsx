import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import type { AuthUser } from '../context/AuthContext'

function initials(user: AuthUser): string {
  const fromName = user.name?.trim().split(/\s+/).map((p) => p[0]).join('').slice(0, 2)
  if (fromName) return fromName.toUpperCase()
  return (user.email[0] ?? 'U').toUpperCase()
}

export function UserMenu({ user, onLogout }: { user: AuthUser; onLogout: () => void }) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()

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

  return (
    <div className="relative ml-1 sm:ml-2 pl-1 sm:pl-2 border-l border-civic-700/80 shrink-0" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 rounded-xl px-2 py-1.5 hover:bg-civic-800/80 transition-colors"
        aria-expanded={open}
        aria-haspopup="menu"
      >
        {user.picture ? (
          <img src={user.picture} alt="" className="w-8 h-8 rounded-full ring-2 ring-civic-600 object-cover" />
        ) : (
          <span className="w-8 h-8 rounded-full bg-civic-600 ring-2 ring-civic-500 flex items-center justify-center text-xs font-semibold">
            {initials(user)}
          </span>
        )}
        <span className="hidden md:block text-left max-w-[120px]">
          <span className="block text-sm font-medium truncate">{user.name || 'Citizen'}</span>
          <span className="block text-[10px] text-civic-200 truncate">{user.email}</span>
        </span>
        <svg className={`w-4 h-4 text-civic-200 transition-transform ${open ? 'rotate-180' : ''}`} viewBox="0 0 20 20" fill="currentColor" aria-hidden>
          <path fillRule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 10.94l3.71-3.71a.75.75 0 111.06 1.06l-4.24 4.25a.75.75 0 01-1.06 0L5.21 8.29a.75.75 0 01.02-1.08z" clipRule="evenodd" />
        </svg>
      </button>

      {open && (
        <div
          className="absolute right-0 top-full mt-2 w-56 rounded-xl bg-white text-slate-800 shadow-xl border border-slate-100 py-1 z-50"
          role="menu"
        >
          <div className="px-4 py-3 border-b border-slate-100">
            <p className="font-semibold text-sm truncate">{user.name || 'Citizen'}</p>
            <p className="text-xs text-slate-500 truncate">{user.email}</p>
          </div>
          <Link
            to="/profile"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2 px-4 py-2.5 text-sm hover:bg-slate-50"
            role="menuitem"
          >
            <span>👤</span> Profile
          </Link>
          <Link
            to="/new"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2 px-4 py-2.5 text-sm hover:bg-slate-50"
            role="menuitem"
          >
            <span>📸</span> Report Issue
          </Link>
          <button
            type="button"
            onClick={handleLogout}
            className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 border-t border-slate-100 mt-1"
            role="menuitem"
          >
            <span>↩</span> Sign out
          </button>
        </div>
      )}
    </div>
  )
}
