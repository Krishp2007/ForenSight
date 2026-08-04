import { useState, useEffect } from 'react'
import api from '../../services/api'
import { Spinner, EmptyState } from '../ui'
import { Link2, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react'
import { humanize } from '../../utils/formatters'

// Inlined from correlationService
const getCorrelations = (caseId) => api.get(`/cases/${caseId}/correlations`).then(r => r.data)
const runCorrelations = (caseId) => api.post(`/cases/${caseId}/correlations/run`).then(r => r.data)

const RULE_STYLES = {
  PROCESS_INITIATED_CONNECTION: { bg: 'rgba(74,127,232,0.2)', color: '#93c5fd' },
  REGISTRY_RUN_KEY_PERSISTENCE:  { bg: 'rgba(239,68,68,0.2)',  color: '#fca5a5' },
  PARENT_OF:                     { bg: 'rgba(167,139,250,0.2)', color: '#c4b5fd' },
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

  const correlations = data?.correlations || []
  const groups = correlations.reduce((acc, c) => {
    const r = c.rule || 'UNKNOWN'; acc[r] = acc[r] || []; acc[r].push(c); return acc
  }, {})

  if (evidenceCount === 0) {
    return (
      <EmptyState
        icon={Link2}
        title="No Evidence Files Uploaded"
        description="Upload an evidence file (.evtx, .pcapng, .sqlite, .csv) to detect process correlations and network relationships."
      />
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <p style={{ color: '#9aa8c0', fontSize: '13px', margin: 0 }}>{correlations.length} derived relationships from 3 Cypher rules</p>
        <button onClick={handleRun} disabled={running || evidenceCount === 0} style={{
          display: 'flex', alignItems: 'center', gap: '6px',
          padding: '6px 12px', background: '#4a7fe8', border: 'none',
          borderRadius: '7px', color: '#fff', fontSize: '12px', fontWeight: '500',
          cursor: running || evidenceCount === 0 ? 'not-allowed' : 'pointer', fontFamily: 'inherit',
          opacity: running || evidenceCount === 0 ? 0.6 : 1,
        }}>
          {running ? <Spinner size="sm" /> : <RefreshCw size={13} />}
          Re-run Rules
        </button>
      </div>

      {error && <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.35)', borderRadius: '8px', padding: '10px 14px', color: '#fca5a5', fontSize: '12px' }}>{error}</div>}

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '48px' }}><Spinner size="lg" /></div>
      ) : correlations.length === 0 ? (
        <EmptyState icon={Link2} title="No correlations yet" description="Click 'Re-run Rules' after parsing evidence to derive relationships." />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {Object.entries(groups).map(([rule, items]) => {
            const isOpen = openRule === rule
            const rs = RULE_STYLES[rule] || { bg: 'rgba(107,127,163,0.2)', color: '#9aa8c0' }
            return (
              <div key={rule} style={{ border: '1px solid #3d4f6a', borderRadius: '10px', overflow: 'hidden' }}>
                <button onClick={() => setOpenRule(isOpen ? null : rule)} style={{
                  width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '12px 16px', background: '#253347', border: 'none', cursor: 'pointer', fontFamily: 'inherit',
                  transition: 'background 0.15s',
                }}
                onMouseEnter={e => e.currentTarget.style.background = '#2a3347'}
                onMouseLeave={e => e.currentTarget.style.background = '#253347'}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ padding: '3px 10px', borderRadius: '6px', fontSize: '11px', fontWeight: '600', background: rs.bg, color: rs.color }}>
                      {humanize(rule.replace(/_/g, ' '))}
                    </span>
                    <span style={{ color: '#6b7fa3', fontSize: '12px' }}>{items.length} relationships</span>
                    {items[0]?.mitre && (
                      <span style={{ fontSize: '11px', fontFamily: 'monospace', background: 'rgba(167,139,250,0.15)', color: '#c4b5fd', padding: '2px 7px', borderRadius: '4px' }}>
                        {items[0].mitre}
                      </span>
                    )}
                  </div>
                  {isOpen ? <ChevronUp size={14} color="#6b7fa3" /> : <ChevronDown size={14} color="#6b7fa3" />}
                </button>

                {isOpen && (
                  <div>
                    {items.slice(0, 50).map((c, i) => (
                      <div key={i} style={{
                        display: 'flex', alignItems: 'center', gap: '8px',
                        padding: '8px 16px', fontSize: '12px',
                        borderTop: '1px solid #2d3748',
                        background: i % 2 === 0 ? '#1e2a3d' : '#253347',
                      }}
                      onMouseEnter={e => e.currentTarget.style.background = '#2a3347'}
                      onMouseLeave={e => e.currentTarget.style.background = i % 2 === 0 ? '#1e2a3d' : '#253347'}>
                        <span style={{ color: '#60a5fa', fontWeight: '500', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '200px' }}>{c.source}</span>
                        <span style={{ color: '#3d4f6a', flexShrink: 0 }}>→</span>
                        <span style={{ color: '#6ee7b7', fontWeight: '500', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '200px' }}>{c.target}</span>
                        {c.technique && <span style={{ marginLeft: 'auto', color: '#6b7fa3', fontSize: '11px', flexShrink: 0 }}>{c.technique}</span>}
                      </div>
                    ))}
                    {items.length > 50 && (
                      <p style={{ padding: '8px 16px', color: '#6b7fa3', fontSize: '11px', margin: 0, borderTop: '1px solid #2d3748', background: '#1e2a3d' }}>
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
