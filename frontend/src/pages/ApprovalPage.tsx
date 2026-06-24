import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { approvePetition, getPetition, getPendingApprovals } from '../api/client'
import { StatusBadge } from '../components/StatusBadge'
import type { Petition } from '../types'

export function ApprovalsPage() {
  const [complaints, setComplaints] = useState<Petition[]>([])
  const [escalations, setEscalations] = useState<Petition[]>([])

  useEffect(() => {
    getPendingApprovals().then((data) => {
      setComplaints(data.complaints)
      setEscalations(data.escalations)
    })
  }, [])

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
      className="flex gap-4 bg-white border rounded-xl p-4 hover:shadow-md"
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

export function ApprovalDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const params = new URLSearchParams(window.location.search)
  const isEscalation = params.get('escalation') === '1'

  const [petition, setPetition] = useState<Petition | null>(null)
  const [subject, setSubject] = useState('')
  const [body, setBody] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

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
      setLoading(false)
    })
  }, [id, isEscalation])

  const handleApprove = async (approved: boolean) => {
    if (!id) return
    setSubmitting(true)
    try {
      await approvePetition(id, { subject, body, approved, is_escalation: isEscalation })
      navigate(`/petitions/${id}`)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <p className="text-slate-500">Loading…</p>
  if (!petition) return <p className="text-red-600">Not found</p>

  return (
    <div className="max-w-4xl mx-auto">
      <Link to="/approvals" className="text-sm text-civic-600 hover:underline mb-4 inline-block">
        ← Back to approvals
      </Link>
      <h2 className="text-2xl font-bold text-civic-900 mb-2">
        {isEscalation ? 'Review Escalation Email' : 'Review Complaint Email'}
      </h2>
      <p className="text-slate-600 mb-6">Human-in-the-loop: edit the AI draft before sending.</p>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl border p-4 space-y-3">
          <h3 className="font-semibold">Issue Evidence</h3>
          <img src={petition.photo_url} alt="Issue" className="w-full rounded-xl" />
          <dl className="text-sm space-y-1">
            <div><dt className="text-slate-500 inline">Type: </dt><dd className="inline capitalize">{petition.issue_type?.replace('_', ' ')}</dd></div>
            <div><dt className="text-slate-500 inline">Department: </dt><dd className="inline">{petition.department}</dd></div>
            <div><dt className="text-slate-500 inline">To: </dt><dd className="inline">{petition.department_email}</dd></div>
            <div><dt className="text-slate-500 inline">Location: </dt><dd className="inline">{petition.location?.address || `${petition.location?.lat}, ${petition.location?.lng}`}</dd></div>
          </dl>
        </div>

        <div className="bg-white rounded-2xl border p-4 space-y-4">
          <h3 className="font-semibold">Email Draft</h3>
          <div>
            <label className="text-sm font-medium">Subject</label>
            <input
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm mt-1"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Body</label>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={14}
              className="w-full border rounded-lg px-3 py-2 text-sm mt-1 font-mono"
            />
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => handleApprove(true)}
              disabled={submitting}
              className="flex-1 py-2.5 bg-emerald-600 text-white rounded-xl font-medium hover:bg-emerald-700 disabled:opacity-50"
            >
              {submitting ? 'Sending…' : '✓ Approve & Send'}
            </button>
            <button
              onClick={() => handleApprove(false)}
              disabled={submitting}
              className="px-4 py-2.5 border border-red-300 text-red-700 rounded-xl font-medium hover:bg-red-50"
            >
              Reject
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
