import { useState, useEffect } from 'react'
import { listEvents } from '../../services/eventService'
import Badge from '../ui/Badge'
import Spinner from '../ui/Spinner'
import EmptyState from '../ui/EmptyState'
import { Clock, Filter } from 'lucide-react'
import { formatDateTime, severityColor, humanize } from '../../utils/formatters'
import { SEVERITY_LEVELS, EVENT_TYPES } from '../../utils/constants'

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
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [caseId, severity, eventType, limit])

  const selectCls = 'bg-gray-700 border border-gray-600 text-gray-200 text-xs rounded-lg px-2 py-1.5 focus:outline-none focus:border-blue-500'

  return (
    <div className="flex flex-col gap-4">
      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-1.5 text-gray-400 text-xs">
          <Filter size={13} />
          <span>Filters:</span>
        </div>
        <select value={severity} onChange={(e) => setSeverity(e.target.value)} className={selectCls}>
          <option value="">All severities</option>
          {SEVERITY_LEVELS.map((s) => <option key={s} value={s}>{humanize(s)}</option>)}
        </select>
        <select value={eventType} onChange={(e) => setEventType(e.target.value)} className={selectCls}>
          <option value="">All types</option>
          {EVENT_TYPES.map((t) => <option key={t} value={t}>{humanize(t)}</option>)}
        </select>
        <select value={limit} onChange={(e) => setLimit(Number(e.target.value))} className={selectCls}>
          {[50, 100, 250, 500, 1000].map((n) => <option key={n} value={n}>Limit {n}</option>)}
        </select>
        <span className="text-gray-500 text-xs ml-auto">{events.length} events</span>
      </div>

      {/* Timeline list */}
      {loading ? (
        <div className="flex justify-center py-12"><Spinner size="lg" /></div>
      ) : events.length === 0 ? (
        <EmptyState icon={Clock} title="No events found" description="Parse evidence or adjust filters." />
      ) : (
        <div className="flex flex-col gap-0 border border-gray-700 rounded-xl overflow-hidden">
          {events.map((ev, i) => (
            <div
              key={ev.id}
              className={`flex gap-4 px-4 py-3 border-b border-gray-700 last:border-0 hover:bg-gray-700/40 transition-colors ${ev.is_anomaly ? 'border-l-2 border-l-orange-500' : ''}`}
            >
              {/* Time column */}
              <div className="shrink-0 w-36 text-gray-500 text-xs pt-0.5">
                {formatDateTime(ev.timestamp)}
              </div>

              {/* Content */}
              <div className="flex flex-col gap-1 flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <Badge label={humanize(ev.event_type)} colorClass="bg-gray-600 text-gray-200" />
                  <Badge label={ev.severity} colorClass={severityColor(ev.severity)} />
                  <span className="text-xs text-gray-500 uppercase">{ev.source}</span>
                  {ev.is_anomaly && (
                    <Badge label="Anomaly" colorClass="bg-orange-500 text-white" />
                  )}
                </div>
                <p className="text-white text-sm">
                  <span className="text-blue-400">{ev.subject}</span>
                  <span className="text-gray-400 mx-1">→</span>
                  <span className="text-gray-200">{ev.action}</span>
                  <span className="text-gray-400 mx-1">→</span>
                  <span className="text-green-400">{ev.object}</span>
                </p>
                {ev.mitre_techniques?.length > 0 && (
                  <div className="flex gap-1 flex-wrap mt-0.5">
                    {ev.mitre_techniques.map((t) => (
                      <span key={t} className="text-xs bg-purple-800/60 text-purple-300 px-1.5 py-0.5 rounded font-mono">{t}</span>
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
