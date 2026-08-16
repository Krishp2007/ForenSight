import { useState, useEffect } from 'react'
import api from '../../services/api'
import { Spinner, EmptyState } from '../ui'
import { Link2, RefreshCw, ChevronDown, ChevronUp, ShieldAlert, ArrowRight, Activity, Terminal, Database, Globe } from 'lucide-react'

const getCorrelations = (caseId) => api.get(`/cases/${caseId}/correlations`).then(r => r.data)
const runCorrelations = (caseId) => api.post(`/cases/${caseId}/correlations/run`).then(r => r.data)

const RULE_META = {
  ATTACK_PATH: {
    label: 'End-to-End Attack Paths',
    icon: Activity,
    bg: 'rgba(239, 68, 68, 0.12)', color: '#ef4444', border: 'rgba(239, 68, 68, 0.3)',
    desc: 'Correlated multi-stage attack lineage linking User ➔ Process ➔ Network Connection ➔ Port.'
  },
  PROCESS_CHAIN: {
    label: 'Process Lineage Chains',
    icon: Terminal,
    bg: 'rgba(168, 85, 247, 0.12)', color: '#a855f7', border: 'rgba(168, 85, 247, 0.3)',
    desc: 'Parent-child process execution trees (e.g., Office macro spawning PowerShell or CMD).'
  },
  CROSS_EVIDENCE_CORRELATION: {
    label: 'Cross-Evidence Corroboration',
    icon: ShieldAlert,
    bg: 'rgba(16, 185, 129, 0.12)', color: '#10b981', border: 'rgba(16, 185, 129, 0.3)',
    desc: 'Multi-vector verification matching Event Log activity with raw PCAP packet captures.'
  },
  SUSPICIOUS_LOLBIN_EXECUTION: {
    label: 'Suspicious Living-off-the-Land (LOLBin)',
    icon: Terminal,
    bg: 'rgba(245, 158, 11, 0.12)', color: '#f59e0b', border: 'rgba(245, 158, 11, 0.3)',
    desc: 'Execution of legitimate system binaries (PowerShell, Certutil, Mshta) with suspicious flags.'
  },
  REGISTRY_RUN_KEY_PERSISTENCE: {
    label: 'Registry Persistence Modifications',
    icon: Database,
    bg: 'rgba(236, 72, 153, 0.12)', color: '#ec4899', border: 'rgba(236, 72, 153, 0.3)',
    desc: 'Autostart registry keys or system service modifications establishing persistent access.'
  },
  DOMAIN_RESOLUTION: {
    label: 'C2 Domain & DNS Resolutions',
    icon: Globe,
    bg: 'rgba(59, 130, 246, 0.12)', color: '#3b82f6', border: 'rgba(59, 130, 246, 0.3)',
    desc: 'Outbound DNS queries and external domain communications.'
  },
}

const formatVal = (v, fallback = 'System') => {
  if (!v || String(v).trim().toLowerCase() === 'none' || String(v).trim().toLowerCase() === 'null') {
    return fallback
  }
  return v
}

const ScoreBadge = ({ score }) => {
  const isHigh = score >= 80
  const isMed  = score >= 60
  const color  = isHigh ? '#ef4444' : isMed ? '#f59e0b' : '#3b82f6'
  const bg     = isHigh ? 'rgba(239, 68, 68, 0.12)' : isMed ? 'rgba(245, 158, 11, 0.12)' : 'rgba(59, 130, 246, 0.12)'
  const border = isHigh ? 'rgba(239, 68, 68, 0.3)' : isMed ? 'rgba(245, 158, 11, 0.3)' : 'rgba(59, 130, 246, 0.3)'

  return (
    <span style={{
      padding: '3px 9px', borderRadius: '6px', fontSize: '11.5px', fontWeight: '700',
      background: bg, color: color, border: `1px solid ${border}`, fontFamily: 'monospace'
    }}>
      Threat Score: {score}
    </span>
  )
}

const CorrelationsPanel = ({ caseId, evidenceCount }) => {
  const [data, setData]         = useState(null)
  const [loading, setLoading]   = useState(true)
  const [running, setRunning]   = useState(false)
  const [openRule, setOpenRule] = useState(null)
  const [error, setError]       = useState(null)

  const load = async () => {
    if (evidenceCount === 0) {
      setLoading(false)
      setData({ correlations: [] })
      return
    }
    setLoading(true)
    try {
      const res = await getCorrelations(caseId)
      setData(res)
      // Auto-open first group if available
      const findings = res?.correlations || res?.findings || []
      if (findings.length > 0) {
        const firstRule = findings[0].rule || findings[0].type || 'UNKNOWN'
        setOpenRule(firstRule)
      }
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load correlations')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [caseId, evidenceCount])

  const handleRun = async () => {
    if (evidenceCount === 0) return
    setRunning(true); setError(null)
    try {
      await runCorrelations(caseId)
      await load()
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to run correlation analysis')
    } finally {
      setRunning(false)
    }
  }

  const correlations = data?.correlations || data?.findings || []

  // Group by Rule Type
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
        description="Upload an evidence file (.evtx, .pcapng, .sqlite) to run relationship correlation rules."
      />
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', fontFamily: 'inherit' }}>
      {/* Top Header Controls */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h3 style={{ color: 'var(--forensic-text-main, #0f172a)', fontSize: '16px', fontWeight: '700', margin: '0 0 2px 0' }}>
            Automated Forensic Correlations
          </h3>
          <p style={{ color: 'var(--forensic-text-muted, #64748b)', fontSize: '12.5px', margin: 0 }}>
            Derived {correlations.length} attack path pattern{correlations.length !== 1 ? 's' : ''} across active evidence logs.
          </p>
        </div>

        <button
          onClick={handleRun}
          disabled={running || evidenceCount === 0}
          style={{
            display: 'flex', alignItems: 'center', gap: '6px',
            padding: '8px 16px', background: 'var(--forensic-primary, #2563eb)', border: 'none',
            borderRadius: '10px', color: '#ffffff', fontSize: '12.5px', fontWeight: '700',
            cursor: running || evidenceCount === 0 ? 'not-allowed' : 'pointer', fontFamily: 'inherit',
            opacity: running || evidenceCount === 0 ? 0.6 : 1,
            boxShadow: '0 2px 8px rgba(37, 99, 235, 0.25)',
            transition: 'all 0.2s ease',
          }}
        >
          {running ? <Spinner size="sm" /> : <RefreshCw size={13} />}
          {running ? 'Analyzing Graphs…' : 'Re-run Correlation Rules'}
        </button>
      </div>

      {error && (
        <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.35)', borderRadius: '10px', padding: '12px 16px', color: '#dc2626', fontSize: '13px', fontWeight: '500' }}>
          {error}
        </div>
      )}

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '48px' }}><Spinner size="lg" /></div>
      ) : correlations.length === 0 ? (
        <EmptyState
          icon={Link2}
          title="No Derived Correlations Found"
          description="Click 'Re-run Correlation Rules' to analyze event relationships and detect threat patterns across evidence."
        />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {Object.entries(groups).map(([ruleKey, items]) => {
            const isOpen = openRule === ruleKey
            const meta   = RULE_META[ruleKey] || {
              label: ruleKey.replace(/_/g, ' '),
              icon: Link2,
              bg: 'rgba(100, 116, 139, 0.12)', color: 'var(--forensic-text-muted, #64748b)', border: 'rgba(100, 116, 139, 0.3)',
              desc: 'Derived forensic relationship pattern.'
            }
            const IconComp = meta.icon || Link2
            const maxScore = Math.max(...items.map(i => i.score || 0))

            return (
              <div key={ruleKey} style={{
                border: `1px solid ${isOpen ? meta.border : 'var(--forensic-border, #e2e8f0)'}`,
                borderRadius: '16px',
                background: 'var(--forensic-card-bg, #ffffff)',
                overflow: 'hidden',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)',
                transition: 'border-color 0.2s ease'
              }}>
                {/* Accordion Group Title Bar */}
                <button
                  onClick={() => setOpenRule(isOpen ? null : ruleKey)}
                  style={{
                    width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '16px 20px', background: 'var(--forensic-card-bg, #ffffff)', border: 'none',
                    cursor: 'pointer', fontFamily: 'inherit', textTransform: 'none', textAlign: 'left',
                    transition: 'background 0.15s ease', gap: '12px'
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--forensic-panel-bg, #f8fafc)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'var(--forensic-card-bg, #ffffff)'}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1, minWidth: 0 }}>
                    <div style={{
                      padding: '8px', borderRadius: '10px', background: meta.bg, border: `1px solid ${meta.border}`,
                      color: meta.color, display: 'flex', flexShrink: 0
                    }}>
                      <IconComp size={18} />
                    </div>

                    <div style={{ overflow: 'hidden' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                        <span style={{ color: 'var(--forensic-text-main, #0f172a)', fontSize: '14.5px', fontWeight: '700' }}>
                          {meta.label}
                        </span>
                        <span style={{ padding: '2px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: '700', background: 'var(--forensic-panel-bg, #f1f5f9)', color: 'var(--forensic-text-muted, #64748b)' }}>
                          {items.length} finding{items.length !== 1 ? 's' : ''}
                        </span>
                      </div>
                      <p style={{ color: 'var(--forensic-text-muted, #64748b)', fontSize: '12px', margin: '2px 0 0 0', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                        {meta.desc}
                      </p>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexShrink: 0 }}>
                    <ScoreBadge score={maxScore} />
                    {isOpen ? <ChevronUp size={18} style={{ color: 'var(--forensic-text-muted, #64748b)' }} /> : <ChevronDown size={18} style={{ color: 'var(--forensic-text-muted, #64748b)' }} />}
                  </div>
                </button>

                {/* Group Findings Breakdown */}
                {isOpen && (
                  <div style={{ borderTop: '1px solid var(--forensic-border, #e2e8f0)', background: 'var(--forensic-panel-bg, #f8fafc)', padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {items.map((c, idx) => {
                      const sourceStr = formatVal(c.source, 'Parent / Origin Entity')
                      const targetStr = formatVal(c.target, 'Child / Destination')

                      return (
                        <div key={idx} style={{
                          background: 'var(--forensic-card-bg, #ffffff)',
                          border: '1px solid var(--forensic-border, #e2e8f0)',
                          borderRadius: '12px',
                          padding: '14px 16px',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '8px',
                          boxShadow: '0 1px 3px rgba(0,0,0,0.03)'
                        }}>
                          {/* Top Line: Source -> Target or Process Chain */}
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
                            {c.chain && c.chain.length > 0 ? (
                              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap', fontSize: '13px' }}>
                                <span style={{ color: 'var(--forensic-text-muted, #64748b)', fontSize: '11px', fontWeight: '700', textTransform: 'uppercase' }}>Lineage:</span>
                                {c.chain.map((p, pi) => (
                                  <span key={pi} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <span style={{
                                      fontFamily: 'monospace', fontWeight: '700', fontSize: '12.5px',
                                      color: pi === 0 ? '#2563eb' : pi === c.chain.length - 1 ? '#ef4444' : '#059669',
                                      background: 'var(--forensic-panel-bg, #f1f5f9)', padding: '2px 7px', borderRadius: '6px'
                                    }}>
                                      {p}
                                    </span>
                                    {pi < c.chain.length - 1 && <ArrowRight size={13} style={{ color: 'var(--forensic-text-muted, #94a3b8)' }} />}
                                  </span>
                                ))}
                              </div>
                            ) : (
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', fontWeight: '600' }}>
                                <span style={{ color: '#2563eb', fontFamily: 'monospace', background: 'rgba(37,99,235,0.08)', padding: '2px 8px', borderRadius: '6px' }}>
                                  {sourceStr}
                                </span>
                                <ArrowRight size={14} style={{ color: 'var(--forensic-text-muted, #94a3b8)' }} />
                                <span style={{ color: '#059669', fontFamily: 'monospace', background: 'rgba(16,185,129,0.08)', padding: '2px 8px', borderRadius: '6px' }}>
                                  {targetStr}
                                </span>
                              </div>
                            )}

                            {c.score && <ScoreBadge score={c.score} />}
                          </div>

                          {/* Explanation Sentence */}
                          {c.explanation && (
                            <p style={{ color: 'var(--forensic-text-main, #1e293b)', fontSize: '13px', margin: 0, fontWeight: '500', lineHeight: '1.4' }}>
                              {c.explanation}
                            </p>
                          )}

                          {/* Derived Evidence Reasons */}
                          {c.reasons && c.reasons.length > 0 && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '2px' }}>
                              {c.reasons.map((r, ri) => (
                                <div key={ri} style={{ display: 'flex', alignItems: 'flex-start', gap: '6px', color: 'var(--forensic-text-muted, #64748b)', fontSize: '12px' }}>
                                  <span style={{ color: 'var(--forensic-primary, #2563eb)', fontWeight: 'bold' }}>•</span>
                                  <span>{r}</span>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )
                    })}
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
