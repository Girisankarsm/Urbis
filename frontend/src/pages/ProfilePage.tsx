import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { listMyPetitions } from '../api/client'
import { LoginPrompt } from '../components/LoginPrompt'
import { StatusBadge } from '../components/StatusBadge'
import { useAuth } from '../context/AuthContext'
import type { Petition } from '../types'

function avatarInitials(name: string, email: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (email[0] ?? 'U').toUpperCase()
}

export function ProfilePage() {
  const { user, loading: authLoading, googleEnabled } = useAuth()
  const [petitions, setPetitions] = useState<Petition[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) return
    setLoading(true)
    listMyPetitions()
      .then(setPetitions)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [user])

  if (!authLoading && googleEnabled && !user) {
    return (
      <LoginPrompt
        title="Sign in to view your profile"
        description="Your profile shows your account details and civic reports."
      />
    )
  }

  if (authLoading || !user) {
    return (
      <div className="flex items-center justify-center py-24">
        <p className="text-slate-500">Loading profile…</p>
      </div>
    )
  }

  const active = petitions.filter((p) => p.status === 'submitted' || p.status === 'under_review').length
  const resolved = petitions.filter((p) => p.status === 'resolved').length
  const initials = avatarInitials(user.name || '', user.email)

  return (
    <div className="space-y-8">
      {/* Page header — matches Dashboard rhythm */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-civic-600 mb-1">Account</p>
          <h2 className="text-2xl font-bold text-civic-900">My Profile</h2>
          <p className="text-slate-600 text-sm mt-1">Manage your account and track your civic reports</p>
        </div>
        <Link
          to="/new"
          className="inline-flex items-center justify-center px-4 py-2.5 bg-civic-600 text-white rounded-xl font-medium hover:bg-civic-700 shrink-0"
        >
          + Report Issue
        </Link>
      </div>

      <div className="grid lg:grid-cols-3 gap-6 items-start">
        {/* Left column — identity + stats */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="h-20 bg-gradient-to-br from-civic-800 via-civic-700 to-civic-500" />
            <div className="px-6 pb-6">
              <div className="flex flex-col items-center text-center -mt-12">
                {user.picture ? (
                  <img
                    src={user.picture}
                    alt=""
                    className="w-24 h-24 rounded-2xl ring-4 ring-white object-cover shadow-lg bg-white"
                  />
                ) : (
                  <div className="w-24 h-24 rounded-2xl ring-4 ring-white bg-gradient-to-br from-civic-600 to-civic-800 text-white flex items-center justify-center text-3xl font-bold shadow-lg">
                    {initials}
                  </div>
                )}
                <h3 className="mt-4 text-xl font-bold text-civic-900">{user.name || 'Citizen'}</h3>
                <p className="text-sm text-slate-500 break-all">{user.email}</p>
                <span
                  className={`mt-3 inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${
                    user.can_send_gmail
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      : 'bg-amber-50 text-amber-800 border border-amber-200'
                  }`}
                >
                  <span className={`w-1.5 h-1.5 rounded-full ${user.can_send_gmail ? 'bg-emerald-500' : 'bg-amber-500'}`} />
                  {user.can_send_gmail ? 'Gmail connected' : 'Brevo email fallback'}
                </span>
              </div>

              <div className="mt-6 pt-6 border-t border-slate-100 grid grid-cols-3 gap-2">
                <StatCard label="Reports" value={petitions.length} />
                <StatCard label="Active" value={active} />
                <StatCard label="Resolved" value={resolved} />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
            <h4 className="text-sm font-semibold text-slate-900">Quick links</h4>
            <nav className="flex flex-col gap-1">
              <ProfileLink to="/dashboard" label="Dashboard" description="All petitions overview" />
              <ProfileLink to="/new" label="Report issue" description="Submit a new complaint" />
              <ProfileLink to="/approvals" label="Approvals" description="Review pending emails" />
            </nav>
          </div>
        </div>

        {/* Right column — reports */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm">
            <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between gap-4">
              <div>
                <h3 className="text-lg font-semibold text-civic-900">Your reports</h3>
                <p className="text-sm text-slate-500">Issues you have filed with Urbis</p>
              </div>
              {petitions.length > 0 && (
                <span className="text-xs font-medium text-slate-500 bg-slate-100 px-2.5 py-1 rounded-full">
                  {petitions.length} total
                </span>
              )}
            </div>

            <div className="p-6">
              {loading ? (
                <div className="py-12 text-center text-slate-500 text-sm">Loading your reports…</div>
              ) : petitions.length === 0 ? (
                <div className="py-12 text-center">
                  <p className="text-4xl mb-3">📋</p>
                  <p className="text-slate-600 font-medium mb-1">No reports yet</p>
                  <p className="text-sm text-slate-500 mb-5">Photograph a civic issue and Urbis will draft the complaint for you.</p>
                  <Link
                    to="/new"
                    className="inline-flex px-4 py-2 bg-civic-600 text-white rounded-xl text-sm font-medium hover:bg-civic-700"
                  >
                    Report your first issue
                  </Link>
                </div>
              ) : (
                <ul className="divide-y divide-slate-100">
                  {petitions.map((p) => (
                    <li key={p.id}>
                      <Link
                        to={`/petitions/${p.id}`}
                        className="flex gap-4 py-4 first:pt-0 last:pb-0 hover:bg-slate-50 -mx-2 px-2 rounded-xl transition-colors group"
                      >
                        <img
                          src={p.photo_url}
                          alt=""
                          className="w-16 h-16 rounded-xl object-cover flex-shrink-0 border border-slate-100"
                        />
                        <div className="min-w-0 flex-1 flex flex-col justify-center">
                          <div className="flex flex-wrap items-center gap-2 mb-1">
                            <StatusBadge status={p.status} />
                            {p.issue_type && (
                              <span className="text-xs text-slate-400 capitalize">
                                {p.issue_type.replace('_', ' ')}
                              </span>
                            )}
                          </div>
                          <p className="font-medium text-slate-900 truncate group-hover:text-civic-700">
                            {p.description || 'Civic issue report'}
                          </p>
                          <p className="text-sm text-slate-500 truncate">
                            {p.department ?? 'Department pending'} ·{' '}
                            {p.location?.address || `${p.location?.lat?.toFixed(4)}, ${p.location?.lng?.toFixed(4)}`}
                          </p>
                        </div>
                        <span className="hidden sm:flex items-center text-slate-300 group-hover:text-civic-500 self-center">
                          →
                        </span>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl bg-slate-50 border border-slate-100 px-2 py-3 text-center">
      <p className="text-xl font-bold text-civic-900 tabular-nums">{value}</p>
      <p className="text-[11px] font-medium text-slate-500 uppercase tracking-wide mt-0.5">{label}</p>
    </div>
  )
}

function ProfileLink({ to, label, description }: { to: string; label: string; description: string }) {
  return (
    <Link
      to={to}
      className="flex items-center justify-between gap-3 rounded-xl px-3 py-2.5 hover:bg-slate-50 transition-colors group"
    >
      <div className="min-w-0">
        <p className="text-sm font-medium text-slate-900 group-hover:text-civic-700">{label}</p>
        <p className="text-xs text-slate-500">{description}</p>
      </div>
      <span className="text-slate-300 group-hover:text-civic-500 shrink-0">→</span>
    </Link>
  )
}
