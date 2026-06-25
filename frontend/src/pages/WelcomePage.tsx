import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { WelcomeLoader } from '../components/WelcomeLoader'
import { useAuth } from '../context/AuthContext'

const AUTH_ERROR_MESSAGES: Record<string, string> = {
  access_denied: 'Google sign-in was cancelled. Add your email as a test user in Google Cloud Console if the app is in Testing mode.',
  denied: 'Google sign-in was denied. Publish the OAuth consent screen or add yourself as a test user.',
}

const STEPS = [
  {
    icon: '📸',
    title: 'Report the issue',
    description: 'Photograph a pothole, garbage pile, broken streetlight, or other civic problem and pin the location on the map.',
  },
  {
    icon: '🤖',
    title: 'AI classifies & drafts',
    description: 'Urbis identifies the issue type, routes it to the right municipal department, and drafts a formal complaint email.',
  },
  {
    icon: '✅',
    title: 'You approve before sending',
    description: 'Review and edit the AI-drafted email. Nothing is sent without your explicit approval — human-in-the-loop by design.',
  },
  {
    icon: '📧',
    title: 'Complaint goes to authority',
    description: 'The email is sent from your Gmail to the municipal contact for your area (e.g. BBMP, BMC).',
  },
  {
    icon: '📊',
    title: 'Track resolution',
    description: 'Follow petition status on your dashboard, upload follow-up photos, and escalate if nothing changes.',
  },
]

export function WelcomePage() {
  const navigate = useNavigate()
  const { user, loading, googleEnabled, login } = useAuth()
  const [authError, setAuthError] = useState('')
  const [contentReady, setContentReady] = useState(false)
  const [loaderPhase, setLoaderPhase] = useState<'loading' | 'exiting' | 'done'>('loading')

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const code = params.get('auth_error')
    if (code) {
      setAuthError(AUTH_ERROR_MESSAGES[code] ?? 'Sign-in failed. Please try again.')
      window.history.replaceState({}, '', window.location.pathname)
    }
  }, [])

  useEffect(() => {
    if (loading) return
    const exitTimer = setTimeout(() => {
      setContentReady(true)
      setLoaderPhase('exiting')
    }, 350)
    const doneTimer = setTimeout(() => setLoaderPhase('done'), 900)
    return () => {
      clearTimeout(exitTimer)
      clearTimeout(doneTimer)
    }
  }, [loading])

  const signedIn = Boolean(user)

  return (
    <>
      {loaderPhase !== 'done' && <WelcomeLoader exiting={loaderPhase === 'exiting'} />}

      <div
        className={`relative min-h-screen flex flex-col bg-gradient-to-b from-civic-900 via-civic-800 to-slate-50 transition-opacity duration-700 ${
          contentReady ? 'opacity-100' : 'opacity-0'
        }`}
      >
        {/* Hero background accents */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-20 left-1/4 w-72 h-72 rounded-full bg-civic-500/10 blur-3xl" />
          <div className="absolute top-40 right-1/4 w-56 h-56 rounded-full bg-sky-300/10 blur-3xl" />
        </div>

        <header className="relative px-4 sm:px-6 py-6 animate-welcome-fade-up">
          <div className="max-w-4xl mx-auto flex items-center gap-3 text-white">
            <div className="w-12 h-12 rounded-xl bg-white/10 backdrop-blur border border-white/20 flex items-center justify-center text-2xl shadow-lg">
              🏛️
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Urbis</h1>
              <p className="text-sm text-civic-100">Citizen civic-issue reporting</p>
            </div>
          </div>
        </header>

        <main className="relative flex-1 px-4 sm:px-6 pb-12">
          <div className="max-w-4xl mx-auto">
            <section
              className="text-center text-white mb-10 pt-4 animate-welcome-fade-up"
              style={{ animationDelay: '0.1s' }}
            >
              <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 border border-white/20 text-xs font-medium text-civic-100 mb-5 backdrop-blur-sm">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Civic tech · Powered by Lemma SDK
              </span>
              <h2 className="text-3xl sm:text-5xl font-bold mb-4 leading-tight">
                Report civic issues.
                <br />
                <span className="text-civic-200">Get them fixed.</span>
              </h2>
              <p className="text-civic-100 text-lg sm:text-xl max-w-2xl mx-auto leading-relaxed">
                Photograph problems, draft complaints with AI, and send them to the right municipal authority —
                with you in control every step of the way.
              </p>
            </section>

            <section
              className="bg-white/95 backdrop-blur rounded-3xl shadow-2xl border border-white/50 p-6 sm:p-10 mb-8 animate-welcome-fade-up"
              style={{ animationDelay: '0.2s' }}
            >
              <h3 className="text-lg font-semibold text-civic-900 mb-2 text-center">How Urbis works</h3>
              <p className="text-sm text-slate-500 text-center mb-8">Five steps from photo to resolution</p>
              <ol className="grid gap-4 sm:grid-cols-2">
                {STEPS.map((step, index) => (
                  <li
                    key={step.title}
                    className={`group flex gap-4 p-4 rounded-2xl border border-slate-100 bg-slate-50/50 hover:bg-white hover:border-civic-200 hover:shadow-md transition-all duration-300 ${
                      index === STEPS.length - 1 ? 'sm:col-span-2 sm:max-w-md sm:mx-auto sm:w-full' : ''
                    }`}
                  >
                    <div className="shrink-0 w-11 h-11 rounded-xl bg-gradient-to-br from-civic-600 to-civic-800 text-white flex items-center justify-center text-lg shadow-md group-hover:scale-105 transition-transform">
                      {step.icon}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-civic-600">
                          Step {index + 1}
                        </span>
                      </div>
                      <h4 className="font-semibold text-civic-900 mb-1">{step.title}</h4>
                      <p className="text-sm text-slate-600 leading-relaxed">{step.description}</p>
                    </div>
                  </li>
                ))}
              </ol>
            </section>

            <section
              className="bg-white rounded-2xl border border-slate-200 shadow-xl p-6 sm:p-8 text-center animate-welcome-fade-up"
              style={{ animationDelay: '0.35s' }}
            >
              {authError && (
                <div className="mb-6 text-sm text-amber-900 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-left">
                  {authError}
                </div>
              )}
              <h3 className="text-xl font-bold text-civic-900 mb-2">
                {signedIn ? 'Welcome back' : 'Ready to get started?'}
              </h3>
              <p className="text-slate-600 text-sm mb-6 max-w-md mx-auto">
                {signedIn
                  ? `Signed in as ${user?.email}. Head to your dashboard to track petitions or report a new issue.`
                  : googleEnabled
                    ? 'Sign in with Google so complaints are sent from your Gmail to the municipal authority.'
                    : 'Continue to the app and report your first civic issue.'}
              </p>
              {signedIn ? (
                <button
                  type="button"
                  onClick={() => navigate('/dashboard')}
                  className="inline-flex items-center gap-2 px-8 py-3.5 bg-gradient-to-r from-civic-600 to-civic-700 text-white rounded-xl font-semibold hover:from-civic-700 hover:to-civic-800 shadow-lg shadow-civic-600/25 hover:shadow-civic-600/40 transition-all duration-300 hover:-translate-y-0.5"
                >
                  Go to dashboard →
                </button>
              ) : googleEnabled ? (
                <button
                  type="button"
                  onClick={login}
                  className="inline-flex items-center gap-3 px-8 py-3.5 bg-white border border-slate-200 rounded-xl font-semibold hover:bg-slate-50 shadow-md hover:shadow-lg transition-all duration-300 hover:-translate-y-0.5"
                >
                  <GoogleIcon />
                  Sign in with Google
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => navigate('/dashboard')}
                  className="inline-flex items-center gap-2 px-8 py-3.5 bg-gradient-to-r from-civic-600 to-civic-700 text-white rounded-xl font-semibold hover:from-civic-700 hover:to-civic-800 shadow-lg shadow-civic-600/25 transition-all duration-300 hover:-translate-y-0.5"
                >
                  Get started →
                </button>
              )}
              <p className="mt-6 text-xs text-slate-400">Gappy AI Hackathon · Human-in-the-loop civic reporting</p>
            </section>
          </div>
        </main>
      </div>
    </>
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
