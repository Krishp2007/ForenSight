import { useEffect, useRef, useState } from 'react'
import { getEvidence, reprocessEvidence } from '../../services/evidenceService'
import { formatBytes, formatDateTime, humanize } from '../../utils/formatters'
import { FileText, RefreshCw, RotateCcw } from 'lucide-react'
import EmptyState from '../ui/EmptyState'

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
    <span style={{
      display: 'inline-block',
      padding: '2px 8px',
      borderRadius: '99px',
      fontSize: '11px',
      fontWeight: '600',
      textTransform: 'uppercase',
      letterSpacing: '0.5px',
      background: s.bg,
      color: s.color,
    }}>
      {humanize(status)}
    </span>
  )
}

const EvidenceList = ({ items, caseId, onItemUpdated }) => {
  const timerRef = useRef(null)
  const [reprocessing, setReprocessing] = useState({})

  const handleReprocess = async (ev) => {
    setReprocessing(p => ({ ...p, [ev.id]: true }))
    try {
      await reprocessEvidence(caseId, ev.id)
      onItemUpdated({ ...ev, status: 'queued' })
    } catch (e) {
      console.error('Reprocess failed', e)
    } finally {
      setReprocessing(p => ({ ...p, [ev.id]: false }))
    }
  }

  useEffect(() => {
    const pending = items.filter((e) => !TERMINAL.includes(e.status))
    if (pending.length === 0) return
    timerRef.current = setInterval(async () => {
      for (const ev of pending) {
        try {
          const updated = await getEvidence(ev.id)
          if (updated.status !== ev.status) onItemUpdated(updated)
        } catch { /* silent */ }
      }
    }, POLLING_INTERVAL)
    return () => clearInterval(timerRef.current)
  }, [items])

  if (!items.length) {
    return <EmptyState icon={FileText} title="No evidence yet" description="Upload your first forensic file above." />
  }

  const thStyle = {
    padding: '10px 16px',
    textAlign: 'left',
    color: '#6b7fa3',
    fontSize: '10px',
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: '1px',
    borderBottom: '1px solid #3d4f6a',
    whiteSpace: 'nowrap',
  }

  return (
    <div style={{ overflowX: 'auto', borderRadius: '12px', border: '1px solid #3d4f6a' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
        <thead>
          <tr style={{ background: '#1e2a3d' }}>
            <th style={thStyle}>Filename</th>
            <th style={thStyle}>Type</th>
            <th style={thStyle}>Size</th>
            <th style={thStyle}>Status</th>
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
                transition: 'background 0.15s',
              }}
              onMouseEnter={el => el.currentTarget.style.background = '#323d52'}
              onMouseLeave={el => el.currentTarget.style.background = i % 2 === 0 ? '#2d3748' : '#283141'}
            >
              <td style={{ padding: '10px 16px', color: '#ffffff', fontWeight: '500', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {e.filename}
              </td>
              <td style={{ padding: '10px 16px', color: '#9aa8c0', textTransform: 'uppercase', fontSize: '11px', whiteSpace: 'nowrap' }}>
                {e.file_type}
              </td>
              <td style={{ padding: '10px 16px', color: '#9aa8c0', whiteSpace: 'nowrap' }}>
                {formatBytes(e.size_bytes)}
              </td>
              <td style={{ padding: '10px 16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <StatusPill status={e.status} />
                  {!TERMINAL.includes(e.status) && (
                    <RefreshCw size={12} color="#6b7fa3" style={{ animation: 'spin 1s linear infinite' }} />
                  )}
                </div>
                {e.error_message && (
                  <p style={{ color: '#fca5a5', fontSize: '11px', margin: '4px 0 0 0' }}>{e.error_message}</p>
                )}
              </td>
              <td style={{ padding: '10px 16px', color: '#9aa8c0', fontSize: '11px', whiteSpace: 'nowrap' }}>
                {formatDateTime(e.created_at)}
              </td>
              <td style={{ padding: '10px 16px', color: '#4a5568', fontSize: '11px', fontFamily: 'monospace', maxWidth: '120px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {e.sha256?.slice(0, 12)}…
              </td>
              <td style={{ padding: '10px 16px' }}>
                <button
                  onClick={() => handleReprocess(e)}
                  disabled={reprocessing[e.id] || !['parsed', 'failed', 'uploaded'].includes(e.status)}
                  title="Re-run full pipeline: re-sync to Neo4j, re-run anomaly detection and embeddings"
                  style={{
                    display: 'flex', alignItems: 'center', gap: '5px',
                    padding: '4px 10px', borderRadius: '6px', border: 'none',
                    background: reprocessing[e.id] ? 'rgba(96,165,250,0.1)' : 'rgba(96,165,250,0.15)',
                    color: '#60a5fa', fontSize: '11px', fontWeight: '600',
                    cursor: (reprocessing[e.id] || !['parsed', 'failed', 'uploaded'].includes(e.status))
                      ? 'not-allowed' : 'pointer',
                    opacity: !['parsed', 'failed', 'uploaded'].includes(e.status) ? 0.4 : 1,
                    fontFamily: 'inherit', whiteSpace: 'nowrap',
                    transition: 'background 0.15s',
                  }}
                  onMouseEnter={el => { if (!reprocessing[e.id]) el.currentTarget.style.background = 'rgba(96,165,250,0.25)' }}
                  onMouseLeave={el => el.currentTarget.style.background = 'rgba(96,165,250,0.15)'}
                >
                  <RotateCcw size={11} style={{ animation: reprocessing[e.id] ? 'spin 1s linear infinite' : 'none' }} />
                  {reprocessing[e.id] ? 'Starting…' : 'Re-process'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

export default EvidenceList
