import { useEffect } from 'react'
import { Outlet, useNavigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'

export function RequireAuth() {
  const { user, loading, googleEnabled } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (!loading && googleEnabled && !user) {
      navigate('/', { replace: true })
    }
  }, [loading, googleEnabled, user, navigate])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <p className="text-slate-500">Loading…</p>
      </div>
    )
  }

  if (googleEnabled && !user) return null

  return <Outlet />
}
