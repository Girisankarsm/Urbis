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
      <header className="dashboard-page-header">
        <div className="dashboard-page-intro">
          <h2 className="dashboard-page-title">My Petitions</h2>
          <p className="dashboard-page-subtitle">Track civic issues you've reported</p>
        </div>
        <Link to="/new" className="dashboard-btn-primary dashboard-page-cta">
          + Report Issue
        </Link>
      </header>

      <div className="dashboard-card">
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
            <ul className="dashboard-petition-list">
            {petitions.map((p) => (
              <li key={p.id}>
                <div className="dashboard-petition-card group">
                  <Link to={`/petitions/${p.id}`} className="dashboard-petition-link">
                    <div className="dashboard-petition-media">
                      <img src={p.photo_url} alt="" className="dashboard-petition-photo" />
                    </div>
                    <div className="dashboard-petition-body">
                      <div className="dashboard-petition-meta">
                        <StatusBadge status={p.status} />
                        {p.issue_type && (
                          <span className="dashboard-petition-type">
                            {p.issue_type.replace('_', ' ')}
                          </span>
                        )}
                      </div>
                      <p className="dashboard-petition-location">
                        {p.location?.address || `${p.location?.lat?.toFixed(4)}, ${p.location?.lng?.toFixed(4)}`}
                      </p>
                      <p className="dashboard-petition-desc">{p.description || 'No description'}</p>
                      {p.department && (
                        <p className="dashboard-petition-dept">→ {p.department}</p>
                      )}
                    </div>
                  </Link>
                  {p.status === 'draft' && (
                    <Link to={`/approvals/${p.id}`} className="dashboard-petition-approve">
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
