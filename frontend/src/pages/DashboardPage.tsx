import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { listMyPetitions, listPetitions } from '../api/client'
import { DashboardFilterTabs } from '../components/dashboard/DashboardFilterTabs'
import { DashboardEmptyDoodle } from '../components/dashboard/DashboardIcons'
import { StatusBadge } from '../components/StatusBadge'
import { useAuth } from '../context/AuthContext'
import type { Petition, PetitionStatus } from '../types'

const FILTERS: { label: string; value: PetitionStatus | '' }[] = [
  { label: 'All', value: '' },
  { label: 'Draft', value: 'draft' },
  { label: 'Submitted', value: 'submitted' },
  { label: 'Under Review', value: 'under_review' },
  { label: 'Resolved', value: 'resolved' },
  { label: 'Escalated', value: 'escalated' },
]

export function DashboardPage() {
  const { user, loading: authLoading, googleEnabled } = useAuth()
  const [petitions, setPetitions] = useState<Petition[]>([])
  const [filter, setFilter] = useState<PetitionStatus | ''>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showEmpty, setShowEmpty] = useState(false)

  useEffect(() => {
    if (authLoading) return

    setLoading(true)
    setError('')
    setShowEmpty(false)
    const fetchPetitions = googleEnabled ? listMyPetitions : listPetitions
    fetchPetitions(filter || undefined)
      .then(setPetitions)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load petitions'))
      .finally(() => setLoading(false))
  }, [filter, authLoading, googleEnabled, user])

  useEffect(() => {
    if (!loading && petitions.length === 0) {
      const t = requestAnimationFrame(() => setShowEmpty(true))
      return () => cancelAnimationFrame(t)
    }
    setShowEmpty(false)
  }, [loading, petitions.length])

  return (
    <div className="dashboard-page">
      <header className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 sm:gap-6 mb-[clamp(1.5rem,4vw,2.25rem)]">
        <div className="text-center sm:text-left">
          <h2 className="text-[clamp(1.5rem,4vw,1.75rem)] font-semibold text-civic-900 tracking-tight">
            My Petitions
          </h2>
          <p className="text-slate-600 text-[clamp(0.875rem,2vw,0.95rem)] mt-1">
            Track civic issues you've reported
          </p>
        </div>
        <Link to="/new" className="dashboard-btn-primary w-full sm:w-auto inline-flex items-center justify-center min-h-[48px] px-5 py-2.5 rounded-[1.1rem] font-medium text-white">
          + Report Issue
        </Link>
      </header>

      <div className="dashboard-card rounded-[1.5rem] sm:rounded-[1.75rem] border border-stone-200/70 bg-white shadow-[0_4px_28px_-10px_rgba(12,74,110,0.1)] p-[clamp(1rem,3vw,1.75rem)] sm:p-[clamp(1.25rem,3.5vw,2rem)]">
        <DashboardFilterTabs filters={FILTERS} value={filter} onChange={setFilter} />

        {error && (
          <p className="mb-4 text-sm text-red-700 bg-red-50 border border-red-100 rounded-[1rem] px-4 py-3">
            {error}
          </p>
        )}

        {loading ? (
          <p className="text-slate-500 text-sm py-8 text-center">Loading your petitions…</p>
        ) : petitions.length === 0 ? (
          <div
            className={`dashboard-empty text-center py-[clamp(2rem,6vw,3.5rem)] px-[clamp(1rem,4vw,2rem)] ${
              showEmpty ? 'dashboard-empty-visible' : ''
            }`}
          >
            <DashboardEmptyDoodle className="w-48 sm:w-56 mx-auto mb-6 sm:mb-8 text-civic-600/50 dashboard-empty-doodle" />
            <p className="text-[clamp(1rem,2.5vw,1.125rem)] text-slate-700 font-medium mb-8 max-w-sm mx-auto leading-relaxed">
              No petitions yet. Report your first civic issue!
            </p>
            <Link to="/new" className="dashboard-btn-secondary group inline-flex items-center justify-center gap-2 min-h-[48px] px-6 py-3 rounded-[1.1rem] font-medium text-civic-700">
              <span>Report an issue</span>
              <ArrowIcon />
            </Link>
          </div>
        ) : (
            <ul className="grid gap-3 sm:gap-4">
            {petitions.map((p) => (
              <li key={p.id}>
                <div className="dashboard-petition-card group flex gap-4 p-4 sm:p-5 rounded-[1.25rem] border border-stone-100 bg-stone-50/40">
                  <Link to={`/petitions/${p.id}`} className="flex gap-4 flex-1 min-w-0">
                    <img
                      src={p.photo_url}
                      alt=""
                      className="w-[4.5rem] h-[4.5rem] sm:w-20 sm:h-20 object-cover rounded-[1rem] flex-shrink-0 border border-stone-100"
                    />
                    <div className="flex-1 min-w-0 text-left">
                      <div className="flex flex-wrap items-center gap-2 mb-1">
                        <StatusBadge status={p.status} />
                        {p.issue_type && (
                          <span className="text-xs text-slate-500 capitalize">
                            {p.issue_type.replace('_', ' ')}
                          </span>
                        )}
                      </div>
                      <p className="font-medium text-civic-900 truncate group-hover:text-civic-700 transition-colors duration-200">
                        {p.location?.address || `${p.location?.lat?.toFixed(4)}, ${p.location?.lng?.toFixed(4)}`}
                      </p>
                      <p className="text-sm text-slate-500 truncate mt-0.5">{p.description || 'No description'}</p>
                      {p.department && (
                        <p className="text-xs text-slate-400 mt-1.5">→ {p.department}</p>
                      )}
                    </div>
                  </Link>
                  {p.status === 'draft' && (
                    <Link
                      to={`/approvals/${p.id}`}
                      className="self-center shrink-0 px-3 py-2 text-sm font-medium bg-civic-600 text-white rounded-xl hover:bg-civic-700"
                    >
                      Approve
                    </Link>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

function ArrowIcon() {
  return (
    <svg
      className="w-4 h-4 transition-transform duration-200 ease-out group-hover:translate-x-1"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d="M3 8h10M9 4l4 4-4 4" />
    </svg>
  )
}
