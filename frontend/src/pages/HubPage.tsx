import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { getHubReports, toggleHubUpvote } from '../api/client'
import { LoginPrompt } from '../components/LoginPrompt'
import { StatusBadge } from '../components/StatusBadge'
import { useAuth } from '../context/AuthContext'
import type { HubReport } from '../types'

type SortMode = 'popular' | 'recent'

export function HubPage() {
  const { user, loading: authLoading, googleEnabled } = useAuth()
  const [reports, setReports] = useState<HubReport[]>([])
  const [sort, setSort] = useState<SortMode>('popular')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [votingId, setVotingId] = useState<string | null>(null)

  useEffect(() => {
    if (authLoading) return
    setLoading(true)
    setError('')
    getHubReports(sort)
      .then((data) => setReports(data.reports))
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load hub'))
      .finally(() => setLoading(false))
  }, [authLoading, googleEnabled, user, sort])

  const handleUpvote = async (reportId: string) => {
    if (googleEnabled && !user) return
    setVotingId(reportId)
    try {
      const result = await toggleHubUpvote(reportId)
      setReports((prev) =>
        prev.map((r) =>
          r.id === reportId
            ? { ...r, upvote_count: result.upvote_count, upvoted_by_me: result.upvoted_by_me }
            : r,
        ),
      )
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Could not upvote')
    } finally {
      setVotingId(null)
    }
  }

  if (!authLoading && googleEnabled && !user) {
    return (
      <LoginPrompt
        title="Sign in to explore the community hub"
        description="See civic reports filed by citizens in your city and upvote issues that matter."
      />
    )
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-civic-900">Community Hub</h2>
          <p className="text-slate-600 mt-1">
            See reports filed by citizens and upvote issues that need attention
          </p>
        </div>
        <div className="flex gap-2">
          <SortButton active={sort === 'popular'} onClick={() => setSort('popular')}>
            Most upvoted
          </SortButton>
          <SortButton active={sort === 'recent'} onClick={() => setSort('recent')}>
            Recent
          </SortButton>
        </div>
      </header>

      <p className="text-sm text-slate-500">
        Your pending email approvals are on{' '}
        <Link to="/dashboard" className="text-civic-700 font-medium underline">
          Dashboard
        </Link>{' '}
        (draft status).
      </p>

      {error && (
        <p className="text-sm text-red-700 bg-red-50 border border-red-100 rounded-xl px-4 py-3">{error}</p>
      )}

      {loading ? (
        <p className="text-slate-500 py-12 text-center">Loading community reports…</p>
      ) : reports.length === 0 ? (
        <div className="text-center py-16 rounded-2xl border border-dashed border-stone-200 bg-stone-50/50">
          <p className="text-4xl mb-3">🏘️</p>
          <p className="font-medium text-civic-900">No public reports yet</p>
          <p className="text-slate-500 text-sm mt-1 max-w-md mx-auto">
            When citizens file and approve complaints, they appear here for the community to support.
          </p>
          <Link
            to="/new"
            className="inline-flex mt-5 px-5 py-2.5 bg-civic-600 text-white rounded-xl text-sm font-medium"
          >
            Report the first issue
          </Link>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {reports.map((report) => (
            <HubCard
              key={report.id}
              report={report}
              onUpvote={() => handleUpvote(report.id)}
              voting={votingId === report.id}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function SortButton({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors ${
        active
          ? 'bg-civic-900 text-white border-civic-900'
          : 'bg-white text-slate-600 border-stone-200 hover:border-civic-300'
      }`}
    >
      {children}
    </button>
  )
}

function HubCard({
  report,
  onUpvote,
  voting,
}: {
  report: HubReport
  onUpvote: () => void
  voting: boolean
}) {
  return (
    <article className="bg-white rounded-2xl border border-stone-200/80 shadow-sm overflow-hidden flex flex-col hover:shadow-md transition-shadow">
      <Link to={`/petitions/${report.id}`} className="block">
        <img
          src={report.photo_url}
          alt=""
          className="w-full h-40 object-cover"
          loading="lazy"
        />
      </Link>
      <div className="p-4 flex flex-col flex-1 gap-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="font-semibold text-civic-900 capitalize truncate">
              {report.issue_type?.replace('_', ' ') || 'Civic issue'}
            </p>
            <p className="text-xs text-slate-500 truncate mt-0.5">{report.area_label}</p>
          </div>
          <StatusBadge status={report.status} />
        </div>
        {report.description && (
          <p className="text-sm text-slate-600 line-clamp-2">{report.description}</p>
        )}
        <div className="flex items-center justify-between mt-auto pt-1">
          <span className="text-xs text-slate-400">by {report.reporter_display}</span>
          <button
            type="button"
            onClick={onUpvote}
            disabled={voting}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium border transition-colors ${
              report.upvoted_by_me
                ? 'bg-civic-50 border-civic-300 text-civic-800'
                : 'bg-stone-50 border-stone-200 text-slate-700 hover:border-civic-300 hover:text-civic-800'
            }`}
            aria-pressed={report.upvoted_by_me}
          >
            <span aria-hidden>{report.upvoted_by_me ? '▲' : '△'}</span>
            {report.upvote_count}
          </button>
        </div>
      </div>
    </article>
  )
}
