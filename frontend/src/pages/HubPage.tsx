import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { getHubReports, toggleHubUpvote } from '../api/client'
import { LoginPrompt } from '../components/LoginPrompt'
import { StatusBadge } from '../components/StatusBadge'
import { useAuth } from '../context/AuthContext'
import type { HubReport } from '../types'

type SortMode = 'popular' | 'recent'
type IssueFilter = '' | 'pothole' | 'garbage' | 'streetlight' | 'water_leak' | 'sewage' | 'other'

const ISSUE_FILTERS: { label: string; value: IssueFilter }[] = [
  { label: 'All issues', value: '' },
  { label: 'Garbage', value: 'garbage' },
  { label: 'Potholes', value: 'pothole' },
  { label: 'Drainage', value: 'sewage' },
  { label: 'Streetlights', value: 'streetlight' },
  { label: 'Water', value: 'water_leak' },
  { label: 'Other', value: 'other' },
]

export function HubPage() {
  const { user, loading: authLoading, googleEnabled } = useAuth()
  const [reports, setReports] = useState<HubReport[]>([])
  const [sort, setSort] = useState<SortMode>('popular')
  const [issueFilter, setIssueFilter] = useState<IssueFilter>('')
  const [filterOpen, setFilterOpen] = useState(false)
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

  const filtered = useMemo(() => {
    if (!issueFilter) return reports
    return reports.filter((r) => r.issue_type === issueFilter)
  }, [reports, issueFilter])

  const stats = useMemo(() => {
    const totalUpvotes = reports.reduce((sum, r) => sum + (r.upvote_count || 0), 0)
    const yours = reports.filter((r) => r.upvoted_by_me).length
    const top = reports[0]
    return { count: reports.length, totalUpvotes, yours, top }
  }, [reports])

  const activeFilterLabel = ISSUE_FILTERS.find((f) => f.value === issueFilter)?.label ?? 'All issues'

  const handleFilterSelect = (value: IssueFilter) => {
    setIssueFilter(value)
    setFilterOpen(false)
  }

  const handleUpvote = async (reportId: string, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
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
    <div className="hub-page">
      <header className="hub-header">
        <div className="hub-header-text">
          <p className="hub-eyebrow">Community</p>
          <h2 className="hub-title">Civic Reports Hub</h2>
          <p className="hub-subtitle">
            Discover issues filed by citizens, support what matters most, and help prioritize fixes in your city.
          </p>
        </div>
        <Link to="/new" className="dashboard-btn-primary hub-cta">
          + Report Issue
        </Link>
      </header>

      {!loading && reports.length > 0 && (
        <section className="hub-stats" aria-label="Hub statistics">
          <StatCard label="Public reports" value={String(stats.count)} />
          <StatCard label="Community upvotes" value={String(stats.totalUpvotes)} />
          <StatCard
            label="You supported"
            value={String(stats.yours)}
            hint={stats.yours === 1 ? 'report' : 'reports'}
          />
        </section>
      )}

      <section className="hub-panel">
        <div className="hub-toolbar">
          {!filterOpen ? (
            <div className="hub-toolbar-row">
              <div className="hub-toolbar-group">
                <span className="hub-toolbar-label">Sort</span>
                <div className="hub-pill-group" role="tablist" aria-label="Sort reports">
                  <SortButton active={sort === 'popular'} onClick={() => setSort('popular')}>
                    Most upvoted
                  </SortButton>
                  <SortButton active={sort === 'recent'} onClick={() => setSort('recent')}>
                    Most recent
                  </SortButton>
                </div>
              </div>
              <button
                type="button"
                className={`hub-filter-toggle ${issueFilter ? 'hub-filter-toggle--selected' : ''}`}
                onClick={() => setFilterOpen(true)}
                aria-expanded={false}
              >
                Filter
                {issueFilter ? <span className="hub-filter-toggle-value">{activeFilterLabel}</span> : null}
              </button>
            </div>
          ) : (
            <div className="hub-filter-panel">
              <div className="hub-filter-panel-head">
                <span className="hub-toolbar-label">Filter</span>
                <button
                  type="button"
                  className="hub-filter-close"
                  onClick={() => setFilterOpen(false)}
                  aria-label="Close filter"
                >
                  Done
                </button>
              </div>
              <div className="hub-filter-scroll">
                {ISSUE_FILTERS.map((f) => (
                  <button
                    key={f.value || 'all'}
                    type="button"
                    onClick={() => handleFilterSelect(f.value)}
                    className={`hub-filter-chip ${issueFilter === f.value ? 'hub-filter-chip--active' : ''}`}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        <p className="hub-hint">
          Draft complaints awaiting your approval live on{' '}
          <Link to="/dashboard" className="hub-hint-link">
            Dashboard
          </Link>
          . Only filed reports appear here.
        </p>

        {error && <p className="hub-error">{error}</p>}

        {loading ? (
          <div className="hub-grid hub-grid--loading" aria-busy="true">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="hub-skeleton" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="hub-empty">
            <p className="hub-empty-icon" aria-hidden>
              🏘️
            </p>
            <p className="hub-empty-title">
              {reports.length === 0 ? 'No public reports yet' : 'No reports match this filter'}
            </p>
            <p className="hub-empty-text">
              {reports.length === 0
                ? 'When citizens file and approve complaints, they appear here for the community to support.'
                : 'Try a different issue type or clear the filter.'}
            </p>
            {reports.length === 0 ? (
              <Link to="/new" className="dashboard-btn-primary hub-empty-cta">
                Report the first issue
              </Link>
            ) : (
              <button type="button" className="hub-filter-chip hub-filter-chip--active" onClick={() => { setIssueFilter(''); setFilterOpen(true) }}>
                Show all issues
              </button>
            )}
          </div>
        ) : (
          <>
            <p className="hub-results-count">
              Showing <strong>{filtered.length}</strong> of {reports.length} reports
            </p>
            <div className="hub-grid">
              {filtered.map((report, index) => (
                <HubCard
                  key={report.id}
                  report={report}
                  rank={sort === 'popular' && issueFilter === '' ? index + 1 : undefined}
                  onUpvote={(e) => handleUpvote(report.id, e)}
                  voting={votingId === report.id}
                />
              ))}
            </div>
          </>
        )}
      </section>
    </div>
  )
}

function StatCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="hub-stat-card">
      <p className="hub-stat-value">
        {value}
        {hint && <span className="hub-stat-hint"> {hint}</span>}
      </p>
      <p className="hub-stat-label">{label}</p>
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
      role="tab"
      aria-selected={active}
      onClick={onClick}
      className={`hub-sort-btn ${active ? 'hub-sort-btn--active' : ''}`}
    >
      {children}
    </button>
  )
}

function HubCard({
  report,
  rank,
  onUpvote,
  voting,
}: {
  report: HubReport
  rank?: number
  onUpvote: (e: React.MouseEvent) => void
  voting: boolean
}) {
  const issueLabel = report.issue_type?.replace(/_/g, ' ') || 'civic issue'
  const when = formatWhen(report.submitted_at || report.created_at)

  return (
    <article className="hub-card">
      <Link to={`/petitions/${report.id}`} className="hub-card-link">
        <div className="hub-card-media">
          <img src={report.photo_url} alt="" className="hub-card-image" loading="lazy" />
          <div className="hub-card-media-overlay">
            {rank != null && rank <= 3 && (
              <span className={`hub-rank hub-rank--${rank}`}>#{rank}</span>
            )}
            <span className="hub-issue-chip">{issueLabel}</span>
          </div>
        </div>

        <div className="hub-card-body">
          <div className="hub-card-meta">
            <StatusBadge status={report.status} />
            {report.severity_level && (
              <span className="hub-severity">{report.severity_level}</span>
            )}
          </div>

          <h3 className="hub-card-title">{report.area_label}</h3>

          {report.description && <p className="hub-card-desc">{report.description}</p>}

          <div className="hub-card-footer">
            <div className="hub-card-byline">
              <span>{report.reporter_display}</span>
              {when && <span className="hub-card-dot">·</span>}
              {when && <time dateTime={report.submitted_at || report.created_at}>{when}</time>}
            </div>
          </div>
        </div>
      </Link>

      <button
        type="button"
        onClick={onUpvote}
        disabled={voting}
        className={`hub-upvote ${report.upvoted_by_me ? 'hub-upvote--active' : ''}`}
        aria-pressed={report.upvoted_by_me}
        aria-label={`Upvote, ${report.upvote_count} votes`}
      >
        <UpvoteIcon filled={report.upvoted_by_me} />
        <span className="hub-upvote-count">{report.upvote_count}</span>
      </button>
    </article>
  )
}

function UpvoteIcon({ filled }: { filled: boolean }) {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill={filled ? 'currentColor' : 'none'} aria-hidden>
      <path
        d="M12 4l2.2 4.5 5 .7-3.6 3.5.9 5.2L12 15.8 7.5 18l.9-5.2L4.8 9.2l5-.7L12 4z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function formatWhen(iso?: string): string {
  if (!iso) return ''
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ''
  const diff = Date.now() - date.getTime()
  const days = Math.floor(diff / 86400000)
  if (days < 1) return 'Today'
  if (days === 1) return 'Yesterday'
  if (days < 7) return `${days}d ago`
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}
