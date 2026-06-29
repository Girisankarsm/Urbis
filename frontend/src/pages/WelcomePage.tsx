import { useEffect, useState, type ComponentType, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'

import { WelcomeLoader } from '../components/WelcomeLoader'
import { WelcomeBlobs } from '../components/welcome/WelcomeBlobs'
import { CivicBuildingIcon, HeroDoodle, STEP_ICONS } from '../components/welcome/WelcomeIcons'
import { useAuth } from '../context/AuthContext'
import { useInView } from '../hooks/useInView'

const AUTH_ERROR_MESSAGES: Record<string, string> = {
  access_denied: 'Google sign-in was cancelled. Add your email as a test user in Google Cloud Console if the app is in Testing mode.',
  denied: 'Google sign-in was denied. Publish the OAuth consent screen or add yourself as a test user.',
  oauth_failed:
    'Google sign-in could not be completed. Add this site’s /api/auth/google/callback URL to Google Cloud Console → OAuth redirect URIs, then try again.',
  unknown:
    'Google sign-in could not be completed. Add this site’s /api/auth/google/callback URL to Google Cloud Console → OAuth redirect URIs, then try again.',
  redirect_uri_mismatch:
    'Google blocked sign-in: redirect URI mismatch. In Google Cloud Console → Credentials, add the exact callback URL for this site (see the note below if you are on localhost).',
  session_failed:
    'Sign-in completed but your session was not saved. On mobile, use the site in Safari/Chrome (not an in-app browser). Try again, or clear site data and sign in once more.',
}

const STEPS = [
  {
    title: 'Report the issue',
    description: 'Photograph a pothole, garbage pile, broken streetlight, or other civic problem and pin the location on the map.',
  },
  {
    title: 'AI classifies & drafts',
    description: 'Urbis identifies the issue type, routes it to the right municipal department, and drafts a formal complaint email.',
  },
  {
    title: 'You approve before sending',
    description: 'Review and edit the AI-drafted email. Nothing is sent without your explicit approval — human-in-the-loop by design.',
  },
  {
    title: 'Complaint goes to authority',
    description: 'The email is sent from your Gmail to the municipal contact for your area (e.g. BBMP, BMC).',
  },
  {
    title: 'Track resolution',
    description: 'Follow petition status on your dashboard, upload follow-up photos, and escalate if nothing changes.',
  },
]

export function WelcomePage() {
  const navigate = useNavigate()
  const { user, loading, googleEnabled, authError: contextAuthError, clearAuthError, login } = useAuth()
  const [authError, setAuthError] = useState('')
  const [devOAuthHint, setDevOAuthHint] = useState('')
  const [contentReady, setContentReady] = useState(false)
  const [loaderPhase, setLoaderPhase] = useState<'loading' | 'exiting' | 'done'>('loading')

  const heroRef = useInView<HTMLElement>(0.08)
  const stepsRef = useInView<HTMLElement>(0.06)
  const ctaRef = useInView<HTMLElement>(0.1)

  useEffect(() => {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      setDevOAuthHint(
        'Local dev: in Google Cloud Console add redirect URI http://localhost:8000/api/auth/google/callback and JavaScript origin http://localhost:5173',
      )
    }
  }, [])

  useEffect(() => {
    if (code) {
      setAuthError(AUTH_ERROR_MESSAGES[code] ?? 'Sign-in failed. Please try again.')
    }
  }, [])

  useEffect(() => {
    if (!contextAuthError) return
    setAuthError(AUTH_ERROR_MESSAGES[contextAuthError] ?? 'Sign-in failed. Please try again.')
    clearAuthError()
  }, [contextAuthError, clearAuthError])

  useEffect(() => {
    if (loading) return
    const exitTimer = setTimeout(() => {
      setContentReady(true)
      setLoaderPhase('exiting')
    }, 400)
    const doneTimer = setTimeout(() => setLoaderPhase('done'), 1000)
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
        className={`relative min-h-screen flex flex-col bg-stone-100 transition-opacity duration-700 ease-out ${
          contentReady ? 'opacity-100' : 'opacity-0'
        }`}
      >
        <WelcomeBlobs />

        <header className="relative px-4 sm:px-8 lg:px-12 py-5 sm:py-7">
          <div className="max-w-5xl mx-auto flex items-center gap-3 text-white">
            <div className="w-11 h-11 sm:w-12 sm:h-12 rounded-[1rem] bg-white/10 backdrop-blur-sm border border-white/15 flex items-center justify-center text-warm-200">
              <CivicBuildingIcon className="w-6 h-6 sm:w-7 sm:h-7" />
            </div>
            <div>
              <h1 className="text-[clamp(1.25rem,3vw,1.5rem)] font-semibold tracking-tight">Urbis</h1>
              <p className="text-sm text-civic-100/85">Citizen civic-issue reporting</p>
            </div>
          </div>
        </header>

        <main className="relative flex-1 px-4 sm:px-8 lg:px-12 pb-10 sm:pb-16">
          <div className="max-w-5xl mx-auto">
            {/* Hero */}
            <section
              ref={heroRef.ref}
              className={`mb-10 sm:mb-14 pt-2 sm:pt-6 welcome-reveal ${heroRef.inView ? 'welcome-reveal-visible' : ''}`}
            >
              <div className="flex flex-col lg:flex-row lg:items-center lg:gap-12 xl:gap-16">
                <div className="text-center lg:text-left flex-1">
                  <span className="welcome-badge inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/10 border border-white/20 text-xs font-medium text-civic-50 mb-5 sm:mb-6 backdrop-blur-sm">
                    <span className="w-1.5 h-1.5 rounded-full bg-warm-400 welcome-badge-pulse" />
                    Civic tech · Powered by Lemma SDK
                  </span>
                  <h2 className="text-[clamp(1.875rem,5vw,3rem)] font-semibold text-white mb-4 leading-[1.15] tracking-tight">
                    Report civic issues.
                    <br />
                    <span className="text-warm-200">Get them fixed.</span>
                  </h2>
                  <p className="text-[clamp(1rem,2.2vw,1.2rem)] text-civic-100/90 max-w-xl mx-auto lg:mx-0 leading-relaxed">
                    Photograph problems, draft complaints with AI, and send them to the right municipal authority —
                    with you in control every step of the way.
                  </p>
                </div>
                <div className="hidden sm:flex justify-center lg:justify-end flex-shrink-0 mt-8 lg:mt-0">
                  <HeroDoodle className="w-44 lg:w-52 xl:w-56 text-white/35 welcome-icon-float" />
                </div>
              </div>
              <div className="flex sm:hidden justify-center mt-6">
                <HeroDoodle className="w-36 text-white/30 welcome-icon-float" />
              </div>
            </section>

            {/* Steps */}
            <section
              ref={stepsRef.ref}
              className={`bg-white/92 backdrop-blur-sm rounded-[1.75rem] sm:rounded-[2rem] shadow-[0_8px_40px_-12px_rgba(12,74,110,0.15)] border border-white/80 p-5 sm:p-8 lg:p-10 mb-6 sm:mb-8 welcome-reveal ${stepsRef.inView ? 'welcome-reveal-visible' : ''}`}
              style={{ transitionDelay: '80ms' }}
            >
              <h3 className="text-[clamp(1.05rem,2.5vw,1.2rem)] font-semibold text-civic-900 mb-1 text-center sm:text-left">
                How Urbis works
              </h3>
              <p className="text-sm text-slate-500 mb-6 sm:mb-8 text-center sm:text-left">
                Five steps from photo to resolution
              </p>

              <ol className="grid grid-cols-1 md:grid-cols-6 gap-3 sm:gap-4">
                {STEPS.map((step, index) => (
                  <StepCard
                    key={step.title}
                    index={index}
                    title={step.title}
                    description={step.description}
                    Icon={STEP_ICONS[index]}
                    animate={stepsRef.inView}
                  />
                ))}
              </ol>
            </section>

            {/* CTA */}
            <section
              ref={ctaRef.ref}
              className={`bg-white rounded-[1.75rem] sm:rounded-[2rem] border border-stone-200/80 shadow-[0_4px_24px_-8px_rgba(12,74,110,0.1)] p-6 sm:p-8 lg:p-10 text-center welcome-reveal ${ctaRef.inView ? 'welcome-reveal-visible' : ''}`}
              style={{ transitionDelay: '160ms' }}
            >
              {devOAuthHint && (
                <div className="mb-6 text-sm text-sky-900 bg-sky-50 border border-sky-200/80 rounded-[1rem] px-4 py-3 text-left">
                  {devOAuthHint}
                </div>
              )}
              {authError && (
                <div className="mb-6 text-sm text-amber-900 bg-amber-50 border border-amber-200/80 rounded-[1rem] px-4 py-3 text-left">
                  {authError}
                </div>
              )}
              <h3 className="text-[clamp(1.15rem,2.8vw,1.35rem)] font-semibold text-civic-900 mb-2">
                {signedIn ? 'Welcome back' : 'Ready to get started?'}
              </h3>
              <p className="text-slate-600 text-[clamp(0.875rem,2vw,0.95rem)] mb-7 sm:mb-8 max-w-md mx-auto leading-relaxed">
                {signedIn
                  ? `Signed in as ${user?.email}. Head to your dashboard to track petitions or report a new issue.`
                  : googleEnabled
                    ? 'Sign in with Google so complaints are sent from your Gmail to the municipal authority.'
                    : 'Continue to the app and report your first civic issue.'}
              </p>

              {signedIn ? (
                <WelcomeButton onClick={() => navigate('/dashboard')}>
                  Go to dashboard
                  <ArrowIcon />
                </WelcomeButton>
              ) : googleEnabled ? (
                <button
                  type="button"
                  onClick={login}
                  className="welcome-btn-secondary inline-flex items-center justify-center gap-3 min-h-[48px] px-7 sm:px-8 py-3.5 rounded-[1.1rem] font-medium text-civic-900"
                >
                  <GoogleIcon />
                  Sign in with Google
                </button>
              ) : (
                <WelcomeButton onClick={() => navigate('/dashboard')}>
                  Get started
                  <ArrowIcon />
                </WelcomeButton>
              )}

              <p className="mt-6 sm:mt-7 text-xs text-slate-400">
                Gappy AI Hackathon · Human-in-the-loop civic reporting
              </p>
            </section>
          </div>
        </main>
      </div>
    </>
  )
}

function StepCard({
  index,
  title,
  description,
  Icon,
  animate,
}: {
  index: number
  title: string
  description: string
  Icon: ComponentType<{ className?: string }>
  animate: boolean
}) {
  const colClass =
    index < 3 ? 'md:col-span-2' : 'md:col-span-3'

  return (
    <li
      className={`welcome-step-card group flex gap-3.5 sm:gap-4 p-4 sm:p-5 rounded-[1.25rem] sm:rounded-[1.35rem] border border-stone-100 bg-stone-50/60 ${colClass} ${
        animate ? 'welcome-step-visible' : ''
      }`}
      style={{ transitionDelay: animate ? `${index * 100}ms` : '0ms' }}
    >
      <div className="shrink-0 w-11 h-11 sm:w-12 sm:h-12 rounded-[1rem] bg-civic-50 border border-civic-100/80 text-civic-700 flex items-center justify-center welcome-icon-float">
        <Icon className="w-5 h-5 sm:w-6 sm:h-6" />
      </div>
      <div className="min-w-0 text-left">
        <span className="text-[10px] sm:text-[11px] font-medium uppercase tracking-wider text-warm-600/90">
          Step {index + 1}
        </span>
        <h4 className="font-semibold text-civic-900 mt-0.5 mb-1 text-[clamp(0.95rem,2vw,1.05rem)]">{title}</h4>
        <p className="text-sm text-slate-600 leading-relaxed">{description}</p>
      </div>
    </li>
  )
}

function WelcomeButton({ children, onClick }: { children: ReactNode; onClick: () => void }) {
  return (
    <button type="button" onClick={onClick} className="welcome-btn-primary group inline-flex items-center justify-center gap-2 min-h-[48px] px-7 sm:px-8 py-3.5 rounded-[1.1rem] font-medium text-white">
      {children}
    </button>
  )
}

function ArrowIcon() {
  return (
    <svg
      className="w-4 h-4 transition-transform duration-500 ease-out group-hover:translate-x-1"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d="M3 8h10M9 4l4 4-4 4" />
    </svg>
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
