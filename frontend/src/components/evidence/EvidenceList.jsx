import { useEffect, useRef, useState } from 'react'
import { getEvidence, reprocessEvidence, deleteEvidence } from '../../services/evidenceService'
import { formatBytes, formatDateTime, humanize } from '../../utils/formatters'
import { FileText, RefreshCw, RotateCcw, Trash2, Eye } from 'lucide-react'
import { EmptyState, ConfirmModal } from '../ui'
import EvidenceDrawer from './EvidenceDrawer'
import useParseTimerStore from '../../store/parseTimerStore'
import useRole from '../../hooks/useRole'

const POLLING_INTERVAL = 2000
const TERMINAL = ['parsed', 'failed']

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

const parseUtcDate = (d) => {
  if (!d) return null
  if (typeof d === 'number') return d
  const str = String(d).trim()
  if (!str) return null
  // If string has no timezone specifier, append 'Z' so JS parses as UTC
  const isoStr = (str.includes('Z') || str.includes('+') || (str.length > 10 && str.lastIndexOf('-') > 10))
    ? str
    : str + 'Z'
  const ms = new Date(isoStr).getTime()
  return isNaN(ms) ? null : ms
}

const EvidenceList = ({ items, caseId, onItemUpdated, onItemDeleted }) => {
  const timerRef = useRef(null)
  const [reprocessing, setReprocessing] = useState({})
  const [deleting, setDeleting]         = useState({})
  const [confirmDelete, setConfirmDelete] = useState(null)
  const [drawerEvidence, setDrawerEvidence] = useState(null)

  const { canReprocess, canDelete } = useRole()

  // Parse timers live in a Zustand store — survives tab/page navigation
  const { markStarted, resetTimer, markDone, getStartMs } = useParseTimerStore()

  // Live tick — active while any evidence item is processing
  const [now, setNow] = useState(Date.now())
  useEffect(() => {
    const active = items.some(e => !TERMINAL.includes(e.status))
    if (!active) return
    const timer = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(timer)
  }, [items])

  // Register / clean up timer entries whenever item statuses change
  useEffect(() => {
    items.forEach(e => {
      if (!TERMINAL.includes(e.status)) {
        markStarted(e.id || e._id, e.parsing_started_at || e.created_at)
      } else {
        markDone(e.id || e._id)
      }
    })
  }, [items])

  // Poll non-terminal items every 2 seconds
  useEffect(() => {
    const pending = items.filter(e => !TERMINAL.includes(e.status))

    if (!pending.length) return

    timerRef.current = setInterval(async () => {
      for (const ev of pending) {
        try {
          const targetId = ev.id || ev._id
          const updated = await getEvidence(targetId)
          if (
            updated.status !== ev.status ||
            updated.parsed_at !== ev.parsed_at ||
            updated.error_message !== ev.error_message
          ) {
            onItemUpdated(updated)
          }
        } catch {
          /* silent */
        }
      }
    }, POLLING_INTERVAL)

    return () => clearInterval(timerRef.current)
  }, [items])

  const handleReprocess = async (ev) => {
    const targetId = ev.id || ev._id
    setReprocessing(p => ({ ...p, [targetId]: true }))
    try {
      await reprocessEvidence(caseId, targetId)
      const nowIso = new Date().toISOString()
      resetTimer(targetId, Date.now())
      onItemUpdated({
        ...ev,
        status: 'parsing',
        created_at: nowIso,
        parsing_started_at: nowIso,
        parsed_at: null
      })
    } catch (e) {
      console.error(e)
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

      if (onItemDeleted) {
        onItemDeleted(targetId)
      }
    } catch (e) {
      console.error('Delete failed', e)
      if (e?.response?.status === 404) {
        // Item is already gone from server — remove from UI table
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
                key={e.id}
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

                    {!TERMINAL.includes(e.status) && (
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

                {/* LIVE SCAN TIME (Starts from uploaded created_at for 100% continuous freeze) */}
                <td style={{ padding: '10px 14px', whiteSpace: 'nowrap' }}>
                  {(() => {
                    const targetId = e.id || e._id
                    // Always anchor to created_at (file upload start) for 100% smooth continuous duration
                    const startMs = parseUtcDate(e.created_at) || getStartMs(targetId) || parseUtcDate(e.parsing_started_at) || now

                    // Parsing / Queued / Uploaded → live ticking counter
                    if (['parsing', 'queued', 'uploaded'].includes(e.status)) {
                      const secs = Math.max(0, Math.floor((now - startMs) / 1000))
                      return (
                        <span style={{ fontSize: '12px', fontWeight: '600', color: '#fbbf24' }}>
                          {secs}s
                        </span>
                      )
                    }

                    // Parsed → frozen final scan duration from upload creation (created_at) to completion (parsed_at)
                    if (e.status === 'parsed') {
                      const endMs = parseUtcDate(e.parsed_at) || now
                      const rawSecs = Math.round((endMs - startMs) / 1000)
                      const secs = Math.max(1, rawSecs)
                      const color = secs < 10 ? '#34d399' : secs < 60 ? '#fbbf24' : '#f87171'
                      return (
                        <span style={{ fontSize: '12px', fontWeight: '600', color }}>
                          {secs}s
                        </span>
                      )
                    }

                    return (
                      <span style={{ color: '#4a5568', fontSize: '11px' }}>—</span>
                    )
                  })()}
                </td>

                <td style={{ padding: '10px 14px', color: '#9aa8c0', fontSize: '11px', whiteSpace: 'nowrap' }}>
                  {formatDateTime(e.created_at)}
                </td>

                <td style={{ padding: '10px 14px', color: '#4a5568', fontSize: '11px', fontFamily: 'monospace', maxWidth: '100px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {e.sha256?.slice(0, 12)}…
                </td>

                <td style={{ padding: '10px 14px' }}>
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>

                    {/* View Graph + Report — all roles */}
                    <ActionBtn
                      onClick={() => setDrawerEvidence(e)}
                      disabled={e.status !== 'parsed'}
                      title="View evidence graph and report"
                      color="#60a5fa"
                    >
                      <Eye size={10} /> View
                    </ActionBtn>

                    {/* Re-process — investigator + admin only */}
                    {canReprocess && (
                      <ActionBtn
                        onClick={() => handleReprocess(e)}
                        disabled={
                          reprocessing[e.id] ||
                          !['parsed', 'failed', 'uploaded'].includes(e.status)
                        }
                        title="Re-run full pipeline"
                        color="#a78bfa"
                      >
                        <RotateCcw
                          size={10}
                          style={{ animation: reprocessing[e.id] ? 'spin 1s linear infinite' : 'none' }}
                        />
                        {reprocessing[e.id] ? 'Starting…' : 'Re-process'}
                      </ActionBtn>
                    )}

                    {/* Delete — investigator + admin only */}
                    {canDelete && (
                      <ActionBtn
                        onClick={() => setConfirmDelete(e)}
                        disabled={deleting[e.id]}
                        title="Delete this evidence file"
                        color="#f87171"
                      >
                        <Trash2 size={10} />
                        {deleting[e.id] ? 'Deleting…' : 'Delete'}
                      </ActionBtn>
                    )}

                  </div>
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