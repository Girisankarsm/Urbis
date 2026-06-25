export function WelcomeLoader({ exiting }: { exiting?: boolean }) {
  return (
    <div
      className={`fixed inset-0 z-50 flex flex-col items-center justify-center overflow-hidden bg-gradient-to-br from-civic-900 via-civic-800 to-civic-900 transition-opacity duration-500 ${
        exiting ? 'opacity-0 pointer-events-none' : 'opacity-100'
      }`}
      aria-live="polite"
      aria-busy={!exiting}
    >
      {/* Ambient background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-24 -left-24 w-96 h-96 rounded-full bg-civic-500/10 blur-3xl animate-welcome-fade-in" />
        <div className="absolute -bottom-32 -right-16 w-80 h-80 rounded-full bg-sky-400/10 blur-3xl animate-welcome-fade-in" style={{ animationDelay: '0.2s' }} />
        <div
          className="absolute inset-0 opacity-[0.04]"
          style={{
            backgroundImage: 'radial-gradient(circle at 1px 1px, white 1px, transparent 0)',
            backgroundSize: '32px 32px',
          }}
        />
      </div>

      <div className="relative flex flex-col items-center">
        {/* Logo ring animation */}
        <div className="relative w-28 h-28 mb-8">
          <span className="absolute inset-0 rounded-full border-2 border-civic-400/30 animate-welcome-pulse-ring" />
          <span
            className="absolute inset-0 rounded-full border-2 border-civic-400/20 animate-welcome-pulse-ring"
            style={{ animationDelay: '0.6s' }}
          />
          <div className="absolute inset-2 rounded-full border border-dashed border-white/20 animate-welcome-spin-slow" />
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-20 h-20 rounded-2xl bg-white/10 backdrop-blur-sm border border-white/20 shadow-2xl flex items-center justify-center text-4xl">
              🏛️
            </div>
          </div>
        </div>

        {/* Brand */}
        <h1 className="text-3xl font-bold text-white tracking-tight mb-2 animate-welcome-fade-up">Urbis</h1>
        <p className="text-civic-100 text-sm mb-8 animate-welcome-fade-up" style={{ animationDelay: '0.1s' }}>
          Citizen civic-issue reporting
        </p>

        {/* Progress bar */}
        <div className="w-48 h-1.5 rounded-full bg-white/10 overflow-hidden mb-6 animate-welcome-fade-up" style={{ animationDelay: '0.2s' }}>
          <div className="h-full w-1/3 rounded-full bg-gradient-to-r from-transparent via-civic-400 to-transparent animate-welcome-shimmer" />
        </div>

        {/* Bouncing dots */}
        <div className="flex items-center gap-2 animate-welcome-fade-up" style={{ animationDelay: '0.3s' }}>
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="w-2 h-2 rounded-full bg-civic-300 animate-welcome-dot-bounce"
              style={{ animationDelay: `${i * 0.16}s` }}
            />
          ))}
        </div>

        <p className="mt-6 text-xs text-civic-200/70 animate-welcome-fade-up" style={{ animationDelay: '0.4s' }}>
          Preparing your civic workspace…
        </p>
      </div>
    </div>
  )
}
