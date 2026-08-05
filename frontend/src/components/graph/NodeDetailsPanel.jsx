import { useState, useEffect } from 'react'
import { X, ShieldAlert, Cpu, User, HardDrive, Globe, Key, Wrench,
         FileText, Activity, Network, Maximize2, AlertTriangle, Clipboard, Check, Map } from 'lucide-react'

const ICON_MAP = {
  Process:      Cpu,
  User:         User,
  Host:         HardDrive,
  File:         FileText,
  IPAddress:    Network,
  Domain:       Globe,
  RegistryKey:  Key,
  Service:      Wrench,
  BrowserVisit: Globe,
  Evidence:     FileText,
  default:      Activity,
}

const RISK_COLOR = {
  critical: '#ef4444',
  high:     '#f97316',
  medium:   '#eab308',
  low:      '#22c55e',
  info:     '#64748b',
}

function RiskBadge({ score, is_anomaly }) {
  if (is_anomaly)    return <Tag color={RISK_COLOR.critical} label={`Suspicious Anomaly · ${(score||0).toFixed(2)}`} />
  if (score > 0.75)  return <Tag color={RISK_COLOR.high}     label={`High Risk · ${score.toFixed(2)}`} />
  if (score > 0.5)   return <Tag color={RISK_COLOR.medium}   label={`Medium Risk · ${score.toFixed(2)}`} />
  return <Tag color={RISK_COLOR.low} label="Low Risk" />
}

function Tag({ color, label }) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '4px 10px', borderRadius: 99, fontSize: 10.5, fontWeight: 700, background: `${color}15`, border: `1px solid ${color}45`, color }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: color }} />
      {label}
    </span>
  )
}

function Prop({ label, value, mono }) {
  if (value === undefined || value === null || value === '') return null
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 3, width: '100%' }}>
      <span style={{ fontSize: 9.5, color: '#475569', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.6px' }}>{label}</span>
      {mono
        ? <pre style={{ margin: 0, padding: '6px 8px', background: 'rgba(0,0,0,0.45)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: 6, fontSize: 11, color: '#a5b4fc', whiteSpace: 'pre-wrap', wordBreak: 'break-all', maxHeight: 110, overflow: 'auto', fontFamily: 'var(--font-mono, monospace)' }}>{String(value)}</pre>
        : <span style={{ fontSize: 12.5, color: '#cbd5e1', wordBreak: 'break-word' }}>{String(value)}</span>
      }
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 12, marginTop: 12, display: 'flex', flexDirection: 'column', gap: 9, width: '100%' }}>
      <span style={{ fontSize: 10, color: '#818cf8', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.8px' }}>{title}</span>
      {children}
    </div>
  )
}

const NodeDetailsPanel = ({ node, onClose, onExpandNeighbors, onSetPathNode }) => {
  const [copied, setCopied] = useState(false)
  const [neighborFocused, setNeighborFocused] = useState(false)

  // Reset toggle when the selected node changes
  useEffect(() => { setNeighborFocused(false) }, [node?.id])

  if (!node) return null

  const type  = node.type || 'Entity'
  const Icon  = ICON_MAP[type] || ICON_MAP.default
  const props = node.properties || {}
  const score = node.anomaly_score || props.anomaly_score || 0
  const isAnomaly = node.is_anomaly || props.is_anomaly || false
  const sev = (node.severity || props.severity || 'info').toLowerCase()
  const sevColor = RISK_COLOR[sev] || RISK_COLOR.info

  const mitre = node.mitre_attack || props.mitre_attack || []
  const explanation = node.explanation || props.explanation || ""

  const handleCopy = () => {
    const textParts = [
      `Node Label: ${node.label || node.id}`,
      `Node Type: ${type}`,
      `Risk Level: ${sev.toUpperCase()}`,
      `Anomaly Score: ${score}`,
      `Suspicious: ${node.suspicious ? 'Yes' : 'No'}`,
      `MITRE Mappings: ${mitre.map(m => `${m.id} (${m.name})`).join(', ') || 'None'}`
    ]

    Object.entries(props).forEach(([key, val]) => {
      if (typeof val !== 'object' && val) {
        textParts.push(`${key}: ${val}`)
      }
    })

    navigator.clipboard.writeText(textParts.join('\n'))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div style={{
      position: 'absolute', top: 12, right: 12, width: 340,
      maxHeight: 'calc(100% - 24px)', overflowY: 'auto',
      background: 'rgba(9, 13, 26, 0.96)', backdropFilter: 'blur(24px)',
      border: '1px solid rgba(255,255,255,0.08)', borderRadius: 16,
      padding: 18, color: '#e2e8f0',
      boxShadow: '0 24px 48px rgba(0,0,0,0.65), 0 0 0 1px rgba(255,255,255,0.04)',
      zIndex: 25,
      display: 'flex',
      flexDirection: 'column',
      gap: 12
    }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ padding: 8, borderRadius: 10, background: 'rgba(99,102,241,0.15)', color: '#818cf8', border: '1px solid rgba(99,102,241,0.25)', flexShrink: 0 }}>
            <Icon size={18} />
          </div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: '#fff', lineHeight: '1.3', wordBreak: 'break-word', maxWidth: 220 }}>
              {node.label || node.id}
              {node.suspicious && (
                <span style={{ marginLeft: 6, fontSize: 9.5, background: 'rgba(239,68,68,0.2)', color: '#f87171', border: '1px solid rgba(239,68,68,0.45)', borderRadius: 4, padding: '1px 5px', verticalAlign: 'middle', fontWeight: 800 }}>SUSPICIOUS</span>
              )}
            </div>
            <div style={{ fontSize: 10.5, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.6px', marginTop: 2 }}>{type}</div>
          </div>
        </div>
        <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#475569', cursor: 'pointer', padding: 4, flexShrink: 0 }}><X size={16} /></button>
      </div>

      {/* Risk badges */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
        <RiskBadge score={score} is_anomaly={isAnomaly} />
        {sev !== 'info' && <Tag color={sevColor} label={sev.charAt(0).toUpperCase() + sev.slice(1)} />}
      </div>

      {/* AI Forensic Explanation */}
      {explanation && (
        <Section title="AI Suspicious Analysis">
          <div style={{ padding: '10px 12px', background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 10, color: '#cbd5e1', fontSize: 12, lineHeight: 1.45, fontStyle: 'italic' }}>
            {explanation}
          </div>
        </Section>
      )}

      {/* MITRE ATT&CK Mappings */}
      {mitre.length > 0 && (
        <Section title="MITRE ATT&CK Mapping">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {mitre.map((m, idx) => (
              <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: 2, padding: '8px 10px', background: 'rgba(234,179,8,0.05)', border: '1px solid rgba(234,179,8,0.2)', borderRadius: 8 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: '#facc15' }}>{m.id}</span>
                  <span style={{ fontSize: 10, color: '#64748b', fontWeight: 600 }}>{m.tactic}</span>
                </div>
                <span style={{ fontSize: 11.5, color: '#e2e8f0' }}>{m.name}</span>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Per-type details */}
      <Section title="Properties">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {type === 'Process' && <>
            <Prop label="Process Name" value={props.process_name || node.label} />
            <Prop label="PID" value={props.pid} />
            <Prop label="Command Line" value={props.command_line} mono />
            <Prop label="Hash (SHA256)" value={props.hash} mono />
            <Prop label="Host ID" value={props.host_id} />
          </>}

          {type === 'User' && <>
            <Prop label="Username" value={props.username || node.label} />
            <Prop label="Domain" value={props.domain} />
          </>}

          {type === 'Host' && <>
            <Prop label="Hostname" value={props.hostname || node.label} />
            <Prop label="Host ID" value={props.host_id} />
          </>}

          {type === 'IPAddress' && <>
            <Prop label="IP Address" value={props.address || node.label} />
            <Prop label="Visibility" value={props.is_private ? 'Internal (Private RFC1918)' : 'External (Internet)'} />
          </>}

          {type === 'Domain' && <>
            <Prop label="Domain" value={props.domain_name || node.label} />
          </>}

          {type === 'File' && <>
            <Prop label="Filename" value={props.filename || node.label} />
            <Prop label="Path" value={props.filepath || props.path} />
            <Prop label="SHA256" value={props.sha256} mono />
          </>}

          {type === 'RegistryKey' && <>
            <Prop label="Registry Path" value={props.path || node.label} mono />
          </>}

          {type === 'Service' && <>
            <Prop label="Service Name" value={props.service_name || node.label} />
          </>}

          {type === 'BrowserVisit' && <>
            <Prop label="URL" value={props.url || node.label} mono />
            <Prop label="Title" value={props.title} />
            <Prop label="Visit Count" value={props.visit_count} />
          </>}
        </div>
      </Section>

      {/* Provenance */}
      <Section title="Evidence Provenance">
        <Prop label="Evidence File" value={props.source_file || props.evidence_id} />
        <Prop label="Timestamp" value={props.timestamp} />
      </Section>

      {/* Actions */}
      <Section title="Investigation Actions">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 4 }}>
          {onExpandNeighbors && (
            <button
              onClick={() => {
                onExpandNeighbors(node, neighborFocused)
                setNeighborFocused(f => !f)
              }}
              style={{
                width: '100%', padding: '9px', borderRadius: 10,
                background: neighborFocused
                  ? 'linear-gradient(135deg, rgba(239,68,68,0.25), rgba(220,38,38,0.2))'
                  : 'linear-gradient(135deg, rgba(59,130,246,0.2), rgba(99,102,241,0.2))',
                color: neighborFocused ? '#fca5a5' : '#93c5fd',
                border: neighborFocused ? '1px solid rgba(239,68,68,0.4)' : '1px solid rgba(59,130,246,0.3)',
                fontWeight: 600, fontSize: 12.5, cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 7,
                fontFamily: 'inherit', transition: 'all 0.2s',
              }}
            >
              <Maximize2 size={13} />
              {neighborFocused ? 'Cancel Focus Neighborhood' : 'Focus Neighborhood'}
            </button>
          )}

          {onSetPathNode && (
            <div style={{ display: 'flex', gap: 6 }}>
              <button
                onClick={() => onSetPathNode('source', node.id)}
                style={{ flex: 1, padding: '7px 8px', borderRadius: 8, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: '#cbd5e1', fontSize: 11, cursor: 'pointer', fontFamily: 'inherit', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}
              >
                <Map size={11} /> Start Node
              </button>
              <button
                onClick={() => onSetPathNode('target', node.id)}
                style={{ flex: 1, padding: '7px 8px', borderRadius: 8, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: '#cbd5e1', fontSize: 11, cursor: 'pointer', fontFamily: 'inherit', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}
              >
                <Map size={11} /> End Node
              </button>
            </div>
          )}

          <button
            onClick={handleCopy}
            style={{ width: '100%', padding: '8px', borderRadius: 8, background: 'transparent', border: '1px solid rgba(255,255,255,0.08)', color: '#94a3b8', fontSize: 11.5, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, fontFamily: 'inherit', transition: 'all 0.15s' }}
          >
            {copied ? <><Check size={12} style={{ color: '#22c55e' }} /> Copied!</> : <><Clipboard size={12} /> Copy Node Details</>}
          </button>
        </div>
      </Section>
    </div>
  )
}

export default NodeDetailsPanel
