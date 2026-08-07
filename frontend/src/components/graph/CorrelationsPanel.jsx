import { useState, useEffect } from 'react'
import api from '../../services/api'
import { Spinner, EmptyState } from '../ui'
import { Link2, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react'
import { humanize } from '../../utils/formatters'

// Inlined from correlationService
const getCorrelations = (caseId) => api.get(`/cases/${caseId}/correlations`).then(r => r.data)
const runCorrelations = (caseId) => api.post(`/cases/${caseId}/correlations/run`).then(r => r.data)

const RULE_STYLES = {
  PROCESS_INITIATED_CONNECTION: { bg: 'rgba(37, 99, 235, 0.15)', color: '#2563eb' },
  REGISTRY_RUN_KEY_PERSISTENCE:  { bg: 'rgba(220, 38, 38, 0.15)',  color: '#dc2626' },
  PARENT_OF:                     { bg: 'rgba(124, 58, 237, 0.15)', color: '#7c3aed' },
}

const CorrelationsPanel = ({ caseId, evidenceCount }) => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [openRule, setOpenRule] = useState(null)
  const [error, setError] = useState(null)

  const load = async () => {
    if (evidenceCount === 0) {
      setLoading(false)
      setData({ correlations: [] })
      return
    }
    setLoading(true)
    try { setData(await getCorrelations(caseId)) }
    catch (e) { setError(e.response?.data?.detail || 'Failed to load correlations') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [caseId, evidenceCount])

  const handleRun = async () => {
    if (evidenceCount === 0) return
    setRunning(true); setError(null)
    try { await runCorrelations(caseId); await load() }
    catch (e) { setError(e.response?.data?.detail || 'Failed to run correlations') }
    finally { setRunning(false) }
  }

  const correlations = data?.correlations || data?.findings || []
  const groups = correlations.reduce((acc, c) => {
    const r = c.rule || c.type || 'UNKNOWN'
    acc[r] = acc[r] || []
    acc[r].push(c)
    return acc
  }, {})

  if (evidenceCount === 0) {
    return (
      <EmptyState
        icon={Link2}
        title="No Evidence Files Uploaded"
        description="Upload an evidence file (.pcapng, .sqlite, .csv) to detect process correlations and network relationships."
      />
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', fontFamily: 'inherit' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <p style={{ color: 'var(--forensic-text-muted, #64748b)', fontSize: '13px', margin: 0, fontWeight: '600' }}>{correlations.length} derived relationships</p>
        <button onClick={handleRun} disabled={running || evidenceCount === 0} style={{
          display: 'flex', alignItems: 'center', gap: '6px',
          padding: '8px 16px', background: 'var(--forensic-primary, #2563eb)', border: 'none',
          borderRadius: '10px', color: '#ffffff', fontSize: '12.5px', fontWeight: '700',
          cursor: running || evidenceCount === 0 ? 'not-allowed' : 'pointer', fontFamily: 'inherit',
          opacity: running || evidenceCount === 0 ? 0.6 : 1,
          boxShadow: '0 2px 8px rgba(37, 99, 235, 0.25)',
          transition: 'all 0.2s ease',
        }}>
          {running ? <Spinner size="sm" /> : <RefreshCw size={13} />}
          Re-run Rules
        </button>
      </div>

      {error && <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.35)', borderRadius: '10px', padding: '12px 16px', color: '#dc2626', fontSize: '13px', fontWeight: '500' }}>{error}</div>}

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '48px' }}><Spinner size="lg" /></div>
      ) : correlations.length === 0 ? (
        <EmptyState icon={Link2} title="No correlations yet" description="Click 'Re-run Rules' after parsing evidence to derive relationships." />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {Object.entries(groups).map(([rule, items]) => {
            const isOpen = openRule === rule
            const rs = RULE_STYLES[rule] || { bg: 'rgba(100, 116, 139, 0.15)', color: 'var(--forensic-text-muted, #64748b)' }
            return (
              <div key={rule} style={{
                border: '1px solid var(--forensic-border, #e2e8f0)',
                borderRadius: '16px',
                background: 'var(--forensic-card-bg, #ffffff)',
                overflow: 'hidden',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)',
              }}>
                <button onClick={() => setOpenRule(isOpen ? null : rule)} style={{
                  width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '14px 18px', background: 'var(--forensic-card-bg, #ffffff)', border: 'none', cursor: 'pointer', fontFamily: 'inherit',
                  transition: 'background 0.15s ease',
                }}
                onMouseEnter={e => e.currentTarget.style.background = 'var(--forensic-panel-bg, #f8fafc)'}
                onMouseLeave={e => e.currentTarget.style.background = 'var(--forensic-card-bg, #ffffff)'}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ padding: '4px 12px', borderRadius: '8px', fontSize: '11.5px', fontWeight: '700', background: rs.bg, color: rs.color, border: `1px solid ${rs.color}30` }}>
                      {humanize(rule.replace(/_/g, ' '))}
                    </span>
                    <span style={{ color: 'var(--forensic-text-muted, #64748b)', fontSize: '12.5px', fontWeight: '600' }}>{items.length} findings</span>
                    {(items[0]?.mitre || items[0]?.score) && (
                      <span style={{ fontSize: '11px', fontFamily: 'monospace', background: 'rgba(124, 58, 237, 0.12)', color: '#7c3aed', padding: '3px 8px', borderRadius: '6px', fontWeight: '600' }}>
                        {items[0]?.mitre || `Score ${items[0]?.score}`}
                      </span>
                    )}
                  </div>
                  {isOpen ? <ChevronUp size={16} style={{ color: 'var(--forensic-text-muted, #64748b)' }} /> : <ChevronDown size={16} style={{ color: 'var(--forensic-text-muted, #64748b)' }} />}
                </button>

                {isOpen && (
                  <div>
                    {items.slice(0, 50).map((c, i) => {
                      const displaySource = c.source || (c.chain ? c.chain[0] : null) || c.explanation?.substring(0, 60) || '—'
                      const displayTarget = c.target || (c.chain ? c.chain.slice(-1)[0] : null) || ''
                      const displayDetail = c.technique || c.severity || ''
                      return (
                        <div key={i} style={{
                          display: 'flex', alignItems: 'flex-start', gap: '8px',
                          padding: '10px 18px', fontSize: '12.5px',
                          borderTop: '1px solid var(--forensic-border, #e2e8f0)',
                          background: i % 2 === 0 ? 'var(--forensic-card-bg, #ffffff)' : 'var(--forensic-panel-bg, #f8fafc)',
                        }}
                        onMouseEnter={e => e.currentTarget.style.background = 'rgba(99, 102, 241, 0.06)'}
                        onMouseLeave={e => e.currentTarget.style.background = i % 2 === 0 ? 'var(--forensic-card-bg, #ffffff)' : 'var(--forensic-panel-bg, #f8fafc)'}>
                          {c.chain && c.chain.length > 0 ? (
                            <span style={{ color: 'var(--forensic-text-main, #0f172a)', flex: 1, fontWeight: '500' }}>
                              {c.chain.map((p, pi) => (
                                <span key={pi}>
                                  <span style={{ color: pi === 0 ? '#2563eb' : pi === c.chain.length - 1 ? '#059669' : 'var(--forensic-text-muted, #64748b)', fontWeight: '600' }}>{p}</span>
                                  {pi < c.chain.length - 1 && <span style={{ color: 'var(--forensic-border, #cbd5e1)', margin: '0 6px' }}>→</span>}
                                </span>
                              ))}
                            </span>
                          ) : (
                            <>
                              <span style={{ color: '#2563eb', fontWeight: '600', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '220px' }}>{displaySource}</span>
                              {displayTarget && (
                                <>
                                  <span style={{ color: 'var(--forensic-border, #cbd5e1)', flexShrink: 0 }}>→</span>
                                  <span style={{ color: '#059669', fontWeight: '600', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '220px' }}>{displayTarget}</span>
                                </>
                              )}
                            </>
                          )}
                          {c.score && (
                            <span style={{ marginLeft: 'auto', fontSize: '11.5px', color: c.score >= 80 ? '#dc2626' : c.score >= 60 ? '#d97706' : 'var(--forensic-text-muted, #64748b)', flexShrink: 0, fontWeight: 700 }}>
                              Score: {c.score}
                            </span>
                          )}
                          {!c.score && displayDetail && (
                            <span style={{ marginLeft: 'auto', color: 'var(--forensic-text-muted, #64748b)', fontSize: '11.5px', flexShrink: 0 }}>{displayDetail}</span>
                          )}
                        </div>
                      )
                    })}
                    {items.length > 50 && (
                      <p style={{ padding: '10px 18px', color: 'var(--forensic-text-muted, #64748b)', fontSize: '12px', margin: 0, borderTop: '1px solid var(--forensic-border, #e2e8f0)', background: 'var(--forensic-panel-bg, #f8fafc)' }}>
                        …and {items.length - 50} more
                      </p>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
export default CorrelationsPanel
