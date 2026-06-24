import { Link } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'

export function LoginPrompt({ title, description }: { title: string; description: string }) {
  const { login, googleEnabled } = useAuth()

  return (
    <div className="max-w-md mx-auto bg-white rounded-2xl shadow-sm border p-8 text-center">
      <div className="text-4xl mb-4">🔐</div>
      <h2 className="text-xl font-bold text-civic-900 mb-2">{title}</h2>
      <p className="text-slate-600 text-sm mb-6">{description}</p>
      {googleEnabled ? (
        <button
          type="button"
          onClick={login}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-white border border-slate-300 rounded-xl font-medium hover:bg-slate-50 shadow-sm"
        >
          <GoogleIcon />
          Sign in with Google
        </button>
      ) : (
        <p className="text-amber-700 text-sm bg-amber-50 border border-amber-200 rounded-lg p-3">
          Google sign-in is not configured yet. Add <code className="text-xs">GOOGLE_CLIENT_ID</code> and{' '}
          <code className="text-xs">GOOGLE_CLIENT_SECRET</code> to <code className="text-xs">.env</code>.
        </p>
      )}
      <p className="mt-4 text-xs text-slate-500">
        <Link to="/" className="text-civic-600 hover:underline">
          Back to dashboard
        </Link>
      </p>
    </div>
  )
}

function GoogleIcon() {
  return (
    <svg className="w-5 h-5" viewBox="0 0 24 24" aria-hidden>
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
    </svg>
  )
}
