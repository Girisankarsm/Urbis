import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { getHubReports, toggleHubUpvote } from '../api/client'
import { LoginPrompt } from '../components/LoginPrompt'
import { useAuth } from '../context/AuthContext'
import type { HubReport, PetitionStatus } from '../types'

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

const STATUS_LABELS: Record<PetitionStatus, string> = {
  draft: 'Draft',
  submitted: 'Submitted',
  under_review: 'Under review',
  resolved: 'Resolved',
  escalated: 'Escalated',
}

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
    return { count: reports.length, totalUpvotes, yours }
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
      <div className="hub-intro">
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
            <StatCard label="Public reports" value={stats.count} />
            <StatCard label="Community upvotes" value={stats.totalUpvotes} />
            <StatCard label="You supported" value={stats.yours} />
          </section>
        )}
      </div>

      <section className="hub-panel">
        <div className="hub-list-toolbar">
          {filterOpen ? (
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
          ) : (
            <>
              <p className="hub-results-count">
                {loading ? (
                  'Loading reports…'
                ) : reports.length === 0 ? (
                  'No reports yet'
                ) : (
                  <>
                    Showing <strong>{filtered.length}</strong> of {reports.length}
                  </>
                )}
              </p>
              <div className="hub-list-toolbar-actions">
                <div className="hub-pill-group" role="tablist" aria-label="Sort reports">
                  <SortButton active={sort === 'popular'} onClick={() => setSort('popular')}>
                    Most upvoted
                  </SortButton>
                  <SortButton active={sort === 'recent'} onClick={() => setSort('recent')}>
                    Most recent
                  </SortButton>
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
            </>
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
              <button
                type="button"
                className="hub-filter-chip hub-filter-chip--active"
                onClick={() => {
                  setIssueFilter('')
                  setFilterOpen(true)
                }}
              >
                Show all issues
              </button>
            )}
          </div>
        ) : (
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
        )}
      </section>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="hub-stat-card">
      <p className="hub-stat-value">{value}</p>
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
  const issueLabel = capitalize(report.issue_type?.replace(/_/g, ' ') || 'Issue')
  const areaTitle = formatAreaTitle(report)
  const fullAddress = formatFullAddress(report)
  const when = formatWhen(report.submitted_at || report.created_at)

  return (
    <article className="hub-card">
      <Link to={`/petitions/${report.id}`} className="hub-card-link">
        <div className="hub-card-media">
          <img src={report.photo_url} alt="" className="hub-card-image" loading="lazy" />
          <span className="hub-issue-chip">{issueLabel}</span>
        </div>

        <div className="hub-card-body">
          <div className="hub-meta-pills">
            {rank != null && rank <= 3 && (
              <span className={`hub-meta-pill hub-meta-pill--rank hub-meta-pill--rank-${rank}`}>#{rank}</span>
            )}
            <span className={`hub-meta-pill hub-meta-pill--status hub-meta-pill--status-${report.status}`}>
              {STATUS_LABELS[report.status]}
            </span>
            {report.severity_level && (
              <span className="hub-meta-pill hub-meta-pill--severity">{report.severity_level}</span>
            )}
          </div>

          <h3 className="hub-card-title">{areaTitle}</h3>

          {fullAddress && fullAddress !== areaTitle && (
            <p className="hub-card-address" title={fullAddress}>
              {fullAddress}
            </p>
          )}

          {report.description && <p className="hub-card-desc">{report.description}</p>}

          <div className="hub-card-byline">
            <span>{report.reporter_display}</span>
            {when && <span className="hub-card-dot">·</span>}
            {when && <time dateTime={report.submitted_at || report.created_at}>{when}</time>}
          </div>
        </div>
      </Link>

      <div className="hub-card-actions">
        <button
          type="button"
          onClick={onUpvote}
          disabled={voting}
          className={`hub-upvote ${report.upvoted_by_me ? 'hub-upvote--active' : ''}`}
          aria-pressed={report.upvoted_by_me}
          aria-label={`Upvote, ${report.upvote_count} votes`}
        >
          <UpvoteIcon filled={report.upvoted_by_me} />
          <span>{report.upvoted_by_me ? 'Supported' : 'Upvote'}</span>
          <span className="hub-upvote-count">{report.upvote_count}</span>
        </button>
      </div>
    </article>
  )
}


function UpvoteIcon({ filled }: { filled: boolean }) {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill={filled ? 'currentColor' : 'none'} aria-hidden>
      <path
        d="M12 4l2.2 4.5 5 .7-3.6 3.5.9 5.2L12 15.8 7.5 18l.9-5.2L4.8 9.2l5-.7L12 4z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function capitalize(text: string): string {
  return text.replace(/\b\w/g, (c) => c.toUpperCase())
}

function formatAreaTitle(report: HubReport): string {
  const area = report.area_info
  if (area) {
    const locality =
      area.display_name?.split(',')[0]?.trim() ||
      report.location?.address?.split(',')[0]?.trim() ||
      ''
    const region = area.municipality || area.city || area.state || ''
    if (locality && region && locality.toLowerCase() !== region.toLowerCase()) {
      return `${locality}, ${region}`
    }
    return region || locality || shortenAreaLabel(report.area_label)
  }
  return shortenAreaLabel(report.area_label)
}

function shortenAreaLabel(label: string): string {
  const parts = label
    .split(',')
    .map((s) => s.trim())
    .filter((s) => s && !/^\d{5,6}$/.test(s))
  if (parts.length >= 2) return `${parts[0]}, ${parts[1]}`
  return parts[0] || label
}

function formatFullAddress(report: HubReport): string {
  return report.location?.address?.trim() || report.area_label?.trim() || ''
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
