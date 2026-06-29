import type { ActivityEvent, HubReport, Petition } from '../types'

export interface AuthUser {
  id: string
  email: string
  name: string
  picture?: string
  can_send_gmail: boolean
}

function resolveApiBase(): string {
  // On the deployed Vercel site, always use same-origin /api (proxied to Render).
  // Mobile Safari blocks third-party cookies when VITE_API_URL points at Render directly.
  if (import.meta.env.PROD && typeof window !== 'undefined') {
    const host = window.location.hostname
    if (host !== 'localhost' && host !== '127.0.0.1') {
      return ''
    }
  }
  return (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')
}

function apiPath(): string {
  const base = resolveApiBase()
  return base ? `${base}/api` : '/api'
}

export function apiBaseUrl(): string {
  return resolveApiBase()
}

export function loginUrl(reconnect = false): string {
  const path = reconnect ? '/api/auth/google?reconnect=1' : '/api/auth/google'
  const base = resolveApiBase()
  return base ? `${base}${path}` : path
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${apiPath()}${path}`, {
    credentials: 'include',
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    const detail = err.detail
    const message = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail[0]?.msg : 'Request failed'
    throw new Error(message || 'Request failed')
  }
  return res.json()
}

export async function fetchAuthStatus(): Promise<{
  google_auth_enabled: boolean
  login_url: string | null
  oauth_production_notes?: string
}> {
  return request('/auth/status')
}

export async function fetchAuthMe(): Promise<AuthUser> {
  return request('/auth/me')
}

export async function completeSignIn(code: string): Promise<AuthUser> {
  return request('/auth/complete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code }),
  })
}

export async function logout(): Promise<void> {
  await request('/auth/logout', { method: 'POST' })
}

export async function uploadPhoto(file: File, kind: 'petitions' | 'follow-up' = 'petitions'): Promise<string> {
  const form = new FormData()
  form.append('file', file)
  const query = kind === 'follow-up' ? '?kind=follow-up' : ''
  const res = await fetch(`${apiPath()}/uploads${query}`, { method: 'POST', body: form, credentials: 'include' })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    const detail = err.detail
    const message = typeof detail === 'string' ? detail : 'Upload failed'
    throw new Error(message)
  }
  const data = await res.json()
  return data.url
}

export async function listPetitions(status?: string): Promise<Petition[]> {
  const q = new URLSearchParams()
  if (status) q.set('status', status)
  const query = q.toString()
  return request<Petition[]>(`/petitions${query ? `?${query}` : ''}`)
}

export async function listMyPetitions(status?: string): Promise<Petition[]> {
  const q = new URLSearchParams({ mine: 'true' })
  if (status) q.set('status', status)
  return request<Petition[]>(`/petitions?${q}`)
}

export async function getPetition(id: string): Promise<{ petition: Petition; activity: ActivityEvent[] }> {
  return request(`/petitions/${id}`)
}

export async function createPetition(data: {
  photo_url: string
  location: { address: string; lat: number; lng: number }
  description: string
  vision_issue_type_override?: string
  vision_classification?: { issue_type: string; confidence: number; reasoning: string; source: string }
}): Promise<{ petition: Petition }> {
  return request('/petitions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
}

export async function approvePetition(
  id: string,
  data: { subject: string; body: string; approved: boolean; is_escalation?: boolean; to_email?: string },
): Promise<{
  petition: Petition
  email_sent?: boolean
  contact_filed?: boolean
  sent_to?: string
  intended_to?: string
  send_message?: string
}> {
  return request(`/petitions/${id}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
}

export async function deletePetition(id: string): Promise<{ message: string; id: string }> {
  return request(`/petitions/${id}`, { method: 'DELETE' })
}

export async function uploadFollowUp(id: string, follow_up_photo_url: string): Promise<{ petition: Petition }> {
  return request(`/petitions/${id}/follow-up`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ follow_up_photo_url }),
  })
}

export async function checkEscalation(): Promise<{ petition: Petition | null; message: string }> {
  return request('/petitions/escalation/check', { method: 'POST' })
}

export async function fetchLemmaHealth(): Promise<{
  live?: boolean
  active_path?: string
  token_valid?: boolean
  api_reachable?: boolean
  pod_name?: string
  reason?: string
  last_invocations?: string[]
}> {
  return request('/health/lemma')
}

export async function getHubReports(sort: 'popular' | 'recent' = 'popular'): Promise<{
  reports: HubReport[]
  count: number
}> {
  const q = new URLSearchParams({ sort })
  return request(`/hub/reports?${q}`)
}

export async function toggleHubUpvote(petitionId: string): Promise<{
  petition_id: string
  upvote_count: number
  upvoted_by_me: boolean
}> {
  return request(`/hub/reports/${petitionId}/upvote`, { method: 'POST' })
}

export async function getPendingApprovals(): Promise<{
  complaints: Petition[]
  escalations: Petition[]
}> {
  return request('/petitions/pending-approvals')
}

export async function classifyVision(photo_url: string, description = ''): Promise<{
  classification: { issue_type: string; confidence: number; reasoning: string; source: string }
  issue_types: string[]
}> {
  return request('/vision/classify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ photo_url, description }),
  })
}

export async function checkDuplicates(data: {
  lat: number
  lng: number
  issue_type?: string
  photo_url?: string
}): Promise<{
  duplicates: Array<{
    petition_id: string
    issue_type: string
    distance_m: number
    likelihood: number
    description?: string
  }>
  has_duplicates: boolean
}> {
  return request('/petitions/check-duplicates', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
}

export async function getNearbyInfrastructure(
  lat: number,
  lng: number,
): Promise<{ markers: Array<{ category: string; icon: string; lat: number; lng: number; name?: string }>; source: string }> {
  const q = new URLSearchParams({ lat: String(lat), lng: String(lng) })
  return request(`/infrastructure/nearby?${q}`)
}

export async function getAnalyticsSummary(): Promise<Record<string, unknown>> {
  return request('/analytics/summary')
}
