import { CivicBuildingIcon } from './welcome/WelcomeIcons'
import { WelcomeBlobs } from './welcome/WelcomeBlobs'

export function WelcomeLoader({ exiting }: { exiting?: boolean }) {
  return (
    <div
      className={`fixed inset-0 z-50 flex flex-col items-center justify-center overflow-hidden bg-civic-900 transition-opacity duration-700 ease-out ${
        exiting ? 'opacity-0 pointer-events-none' : 'opacity-100'
      }`}
      aria-live="polite"
      aria-busy={!exiting}
    >
      <WelcomeBlobs />

      <div className="relative flex flex-col items-center px-6">
        <div className="mb-8 text-warm-300/90 welcome-icon-float">
          <div className="w-16 h-16 rounded-[1.25rem] bg-white/8 backdrop-blur-sm border border-white/15 flex items-center justify-center">
            <CivicBuildingIcon className="w-9 h-9" />
          </div>
        </div>

        <h1 className="text-[clamp(1.75rem,4vw,2rem)] font-semibold text-white tracking-tight mb-2">Urbis</h1>
        <p className="text-civic-100/80 text-sm mb-10">Citizen civic-issue reporting</p>

        <div className="flex items-center gap-2.5" aria-hidden>
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="w-1.5 h-1.5 rounded-full bg-warm-300/60 welcome-dot-soft"
              style={{ animationDelay: `${i * 0.35}s` }}
            />
          ))}
        </div>

        <p className="mt-8 text-xs text-civic-200/60">Preparing your civic workspace…</p>
      </div>
    </div>
  )
}
