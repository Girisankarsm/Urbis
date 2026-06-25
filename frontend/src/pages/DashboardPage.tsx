import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { listMyPetitions, listPetitions } from '../api/client'
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

  useEffect(() => {
    if (authLoading) return

    setLoading(true)
    setError('')
    const fetchPetitions = googleEnabled ? listMyPetitions : listPetitions
    fetchPetitions(filter || undefined)
      .then(setPetitions)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load petitions'))
      .finally(() => setLoading(false))
  }, [filter, authLoading, googleEnabled, user])

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-2xl font-bold text-civic-900">My Petitions</h2>
          <p className="text-slate-600 text-sm">Track civic issues you've reported</p>
        </div>
        <Link
          to="/new"
          className="px-4 py-2 bg-civic-600 text-white rounded-xl font-medium hover:bg-civic-700"
        >
          + Report Issue
        </Link>
      </div>

      <div className="flex flex-wrap gap-2 mb-6">
        {FILTERS.map((f) => (
          <button
            key={f.label}
            onClick={() => setFilter(f.value)}
            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
              filter === f.value ? 'bg-civic-600 text-white' : 'bg-white border text-slate-600 hover:bg-slate-50'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {error && (
        <p className="mb-4 text-sm text-red-600 bg-red-50 border border-red-100 rounded-xl px-4 py-3">{error}</p>
      )}

      {loading ? (
        <p className="text-slate-500">Loading…</p>
      ) : petitions.length === 0 ? (
        <div className="bg-white rounded-2xl border p-12 text-center">
          <p className="text-4xl mb-3">🏙️</p>
          <p className="text-slate-600 mb-4">No petitions yet. Report your first civic issue!</p>
          <Link to="/new" className="text-civic-600 font-medium hover:underline">
            Report an issue →
          </Link>
        </div>
      ) : (
        <div className="grid gap-4">
          {petitions.map((p) => (
            <Link
              key={p.id}
              to={`/petitions/${p.id}`}
              className="bg-white rounded-2xl border p-4 flex gap-4 hover:shadow-md transition-shadow"
            >
              <img
                src={p.photo_url}
                alt=""
                className="w-20 h-20 object-cover rounded-xl flex-shrink-0"
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <StatusBadge status={p.status} />
                  {p.issue_type && (
                    <span className="text-xs text-slate-500 capitalize">
                      {p.issue_type.replace('_', ' ')}
                    </span>
                  )}
                </div>
                <p className="font-medium truncate">
                  {p.location?.address || `${p.location?.lat?.toFixed(4)}, ${p.location?.lng?.toFixed(4)}`}
                </p>
                <p className="text-sm text-slate-500 truncate">{p.description || 'No description'}</p>
                {p.department && (
                  <p className="text-xs text-slate-400 mt-1">→ {p.department}</p>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
