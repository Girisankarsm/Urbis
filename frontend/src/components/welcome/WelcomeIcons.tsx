const stroke = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.6,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
}

export function CivicBuildingIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 32 32" aria-hidden>
      <path {...stroke} d="M6 26V14l10-6 10 6v12" />
      <path {...stroke} d="M11 26v-8h4v8M17 26v-6h4v6" />
      <path {...stroke} d="M4 26h24" />
      <path {...stroke} d="M13 10h1.5M17.5 10h1.5" />
    </svg>
  )
}

export function HeroDoodle({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 200 160" aria-hidden>
      {/* pothole */}
      <ellipse {...stroke} cx="52" cy="118" rx="28" ry="10" opacity="0.7" />
      <path {...stroke} d="M38 112c4-6 12-8 18-4s10 2 14-2" opacity="0.5" />
      {/* streetlight */}
      <path {...stroke} d="M128 130V52" />
      <path {...stroke} d="M118 52h22c2 0 3 1 3 3v4c0 2-1 3-3 3h-22" />
      <path {...stroke} d="M131 68c-8 2-12 8-10 16" opacity="0.6" />
      <circle {...stroke} cx="131" cy="44" r="3" fill="currentColor" fillOpacity="0.15" />
      {/* trash bin sketch */}
      <path {...stroke} d="M72 98h16l-2 24H74l-2-24z" />
      <path {...stroke} d="M68 98h24M70 90h16" />
      <path {...stroke} d="M76 106v10M84 106v10" opacity="0.5" />
      {/* ground line */}
      <path {...stroke} d="M20 130h160" opacity="0.35" />
    </svg>
  )
}

export function StepCameraIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 32 32" aria-hidden>
      <path {...stroke} d="M6 10h5l2-3h8l2 3h5v14H6z" />
      <circle {...stroke} cx="16" cy="17" r="5" />
      <circle {...stroke} cx="24" cy="13" r="1" fill="currentColor" />
    </svg>
  )
}

export function StepAiIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 32 32" aria-hidden>
      <path {...stroke} d="M16 6c-4 4-6 8-6 12a6 6 0 1012 0c0-4-2-8-6-12z" />
      <path {...stroke} d="M12 20h8M14 23h4" opacity="0.6" />
    </svg>
  )
}

export function StepApproveIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 32 32" aria-hidden>
      <path {...stroke} d="M8 17l5 5 12-13" />
      <rect {...stroke} x="5" y="5" width="22" height="22" rx="4" opacity="0.4" />
    </svg>
  )
}

export function StepEmailIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 32 32" aria-hidden>
      <path {...stroke} d="M5 9h22v14H5z" />
      <path {...stroke} d="M5 11l11 8 11-8" />
    </svg>
  )
}

export function StepTrackIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 32 32" aria-hidden>
      <path {...stroke} d="M6 24V14M12 24V10M18 24V16M24 24V8" />
      <path {...stroke} d="M4 26h24" opacity="0.35" />
    </svg>
  )
}

export const STEP_ICONS = [StepCameraIcon, StepAiIcon, StepApproveIcon, StepEmailIcon, StepTrackIcon] as const
