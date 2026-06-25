const stroke = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.5,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
}

export function CameraDoodleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 48 40" aria-hidden>
      <path {...stroke} d="M6 14h8l3-5h14l3 5h8v18H6z" />
      <circle {...stroke} cx="24" cy="23" r="7" />
      <circle {...stroke} cx="35" cy="17" r="1.5" fill="currentColor" />
      <path {...stroke} d="M4 32h40" opacity="0.25" />
    </svg>
  )
}

export function LocationPinIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 20 24" aria-hidden>
      <path {...stroke} d="M10 22s7-6.2 7-12a7 7 0 10-14 0c0 5.8 7 12 7 12z" />
      <circle {...stroke} cx="10" cy="10" r="2.5" />
    </svg>
  )
}
