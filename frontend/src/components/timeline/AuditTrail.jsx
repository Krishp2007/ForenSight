import { useState, useEffect, useCallback } from 'react'
import api from '../../services/api'
import { formatDateTime, humanize } from '../../utils/formatters'
import { Spinner, EmptyState } from '../ui'
import { ShieldCheck, Hash, ChevronDown, ChevronUp, RefreshCw, CheckCircle, XCircle } from 'lucide-react'
import { useRole } from '../../store/authStore'

// Inlined from auditService
const getCaseAuditLog  = (caseId, limit = 200) => api.get(`/cases/${caseId}/audit`, { params: { limit } }).then(r => r.data)
const verifyAuditChain = () => api.get('/audit/verify').then(r => r.data)

const ACTION_COLORS = {
  'case.create':           '#34d399',
  'case.update':           '#60a5fa',
  'evidence.upload':       '#fbbf24',
  'evidence.reprocess':    '#fb923c',
  'evidence.delete':       '#fca5a5',
  'graph.clear':           '#f87171',
  'correlations.run':      '#c4b5fd',
  'report.generate':       '#67e8f9',
  'report.export':         '#67e8f9',
  'user.login':            '#86efac',
  'user.logout':           '#94a3b8',
}

const getActionColor = (action) =>
  ACTION_COLORS[action] || '#9aa8c0'

const AuditTrail = ({ caseId }) => {
  const [rows,     setRows]     = useState([])
  const [loading,  setLoading]  = useState(true)
  const [error,    setError]    = useState(null)
  const [expanded, setExpanded] = useState(null)
  const [chain,    setChain]    = useState(null)
  const [verifying, setVerifying] = useState(false)

  const { isAdmin } = useRole()

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getCaseAuditLog(caseId, 200)
      setRows(data)
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || 'Failed to load audit log')
    } finally {
      setLoading(false)
    }
  }, [caseId])

  useEffect(() => { load() }, [load])

  const handleVerify = async () => {
    setVerifying(true)
    try {
      const result = await verifyAuditChain()
      setChain(result)
    } catch {
      setChain({ valid: false, total: 0, broken_at: null, broken_id: null })
    } finally {
      setVerifying(false)
    }
  }

  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: '48px' }}>
      <Spinner size="lg" />
    </div>
  )

  if (error) return (
    <div style={{ padding: '32px', textAlign: 'center' }}>
      <p style={{ color: '#fca5a5', fontSize: '14px', marginBottom: '12px' }}>{error}</p>
      <button
        onClick={load}
        style={{ background: '#2a3347', border: '1px solid #3d4f6a', color: '#9aa8c0', borderRadius: '8px', padding: '8px 16px', cursor: 'pointer', fontSize: '13px', fontFamily: 'inherit' }}
      >
        Retry
      </button>
    </div>
  )

  if (!rows.length) return (
    <EmptyState
      icon={ShieldCheck}
      title="No audit entries yet"
      description="Every case action (upload, reprocess, delete, update) is recorded here with a Merkle hash chain."
    />
  )

  // Show newest first
  const sorted = [...rows].sort((a, b) => new Date(b.created_at) - new Date(a.created_at))

  const handleClearAuditLogs = async () => {
    if (!window.confirm('Are you sure you want to clear historical evidence audit logs for this case?')) return
    try {
      await api.delete(`/cases/${caseId}/audit`)
      await load()
    } catch (e) {
      setError(e?.response?.data?.detail || 'Failed to clear audit logs')
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>

      {/* Header bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
        <span style={{ color: '#9aa8c0', fontSize: '13px' }}>
          {rows.length} audit entr{rows.length === 1 ? 'y' : 'ies'}
        </span>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {/* Clear Audit Logs button */}
          <button
            onClick={handleClearAuditLogs}
            style={{
              display: 'flex', alignItems: 'center', gap: '5px',
              background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.35)',
              color: '#fca5a5', borderRadius: '8px',
              padding: '5px 12px', cursor: 'pointer',
              fontSize: '12px', fontFamily: 'inherit',
            }}
          >
            Clear Audit Logs
          </button>

          {/* Chain integrity badge — only shown after verify, admin only */}
          {chain && isAdmin && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              padding: '4px 10px', borderRadius: '99px', fontSize: '11px', fontWeight: '600',
              background: chain.valid ? 'rgba(52,211,153,0.15)' : 'rgba(248,113,113,0.15)',
              color: chain.valid ? '#34d399' : '#f87171',
              border: `1px solid ${chain.valid ? '#34d39944' : '#f8717144'}`,
            }}>
              {chain.valid
                ? <><CheckCircle size={11} /> Chain intact · {chain.total} entries</>
                : <><XCircle size={11} /> Broken at entry {chain.broken_at}</>
              }
            </div>
          )}

          {/* Verify chain — admin only */}
          {isAdmin && (
          <button
            onClick={handleVerify}
            disabled={verifying}
            style={{
              display: 'flex', alignItems: 'center', gap: '5px',
              background: '#1e2a3d', border: '1px solid #3d4f6a',
              color: '#9aa8c0', borderRadius: '8px',
              padding: '5px 12px', cursor: 'pointer',
              fontSize: '12px', fontFamily: 'inherit',
              opacity: verifying ? 0.6 : 1,
            }}
          >
            <ShieldCheck size={12} />
            {verifying ? 'Verifying…' : 'Verify chain'}
          </button>
          )}

          <button
            onClick={load}
            disabled={loading}
            style={{
              display: 'flex', alignItems: 'center', gap: '5px',
              background: '#1e2a3d', border: '1px solid #3d4f6a',
              color: '#9aa8c0', borderRadius: '8px',
              padding: '5px 12px', cursor: 'pointer',
              fontSize: '12px', fontFamily: 'inherit',
            }}
          >
            <RefreshCw size={12} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
            Refresh
          </button>
        </div>
      </div>

      {/* Entries */}
      <div style={{ border: '1px solid #3d4f6a', borderRadius: '12px', overflow: 'hidden' }}>
        {sorted.map((row, i) => {
          const color  = getActionColor(row.action)
          const isOpen = expanded === i
          return (
            <div
              key={row.id || i}
              style={{
                borderBottom: i < sorted.length - 1 ? '1px solid #2d3748' : 'none',
                background: i % 2 === 0 ? '#1e2a3d' : '#253347',
              }}
            >
              {/* Row header */}
              <div
                onClick={() => setExpanded(isOpen ? null : i)}
                style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '10px 16px', cursor: 'pointer', transition: 'background 0.15s' }}
                onMouseEnter={e => e.currentTarget.style.background = '#2a3347'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
              >
                <ShieldCheck size={14} color={color} style={{ flexShrink: 0 }} />

                {/* Action badge */}
                <span style={{
                  fontSize: '11px', fontFamily: 'monospace', fontWeight: '600',
                  color, whiteSpace: 'nowrap',
                  background: `${color}18`, border: `1px solid ${color}33`,
                  padding: '1px 7px', borderRadius: '4px',
                }}>
                  {row.action}
                </span>

                {/* Entity info */}
                <span style={{ color: '#9aa8c0', fontSize: '12px', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {humanize(row.entity_type)}
                  {row.metadata?.filename && (
                    <span style={{ color: '#6b7fa3' }}> · {row.metadata.filename}</span>
                  )}
                </span>

                <span style={{ color: '#6b7fa3', fontSize: '11px', flexShrink: 0 }}>
                  {formatDateTime(row.created_at)}
                </span>

                {isOpen
                  ? <ChevronUp size={13} color="#6b7fa3" />
                  : <ChevronDown size={13} color="#6b7fa3" />
                }
              </div>

              {/* Expanded detail */}
              {isOpen && (
                <div style={{ padding: '8px 16px 12px 44px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {/* Hashes */}
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
                    <Hash size={11} color="#3d4f6a" style={{ marginTop: '2px', flexShrink: 0 }} />
                    <span style={{ fontSize: '11px', fontFamily: 'monospace', color: '#4a5568', wordBreak: 'break-all' }}>
                      <span style={{ color: '#3d4f6a' }}>prev: </span>{row.prev_hash?.slice(0, 40)}…
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
                    <Hash size={11} color="#3d4f6a" style={{ marginTop: '2px', flexShrink: 0 }} />
                    <span style={{ fontSize: '11px', fontFamily: 'monospace', color: '#4a5568', wordBreak: 'break-all' }}>
                      <span style={{ color: '#3d4f6a' }}>self: </span>{row.self_hash?.slice(0, 40)}…
                    </span>
                  </div>

                  {/* Metadata */}
                  {row.metadata && Object.keys(row.metadata).length > 0 && (
                    <pre style={{
                      background: '#1a2234', borderRadius: '6px',
                      padding: '8px 12px', fontSize: '11px', color: '#9aa8c0',
                      overflowX: 'auto', margin: '4px 0 0 0', fontFamily: 'monospace',
                    }}>
                      {JSON.stringify(row.metadata, null, 2)}
                    </pre>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

export default AuditTrail
