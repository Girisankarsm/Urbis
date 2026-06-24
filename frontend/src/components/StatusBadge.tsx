import type { PetitionStatus } from '../types'

const STYLES: Record<PetitionStatus, string> = {
  draft: 'bg-amber-100 text-amber-800',
  submitted: 'bg-blue-100 text-blue-800',
  under_review: 'bg-purple-100 text-purple-800',
  resolved: 'bg-emerald-100 text-emerald-800',
  escalated: 'bg-red-100 text-red-800',
}

const LABELS: Record<PetitionStatus, string> = {
  draft: 'Draft',
  submitted: 'Submitted',
  under_review: 'Under Review',
  resolved: 'Resolved',
  escalated: 'Escalated',
}

export function StatusBadge({ status }: { status: PetitionStatus }) {
  return (
    <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-semibold ${STYLES[status]}`}>
      {LABELS[status]}
    </span>
  )
}
