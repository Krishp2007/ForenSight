import { useState, useEffect } from 'react'
import { getCaseAuditLog } from '../../services/auditService'
import { formatDateTime, humanize } from '../../utils/formatters'
import Spinner from '../ui/Spinner'
import EmptyState from '../ui/EmptyState'
import { ShieldCheck, Hash, ChevronDown, ChevronUp } from 'lucide-react'

const ACTION_COLORS = {
  'case.create':      '#34d399',
  'case.update':      '#60a5fa',
  'evidence.upload':  '#fbbf24',
  'graph.clear':      '#fca5a5',
  'correlations.run': '#c4b5fd',
  'report.generate':  '#67e8f9',
}

const AuditTrail = ({ caseId }) => {
  const [rows, setRows]       = useState([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState(null)

  useEffect(() => {
    getCaseAuditLog(caseId, 200)
      .then(setRows).catch(() => {}).finally(() => setLoading(false))
  }, [caseId])

  if (loading) return <div style={{ display:'flex', justifyContent:'center', padding:'48px' }}><Spinner size="lg" /></div>
  if (!rows.length) return <EmptyState icon={ShieldCheck} title="No audit entries yet" description="Every case mutation is recorded here with a Merkle hash chain." />

  return (
    <div style={{ border:'1px solid #3d4f6a', borderRadius:'12px', overflow:'hidden', fontFamily:'-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif' }}>
      {[...rows].reverse().map((row, i) => {
        const color = ACTION_COLORS[row.action] || '#9aa8c0'
        const isOpen = expanded === i
        return (
          <div key={row.id || i} style={{ borderBottom: i < rows.length-1 ? '1px solid #2d3748' : 'none', background: i%2===0 ? '#1e2a3d' : '#253347' }}>
            <div
              onClick={() => setExpanded(isOpen ? null : i)}
              style={{ display:'flex', alignItems:'center', gap:'12px', padding:'10px 16px', cursor:'pointer', transition:'background 0.15s' }}
              onMouseEnter={e => e.currentTarget.style.background = '#2a3347'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              <ShieldCheck size={14} color={color} style={{ flexShrink:0 }} />
              <span style={{ fontSize:'12px', fontFamily:'monospace', fontWeight:'600', color, whiteSpace:'nowrap' }}>{row.action}</span>
              <span style={{ color:'#9aa8c0', fontSize:'12px', flex:1, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>
                {humanize(row.entity_type)} · {row.entity_id?.slice(-8)}
              </span>
              <span style={{ color:'#6b7fa3', fontSize:'11px', flexShrink:0 }}>{formatDateTime(row.created_at)}</span>
              {isOpen ? <ChevronUp size={13} color="#6b7fa3" /> : <ChevronDown size={13} color="#6b7fa3" />}
            </div>
            {isOpen && (
              <div style={{ padding:'8px 16px 12px 40px', display:'flex', flexDirection:'column', gap:'6px' }}>
                <div style={{ display:'flex', gap:'8px', alignItems:'flex-start' }}>
                  <Hash size={11} color="#3d4f6a" style={{ marginTop:'2px', flexShrink:0 }} />
                  <span style={{ fontSize:'11px', fontFamily:'monospace', color:'#4a5568', wordBreak:'break-all' }}>
                    <span style={{ color:'#3d4f6a' }}>prev: </span>{row.prev_hash?.slice(0,40)}…
                  </span>
                </div>
                <div style={{ display:'flex', gap:'8px', alignItems:'flex-start' }}>
                  <Hash size={11} color="#3d4f6a" style={{ marginTop:'2px', flexShrink:0 }} />
                  <span style={{ fontSize:'11px', fontFamily:'monospace', color:'#4a5568', wordBreak:'break-all' }}>
                    <span style={{ color:'#3d4f6a' }}>self: </span>{row.self_hash?.slice(0,40)}…
                  </span>
                </div>
                {row.metadata && Object.keys(row.metadata).length > 0 && (
                  <pre style={{ background:'#1a2234', borderRadius:'6px', padding:'8px 12px', fontSize:'11px', color:'#9aa8c0', overflowX:'auto', margin:'4px 0 0 0', fontFamily:'monospace' }}>
                    {JSON.stringify(row.metadata, null, 2)}
                  </pre>
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
export default AuditTrail
