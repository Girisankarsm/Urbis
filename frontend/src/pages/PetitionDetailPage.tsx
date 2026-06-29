import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { getPetition, uploadFollowUp, uploadPhoto } from '../api/client'
import { ComplaintTimeline } from '../components/ComplaintTimeline'
import { StatusBadge } from '../components/StatusBadge'
import type { ActivityEvent, Petition } from '../types'

export function PetitionDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [petition, setPetition] = useState<Petition | null>(null)
  const [activity, setActivity] = useState<ActivityEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)

  const load = () => {
    if (!id) return
    getPetition(id)
      .then((data) => {
        setPetition(data.petition)
        setActivity(data.activity)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(load, [id])

  const handleFollowUp = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !id) return
    setUploading(true)
    try {
      const url = await uploadPhoto(file, 'follow-up')
      const { petition: updated } = await uploadFollowUp(id, url)
      setPetition(updated)
      load()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  if (loading) return <p className="text-slate-500">Loading…</p>
  if (!petition) return <p className="text-red-600">Petition not found</p>

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <Link to="/hub" className="text-sm text-civic-600 hover:underline mb-2 inline-block">← Back to hub</Link>
          <h2 className="text-2xl font-bold text-civic-900 flex items-center gap-3">
            Petition Detail
            <StatusBadge status={petition.status} />
          </h2>
        </div>
        {petition.status === 'draft' && (
          <Link
            to={`/approvals/${petition.id}`}
            className="px-4 py-2 bg-civic-600 text-white rounded-xl text-sm font-medium"
          >
            Review & Approve →
          </Link>
        )}
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl border p-4 space-y-4">
          <h3 className="font-semibold">Before</h3>
          <img src={petition.photo_url} alt="Original" className="w-full rounded-xl" loading="lazy" />
          {petition.follow_up_photo_url ? (
            <>
              <h3 className="font-semibold">After (follow-up)</h3>
              <img src={petition.follow_up_photo_url} alt="Follow-up" className="w-full rounded-xl" loading="lazy" />
            </>
          ) : (
            petition.status !== 'draft' && (
              <label className="block border-2 border-dashed rounded-xl p-4 text-center cursor-pointer hover:border-civic-400">
                <span className="text-sm text-slate-500">
                  {uploading ? 'Uploading…' : '📷 Upload follow-up photo to check resolution'}
                </span>
                <input type="file" accept="image/*" className="hidden" onChange={handleFollowUp} disabled={uploading} />
              </label>
            )
          )}
        </div>

        <div className="space-y-4">
          <div className="bg-white rounded-2xl border p-4">
            <h3 className="font-semibold mb-3">Details</h3>
            <dl className="space-y-2 text-sm">
              <Row label="Issue type" value={petition.issue_type?.replace('_', ' ') || '—'} />
              <Row label="Department" value={petition.department || '—'} />
              <Row label="Location" value={petition.location?.address || `${petition.location?.lat}, ${petition.location?.lng}`} />
              <Row label="Description" value={petition.description || '—'} />
              {petition.severity_score != null && (
                <Row label="Severity" value={`${petition.severity_score}/100 (${petition.severity_level || '—'})`} />
              )}
              {petition.severity_explanation && (
                <div>
                  <dt className="text-slate-500">Severity analysis</dt>
                  <dd className="font-medium text-sm text-slate-700 whitespace-pre-line mt-1">{petition.severity_explanation}</dd>
                </div>
              )}
              {petition.resolution_verdict && (
                <Row
                  label="Resolution"
                  value={`${
                    petition.resolution_verdict.status === 'partially_resolved'
                      ? 'Partially resolved'
                      : petition.resolution_verdict.resolved
                        ? 'Likely resolved'
                        : 'Still open'
                  } (${Math.round(petition.resolution_verdict.confidence * 100)}% confidence)`}
                />
              )}
              {petition.ai_explanations?.authority_routing?.explanation && (
                <Row label="Authority routing" value={petition.ai_explanations.authority_routing.explanation} />
              )}
            </dl>
          </div>

          {petition.complaint_email_draft && (
            <div className="bg-white rounded-2xl border p-4">
              <h3 className="font-semibold mb-2">Complaint Email</h3>
              <p className="text-xs text-slate-500 mb-1">Subject: {petition.complaint_email_subject}</p>
              <pre className="text-xs whitespace-pre-wrap bg-slate-50 p-3 rounded-lg max-h-40 overflow-y-auto">
                {petition.complaint_email_draft}
              </pre>
            </div>
          )}
        </div>
      </div>

      <div className="bg-white rounded-2xl border p-4">
        <h3 className="font-semibold mb-3">Timeline</h3>
        <ComplaintTimeline events={activity} />
      </div>
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-slate-500">{label}</dt>
      <dd className="font-medium capitalize">{value}</dd>
    </div>
  )
}
