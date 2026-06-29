import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'

import type { PetitionStatus } from '../../types'

type FilterOption = { label: string; value: PetitionStatus | '' }

export function DashboardFilterTabs({
  filters,
  value,
  onChange,
}: {
  filters: FilterOption[]
  value: PetitionStatus | ''
  onChange: (value: PetitionStatus | '') => void
}) {
  const containerRef = useRef<HTMLDivElement>(null)
  const tabRefs = useRef<Map<string, HTMLButtonElement>>(new Map())
  const [pill, setPill] = useState({ left: 0, width: 0, ready: false })

  const tabKey = (v: PetitionStatus | '') => v || '__all__'

  const updatePill = useCallback(() => {
    const container = containerRef.current
    const tab = tabRefs.current.get(tabKey(value))
    if (!container || !tab) return
    const cRect = container.getBoundingClientRect()
    const tRect = tab.getBoundingClientRect()
    setPill({
      left: tRect.left - cRect.left + container.scrollLeft,
      width: tRect.width,
      ready: true,
    })
  }, [value])

  useLayoutEffect(() => {
    updatePill()
  }, [updatePill, value])

  useEffect(() => {
    const container = containerRef.current
    if (!container) return
    const onScroll = () => updatePill()
    window.addEventListener('resize', updatePill)
    container.addEventListener('scroll', onScroll, { passive: true })
    return () => {
      window.removeEventListener('resize', updatePill)
      container.removeEventListener('scroll', onScroll)
    }
  }, [updatePill])

  return (
    <div className="dashboard-tabs-wrap relative mb-[clamp(1.25rem,3vw,1.75rem)] max-w-full overflow-hidden">
      <div className="dashboard-tabs-fade dashboard-tabs-fade-left pointer-events-none" aria-hidden />
      <div className="dashboard-tabs-fade dashboard-tabs-fade-right pointer-events-none" aria-hidden />

      <div
        ref={containerRef}
        className="dashboard-tabs-scroll relative flex gap-2 sm:gap-2.5 overflow-x-auto pb-1 scrollbar-none max-w-full"
        role="tablist"
        aria-label="Filter petitions by status"
      >
        <span
          className="dashboard-tab-pill"
          style={{
            transform: `translateX(${pill.left}px)`,
            width: pill.width,
            opacity: pill.ready ? 1 : 0,
          }}
          aria-hidden
        />
        {filters.map((f) => {
          const active = value === f.value
          const key = tabKey(f.value)
          return (
            <button
              key={f.label}
              ref={(el) => {
                if (el) tabRefs.current.set(key, el)
                else tabRefs.current.delete(key)
              }}
              type="button"
              role="tab"
              aria-selected={active}
              onClick={() => onChange(f.value)}
              className={`dashboard-tab relative z-10 shrink-0 px-4 py-2 min-h-[44px] rounded-[1rem] text-sm font-medium transition-colors duration-200 ease-out ${
                active ? 'text-white' : 'text-slate-600 hover:text-civic-700'
              }`}
            >
              {f.label}
            </button>
          )
        })}
      </div>
    </div>
  )
}
