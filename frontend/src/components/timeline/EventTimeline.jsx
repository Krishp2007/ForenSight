import { useState, useEffect } from 'react'
import { listEvents } from '../../services/eventService'
import Spinner from '../ui/Spinner'
import EmptyState from '../ui/EmptyState'
import { Clock, Filter } from 'lucide-react'
import { formatDateTime, humanize } from '../../utils/formatters'
import { SEVERITY_LEVELS, EVENT_TYPES } from '../../utils/constants'

const SEV_COLORS = {
  critical: { bg: 'rgba(239,68,68,0.2)',   color: '#fca5a5' },
  high:     { bg: 'rgba(249,115,22,0.2)',  color: '#fdba74' },
  medium:   { bg: 'rgba(245,158,11,0.2)',  color: '#fcd34d' },
  low:      { bg: 'rgba(96,165,250,0.2)',  color: '#93c5fd' },
  info:     { bg: 'rgba(107,127,163,0.15)', color: '#9aa8c0' },
}

const SevBadge = ({ severity }) => {
  const s = SEV_COLORS[severity] || SEV_COLORS.info
  return (
    <span style={{
      padding: '2px 7px', borderRadius: '99px',
      fontSize: '10px', fontWeight: '600', textTransform: 'uppercase',
      background: s.bg, color: s.color,
    }}>{severity}</span>
  )
}

const TypeBadge = ({ label }) => (
  <span style={{
    padding: '2px 7px', borderRadius: '6px',
    fontSize: '10px', fontWeight: '500',
    background: 'rgba(74,127,232,0.15)', color: '#93c5fd',
  }}>{label}</span>
)

const selectStyle = {
  background: '#2a3347',
  border: '1px solid #3d4f6a',
  color: '#9aa8c0',
  fontSize: '12px',
  borderRadius: '6px',
  padding: '5px 10px',
  outline: 'none',
  cursor: 'pointer',
  fontFamily: 'inherit',
}

const EventTimeline = ({ caseId }) => {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(false)
  const [severity, setSeverity] = useState('')
  const [eventType, setEventType] = useState('')
  const [limit, setLimit] = useState(100)

  const load = async () => {
    setLoading(true)
    try {
      const data = await listEvents(caseId, {
        severity: severity || undefined,
        event_type: eventType || undefined,
        limit,
      })
      setEvents(data)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [caseId, severity, eventType, limit])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Filters */}
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#9aa8c0', fontSize: '12px' }}>
          <Filter size={13} />
          <span>Filters:</span>
        </div>
        <select value={severity} onChange={e => setSeverity(e.target.value)} style={selectStyle}>
          <option value="">All severities</option>
          {SEVERITY_LEVELS.map(s => <option key={s} value={s}>{humanize(s)}</option>)}
        </select>
        <select value={eventType} onChange={e => setEventType(e.target.value)} style={selectStyle}>
          <option value="">All types</option>
          {EVENT_TYPES.map(t => <option key={t} value={t}>{humanize(t)}</option>)}
        </select>
        <select value={limit} onChange={e => setLimit(Number(e.target.value))} style={selectStyle}>
          {[50, 100, 250, 500, 1000].map(n => <option key={n} value={n}>Limit {n}</option>)}
        </select>
        <span style={{ color: '#6b7fa3', fontSize: '12px', marginLeft: 'auto' }}>{events.length} events</span>
      </div>

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '48px 0' }}><Spinner size="lg" /></div>
      ) : events.length === 0 ? (
        <EmptyState icon={Clock} title="No events found" description="Parse evidence or adjust filters." />
      ) : (
        <div style={{ border: '1px solid #3d4f6a', borderRadius: '12px', overflow: 'hidden' }}>
          {events.map((ev, i) => (
            <div
              key={ev.id}
              style={{
                display: 'flex',
                gap: '16px',
                padding: '12px 16px',
                borderBottom: i < events.length - 1 ? '1px solid #2d3748' : 'none',
                background: ev.is_anomaly ? 'rgba(249,115,22,0.05)' : 'transparent',
                borderLeft: ev.is_anomaly ? '3px solid #f97316' : '3px solid transparent',
                transition: 'background 0.15s',
              }}
              onMouseEnter={e => e.currentTarget.style.background = ev.is_anomaly ? 'rgba(249,115,22,0.1)' : 'rgba(74,127,232,0.05)'}
              onMouseLeave={e => e.currentTarget.style.background = ev.is_anomaly ? 'rgba(249,115,22,0.05)' : 'transparent'}
            >
              {/* Timestamp */}
              <div style={{ flexShrink: 0, width: '140px', color: '#6b7fa3', fontSize: '11px', paddingTop: '2px', fontFamily: 'monospace' }}>
                {formatDateTime(ev.timestamp)}
              </div>

              {/* Content */}
              <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                  <TypeBadge label={humanize(ev.event_type)} />
                  <SevBadge severity={ev.severity} />
                  <span style={{ color: '#4a5568', fontSize: '10px', textTransform: 'uppercase' }}>{ev.source}</span>
                  {ev.is_anomaly && (
                    <span style={{ padding: '2px 7px', borderRadius: '99px', fontSize: '10px', fontWeight: '600', background: 'rgba(249,115,22,0.2)', color: '#fdba74' }}>
                      ⚠ Anomaly
                    </span>
                  )}
                </div>
                <p style={{ margin: 0, fontSize: '13px', color: '#e2e8f0', lineHeight: '1.5' }}>
                  <span style={{ color: '#60a5fa', fontWeight: '500' }}>{ev.subject}</span>
                  <span style={{ color: '#4a5568', margin: '0 6px' }}>→</span>
                  <span style={{ color: '#9aa8c0' }}>{ev.action}</span>
                  <span style={{ color: '#4a5568', margin: '0 6px' }}>→</span>
                  <span style={{ color: '#6ee7b7' }}>{ev.object}</span>
                </p>
                {ev.mitre_techniques?.length > 0 && (
                  <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                    {ev.mitre_techniques.map(t => (
                      <span key={t} style={{
                        fontSize: '10px', fontFamily: 'monospace',
                        background: 'rgba(167,139,250,0.15)', color: '#c4b5fd',
                        padding: '2px 6px', borderRadius: '4px',
                      }}>{t}</span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default EventTimeline
