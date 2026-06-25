import { describe, expect, it, vi, beforeEach } from 'vitest'

describe('api client', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'https://api.example.com')
  })

  it('builds login URL from VITE_API_URL', async () => {
    vi.resetModules()
    const { loginUrl } = await import('./client')
    expect(loginUrl()).toBe('https://api.example.com/api/auth/google')
  })

  it('builds reconnect login URL', async () => {
    vi.resetModules()
    const { loginUrl } = await import('./client')
    expect(loginUrl(true)).toBe('https://api.example.com/api/auth/google?reconnect=1')
  })

  it('uses relative API path when VITE_API_URL is unset', async () => {
    vi.stubEnv('VITE_API_URL', '')
    vi.resetModules()
    const { loginUrl } = await import('./client')
    expect(loginUrl()).toBe('/api/auth/google')
  })
})
