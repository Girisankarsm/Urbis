import type { ActivityEvent, Petition } from '../types'

export interface AuthUser {
  id: string
  email: string
  name: string
  picture?: string
  can_send_gmail: boolean
}

const API_BASE = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')
const API = `${API_BASE}/api`

export function apiBaseUrl(): string {
  return API_BASE
}

export function loginUrl(): string {
  return `${API_BASE}/api/auth/google`
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
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

export async function logout(): Promise<void> {
  await request('/auth/logout', { method: 'POST' })
}

export async function uploadPhoto(file: File, kind: 'petitions' | 'follow-up' = 'petitions'): Promise<string> {
  const form = new FormData()
  form.append('file', file)
  const query = kind === 'follow-up' ? '?kind=follow-up' : ''
  const res = await fetch(`${API}/uploads${query}`, { method: 'POST', body: form, credentials: 'include' })
  if (!res.ok) throw new Error('Upload failed')
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
}): Promise<{ petition: Petition }> {
  return request('/petitions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
}

export async function approvePetition(
  id: string,
  data: { subject: string; body: string; approved: boolean; is_escalation?: boolean },
): Promise<{ petition: Petition }> {
  return request(`/petitions/${id}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
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

export async function getPendingApprovals(): Promise<{
  complaints: Petition[]
  escalations: Petition[]
}> {
  return request('/petitions/pending-approvals')
}
