import { useEffect, useRef, useState, useCallback } from 'react'
import { getEvidence, reprocessEvidence, deleteEvidence } from '../../services/evidenceService'
import { formatBytes, formatDateTime, humanize, parseUtcMs, formatDuration } from '../../utils/formatters'
import { FileText, RefreshCw, RotateCcw, Trash2, Eye } from 'lucide-react'
import { EmptyState, ConfirmModal } from '../ui'
import EvidenceDrawer from './EvidenceDrawer'
import useRole from '../../hooks/useRole'

const POLLING_INTERVAL = 2000
const ACTIVE_STATUSES = ['parsing', 'queued', 'uploaded', 'processing', 'analyzing', 'building_graph', 'correlating']
const TERMINAL_STATUSES = ['parsed', 'completed', 'failed', 'cancelled']

const STATUS_COLORS = {
  uploaded: { bg: 'rgba(107,127,163,0.2)', color: '#9aa8c0' },
  queued:   { bg: 'rgba(96,165,250,0.2)',  color: '#60a5fa' },
  parsing:  { bg: 'rgba(245,158,11,0.2)',  color: '#fbbf24' },
  parsed:   { bg: 'rgba(16,185,129,0.2)',  color: '#34d399' },
  failed:   { bg: 'rgba(239,68,68,0.2)',   color: '#fca5a5' },
}

const StatusPill = ({ status }) => {
  const s = STATUS_COLORS[status] || STATUS_COLORS.uploaded
  return (
    <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: '99px', fontSize: '11px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px', background: s.bg, color: s.color }}>
      {humanize(status)}
    </span>
  )
}

const ActionBtn = ({ onClick, disabled, title, color, children }) => (
  <button onClick={onClick} disabled={disabled} title={title}
    style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '4px 9px', borderRadius: '6px', border: `1px solid ${color}22`, background: `${color}18`, color, fontSize: '11px', fontWeight: '600', cursor: disabled ? 'not-allowed' : 'pointer', fontFamily: 'inherit', whiteSpace: 'nowrap', transition: 'all 0.15s', opacity: disabled ? 0.5 : 1 }}
    onMouseEnter={e => { if (!disabled) { e.currentTarget.style.background = `${color}30`; e.currentTarget.style.borderColor = `${color}55` } }}
    onMouseLeave={e => { e.currentTarget.style.background = `${color}18`; e.currentTarget.style.borderColor = `${color}22` }}
  >
    {children}
  </button>
)

const EvidenceList = ({ items, caseId, isDashboard = false, onItemUpdated, onItemDeleted }) => {
  const timerRef = useRef(null)
  const [reprocessing, setReprocessing] = useState({})
  const [deleting, setDeleting]         = useState({})
  const [confirmDelete, setConfirmDelete] = useState(null)
  const [drawerEvidence, setDrawerEvidence] = useState(null)

  const { canReprocess, canDelete } = useRole()

  // Stable ref for onItemUpdated so the polling interval doesn't restart on every render
  const onItemUpdatedRef = useRef(onItemUpdated)
  useEffect(() => { onItemUpdatedRef.current = onItemUpdated }, [onItemUpdated])

  // Shared live clock — ticks every 1000ms only when evidence is actively processing
  const [now, setNow] = useState(Date.now())
  useEffect(() => {
    const hasActive = items.some(e => {
      const s = String(e.status || '').trim().toLowerCase()
      return ACTIVE_STATUSES.includes(s)
    })
    if (!hasActive) return
    const timer = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(timer)
  }, [items])

  // Derive a stable key for polling effect: comma-joined IDs of active evidence
  // This ensures the polling loop only restarts when the SET of active items changes,
  // not on every re-render caused by state updates.
  const pendingIdsKey = items
    .filter(e => ACTIVE_STATUSES.includes(String(e.status || '').trim().toLowerCase()))
    .map(e => e.id || e._id)
    .sort()
    .join(',')

  // Poll active items every 2 seconds to receive backend status changes.
  // Uses onItemUpdatedRef so the interval is NOT recreated when parent re-renders.
  useEffect(() => {
    if (!pendingIdsKey) return   // No active items — do not start any interval

    const pendingIds = pendingIdsKey.split(',')

    timerRef.current = setInterval(async () => {
      for (const targetId of pendingIds) {
        try {
          const updated = await getEvidence(targetId)
          const currentItem = items.find(e => (e.id || e._id) === targetId)
          if (!currentItem) continue
          const oldStatus = String(currentItem.status || '').trim().toLowerCase()
          const newStatus = String(updated.status || '').trim().toLowerCase()
          if (
            newStatus !== oldStatus ||
            updated.parsed_at !== currentItem.parsed_at ||
            updated.processing_finished_at !== currentItem.processing_finished_at ||
            updated.scan_duration_ms !== currentItem.scan_duration_ms ||
            updated.error_message !== currentItem.error_message
          ) {
            onItemUpdatedRef.current(updated)
          }
        } catch (err) {
          // On 401 Unauthorized: stop polling to avoid a request storm
          if (err?.response?.status === 401) {
            clearInterval(timerRef.current)
            timerRef.current = null
            return
          }
          /* other errors: silent */
        }
      }
    }, POLLING_INTERVAL)

    return () => {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingIdsKey])  // Only restart when the SET of active evidence IDs changes

  const handleReprocess = async (ev) => {
    const targetId = ev.id || ev._id
    const normEvStatus = String(ev.status || '').trim().toLowerCase()
    if (reprocessing[targetId] || ACTIVE_STATUSES.includes(normEvStatus)) return
    setReprocessing(p => ({ ...p, [targetId]: true }))
    try {
      await reprocessEvidence(caseId, targetId)
      const nowIso = new Date().toISOString()
      onItemUpdated({
        ...ev,
        status: 'parsing',
        processing_started_at: nowIso,
        parsing_started_at: nowIso,
        processing_finished_at: null,
        parsed_at: null,
        scan_duration_ms: null,
        error_message: null
      })
    } catch (e) {
      if (e?.response?.status === 409) {
        alert(e.response.data?.detail || 'Evidence is currently being processed.')
      } else {
        console.error('Reprocess error:', e)
      }
    } finally {
      setReprocessing(p => ({ ...p, [targetId]: false }))
    }
  }

  const handleDelete = async () => {
    if (!confirmDelete) return
    const ev = confirmDelete
    const targetId = ev.id || ev._id
    setConfirmDelete(null)
    setDeleting(p => ({ ...p, [targetId]: true }))

    try {
      await deleteEvidence(caseId, targetId)
      // Clear chat history for this case — deleted evidence filenames must not
      // appear in the copilot context via stale conversation history.
      localStorage.removeItem(`forensight_chat_${caseId}`)
      if (onItemDeleted) onItemDeleted(targetId)
    } catch (e) {
      console.error('Delete failed', e)
      if (e?.response?.status === 404) {
        localStorage.removeItem(`forensight_chat_${caseId}`)
        if (onItemDeleted) onItemDeleted(targetId)
      } else {
        alert(`Delete failed: ${e?.response?.data?.detail || e.message}`)
      }
    } finally {
      setDeleting(p => ({ ...p, [targetId]: false }))
    }
  }

  if (!items.length) return (
    <EmptyState
      icon={FileText}
      title="No evidence yet"
      description="Upload your first forensic file above."
    />
  )

  const thStyle = {
    padding: '10px 14px',
    textAlign: 'left',
    color: '#6b7fa3',
    fontSize: '10px',
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: '1px',
    borderBottom: '1px solid #3d4f6a',
    whiteSpace: 'nowrap'
  }

  const renderScanTime = (e) => {
    const normStatus = String(e.status || '').trim().toLowerCase()
    const isTerminal = TERMINAL_STATUSES.includes(normStatus)

    // ── 1. Terminal State (Parsed / Failed / Completed / Cancelled) ──────────
    if (isTerminal) {
      // Primary: Use stored scan_duration_ms recorded by backend
      if (e.scan_duration_ms != null && e.scan_duration_ms >= 0) {
        const totalSecs = Math.round(e.scan_duration_ms / 1000)
        const color = normStatus === 'failed' ? '#fca5a5' : totalSecs < 10 ? '#34d399' : totalSecs < 60 ? '#fbbf24' : '#f87171'
        return (
          <span style={{ fontSize: '12px', fontWeight: '600', color }}>
            {formatDuration(totalSecs)}
          </span>
        )
      }

      // Secondary Fallback: Delta between finish time and start time
      const startMs = parseUtcMs(e.processing_started_at || e.parsing_started_at)
      const finishMs = parseUtcMs(e.processing_finished_at || e.parsed_at)
      if (startMs && finishMs && finishMs >= startMs) {
        const totalSecs = Math.round((finishMs - startMs) / 1000)
        const color = normStatus === 'failed' ? '#fca5a5' : totalSecs < 10 ? '#34d399' : totalSecs < 60 ? '#fbbf24' : '#f87171'
        return (
          <span style={{ fontSize: '12px', fontWeight: '600', color }}>
            {formatDuration(totalSecs)}
          </span>
        )
      }

      // Tertiary Legacy Fallback: Delta between updated_at and created_at
      const createdMs = parseUtcMs(e.created_at)
      const updatedMs = parseUtcMs(e.updated_at)
      if (createdMs && updatedMs && updatedMs > createdMs) {
        const deltaSecs = Math.round((updatedMs - createdMs) / 1000)
        if (deltaSecs > 0 && deltaSecs < 1800) {
          const color = normStatus === 'failed' ? '#fca5a5' : deltaSecs < 10 ? '#34d399' : deltaSecs < 60 ? '#fbbf24' : '#f87171'
          return (
            <span style={{ fontSize: '12px', fontWeight: '600', color }}>
              {formatDuration(deltaSecs)}
            </span>
          )
        }
      }

      // STRICT GUARD: Terminal states NEVER fall through to live clock
      return (
        <span style={{ fontSize: '12px', fontWeight: '600', color: normStatus === 'failed' ? '#fca5a5' : '#34d399' }}>
          0s
        </span>
      )
    }

    // ── 2. Active State (Parsing / Queued / Uploaded) ────────────────────────
    const startMs = parseUtcMs(e.processing_started_at || e.parsing_started_at)
    if (!startMs) {
      return (
        <span style={{ fontSize: '12px', fontWeight: '600', color: '#fbbf24' }}>
          0s
        </span>
      )
    }

    const elapsedSecs = Math.max(0, Math.floor((now - startMs) / 1000))
    return (
      <span style={{ fontSize: '12px', fontWeight: '600', color: '#fbbf24' }}>
        {formatDuration(elapsedSecs)}
      </span>
    )
  }

  return (
    <>
      <div className="touch-horizontal-scroll" style={{ borderRadius: '12px', border: '1px solid #3d4f6a' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ background: '#1e2a3d' }}>
              <th style={thStyle}>Filename</th>
              <th style={thStyle}>Type</th>
              <th style={thStyle}>Size</th>
              <th style={thStyle}>Status</th>
              <th style={thStyle}>Scan Time</th>
              <th style={thStyle}>Uploaded</th>
              <th style={thStyle}>SHA-256</th>
              <th style={thStyle}>Actions</th>
            </tr>
          </thead>

          <tbody>
            {items.map((e, i) => (
              <tr
                key={e.id || e._id || i}
                style={{
                  background: i % 2 === 0 ? '#2d3748' : '#283141',
                  borderBottom: i < items.length - 1 ? '1px solid #3d4f6a' : 'none',
                  transition: 'background 0.15s'
                }}
                onMouseEnter={el => el.currentTarget.style.background = '#323d52'}
                onMouseLeave={el => el.currentTarget.style.background = i % 2 === 0 ? '#2d3748' : '#283141'}
              >
                <td style={{ padding: '10px 14px', color: '#fff', fontWeight: '500', maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {e.filename}
                </td>

                <td style={{ padding: '10px 14px', color: '#9aa8c0', textTransform: 'uppercase', fontSize: '11px', whiteSpace: 'nowrap' }}>
                  {e.file_type}
                </td>

                <td style={{ padding: '10px 14px', color: '#9aa8c0', whiteSpace: 'nowrap' }}>
                  {formatBytes(e.size_bytes)}
                </td>

                <td style={{ padding: '10px 14px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
                    <StatusPill status={e.status} />
                    {ACTIVE_STATUSES.includes(e.status) && (
                      <RefreshCw
                        size={11}
                        color="#6b7fa3"
                        style={{
                          animation: 'spin 1s linear infinite',
                          flexShrink: 0
                        }}
                      />
                    )}
                  </div>
                  {e.error_message && (
                    <p style={{ color: '#fca5a5', fontSize: '11px', margin: '3px 0 0 0' }}>
                      {e.error_message}
                    </p>
                  )}
                </td>

                {/* LIVE SCAN TIME (Real Stopwatch Display) */}
                <td style={{ padding: '10px 14px', whiteSpace: 'nowrap' }}>
                  {renderScanTime(e, now)}
                </td>

                <td style={{ padding: '10px 14px', color: '#9aa8c0', fontSize: '11px', whiteSpace: 'nowrap' }}>
                  {formatDateTime(e.created_at)}
                </td>

                <td style={{ padding: '10px 14px', color: '#4a5568', fontSize: '11px', fontFamily: 'monospace', maxWidth: '100px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {e.sha256?.slice(0, 12)}…
                </td>

                <td style={{ padding: '10px 14px' }}>
                  {!isDashboard ? (
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                      {/* View Graph + Report */}
                      <ActionBtn
                        onClick={() => setDrawerEvidence(e)}
                        disabled={e.status !== 'parsed'}
                        title="View evidence graph and report"
                        color="#60a5fa"
                      >
                        <Eye size={10} /> View
                      </ActionBtn>

                      {/* Re-process */}
                      {canReprocess && (
                        <ActionBtn
                          onClick={() => handleReprocess(e)}
                          disabled={
                            reprocessing[e.id || e._id] ||
                            ACTIVE_STATUSES.includes(e.status)
                          }
                          title="Re-run full pipeline"
                          color="#a78bfa"
                        >
                          <RotateCcw
                            size={10}
                            style={{ animation: reprocessing[e.id || e._id] ? 'spin 1s linear infinite' : 'none' }}
                          />
                          {reprocessing[e.id || e._id] ? 'Starting…' : 'Re-process'}
                        </ActionBtn>
                      )}

                      {/* Delete */}
                      {canDelete && (
                        <ActionBtn
                          onClick={() => setConfirmDelete(e)}
                          disabled={deleting[e.id || e._id]}
                          title="Delete this evidence file"
                          color="#f87171"
                        >
                          <Trash2 size={10} />
                          {deleting[e.id || e._id] ? 'Deleting…' : 'Delete'}
                        </ActionBtn>
                      )}
                    </div>
                  ) : (
                    <span style={{ color: '#64748b', fontSize: '11px' }}>—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <style>
          {`
            @keyframes spin {
              from { transform: rotate(0deg); }
              to { transform: rotate(360deg); }
            }
          `}
        </style>
      </div>

      {/* Delete confirm modal */}
      {confirmDelete && (
        <ConfirmModal
          title="Delete Evidence"
          message={`Delete "${confirmDelete.filename}"? This removes the file, all ${confirmDelete.status === 'parsed' ? 'parsed events, graph nodes, and' : ''} associated data. This cannot be undone.`}
          confirmLabel="Delete"
          confirmColor="#ef4444"
          onConfirm={handleDelete}
          onCancel={() => setConfirmDelete(null)}
        />
      )}

      {/* Per-evidence drawer */}
      {drawerEvidence && (
        <EvidenceDrawer
          evidence={drawerEvidence}
          caseId={caseId}
          onClose={() => setDrawerEvidence(null)}
        />
      )}
    </>
  )
}

export default EvidenceList