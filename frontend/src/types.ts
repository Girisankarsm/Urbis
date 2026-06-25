export type PetitionStatus =
  | 'draft'
  | 'submitted'
  | 'under_review'
  | 'resolved'
  | 'escalated'

export interface Location {
  address: string
  lat: number
  lng: number
}

export interface Petition {
  id: string
  issue_type?: string
  photo_url: string
  follow_up_photo_url?: string
  location: Location
  description?: string
  department?: string
  department_email?: string
  authority_source?: 'web_search' | 'lemma' | 'registry' | 'unknown'
  area_info?: {
    display_name?: string
    city?: string
    municipality?: string
    state?: string
    country?: string
  }
  lemma_powered?: boolean
  status: PetitionStatus
  complaint_email_draft?: string
  complaint_email_subject?: string
  escalation_email_draft?: string
  resolution_verdict?: {
    resolved: boolean
    confidence: number
    reasoning: string
  }
  submitted_at?: string
  resolved_at?: string
  escalated_at?: string
  created_at?: string
}

export interface ActivityEvent {
  id: string
  petition_id: string
  event_type: string
  message: string
  metadata?: Record<string, unknown>
  timestamp?: string
}
