import { useState, useEffect, useCallback } from 'react'
import api from '../../services/api'
import { formatDateTime, humanize } from '../../utils/formatters'
import { Spinner, EmptyState } from '../ui'
import { ShieldCheck, Hash, ChevronDown, ChevronUp, RefreshCw, Copy, Check, Search, Lock } from 'lucide-react'

const getCaseAuditLog = (caseId, limit = 200) => api.get(`/cases/${caseId}/audit`, { params: { limit } }).then(r => r.data)

const ACTION_LABELS = {
  'case.create':           { label: 'Case Created', color: '#059669', icon: '📁', desc: 'Case record created in workspace.' },
  'case.update':           { label: 'Case Updated', color: '#2563eb', icon: '✏️', desc: 'Case parameters or metadata updated.' },
  'evidence.upload':       { label: 'Evidence Ingested', color: '#d97706', icon: '📥', desc: 'New evidence file parsed into case database.' },
  'evidence.reprocess':    { label: 'Evidence Reprocessed', color: '#ea580c', icon: '🔄', desc: 'Evidence re-parsed and resynchronized into graph nodes.' },
  'evidence.delete':       { label: 'Evidence Deleted', color: '#dc2626', icon: '🗑️', desc: 'Evidence file and derived logs purged from case.' },
  'graph.clear':           { label: 'Graph Cleared', color: '#dc2626', icon: '🧹', desc: 'Neo4j graph entities purged for rescan.' },
  'correlations.run':      { label: 'Correlations Executed', color: '#7c3aed', icon: '⚡', desc: 'Graph analytics and attack-path correlations executed.' },
  'report.generate':       { label: 'Report Generated', color: '#0284c7', icon: '📄', desc: 'Forensic PDF investigation report compiled.' },
  'report.export':         { label: 'Report Exported', color: '#0284c7', icon: '💾', desc: 'Investigation report downloaded or exported.' },
  'user.login':            { label: 'User Authenticated', color: '#16a34a', icon: '🔑', desc: 'Investigator logged into active session.' },
  'user.logout':           { label: 'User Logged Out', color: '#64748b', icon: '🚪', desc: 'Investigator session terminated.' },
}

const getActionInfo = (action) => {
  return ACTION_LABELS[action] || {
    label: humanize(action || 'action'),
    color: '#64748b',
    icon: '🛡️',
    desc: 'Audit event recorded in legal ledger.'
  }
}

const AuditTrail = ({ caseId }) => {
  const [rows,     setRows]     = useState([])
  const [loading,  setLoading]  = useState(true)
  const [error,    setError]    = useState(null)
  const [expanded, setExpanded] = useState(null)
  const [copiedHash, setCopiedHash] = useState(null)
  const [search, setSearch]     = useState('')

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

  const copyToClipboard = (text, key) => {
    navigator.clipboard.writeText(text)
    setCopiedHash(key)
    setTimeout(() => setCopiedHash(null), 2000)
  }

  const handleClearAuditLogs = async () => {
    if (!window.confirm('Are you sure you want to clear historical evidence audit logs for this case?')) return
    try {
      await api.delete(`/cases/${caseId}/audit`)
      await load()
    } catch (e) {
      setError(e?.response?.data?.detail || 'Failed to clear audit logs')
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

  const sorted = [...rows].sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  const filtered = sorted.filter(r => {
    if (!search.trim()) return true
    const q = search.toLowerCase()
    return (
      (r.action || '').toLowerCase().includes(q) ||
      (r.entity_type || '').toLowerCase().includes(q) ||
      (r.metadata?.filename || '').toLowerCase().includes(q) ||
      (r.actor_id || '').toLowerCase().includes(q) ||
      (r.self_hash || '').toLowerCase().includes(q)
    )
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', fontFamily: 'inherit' }}>

      {/* Cryptographic Ledger Explanation Banner */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.08) 0%, rgba(124, 58, 237, 0.08) 100%)',
        border: '1px solid rgba(37, 99, 235, 0.25)',
        borderRadius: '16px',
        padding: '16px 20px',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '14px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.02)'
      }}>
        <div style={{
          background: 'var(--forensic-primary, #2563eb)',
          color: '#ffffff',
          borderRadius: '10px',
          padding: '8px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0
        }}>
          <Lock size={18} />
        </div>
        <div style={{ flex: 1 }}>
          <h4 style={{ margin: '0 0 4px 0', fontSize: '14px', fontWeight: '700', color: 'var(--forensic-text-main, #0f172a)' }}>
            Tamper-Evident Cryptographic Chain of Custody
          </h4>
          <p style={{ margin: 0, fontSize: '12.5px', color: 'var(--forensic-text-muted, #475569)', lineHeight: '1.5' }}>
            Every action taken on evidence or cases is cryptographically signed using <strong>SHA-256 block hashing</strong>. Each entry's <code>self_hash</code> is mathematically bound to the previous record's <code>prev_hash</code>.
          </p>
        </div>
      </div>

      {/* Action Header & Search Controls */}
      <div style={{
        background: 'var(--forensic-card-bg, #ffffff)',
        border: '1px solid var(--forensic-border, #e2e8f0)',
        borderRadius: '16px',
        padding: '14px 18px',
        display: 'flex',
        alignItems: 'center',
        justify: 'space-between',
        flexWrap: 'wrap',
        gap: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.03)'
      }}>
        <div style={{ flex: 1, minWidth: '220px', position: 'relative', display: 'flex', alignItems: 'center' }}>
          <Search size={14} style={{ position: 'absolute', left: '12px', color: 'var(--forensic-text-muted, #64748b)' }} />
          <input
            type="text"
            placeholder="Search audit trail by action, filename, user, or hash..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px 8px 34px',
              borderRadius: '8px',
              border: '1px solid var(--forensic-border, #cbd5e1)',
              background: 'var(--forensic-panel-bg, #f8fafc)',
              color: 'var(--forensic-text-main, #0f172a)',
              fontSize: '12.5px',
              outline: 'none',
              fontFamily: 'inherit'
            }}
          />
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
          <button
            onClick={load}
            disabled={loading}
            style={{
              display: 'flex', alignItems: 'center', gap: '5px',
              background: 'var(--forensic-card-bg, #ffffff)', border: '1px solid var(--forensic-border, #cbd5e1)',
              color: 'var(--forensic-text-main, #0f172a)', borderRadius: '8px',
              padding: '7px 14px', cursor: 'pointer',
              fontSize: '12.5px', fontWeight: '600', fontFamily: 'inherit',
              boxShadow: '0 2px 6px rgba(0,0,0,0.03)',
            }}
          >
            <RefreshCw size={13} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
            Refresh
          </button>

          <button
            onClick={handleClearAuditLogs}
            style={{
              display: 'flex', alignItems: 'center', gap: '5px',
              background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#dc2626', borderRadius: '8px',
              padding: '7px 14px', cursor: 'pointer',
              fontSize: '12.5px', fontWeight: '600', fontFamily: 'inherit',
            }}
          >
            Clear Audit Logs
          </button>
        </div>
      </div>

      {/* Audit Log Entries List */}
      {!filtered.length ? (
        <EmptyState
          icon={ShieldCheck}
          title="No matching audit entries"
          description="No audit entries matched your active search query."
        />
      ) : (
        <div style={{ border: '1px solid var(--forensic-border, #e2e8f0)', borderRadius: '16px', overflow: 'hidden', background: 'var(--forensic-card-bg, #ffffff)', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
          {filtered.map((row, i) => {
            const info = getActionInfo(row.action)
            const isOpen = expanded === i
            return (
              <div
                key={row.id || i}
                style={{
                  borderBottom: i < filtered.length - 1 ? '1px solid var(--forensic-border, #e2e8f0)' : 'none',
                  background: i % 2 === 0 ? 'var(--forensic-card-bg, #ffffff)' : 'var(--forensic-panel-bg, #f8fafc)',
                }}
              >
                {/* Row Header */}
                <div
                  onClick={() => setExpanded(isOpen ? null : i)}
                  style={{ display: 'flex', alignItems: 'center', gap: '14px', padding: '14px 20px', cursor: 'pointer', transition: 'background 0.15s ease' }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(37, 99, 235, 0.04)'}
                  onMouseLeave={e => e.currentTarget.style.background = i % 2 === 0 ? 'var(--forensic-card-bg, #ffffff)' : 'var(--forensic-panel-bg, #f8fafc)'}
                >
                  <span style={{ fontSize: '16px', flexShrink: 0 }}>{info.icon}</span>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                      <span style={{
                        fontSize: '11.5px', fontWeight: '700',
                        color: info.color, background: `${info.color}15`, border: `1px solid ${info.color}35`,
                        padding: '2px 8px', borderRadius: '6px',
                      }}>
                        {info.label}
                      </span>

                      {row.metadata?.filename && (
                        <span style={{ color: 'var(--forensic-text-main, #0f172a)', fontSize: '13px', fontWeight: '700', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          📄 {row.metadata.filename}
                        </span>
                      )}

                      <span style={{ color: 'var(--forensic-text-muted, #64748b)', fontSize: '12px', fontWeight: '500' }}>
                        by User: <strong style={{ color: 'var(--forensic-text-main, #334155)' }}>{row.actor_name || row.actor_email || (row.actor_id ? `User (${row.actor_id.slice(-6)})` : 'System')}</strong>
                      </span>
                    </div>

                    <p style={{ margin: 0, fontSize: '12.5px', color: 'var(--forensic-text-muted, #64748b)', fontWeight: '500' }}>
                      {info.desc}
                    </p>
                  </div>

                  <span style={{ color: 'var(--forensic-text-muted, #64748b)', fontSize: '12px', fontFamily: 'monospace', fontWeight: '600', flexShrink: 0 }}>
                    {formatDateTime(row.created_at)}
                  </span>

                  {isOpen
                    ? <ChevronUp size={16} style={{ color: 'var(--forensic-text-muted, #64748b)' }} />
                    : <ChevronDown size={16} style={{ color: 'var(--forensic-text-muted, #64748b)' }} />
                  }
                </div>

                {/* Expanded Cryptographic Proof & Metadata Box */}
                {isOpen && (
                  <div style={{
                    padding: '16px 20px 18px 48px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '12px',
                    background: 'var(--forensic-panel-bg, #0f172a)',
                    color: '#e2e8f0',
                    borderTop: '1px solid var(--forensic-border, #1e293b)'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #1e293b', paddingBottom: '8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: '700', color: '#38bdf8' }}>
                        <Hash size={14} /> Cryptographic Proof (Merkle Chain Link)
                      </div>
                      <span style={{ fontSize: '11px', color: '#64748b', fontFamily: 'monospace' }}>Record ID: {row.id}</span>
                    </div>

                    {/* Hashes Grid */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '10px' }}>
                      {/* Previous Hash */}
                      <div style={{ background: '#1e293b', padding: '10px 12px', borderRadius: '8px', border: '1px solid #334155' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                          <span style={{ fontSize: '11px', color: '#94a3b8', fontWeight: '700' }}>🔗 PREVIOUS BLOCK HASH (prev_hash):</span>
                          <button
                            onClick={() => copyToClipboard(row.prev_hash, `prev_${i}`)}
                            style={{ background: 'none', border: 'none', color: '#38bdf8', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px' }}
                          >
                            {copiedHash === `prev_${i}` ? <Check size={12} color="#10b981" /> : <Copy size={12} />} Copy
                          </button>
                        </div>
                        <code style={{ fontSize: '11px', color: '#f59e0b', wordBreak: 'break-all', fontFamily: 'monospace' }}>
                          {row.prev_hash || '0'.repeat(64)}
                        </code>
                      </div>

                      {/* Self Hash */}
                      <div style={{ background: '#1e293b', padding: '10px 12px', borderRadius: '8px', border: '1px solid #334155' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                          <span style={{ fontSize: '11px', color: '#94a3b8', fontWeight: '700' }}>🔒 CURRENT BLOCK HASH (self_hash):</span>
                          <button
                            onClick={() => copyToClipboard(row.self_hash, `self_${i}`)}
                            style={{ background: 'none', border: 'none', color: '#38bdf8', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px' }}
                          >
                            {copiedHash === `self_${i}` ? <Check size={12} color="#10b981" /> : <Copy size={12} />} Copy
                          </button>
                        </div>
                        <code style={{ fontSize: '11px', color: '#10b981', wordBreak: 'break-all', fontFamily: 'monospace' }}>
                          {row.self_hash || '0'.repeat(64)}
                        </code>
                      </div>
                    </div>

                    {/* Action Context & Clean Metadata */}
                    {row.metadata && Object.keys(row.metadata).length > 0 && (() => {
                      const IGNORED_KEYS = ['case_id', 'org_id', 'organization_id', 'entity_id', '_id', 'created_by']
                      const cleanEntries = Object.entries(row.metadata).filter(([k, v]) => !IGNORED_KEYS.includes(k) && v !== null && v !== undefined)
                      
                      if (cleanEntries.length === 0) return null

                      return (
                        <div style={{ marginTop: '4px' }}>
                          <span style={{ fontSize: '11px', color: '#94a3b8', fontWeight: '700', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>
                            📋 Action Parameters & Log Context:
                          </span>

                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '8px' }}>
                            {cleanEntries.map(([k, v]) => {
                              let displayKey = humanize(k)
                              let displayVal = String(v)

                              if (k === 'total') {
                                displayKey = 'Events Ingested'
                                displayVal = `${v} events`
                              } else if (k === 'status') {
                                displayKey = 'Recorded Status'
                                displayVal = `${v} (snapshot)`
                              } else if (k === 'sha256') {
                                displayKey = 'File SHA-256'
                                displayVal = `${String(v).slice(0, 16)}...`
                              }

                              return (
                                <div key={k} style={{
                                  background: '#1e293b', border: '1px solid #334155', borderRadius: '6px',
                                  padding: '4px 10px', fontSize: '11.5px', display: 'flex', alignItems: 'center', gap: '6px'
                                }}>
                                  <span style={{ color: '#94a3b8', fontWeight: '600' }}>{displayKey}:</span>
                                  <span style={{ color: '#38bdf8', fontWeight: '700', fontFamily: 'monospace' }}>{displayVal}</span>
                                </div>
                              )
                            })}
                          </div>
                        </div>
                      )
                    })()}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

export default AuditTrail
