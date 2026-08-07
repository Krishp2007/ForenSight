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
  'case.create':           '#059669',
  'case.update':           '#2563eb',
  'evidence.upload':       '#d97706',
  'evidence.reprocess':    '#ea580c',
  'evidence.delete':       '#dc2626',
  'graph.clear':           '#dc2626',
  'correlations.run':      '#7c3aed',
  'report.generate':       '#0284c7',
  'report.export':         '#0284c7',
  'user.login':            '#16a34a',
  'user.logout':           '#64748b',
}

const getActionColor = (action) =>
  ACTION_COLORS[action] || 'var(--forensic-text-muted, #64748b)'

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
      <p style={{ color: '#dc2626', fontSize: '14px', marginBottom: '12px', fontWeight: '600' }}>{error}</p>
      <button
        onClick={load}
        style={{ background: 'var(--forensic-panel-bg, #f8fafc)', border: '1px solid var(--forensic-border, #cbd5e1)', color: 'var(--forensic-text-main, #0f172a)', borderRadius: '10px', padding: '8px 16px', cursor: 'pointer', fontSize: '13px', fontFamily: 'inherit', fontWeight: '600' }}
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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontFamily: 'inherit' }}>

      {/* Header bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
        <span style={{ color: 'var(--forensic-text-muted, #64748b)', fontSize: '13px', fontWeight: '600' }}>
          {rows.length} audit entr{rows.length === 1 ? 'y' : 'ies'}
        </span>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            onClick={handleClearAuditLogs}
            style={{
              display: 'flex', alignItems: 'center', gap: '5px',
              background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#dc2626', borderRadius: '10px',
              padding: '6px 14px', cursor: 'pointer',
              fontSize: '12.5px', fontWeight: '600', fontFamily: 'inherit',
            }}
          >
            Clear Audit Logs
          </button>

          {chain && isAdmin && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              padding: '4px 12px', borderRadius: '99px', fontSize: '11.5px', fontWeight: '700',
              background: chain.valid ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
              color: chain.valid ? '#059669' : '#dc2626',
              border: `1px solid ${chain.valid ? '#05966944' : '#dc262644'}`,
            }}>
              {chain.valid
                ? <><CheckCircle size={12} /> Chain intact · {chain.total} entries</>
                : <><XCircle size={12} /> Broken at entry {chain.broken_at}</>
              }
            </div>
          )}

          {isAdmin && (
            <button
              onClick={handleVerify}
              disabled={verifying}
              style={{
                display: 'flex', alignItems: 'center', gap: '5px',
                background: 'var(--forensic-card-bg, #ffffff)', border: '1px solid var(--forensic-border, #cbd5e1)',
                color: 'var(--forensic-text-main, #0f172a)', borderRadius: '10px',
                padding: '6px 14px', cursor: 'pointer',
                fontSize: '12.5px', fontWeight: '600', fontFamily: 'inherit',
                opacity: verifying ? 0.6 : 1,
                boxShadow: '0 2px 6px rgba(0,0,0,0.03)',
              }}
            >
              <ShieldCheck size={13} style={{ color: 'var(--forensic-primary, #2563eb)' }} />
              {verifying ? 'Verifying…' : 'Verify chain'}
            </button>
          )}

          <button
            onClick={load}
            disabled={loading}
            style={{
              display: 'flex', alignItems: 'center', gap: '5px',
              background: 'var(--forensic-card-bg, #ffffff)', border: '1px solid var(--forensic-border, #cbd5e1)',
              color: 'var(--forensic-text-main, #0f172a)', borderRadius: '10px',
              padding: '6px 14px', cursor: 'pointer',
              fontSize: '12.5px', fontWeight: '600', fontFamily: 'inherit',
              boxShadow: '0 2px 6px rgba(0,0,0,0.03)',
            }}
          >
            <RefreshCw size={13} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
            Refresh
          </button>
        </div>
      </div>

      {/* Entries */}
      <div style={{ border: '1px solid var(--forensic-border, #e2e8f0)', borderRadius: '16px', overflow: 'hidden', background: 'var(--forensic-card-bg, #ffffff)', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
        {sorted.map((row, i) => {
          const color  = getActionColor(row.action)
          const isOpen = expanded === i
          return (
            <div
              key={row.id || i}
              style={{
                borderBottom: i < sorted.length - 1 ? '1px solid var(--forensic-border, #e2e8f0)' : 'none',
                background: i % 2 === 0 ? 'var(--forensic-card-bg, #ffffff)' : 'var(--forensic-panel-bg, #f8fafc)',
              }}
            >
              {/* Row header */}
              <div
                onClick={() => setExpanded(isOpen ? null : i)}
                style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 18px', cursor: 'pointer', transition: 'background 0.15s ease' }}
                onMouseEnter={e => e.currentTarget.style.background = 'rgba(99, 102, 241, 0.06)'}
                onMouseLeave={e => e.currentTarget.style.background = i % 2 === 0 ? 'var(--forensic-card-bg, #ffffff)' : 'var(--forensic-panel-bg, #f8fafc)'}
              >
                <ShieldCheck size={15} color={color} style={{ flexShrink: 0 }} />

                <span style={{
                  fontSize: '11.5px', fontFamily: 'monospace', fontWeight: '700',
                  color, whiteSpace: 'nowrap',
                  background: `${color}15`, border: `1px solid ${color}35`,
                  padding: '2px 8px', borderRadius: '6px',
                }}>
                  {row.action}
                </span>

                <span style={{ color: 'var(--forensic-text-main, #0f172a)', fontSize: '13px', fontWeight: '600', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {humanize(row.entity_type)}
                  {row.metadata?.filename && (
                    <span style={{ color: 'var(--forensic-text-muted, #64748b)', fontWeight: '500' }}> · {row.metadata.filename}</span>
                  )}
                </span>

                <span style={{ color: 'var(--forensic-text-muted, #64748b)', fontSize: '12px', flexShrink: 0 }}>
                  {formatDateTime(row.created_at)}
                </span>

                {isOpen
                  ? <ChevronUp size={15} style={{ color: 'var(--forensic-text-muted, #64748b)' }} />
                  : <ChevronDown size={15} style={{ color: 'var(--forensic-text-muted, #64748b)' }} />
                }
              </div>

              {isOpen && (
                <div style={{ padding: '10px 18px 14px 44px', display: 'flex', flexDirection: 'column', gap: '8px', background: 'var(--forensic-panel-bg, #f8fafc)' }}>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
                    <Hash size={12} style={{ color: 'var(--forensic-text-muted, #64748b)', marginTop: '2px', flexShrink: 0 }} />
                    <span style={{ fontSize: '11.5px', fontFamily: 'monospace', color: 'var(--forensic-text-muted, #64748b)', wordBreak: 'break-all' }}>
                      <span style={{ fontWeight: '700' }}>prev: </span>{row.prev_hash?.slice(0, 40)}…
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
                    <Hash size={12} style={{ color: 'var(--forensic-text-muted, #64748b)', marginTop: '2px', flexShrink: 0 }} />
                    <span style={{ fontSize: '11.5px', fontFamily: 'monospace', color: 'var(--forensic-text-muted, #64748b)', wordBreak: 'break-all' }}>
                      <span style={{ fontWeight: '700' }}>self: </span>{row.self_hash?.slice(0, 40)}…
                    </span>
                  </div>

                  {row.metadata && Object.keys(row.metadata).length > 0 && (
                    <pre style={{
                      background: 'var(--forensic-card-bg, #ffffff)', border: '1px solid var(--forensic-border, #e2e8f0)',
                      borderRadius: '8px',
                      padding: '10px 14px', fontSize: '11.5px', color: 'var(--forensic-text-main, #0f172a)',
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
