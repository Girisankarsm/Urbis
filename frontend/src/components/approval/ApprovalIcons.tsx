const stroke = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.5,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
}

export function TypeTagIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 20 20" aria-hidden>
      <path {...stroke} d="M4 10h12M10 4v12" opacity="0.35" />
      <path {...stroke} d="M6 6l8 8M14 6L6 14" />
    </svg>
  )
}

export function BuildingIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 20 20" aria-hidden>
      <path {...stroke} d="M3 17V7l7-4 7 4v10" />
      <path {...stroke} d="M8 17v-5h4v5" />
      <path {...stroke} d="M7 9h1M12 9h1M7 12h1M12 12h1" />
    </svg>
  )
}

export function SourceIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 20 20" aria-hidden>
      <circle {...stroke} cx="9" cy="9" r="5.5" />
      <path {...stroke} d="M13.5 13.5L17 17" />
    </svg>
  )
}

export function AreaIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 20 20" aria-hidden>
      <path {...stroke} d="M3 8l7-4 7 4v9H3z" />
      <path {...stroke} d="M8 17v-6h4v6" />
    </svg>
  )
}

export function PinIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 20 22" aria-hidden>
      <path {...stroke} d="M10 20s6.5-5.5 6.5-11a6.5 6.5 0 10-13 0c0 5.5 6.5 11 6.5 11z" />
      <circle {...stroke} cx="10" cy="9" r="2" />
    </svg>
  )
}

export function BackArrowIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 20 20" aria-hidden>
      <path {...stroke} d="M12 4l-6 6 6 6" />
    </svg>
  )
}

export function VerifyDotIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 8 8" aria-hidden>
      <circle cx="4" cy="4" r="3" fill="currentColor" />
    </svg>
  )
}
