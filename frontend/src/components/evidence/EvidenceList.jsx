import { useEffect, useRef, useState } from 'react'
import { getEvidence, reprocessEvidence, deleteEvidence } from '../../services/evidenceService'
import { formatBytes, formatDateTime, humanize } from '../../utils/formatters'
import { FileText, RefreshCw, RotateCcw, Trash2, Eye } from 'lucide-react'
import EmptyState from '../ui/EmptyState'
import ConfirmModal from '../ui/ConfirmModal'
import EvidenceDrawer from './EvidenceDrawer'
import useParseTimerStore from '../../store/parseTimerStore'

const POLLING_INTERVAL = 4000
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

const EvidenceList = ({ items, caseId, onItemUpdated, onItemDeleted }) => {
  const timerRef = useRef(null)
  const [reprocessing, setReprocessing] = useState({})
  const [deleting, setDeleting]         = useState({})
  const [confirmDelete, setConfirmDelete] = useState(null)
  const [drawerEvidence, setDrawerEvidence] = useState(null)

  // Parse timers live in a Zustand store — survives tab/page navigation
  const { markStarted, markDone, getStartMs } = useParseTimerStore()

  // Live tick — only active while something is parsing
  const [now, setNow] = useState(Date.now())
  useEffect(() => {
    const active = items.some(e => e.status === 'parsing')
    if (!active) return
    const timer = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(timer)
  }, [items])

  // Register / clean up timer entries whenever item statuses change
  useEffect(() => {
    items.forEach(e => {
      if (e.status === 'parsing') {
        markStarted(e.id, e.parsing_started_at)
      } else if (e.status === 'parsed' || e.status === 'failed') {
        markDone(e.id)
      }
    })
  }, [items])

  // Poll non-terminal items
  useEffect(() => {
    const pending = items.filter(e => !TERMINAL.includes(e.status))

    if (!pending.length) return

    timerRef.current = setInterval(async () => {
      for (const ev of pending) {
        try {
          const updated = await getEvidence(ev.id)

          if (updated.status !== ev.status) {
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
    setReprocessing(p => ({ ...p, [ev.id]: true }))
    try {
      await reprocessEvidence(caseId, ev.id)
      // Reset the timer so it starts fresh on re-process
      markDone(ev.id)
      onItemUpdated({ ...ev, status: 'queued', parsing_started_at: null, parsed_at: null })
    } catch (e) {
      console.error(e)
    } finally {
      setReprocessing(p => ({ ...p, [ev.id]: false }))
    }
  }

  const handleDelete = async () => {
    if (!confirmDelete) return

    const ev = confirmDelete

    setConfirmDelete(null)
    setDeleting(p => ({ ...p, [ev.id]: true }))

    try {
      await deleteEvidence(caseId, ev.id)

      if (onItemDeleted) {
        onItemDeleted(ev.id)
      }
    } catch (e) {
      console.error('Delete failed', e)
    } finally {
      setDeleting(p => ({ ...p, [ev.id]: false }))
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
      <div style={{ overflowX: 'auto', borderRadius: '12px', border: '1px solid #3d4f6a' }}>
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

                {/* LIVE SCAN TIME */}
                <td style={{ padding: '10px 14px', whiteSpace: 'nowrap' }}>
                  {(() => {
                    // Parsing → live counter from store (survives navigation)
                    if (e.status === 'parsing') {
                      const startMs = getStartMs(e.id) || now
                      const secs = Math.max(0, Math.floor((now - startMs) / 1000))
                      return (
                        <span style={{ fontSize: '12px', fontWeight: '600', color: '#fbbf24' }}>
                          {secs}s
                        </span>
                      )
                    }

                    // Parsed → frozen final time
                    if (
                      e.status === 'parsed' &&
                      e.parsing_started_at &&
                      e.parsed_at
                    ) {
                      const secs = Math.max(
                        0,
                        Math.round(
                          (new Date(e.parsed_at).getTime() -
                           new Date(e.parsing_started_at).getTime()) / 1000
                        )
                      )
                      const color = secs < 10 ? '#34d399' : secs < 60 ? '#fbbf24' : '#f87171'
                      return (
                        <span style={{ fontSize: '12px', fontWeight: '600', color }}>
                          {secs}s
                        </span>
                      )
                    }

                    // Waiting for worker
                    if (e.status === 'queued') {
                      return (
                        <span style={{ fontSize: '11px', color: '#60a5fa' }}>
                          waiting…
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
                        style={{
                          animation: reprocessing[e.id]
                            ? 'spin 1s linear infinite'
                            : 'none'
                        }}
                      />

                      {reprocessing[e.id] ? 'Starting…' : 'Re-process'}
                    </ActionBtn>

                    {/* Delete */}
                    <ActionBtn
                      onClick={() => setConfirmDelete(e)}
                      disabled={deleting[e.id]}
                      title="Delete this evidence file"
                      color="#f87171"
                    >
                      <Trash2 size={10} />
                      {deleting[e.id] ? 'Deleting…' : 'Delete'}
                    </ActionBtn>

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