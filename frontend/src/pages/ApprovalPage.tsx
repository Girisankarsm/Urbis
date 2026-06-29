import { useEffect, useMemo, useState, type ComponentType, type ReactNode } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import {
  AreaIcon,
  BackArrowIcon,
  BuildingIcon,
  PinIcon,
  SourceIcon,
  TypeTagIcon,
  VerifyDotIcon,
} from '../components/approval/ApprovalIcons'
import { approvePetition, getPetition, getPendingApprovals, loginUrl } from '../api/client'
import { LoginPrompt } from '../components/LoginPrompt'
import { StatusBadge } from '../components/StatusBadge'
import { useAuth } from '../context/AuthContext'
import type { Petition } from '../types'

export function ApprovalsPage() {
  const { user, loading: authLoading, googleEnabled } = useAuth()
  const [complaints, setComplaints] = useState<Petition[]>([])
  const [escalations, setEscalations] = useState<Petition[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (authLoading) return
    if (googleEnabled && !user) {
      setLoading(false)
      return
    }
    getPendingApprovals()
      .then((data) => {
        setComplaints(data.complaints)
        setEscalations(data.escalations)
      })
      .finally(() => setLoading(false))
  }, [authLoading, googleEnabled, user])

  if (!authLoading && googleEnabled && !user) {
    return (
      <LoginPrompt
        title="Sign in to review approvals"
        description="Pending complaint and escalation emails are visible only to your account."
      />
    )
  }

  if (loading) return <p className="text-slate-500">Loading…</p>

  return (
    <div>
      <h2 className="text-2xl font-bold text-civic-900 mb-6">Pending Approvals</h2>
      {complaints.length === 0 && escalations.length === 0 ? (
        <p className="text-slate-500">No pending approvals. All caught up!</p>
      ) : (
        <div className="space-y-6">
          {complaints.length > 0 && (
            <section>
              <h3 className="font-semibold mb-3">Complaint Emails</h3>
              <div className="grid gap-3">
                {complaints.map((p) => (
                  <ApprovalCard key={p.id} petition={p} type="complaint" />
                ))}
              </div>
            </section>
          )}
          {escalations.length > 0 && (
            <section>
              <h3 className="font-semibold mb-3">Escalation Emails</h3>
              <div className="grid gap-3">
                {escalations.map((p) => (
                  <ApprovalCard key={p.id} petition={p} type="escalation" />
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  )
}

function ApprovalCard({ petition, type }: { petition: Petition; type: 'complaint' | 'escalation' }) {
  return (
    <Link
      to={`/approvals/${petition.id}${type === 'escalation' ? '?escalation=1' : ''}`}
      className="flex gap-4 bg-white border rounded-xl p-4 hover:shadow-md transition-shadow duration-200 ease-out"
    >
      <img src={petition.photo_url} alt="" className="w-16 h-16 object-cover rounded-lg" />
      <div>
        <StatusBadge status={petition.status} />
        <p className="font-medium mt-1">{petition.complaint_email_subject || 'Escalation email'}</p>
        <p className="text-sm text-slate-500">{petition.department}</p>
      </div>
    </Link>
  )
}

function MetaRow({
  icon: Icon,
  label,
  value,
}: {
  icon: ComponentType<{ className?: string }>
  label: string
  value: ReactNode
}) {
  return (
    <div className="approval-meta-row">
      <Icon className="approval-meta-icon" />
      <div className="min-w-0">
        <dt className="approval-meta-label">{label}</dt>
        <dd className="approval-meta-value">{value}</dd>
      </div>
    </div>
  )
}

export function ApprovalDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user, loading: authLoading, googleEnabled } = useAuth()
  const params = new URLSearchParams(window.location.search)
  const isEscalation = params.get('escalation') === '1'

  const [petition, setPetition] = useState<Petition | null>(null)
  const [subject, setSubject] = useState('')
  const [body, setBody] = useState('')
  const [toEmail, setToEmail] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [sendingAction, setSendingAction] = useState<'approve' | 'reject' | null>(null)

  const contactChannel = petition?.contact_channel || 'email'
  const isEmailChannel = contactChannel === 'email'
  const contactValue = petition?.contact_value || petition?.department_email || ''

  useEffect(() => {
    if (!id) return
    getPetition(id).then((data) => {
      setPetition(data.petition)
      if (isEscalation) {
        setSubject(`ESCALATION: ${data.petition.issue_type?.replace('_', ' ') || 'Civic issue'}`)
        setBody(data.petition.escalation_email_draft || '')
      } else {
        setSubject(data.petition.complaint_email_subject || '')
        setBody(data.petition.complaint_email_draft || '')
      }
      setToEmail(data.petition.department_email || '')
      setLoading(false)
    })
  }, [id, isEscalation])

  const bodyWordCount = useMemo(
    () => body.trim().split(/\s+/).filter(Boolean).length,
    [body],
  )

  const locationLabel =
    petition?.location?.address ||
    (petition?.location?.lat != null
      ? `${petition.location.lat}, ${petition.location.lng}`
      : '—')

  const handleApprove = async (approved: boolean) => {
    if (!id) return
    if (approved && googleEnabled && user && !user.can_send_gmail) {
      alert(
        'Gmail is not connected. Open Profile → Connect Gmail, sign in again, then return here to send.',
      )
      return
    }
    setSubmitting(true)
    setSendingAction(approved ? 'approve' : 'reject')
    try {
      const result = await approvePetition(id, {
        subject,
        body,
        to_email: toEmail.trim() || undefined,
        approved,
        is_escalation: isEscalation,
      })
      if (!approved) {
        navigate(`/petitions/${id}`)
        return
      }
      if (result.email_sent) {
        const note = result.send_message || `Complaint sent to ${result.sent_to}`
        navigate(`/petitions/${id}`, { state: { flash: note } })
      } else if (result.contact_filed) {
        navigate(`/petitions/${id}`, {
          state: { flash: result.send_message || 'Complaint approved for official channel filing.' },
        })
      } else {
        alert(
          result.send_message ||
            'Email could not be sent. Sign in with Google (for Gmail) or check Brevo SMTP in .env.',
        )
        navigate(`/petitions/${id}`)
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed')
    } finally {
      setSubmitting(false)
      setSendingAction(null)
    }
  }

  if (authLoading) return <p className="text-slate-500">Loading…</p>
  if (googleEnabled && !user) {
    return (
      <LoginPrompt
        title="Sign in to approve & send"
        description="Your complaint will be sent from your Gmail to the municipal authority."
      />
    )
  }
  if (loading) return <p className="text-slate-500">Loading…</p>
  if (!petition) return <p className="text-red-600">Not found</p>

  return (
    <div className="approval-page max-w-5xl mx-auto px-[clamp(0.25rem,2vw,0.5rem)]">
      <Link to="/approvals" className="approval-breadcrumb">
        <BackArrowIcon className="w-4 h-4 shrink-0" />
        Back to approvals
      </Link>

      <header className="approval-header-lead">
        <h2 className="text-2xl font-bold text-civic-900 mb-2">
          {isEscalation ? 'Review Escalation Email' : 'Review Complaint Email'}
        </h2>
        <p className="text-slate-600 leading-relaxed">
          Human-in-the-loop: edit the AI draft before sending.
        </p>
        <div className="approval-header-meta">
          {user?.email && (
            <p className="text-sm text-civic-800">
              <span className="text-slate-500">From:</span>{' '}
              <strong className="font-semibold text-civic-900">{user.email}</strong>
              {user.can_send_gmail ? (
                <span className="text-slate-500"> (your Gmail)</span>
              ) : (
                <span className="text-amber-700"> — Gmail not connected</span>
              )}
            </p>
          )}
          {googleEnabled && user && !user.can_send_gmail && (
            <div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
              <p className="font-medium">Connect Gmail before sending</p>
              <p className="mt-1 text-amber-800">
                Urbis sends complaints from your Gmail so they show up in your Sent folder.
              </p>
              <a
                href={loginUrl(true)}
                className="mt-2 inline-flex text-sm font-semibold text-civic-700 hover:text-civic-900 underline"
              >
                Connect Gmail →
              </a>
            </div>
          )}
          <p className="text-xs text-slate-500 leading-relaxed">
            {isEmailChannel
              ? 'Verify the recipient email below — Urbis uses verified official contacts with source links when available.'
              : 'This location uses an official portal or helpline — approve to mark filed and copy your complaint text.'}
          </p>
        </div>
      </header>

      <div className="approval-grid">
        <section className="approval-panel approval-panel-evidence" aria-labelledby="evidence-heading">
          <h3 id="evidence-heading" className="font-semibold text-civic-900 mb-4">
            Issue Evidence
          </h3>
          <img src={petition.photo_url} alt="Issue evidence" className="approval-photo" />
          <dl className="approval-meta-grid">
            <MetaRow
              icon={TypeTagIcon}
              label="Type"
              value={<span className="capitalize">{petition.issue_type?.replace('_', ' ') || '—'}</span>}
            />
            <MetaRow icon={BuildingIcon} label="Department" value={petition.department || '—'} />
            {petition.authority_source && (
              <MetaRow
                icon={SourceIcon}
                label="Contact source"
                value={<span className="capitalize">{petition.authority_source.replace('_', ' ')}</span>}
              />
            )}
            {petition.contact_channel && petition.contact_channel !== 'email' && (
              <MetaRow
                icon={SourceIcon}
                label="Channel"
                value={<span className="capitalize">{petition.contact_channel}</span>}
              />
            )}
            {petition.source_url && (
              <MetaRow
                icon={SourceIcon}
                label="Official source"
                value={
                  <a
                    href={petition.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-civic-700 underline break-all"
                  >
                    {petition.source_url.replace(/^https?:\/\//, '')}
                  </a>
                }
              />
            )}
            {petition.area_info?.display_name && (
              <MetaRow icon={AreaIcon} label="Area" value={petition.area_info.display_name} />
            )}
            <MetaRow icon={PinIcon} label="Location" value={locationLabel} />
            {petition.lemma_powered && (
              <MetaRow icon={SourceIcon} label="Powered by" value={<span className="text-civic-700">Lemma SDK agents</span>} />
            )}
          </dl>
        </section>

        <section className="approval-panel approval-panel-draft" aria-labelledby="draft-heading">
          <h3 id="draft-heading" className="font-semibold text-civic-900 mb-4">
            Email Draft
          </h3>

          <div className="space-y-[clamp(1rem,3vw,1.25rem)]">
            {!isEmailChannel ? (
              <div className="rounded-xl border border-civic-200 bg-civic-50/80 px-4 py-3">
                <p className="approval-field-label mb-1">
                  Official {contactChannel === 'helpline' ? 'helpline' : 'portal'}
                </p>
                {contactChannel === 'helpline' ? (
                  <p className="text-lg font-semibold text-civic-900 tracking-wide">{contactValue}</p>
                ) : (
                  <a
                    href={contactValue}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-civic-700 font-medium underline break-all"
                  >
                    {contactValue}
                  </a>
                )}
                <p className="approval-hint-verify mt-2">
                  <VerifyDotIcon className="approval-hint-verify-dot" />
                  After approving, open this channel and paste the complaint text below
                </p>
              </div>
            ) : (
              <div>
                <label htmlFor="approval-to" className="approval-field-label">
                  To (municipal authority)
                </label>
                <input
                  id="approval-to"
                  type="email"
                  value={toEmail}
                  onChange={(e) => setToEmail(e.target.value)}
                  placeholder="secretary@tmcofficials.in"
                  className="approval-input approval-input-mono"
                  autoComplete="off"
                  spellCheck={false}
                  required
                />
                <p className="approval-hint-verify">
                  <VerifyDotIcon className="approval-hint-verify-dot" />
                  Auto-filled from verified official contact — please verify before sending
                </p>
              </div>
            )}

            <div>
              <label htmlFor="approval-subject" className="approval-field-label">
                Subject
              </label>
              <input
                id="approval-subject"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="approval-input"
              />
            </div>

            <div>
              <div className="approval-field-label">
                <label htmlFor="approval-body">Body</label>
                <span className="approval-badge-ai">AI-drafted — please review</span>
              </div>
              <textarea
                id="approval-body"
                value={body}
                onChange={(e) => setBody(e.target.value)}
                rows={14}
                className="approval-input approval-input-mono approval-textarea"
              />
              <p className="approval-body-count mt-2 text-right">
                {bodyWordCount} {bodyWordCount === 1 ? 'word' : 'words'}
              </p>
            </div>
          </div>
        </section>
      </div>

      <footer className="approval-footer" role="group" aria-label="Approval actions">
        <div className="approval-footer-inner">
          <button
            type="button"
            onClick={() => handleApprove(false)}
            disabled={submitting}
            className="approval-btn-reject"
          >
            {sendingAction === 'reject' ? 'Rejecting…' : 'Reject'}
          </button>
          <button
            type="button"
            onClick={() => handleApprove(true)}
            disabled={submitting || (isEmailChannel && !toEmail.trim())}
            className={`approval-btn-primary w-full sm:w-auto ${sendingAction === 'approve' ? 'is-sending' : ''}`}
          >
            {sendingAction === 'approve' ? (
              <>
                <span className="approval-send-spinner" aria-hidden />
                {isEmailChannel ? 'Sending…' : 'Saving…'}
              </>
            ) : isEmailChannel ? (
              '✓ Approve & Send'
            ) : (
              '✓ Approve & Mark Filed'
            )}
          </button>
        </div>
      </footer>
    </div>
  )
}
