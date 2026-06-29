import { useState } from 'react'

import type { ActivityEvent } from '../types'

type DotTone = 'neutral' | 'pending' | 'completed' | 'failed'

type TimelineItem = {
  id: string
  title: string
  subtitle: string
  tone: DotTone
  timestamp?: string
  detail?: string
}

export function ComplaintTimeline({ events }: { events: ActivityEvent[] }) {
  const items = events.map(toTimelineItem).filter((item) => item.title)

  if (items.length === 0) {
    return <p className="complaint-timeline-empty">No activity yet.</p>
  }

  return (
    <ul className="complaint-timeline" aria-label="Complaint timeline">
      {items.map((item, index) => (
        <TimelineRow key={item.id} item={item} isLast={index === items.length - 1} />
      ))}
    </ul>
  )
}

function TimelineRow({ item, isLast }: { item: TimelineItem; isLast: boolean }) {
  const [open, setOpen] = useState(false)
  const hasDetail = Boolean(item.detail?.trim())

  return (
    <li className="complaint-timeline-item">
      <div className="complaint-timeline-rail" aria-hidden>
        <span className={`complaint-timeline-dot complaint-timeline-dot--${item.tone}`} />
        {!isLast && <span className="complaint-timeline-line" />}
      </div>

      <div className="complaint-timeline-body">
        <div className="complaint-timeline-row">
          <button
            type="button"
            className={`complaint-timeline-content ${hasDetail ? 'complaint-timeline-content--expandable' : ''}`}
            onClick={() => hasDetail && setOpen((v) => !v)}
            disabled={!hasDetail}
            aria-expanded={hasDetail ? open : undefined}
          >
            <span className="complaint-timeline-title">{item.title}</span>
            <span className="complaint-timeline-subtitle">{item.subtitle}</span>
          </button>
          {item.timestamp && (
            <time className="complaint-timeline-time" dateTime={item.timestamp}>
              {formatTime(item.timestamp)}
            </time>
          )}
        </div>
        {open && hasDetail && <p className="complaint-timeline-detail">{item.detail}</p>}
      </div>
    </li>
  )
}

function toTimelineItem(event: ActivityEvent): TimelineItem {
  const meta = event.metadata ?? {}
  const message = event.message?.trim() ?? ''

  switch (event.event_type) {
    case 'created':
      return {
        id: event.id,
        title: 'Created',
        subtitle: shortLine(extractArea(message) || 'New report'),
        tone: 'neutral',
        timestamp: event.timestamp,
        detail: message,
      }
    case 'vision_classified':
      return {
        id: event.id,
        title: 'Classified',
        subtitle: shortLine(String(meta.issue_type || extractAfterColon(message) || 'Photo analyzed')),
        tone: 'neutral',
        timestamp: event.timestamp,
        detail: message,
      }
    case 'classified':
      return {
        id: event.id,
        title: 'Routed',
        subtitle: shortLine(String(meta.department || extractDepartment(message) || 'Authority lookup')),
        tone: 'neutral',
        timestamp: event.timestamp,
        detail: message,
      }
    case 'drafted':
      return {
        id: event.id,
        title: 'Drafted',
        subtitle: shortLine(extractDraftTarget(message) || String(meta.department || 'Complaint email')),
        tone: 'neutral',
        timestamp: event.timestamp,
        detail: message,
      }
    case 'approval_pending':
    case 'escalation_pending':
      return {
        id: event.id,
        title: 'Pending approval',
        subtitle: shortLine(event.event_type === 'escalation_pending' ? 'Escalation draft' : 'Your review'),
        tone: 'pending',
        timestamp: event.timestamp,
        detail: message,
      }
    case 'email_sent':
    case 'escalation_sent':
      return {
        id: event.id,
        title: 'Sent',
        subtitle: shortLine(
          String(meta.intended_to || meta.to || extractEmailTarget(message) || 'Authority inbox'),
        ),
        tone: 'completed',
        timestamp: event.timestamp,
        detail: message,
      }
    case 'contact_filed':
      return {
        id: event.id,
        title: 'Filed',
        subtitle: shortLine(String(meta.value || extractAfterColon(message) || 'Official channel')),
        tone: 'completed',
        timestamp: event.timestamp,
        detail: message,
      }
    case 'follow_up_uploaded':
      return {
        id: event.id,
        title: 'Follow-up',
        subtitle: 'New photo added',
        tone: 'neutral',
        timestamp: event.timestamp,
        detail: message,
      }
    case 'resolution_checked': {
      const resolved = meta.resolved === true || String(meta.recommended_status) === 'resolved'
      return {
        id: event.id,
        title: resolved ? 'Resolved' : 'Checked',
        subtitle: shortLine(resolved ? 'Issue likely fixed' : 'Still under review'),
        tone: resolved ? 'completed' : 'neutral',
        timestamp: event.timestamp,
        detail: message,
      }
    }
    case 'status_changed': {
      const rejected = /reject/i.test(message)
      return {
        id: event.id,
        title: rejected ? 'Rejected' : 'Updated',
        subtitle: shortLine(rejected ? 'Send cancelled' : 'Status changed'),
        tone: rejected ? 'failed' : 'neutral',
        timestamp: event.timestamp,
        detail: message,
      }
    }
    default:
      return {
        id: event.id,
        title: titleCase(event.event_type),
        subtitle: shortLine(extractAfterColon(message) || '—'),
        tone: 'neutral',
        timestamp: event.timestamp,
        detail: message,
      }
  }
}

function shortLine(text: string, maxWords = 6): string {
  const cleaned = text.replace(/\s+/g, ' ').trim()
  if (!cleaned) return '—'
  const words = cleaned.split(' ')
  if (words.length <= maxWords) return cleaned
  return `${words.slice(0, maxWords).join(' ')}…`
}

function formatTime(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

function titleCase(eventType: string): string {
  return eventType.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

function extractArea(message: string): string {
  const match = message.match(/area:\s*(.+)$/i)
  return match?.[1]?.trim() ?? ''
}

function extractAfterColon(message: string): string {
  const idx = message.indexOf(':')
  if (idx === -1) return message
  return message.slice(idx + 1).trim()
}

function extractDepartment(message: string): string {
  const bracket = message.match(/^\[[^\]]+\]\s*(.+)$/i)
  if (bracket) return bracket[1].split('.')[0]?.trim() ?? ''
  return message.split('.')[0]?.trim() ?? ''
}

function extractDraftTarget(message: string): string {
  const match = message.match(/drafted for\s+([^(]+)/i)
  return match?.[1]?.trim() ?? ''
}

function extractEmailTarget(message: string): string {
  const match = message.match(/to\s+(\S+@\S+)/i)
  return match?.[1]?.trim() ?? ''
}
