import { useState, useEffect } from 'react'
import api from '../../services/api'
import { Spinner, EmptyState } from '../ui'
import { Clock, Filter, Search, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, ShieldAlert, ArrowUpDown, Info, Code } from 'lucide-react'
import { formatDateTime, humanize } from '../../utils/formatters'
import { SEVERITY_LEVELS, EVENT_TYPES } from '../../utils/constants'

const listEvents = (caseId, params = {}) => {
  return api.get(`/cases/${caseId}/events`, { params }).then(r => r.data)
}

const SEV_COLORS = {
  critical: { bg: 'rgba(239, 68, 68, 0.15)', color: '#ef4444', border: 'rgba(239, 68, 68, 0.3)' },
  high:     { bg: 'rgba(249, 115, 22, 0.15)', color: '#f97316', border: 'rgba(249, 115, 22, 0.3)' },
  medium:   { bg: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b', border: 'rgba(245, 158, 11, 0.3)' },
  low:      { bg: 'rgba(59, 130, 246, 0.15)', color: '#3b82f6', border: 'rgba(59, 130, 246, 0.3)' },
  info:     { bg: 'rgba(100, 116, 139, 0.15)', color: '#64748b', border: 'rgba(100, 116, 139, 0.3)' },
}

const SevBadge = ({ severity }) => {
  const s = SEV_COLORS[severity?.toLowerCase()] || SEV_COLORS.info
  return (
    <span style={{
      padding: '2px 8px', borderRadius: '6px',
      fontSize: '11px', fontWeight: '700', textTransform: 'uppercase',
      background: s.bg, color: s.color, border: `1px solid ${s.border}`
    }}>
      {severity || 'INFO'}
    </span>
  )
}

const TypeBadge = ({ label }) => (
  <span style={{
    padding: '2px 8px', borderRadius: '6px',
    fontSize: '11px', fontWeight: '600',
    background: 'rgba(37, 99, 235, 0.1)', color: '#2563eb', border: '1px solid rgba(37, 99, 235, 0.25)'
  }}>
    {humanize(label)}
  </span>
)

const selectStyle = {
  background: 'var(--forensic-card-bg, #ffffff)',
  border: '1px solid var(--forensic-border, #cbd5e1)',
  color: 'var(--forensic-text-main, #0f172a)',
  fontSize: '12.5px',
  fontWeight: '600',
  borderRadius: '8px',
  padding: '7px 12px',
  outline: 'none',
  cursor: 'pointer',
  fontFamily: 'inherit',
  transition: 'border-color 0.15s ease',
}

const EventTimeline = ({ caseId }) => {
  const [eventsData, setEventsData] = useState({ events: [], total: 0, page: 1, limit: 50, total_pages: 1 })
  const [loading, setLoading]       = useState(true)
  const [error, setError]           = useState(null)

  // Filters & State
  const [search, setSearch]         = useState('')
  const [severity, setSeverity]     = useState('')
  const [eventType, setEventType]   = useState('')
  const [onlyAnomalies, setOnlyAnomalies] = useState(false)
  const [sortOrder, setSortOrder]   = useState('desc')
  const [page, setPage]             = useState(1)
  const [limit, setLimit]           = useState(50)
  const [expandedEventId, setExpandedEventId] = useState(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = {
        page,
        limit,
        sort_order: sortOrder,
      }
      if (severity) params.severity = severity
      if (eventType) params.event_type = eventType
      if (search.trim()) params.search = search.trim()
      if (onlyAnomalies) params.is_anomaly = true

      const res = await listEvents(caseId, params)

      if (Array.isArray(res)) {
        // Fallback for array response
        setEventsData({ events: res, total: res.length, page: 1, limit: res.length, total_pages: 1 })
      } else {
        setEventsData({
          events: res.events || [],
          total: res.total || 0,
          page: res.page || 1,
          limit: res.limit || limit,
          total_pages: res.total_pages || 1,
        })
      }
    } catch (e) {
      console.error('[EventTimeline] Fetch error:', e)
      setError(e.response?.data?.detail || e.message || 'Failed to load forensic events timeline.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [caseId, severity, eventType, search, onlyAnomalies, sortOrder, page, limit])

  const handleSearchChange = (e) => {
    setSearch(e.target.value)
    setPage(1)
  }

  const { events, total, total_pages } = eventsData
  const startItem = total === 0 ? 0 : (page - 1) * limit + 1
  const endItem   = Math.min(page * limit, total)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', fontFamily: 'inherit' }}>

      {/* Control Bar: Search & Filters */}
      <div style={{
        background: 'var(--forensic-card-bg, #ffffff)',
        border: '1px solid var(--forensic-border, #e2e8f0)',
        borderRadius: '16px',
        padding: '16px 20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.03)'
      }}>

        {/* Top Row: Search Input & Quick Controls */}
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{
            flex: 1, minWidth: '240px', position: 'relative', display: 'flex', alignItems: 'center'
          }}>
            <Search size={15} style={{ position: 'absolute', left: '12px', color: 'var(--forensic-text-muted, #64748b)' }} />
            <input
              type="text"
              placeholder="Search timeline (Subject, Process, Action, Command line, MITRE ID)..."
              value={search}
              onChange={handleSearchChange}
              style={{
                width: '100%',
                padding: '9px 12px 9px 36px',
                borderRadius: '10px',
                border: '1px solid var(--forensic-border, #cbd5e1)',
                background: 'var(--forensic-panel-bg, #f8fafc)',
                color: 'var(--forensic-text-main, #0f172a)',
                fontSize: '13px',
                outline: 'none',
                fontFamily: 'inherit'
              }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            {/* Anomaly Only Toggle */}
            <button
              onClick={() => { setOnlyAnomalies(!onlyAnomalies); setPage(1); }}
              style={{
                display: 'flex', alignItems: 'center', gap: '6px',
                padding: '8px 12px', borderRadius: '8px',
                fontSize: '12.5px', fontWeight: '700', cursor: 'pointer', fontFamily: 'inherit',
                background: onlyAnomalies ? 'rgba(249, 115, 22, 0.12)' : 'var(--forensic-panel-bg, #f8fafc)',
                color: onlyAnomalies ? '#f97316' : 'var(--forensic-text-muted, #64748b)',
                border: `1px solid ${onlyAnomalies ? 'rgba(249, 115, 22, 0.3)' : 'var(--forensic-border, #cbd5e1)'}`,
                transition: 'all 0.15s ease'
              }}
            >
              <ShieldAlert size={14} />
              {onlyAnomalies ? 'Anomalies Only' : 'Show All'}
            </button>

            {/* Sort Toggle */}
            <button
              onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
              style={{
                display: 'flex', alignItems: 'center', gap: '6px',
                padding: '8px 12px', borderRadius: '8px',
                fontSize: '12.5px', fontWeight: '600', cursor: 'pointer', fontFamily: 'inherit',
                background: 'var(--forensic-panel-bg, #f8fafc)',
                color: 'var(--forensic-text-main, #0f172a)',
                border: '1px solid var(--forensic-border, #cbd5e1)'
              }}
            >
              <ArrowUpDown size={14} />
              {sortOrder === 'desc' ? 'Newest First' : 'Oldest First'}
            </button>
          </div>
        </div>

        {/* Second Row: Dropdown Filters & Page Size */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', borderTop: '1px solid var(--forensic-border, #f1f5f9)', paddingTop: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: 'var(--forensic-text-muted, #64748b)', fontSize: '12px', fontWeight: '600' }}>
              <Filter size={13} />
              <span>Filters:</span>
            </div>

            <select value={severity} onChange={e => { setSeverity(e.target.value); setPage(1); }} style={selectStyle}>
              <option value="">All Severities</option>
              {SEVERITY_LEVELS.map(s => <option key={s} value={s}>{humanize(s)}</option>)}
            </select>

            <select value={eventType} onChange={e => { setEventType(e.target.value); setPage(1); }} style={selectStyle}>
              <option value="">All Event Types</option>
              {EVENT_TYPES.map(t => <option key={t} value={t}>{humanize(t)}</option>)}
            </select>

            <select value={limit} onChange={e => { setLimit(Number(e.target.value)); setPage(1); }} style={selectStyle}>
              <option value={25}>25 per page</option>
              <option value={50}>50 per page</option>
              <option value={100}>100 per page</option>
              <option value={250}>250 per page</option>
            </select>
          </div>

          <div style={{ color: 'var(--forensic-text-muted, #64748b)', fontSize: '12.5px', fontWeight: '600' }}>
            Showing <strong style={{ color: 'var(--forensic-text-main, #0f172a)' }}>{startItem}–{endItem}</strong> of <strong style={{ color: 'var(--forensic-primary, #2563eb)' }}>{total.toLocaleString()}</strong> events
          </div>
        </div>
      </div>

      {error && (
        <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.35)', borderRadius: '10px', padding: '12px 16px', color: '#dc2626', fontSize: '13px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>⚠ {error}</span>
          <button onClick={load} style={{ background: 'var(--forensic-primary, #2563eb)', border: 'none', color: '#fff', padding: '6px 12px', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', fontWeight: '600' }}>Retry</button>
        </div>
      )}

      {/* Main Events List */}
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '48px 0' }}><Spinner size="lg" /></div>
      ) : events.length === 0 ? (
        <EmptyState icon={Clock} title="No forensic events found" description="No logs match your active filters or search query." />
      ) : (
        <div style={{ border: '1px solid var(--forensic-border, #e2e8f0)', borderRadius: '16px', overflow: 'hidden', background: 'var(--forensic-card-bg, #ffffff)', boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)' }}>
          {events.map((ev, i) => {
            const isExpanded = expandedEventId === ev.id
            return (
              <div
                key={ev.id || i}
                style={{
                  borderBottom: i < events.length - 1 ? '1px solid var(--forensic-border, #f1f5f9)' : 'none',
                  background: ev.is_anomaly ? 'rgba(249, 115, 22, 0.04)' : 'transparent',
                  borderLeft: ev.is_anomaly ? '4px solid #f97316' : '4px solid transparent',
                  transition: 'background 0.15s ease'
                }}
              >
                {/* Event Summary Row */}
                <div
                  onClick={() => setExpandedEventId(isExpanded ? null : ev.id)}
                  style={{
                    display: 'flex',
                    gap: '16px',
                    padding: '16px 22px',
                    cursor: 'pointer',
                    alignItems: 'flex-start'
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--forensic-panel-bg, #f8fafc)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  {/* Timestamp */}
                  <div style={{ flexShrink: 0, width: '140px', color: 'var(--forensic-text-muted, #64748b)', fontSize: '12px', fontFamily: 'monospace', fontWeight: '600' }}>
                    {formatDateTime(ev.timestamp)}
                  </div>

                  {/* Main Event Content */}
                  <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: '6px', paddingRight: '12px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                      <TypeBadge label={ev.event_type} />
                      <SevBadge severity={ev.severity} />
                      <span style={{ color: 'var(--forensic-text-muted, #64748b)', fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', background: 'var(--forensic-panel-bg, #f1f5f9)', padding: '2px 6px', borderRadius: '4px' }}>
                        {ev.source}
                      </span>
                      {ev.is_anomaly && (
                        <span style={{ padding: '2px 8px', borderRadius: '6px', fontSize: '11px', fontWeight: '700', background: 'rgba(249, 115, 22, 0.15)', color: '#f97316', border: '1px solid rgba(249, 115, 22, 0.3)' }}>
                          ⚠ Anomaly ({Math.round((ev.anomaly_score || 0.8) * 100)}%)
                        </span>
                      )}
                    </div>

                    <p style={{ margin: 0, fontSize: '13.5px', color: 'var(--forensic-text-main, #0f172a)', lineHeight: '1.5', fontWeight: '500', wordBreak: 'break-word' }}>
                      <span style={{ color: '#2563eb', fontWeight: '700', fontFamily: 'monospace', wordBreak: 'break-all' }}>{ev.subject}</span>
                      <span style={{ color: 'var(--forensic-text-muted, #94a3b8)', margin: '0 8px', fontWeight: 'bold' }}>➔</span>
                      <span style={{ color: 'var(--forensic-text-main, #334155)', fontWeight: '600' }}>{ev.action}</span>
                      <span style={{ color: 'var(--forensic-text-muted, #94a3b8)', margin: '0 8px', fontWeight: 'bold' }}>➔</span>
                      <span style={{ color: '#059669', fontWeight: '700', fontFamily: 'monospace', wordBreak: 'break-all' }}>{ev.object}</span>
                    </p>

                    {ev.description && (
                      <p style={{ margin: '2px 0 0 0', fontSize: '12.5px', color: 'var(--forensic-text-muted, #475569)', fontWeight: '500', lineHeight: '1.4', wordBreak: 'break-word' }}>
                        💡 {ev.description}
                      </p>
                    )}

                    {ev.mitre_techniques?.length > 0 && (
                      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '2px' }}>
                        {ev.mitre_techniques.map(t => (
                          <span key={t} style={{
                            fontSize: '11px', fontFamily: 'monospace', fontWeight: '700',
                            background: 'rgba(168, 85, 247, 0.12)', color: '#a855f7', border: '1px solid rgba(168, 85, 247, 0.3)',
                            padding: '2px 7px', borderRadius: '6px',
                          }}>{t}</span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Expand Code Icon */}
                  <div style={{ color: 'var(--forensic-text-muted, #94a3b8)', paddingTop: '2px' }}>
                    <Code size={16} />
                  </div>
                </div>

                {/* Expanded Raw JSON / Details Drawer */}
                {isExpanded && (
                  <div style={{
                    padding: '14px 18px',
                    background: 'var(--forensic-panel-bg, #0f172a)',
                    color: '#e2e8f0',
                    borderTop: '1px solid var(--forensic-border, #1e293b)',
                    fontFamily: 'monospace',
                    fontSize: '12px'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <span style={{ color: '#94a3b8', fontWeight: 'bold', textTransform: 'uppercase', fontSize: '11px' }}>Raw Parser Event Metadata:</span>
                      <span style={{ color: '#64748b', fontSize: '11px' }}>Event ID: {ev.id}</span>
                    </div>
                    <pre style={{ margin: 0, overflowX: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-all', color: '#38bdf8' }}>
                      {JSON.stringify(ev.details || ev, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Pagination Navigation Bar */}
      {total_pages > 1 && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justify: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
          padding: '12px 18px',
          background: 'var(--forensic-card-bg, #ffffff)',
          border: '1px solid var(--forensic-border, #e2e8f0)',
          borderRadius: '16px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.03)'
        }}>
          <div style={{ fontSize: '12.5px', color: 'var(--forensic-text-muted, #64748b)', fontWeight: '600' }}>
            Page <strong style={{ color: 'var(--forensic-text-main, #0f172a)' }}>{page}</strong> of <strong style={{ color: 'var(--forensic-text-main, #0f172a)' }}>{total_pages}</strong>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <button
              onClick={() => setPage(1)}
              disabled={page === 1 || loading}
              style={{
                padding: '6px 10px', borderRadius: '8px', border: '1px solid var(--forensic-border, #cbd5e1)',
                background: 'var(--forensic-panel-bg, #f8fafc)', color: 'var(--forensic-text-main, #0f172a)',
                cursor: page === 1 || loading ? 'not-allowed' : 'pointer', opacity: page === 1 || loading ? 0.4 : 1,
                display: 'flex', alignItems: 'center'
              }}
            >
              <ChevronsLeft size={16} />
            </button>

            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1 || loading}
              style={{
                padding: '6px 12px', borderRadius: '8px', border: '1px solid var(--forensic-border, #cbd5e1)',
                background: 'var(--forensic-panel-bg, #f8fafc)', color: 'var(--forensic-text-main, #0f172a)',
                cursor: page === 1 || loading ? 'not-allowed' : 'pointer', opacity: page === 1 || loading ? 0.4 : 1,
                display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12.5px', fontWeight: '600'
              }}
            >
              <ChevronLeft size={16} /> Previous
            </button>

            <span style={{ padding: '0 8px', fontSize: '13px', fontWeight: '700', color: 'var(--forensic-primary, #2563eb)' }}>
              {page}
            </span>

            <button
              onClick={() => setPage(p => Math.min(total_pages, p + 1))}
              disabled={page === total_pages || loading}
              style={{
                padding: '6px 12px', borderRadius: '8px', border: '1px solid var(--forensic-border, #cbd5e1)',
                background: 'var(--forensic-panel-bg, #f8fafc)', color: 'var(--forensic-text-main, #0f172a)',
                cursor: page === total_pages || loading ? 'not-allowed' : 'pointer', opacity: page === total_pages || loading ? 0.4 : 1,
                display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12.5px', fontWeight: '600'
              }}
            >
              Next <ChevronRight size={16} />
            </button>

            <button
              onClick={() => setPage(total_pages)}
              disabled={page === total_pages || loading}
              style={{
                padding: '6px 10px', borderRadius: '8px', border: '1px solid var(--forensic-border, #cbd5e1)',
                background: 'var(--forensic-panel-bg, #f8fafc)', color: 'var(--forensic-text-main, #0f172a)',
                cursor: page === total_pages || loading ? 'not-allowed' : 'pointer', opacity: page === total_pages || loading ? 0.4 : 1,
                display: 'flex', alignItems: 'center'
              }}
            >
              <ChevronsRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default EventTimeline
