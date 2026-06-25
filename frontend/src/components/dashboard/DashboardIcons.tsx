const stroke = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.5,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
}

/** Friendly empty-state doodle: skyline + person noting a pothole */
export function DashboardEmptyDoodle({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 240 140" aria-hidden>
      {/* skyline */}
      <path {...stroke} d="M20 95h28v-32h12v32h16V72h14v23h20V58h18v37h14V80h12v15" opacity="0.5" />
      <path {...stroke} d="M16 95h208" opacity="0.3" />
      {/* pothole */}
      <ellipse {...stroke} cx="118" cy="108" rx="22" ry="7" />
      <path {...stroke} d="M104 104c6-5 14-4 20 0s12 2 16-2" opacity="0.45" />
      {/* person */}
      <circle {...stroke} cx="72" cy="62" r="6" />
      <path {...stroke} d="M72 68v18M72 76h-10M72 76h12M72 86v8" />
      <path {...stroke} d="M84 72l28 18" opacity="0.7" />
      {/* small note pad */}
      <rect {...stroke} x="58" y="78" width="12" height="14" rx="2" opacity="0.4" />
    </svg>
  )
}
