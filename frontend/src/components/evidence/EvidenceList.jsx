import { useEffect, useRef, useState, useCallback } from 'react'
import { getEvidence, reprocessEvidence, deleteEvidence } from '../../services/evidenceService'
import { formatBytes, formatDateTime, humanize, parseUtcMs, formatDuration } from '../../utils/formatters'
import { FileText, RefreshCw, RotateCcw, Trash2 } from 'lucide-react'
import { EmptyState, ConfirmModal } from '../ui'
import useRole from '../../hooks/useRole'

const POLLING_INTERVAL = 2000
const ACTIVE_STATUSES = ['parsing', 'queued', 'uploaded', 'processing', 'analyzing', 'building_graph', 'correlating']
const TERMINAL_STATUSES = ['parsed', 'completed', 'failed', 'cancelled']

const STATUS_COLORS = {
  uploaded: { bg: 'rgba(107,127,163,0.18)', color: '#64748b' },
  queued:   { bg: 'rgba(96,165,250,0.18)',  color: '#2563eb' },
  parsing:  { bg: 'rgba(245,158,11,0.18)',  color: '#d97706' },
  parsed:   { bg: 'rgba(16,185,129,0.18)',  color: '#059669' },
  failed:   { bg: 'rgba(239,68,68,0.18)',   color: '#dc2626' },
}

const StatusPill = ({ status }) => {
  const s = STATUS_COLORS[status] || STATUS_COLORS.uploaded
  return (
    <span style={{ display: 'inline-block', padding: '3px 10px', borderRadius: '99px', fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px', background: s.bg, color: s.color, border: `1px solid ${s.color}30` }}>
      {humanize(status)}
    </span>
  )
}

const ActionBtn = ({ onClick, disabled, title, color, children }) => (
  <button onClick={onClick} disabled={disabled} title={title}
    style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '5px 10px', borderRadius: '8px', border: `1px solid ${color}30`, background: `${color}15`, color, fontSize: '11.5px', fontWeight: '600', cursor: disabled ? 'not-allowed' : 'pointer', fontFamily: 'inherit', whiteSpace: 'nowrap', transition: 'all 0.15s', opacity: disabled ? 0.5 : 1 }}
    onMouseEnter={e => { if (!disabled) { e.currentTarget.style.background = `${color}25`; e.currentTarget.style.borderColor = `${color}60` } }}
    onMouseLeave={e => { e.currentTarget.style.background = `${color}15`; e.currentTarget.style.borderColor = `${color}30` }}
  >
    {children}
  </button>
)

const EvidenceList = ({ items, caseId, isDashboard = false, onItemUpdated, onItemDeleted }) => {
  const timerRef = useRef(null)
  const [reprocessing, setReprocessing] = useState({})
  const [deleting, setDeleting]         = useState({})
  const [confirmDelete, setConfirmDelete] = useState(null)
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

  const pendingIdsKey = items
    .filter(e => ACTIVE_STATUSES.includes(String(e.status || '').trim().toLowerCase()))
    .map(e => e.id || e._id)
    .sort()
    .join(',')

  useEffect(() => {
    if (!pendingIdsKey) return

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
          if (err?.response?.status === 401) {
            clearInterval(timerRef.current)
            timerRef.current = null
            return
          }
        }
      }
    }, POLLING_INTERVAL)

    return () => {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }, [pendingIdsKey])

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
      title="No evidence files uploaded yet"
      description="Upload your first evidence file above to start analyzing digital artifacts."
    />
  )

  const thStyle = {
    padding: '12px 16px',
    textAlign: 'left',
    color: 'var(--forensic-text-muted, #64748b)',
    fontSize: '11px',
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: '0.6px',
    borderBottom: '1px solid var(--forensic-border, #cbd5e1)',
    whiteSpace: 'nowrap'
  }

  const renderScanTime = (e) => {
    const normStatus = String(e.status || '').trim().toLowerCase()
    const isTerminal = TERMINAL_STATUSES.includes(normStatus)

    if (isTerminal) {
      if (e.scan_duration_ms != null && e.scan_duration_ms >= 0) {
        const totalSecs = Math.round(e.scan_duration_ms / 1000)
        const color = normStatus === 'failed' ? '#dc2626' : totalSecs < 10 ? '#059669' : totalSecs < 60 ? '#d97706' : '#dc2626'
        return (
          <span style={{ fontSize: '12.5px', fontWeight: '700', color }}>
            {formatDuration(totalSecs)}
          </span>
        )
      }

      const startMs = parseUtcMs(e.processing_started_at || e.parsing_started_at)
      const finishMs = parseUtcMs(e.processing_finished_at || e.parsed_at)
      if (startMs && finishMs && finishMs >= startMs) {
        const totalSecs = Math.round((finishMs - startMs) / 1000)
        const color = normStatus === 'failed' ? '#dc2626' : totalSecs < 10 ? '#059669' : totalSecs < 60 ? '#d97706' : '#dc2626'
        return (
          <span style={{ fontSize: '12.5px', fontWeight: '700', color }}>
            {formatDuration(totalSecs)}
          </span>
        )
      }

      const createdMs = parseUtcMs(e.created_at)
      const updatedMs = parseUtcMs(e.updated_at)
      if (createdMs && updatedMs && updatedMs > createdMs) {
        const deltaSecs = Math.round((updatedMs - createdMs) / 1000)
        if (deltaSecs > 0 && deltaSecs < 1800) {
          const color = normStatus === 'failed' ? '#dc2626' : deltaSecs < 10 ? '#059669' : deltaSecs < 60 ? '#d97706' : '#dc2626'
          return (
            <span style={{ fontSize: '12.5px', fontWeight: '700', color }}>
              {formatDuration(deltaSecs)}
            </span>
          )
        }
      }

      return (
        <span style={{ fontSize: '12.5px', fontWeight: '700', color: normStatus === 'failed' ? '#dc2626' : '#059669' }}>
          0s
        </span>
      )
    }

    const startMs = parseUtcMs(e.processing_started_at || e.parsing_started_at)
    if (!startMs) {
      return (
        <span style={{ fontSize: '12.5px', fontWeight: '700', color: '#d97706' }}>
          0s
        </span>
      )
    }

    const elapsedSecs = Math.max(0, Math.floor((now - startMs) / 1000))
    return (
      <span style={{ fontSize: '12.5px', fontWeight: '700', color: '#d97706' }}>
        {formatDuration(elapsedSecs)}
      </span>
    )
  }

  return (
    <>
      <div className="touch-horizontal-scroll" style={{
        borderRadius: '18px',
        border: '1px solid var(--forensic-border, #e2e8f0)',
        background: 'var(--forensic-card-bg, #ffffff)',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)',
        overflow: 'hidden',
      }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13.5px' }}>
          <thead>
            <tr style={{ background: 'var(--forensic-panel-bg, #f8fafc)' }}>
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
                  background: i % 2 === 0 ? 'var(--forensic-card-bg, #ffffff)' : 'var(--forensic-panel-bg, #f8fafc)',
                  borderBottom: i < items.length - 1 ? '1px solid var(--forensic-border, #e2e8f0)' : 'none',
                  transition: 'background 0.15s ease'
                }}
                onMouseEnter={el => el.currentTarget.style.background = 'rgba(99, 102, 241, 0.06)'}
                onMouseLeave={el => el.currentTarget.style.background = i % 2 === 0 ? 'var(--forensic-card-bg, #ffffff)' : 'var(--forensic-panel-bg, #f8fafc)'}
              >
                <td style={{ padding: '12px 16px', color: 'var(--forensic-text-main, #0f172a)', fontWeight: '700', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {e.filename}
                </td>

                <td style={{ padding: '12px 16px', color: 'var(--forensic-text-muted, #64748b)', textTransform: 'uppercase', fontSize: '11.5px', fontWeight: '600', whiteSpace: 'nowrap' }}>
                  {e.file_type}
                </td>

                <td style={{ padding: '12px 16px', color: 'var(--forensic-text-muted, #64748b)', whiteSpace: 'nowrap' }}>
                  {formatBytes(e.size_bytes)}
                </td>

                <td style={{ padding: '12px 16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <StatusPill status={e.status} />
                    {ACTIVE_STATUSES.includes(e.status) && (
                      <RefreshCw
                        size={12}
                        color="var(--forensic-primary, #2563eb)"
                        style={{
                          animation: 'spin 1s linear infinite',
                          flexShrink: 0
                        }}
                      />
                    )}
                  </div>
                  {e.error_message && (
                    <p style={{ color: '#dc2626', fontSize: '11.5px', margin: '4px 0 0 0', fontWeight: '500' }}>
                      {e.error_message}
                    </p>
                  )}
                </td>

                <td style={{ padding: '12px 16px', whiteSpace: 'nowrap' }}>
                  {renderScanTime(e, now)}
                </td>

                <td style={{ padding: '12px 16px', color: 'var(--forensic-text-muted, #64748b)', fontSize: '12px', whiteSpace: 'nowrap' }}>
                  {formatDateTime(e.created_at)}
                </td>

                <td style={{ padding: '12px 16px', color: 'var(--forensic-text-muted, #64748b)', fontSize: '11.5px', fontFamily: 'monospace', maxWidth: '110px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {e.sha256?.slice(0, 12)}…
                </td>

                <td style={{ padding: '12px 16px' }}>
                  {!isDashboard ? (
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                      {canReprocess && (
                        <ActionBtn
                          onClick={() => handleReprocess(e)}
                          disabled={
                            reprocessing[e.id || e._id] ||
                            ACTIVE_STATUSES.includes(e.status)
                          }
                          title="Re-run full pipeline"
                          color="#7c3aed"
                        >
                          <RotateCcw
                            size={12}
                            style={{ animation: reprocessing[e.id || e._id] ? 'spin 1s linear infinite' : 'none' }}
                          />
                          {reprocessing[e.id || e._id] ? 'Starting…' : 'Re-process'}
                        </ActionBtn>
                      )}

                      {canDelete && (
                        <ActionBtn
                          onClick={() => setConfirmDelete(e)}
                          disabled={deleting[e.id || e._id]}
                          title="Delete this evidence file"
                          color="#dc2626"
                        >
                          <Trash2 size={12} />
                          {deleting[e.id || e._id] ? 'Deleting…' : 'Delete'}
                        </ActionBtn>
                      )}
                    </div>
                  ) : (
                    <span style={{ color: 'var(--forensic-text-muted, #94a3b8)', fontSize: '12px' }}>—</span>
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

      {confirmDelete && (
        <ConfirmModal
          title="Delete Evidence"
          message={`Delete "${confirmDelete.filename}"? This removes the file, all ${confirmDelete.status === 'parsed' ? 'parsed events, graph nodes, and' : ''} associated data. This cannot be undone.`}
          confirmLabel="Delete"
          confirmColor="#dc2626"
          onConfirm={handleDelete}
          onCancel={() => setConfirmDelete(null)}
        />
      )}

    </>
  )
}

export default EvidenceList