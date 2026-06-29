import { useEffect, useState } from 'react'

import { fetchLemmaHealth } from '../api/client'

export function LemmaStatusDot() {
  const [live, setLive] = useState(false)
  const [path, setPath] = useState<'lemma' | 'fallback'>('fallback')
  const [title, setTitle] = useState('Checking Lemma pod…')

  useEffect(() => {
    let cancelled = false
    const load = () => {
      fetchLemmaHealth()
        .then((data) => {
          if (cancelled) return
          const isLive = Boolean(data.live ?? (data.token_valid && data.api_reachable))
          setLive(isLive)
          setPath(data.active_path === 'lemma' ? 'lemma' : 'fallback')
          setTitle(
            isLive
              ? `Lemma pod live${data.active_path === 'lemma' ? ' — processing via agents' : ' — standby'}`
              : `Lemma fallback mode${data.reason ? `: ${data.reason}` : ''}`,
          )
        })
        .catch(() => {
          if (!cancelled) {
            setLive(false)
            setPath('fallback')
            setTitle('Lemma fallback mode — pod unreachable')
          }
        })
    }
    load()
    const timer = window.setInterval(load, 60_000)
    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [])

  return (
    <span
      className="lemma-status"
      title={title}
      aria-label={title}
    >
      <span className={`lemma-status-dot ${live ? 'lemma-status-dot--live' : 'lemma-status-dot--fallback'}`} />
      <span className="lemma-status-label hidden sm:inline">
        {live ? (path === 'lemma' ? 'Lemma' : 'Lemma ready') : 'Fallback'}
      </span>
    </span>
  )
}
