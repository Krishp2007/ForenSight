import { useState } from 'react'
import {
  Copy, Check, ShieldAlert, FileText, Network, GitBranch,
  AlertTriangle, ExternalLink, Cpu, Globe
} from 'lucide-react'

// ── Minimal markdown renderer (no external deps) ──────────────────────────────
function renderMarkdown(text) {
  if (!text) return []

  const lines = text.split('\n')
  const elements = []
  let i = 0
  let key = 0

  while (i < lines.length) {
    const line = lines[i]

    // Code block fence
    if (line.startsWith('```')) {
      const lang = line.slice(3).trim() || 'text'
      const codeLines = []
      i++
      while (i < lines.length && !lines[i].startsWith('```')) {
        codeLines.push(lines[i])
        i++
      }
      elements.push(<CodeBlock key={key++} lang={lang} code={codeLines.join('\n')} />)
      i++
      continue
    }

    // Horizontal rule
    if (line.match(/^---+$/)) {
      elements.push(<hr key={key++} style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.08)', margin: '12px 0' }} />)
      i++
      continue
    }

    // Heading 1-3
    const h3m = line.match(/^###\s+(.+)/)
    const h2m = line.match(/^##\s+(.+)/)
    const h1m = line.match(/^#\s+(.+)/)
    if (h1m) { elements.push(<h3 key={key++} style={{ color: 'var(--forensic-text-main)', fontSize: '15px', fontWeight: 700, margin: '14px 0 6px' }}>{inlineRender(h1m[1])}</h3>); i++; continue }
    if (h2m) { elements.push(<h4 key={key++} style={{ color: 'var(--forensic-text-muted)', fontSize: '13.5px', fontWeight: 700, margin: '12px 0 5px' }}>{inlineRender(h2m[1])}</h4>); i++; continue }
    if (h3m) { elements.push(<h5 key={key++} style={{ color: 'var(--forensic-primary)', fontSize: '12.5px', fontWeight: 700, margin: '10px 0 4px' }}>{inlineRender(h3m[1])}</h5>); i++; continue }

    // Bullet list item
    const bulletMatch = line.match(/^[\-\*]\s+(.+)/)
    if (bulletMatch) {
      const items = []
      while (i < lines.length && lines[i].match(/^[\-\*]\s+/)) {
        const m = lines[i].match(/^[\-\*]\s+(.+)/)
        if (m) items.push(m[1])
        i++
      }
      elements.push(
        <ul key={key++} style={{ margin: '6px 0', paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '3px' }}>
          {items.map((item, idx) => (
            <li key={idx} style={{ color: 'var(--forensic-text-muted)', fontSize: '13px', lineHeight: '1.55' }}>{inlineRender(item)}</li>
          ))}
        </ul>
      )
      continue
    }

    // Numbered list
    const numMatch = line.match(/^\d+\.\s+(.+)/)
    if (numMatch) {
      const items = []
      while (i < lines.length && lines[i].match(/^\d+\.\s+/)) {
        const m = lines[i].match(/^\d+\.\s+(.+)/)
        if (m) items.push(m[1])
        i++
      }
      elements.push(
        <ol key={key++} style={{ margin: '6px 0', paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '3px' }}>
          {items.map((item, idx) => (
            <li key={idx} style={{ color: 'var(--forensic-text-muted)', fontSize: '13px', lineHeight: '1.55' }}>{inlineRender(item)}</li>
          ))}
        </ol>
      )
      continue
    }

    // Table (simple pipe-based)
    if (line.includes('|') && line.trim().startsWith('|')) {
      const tableLines = []
      while (i < lines.length && lines[i].includes('|')) {
        tableLines.push(lines[i])
        i++
      }
      elements.push(<TableBlock key={key++} lines={tableLines} />)
      continue
    }

    // Blockquote
    const bqm = line.match(/^>\s+(.+)/)
    if (bqm) {
      elements.push(
        <blockquote key={key++} style={{ margin: '6px 0', paddingLeft: '12px', borderLeft: `3px solid var(--forensic-primary)`, color: 'var(--forensic-text-muted)', fontSize: '12.5px', fontStyle: 'italic' }}>
          {inlineRender(bqm[1])}
        </blockquote>
      )
      i++
      continue
    }

    // Empty line
    if (!line.trim()) {
      elements.push(<div key={key++} style={{ height: '6px' }} />)
      i++
      continue
    }

    // Regular paragraph
    elements.push(
      <p key={key++} style={{ margin: '4px 0', color: 'var(--forensic-text-muted)', fontSize: '13px', lineHeight: '1.65' }}>{inlineRender(line)}</p>
    )
    i++
  }

  return elements
}

// Inline markdown: **bold**, *italic*, `code`, ~~strike~~
function inlineRender(text) {
  if (!text) return null
  const parts = []
  const regex = /(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`|~~(.+?)~~)/g
  let last = 0
  let match
  let k = 0
  while ((match = regex.exec(text)) !== null) {
    if (match.index > last) parts.push(<span key={k++}>{text.slice(last, match.index)}</span>)
    if (match[2]) parts.push(<strong key={k++} style={{ color: '#f1f5f9', fontWeight: 700 }}>{match[2]}</strong>)
    else if (match[3]) parts.push(<em key={k++} style={{ color: '#94a3b8' }}>{match[3]}</em>)
    else if (match[4]) parts.push(<code key={k++} style={{ background: 'rgba(99,102,241,0.15)', color: '#a5b4fc', padding: '1px 5px', borderRadius: '4px', fontSize: '11.5px', fontFamily: 'monospace' }}>{match[4]}</code>)
    else if (match[5]) parts.push(<s key={k++} style={{ color: '#64748b' }}>{match[5]}</s>)
    last = match.index + match[0].length
  }
  if (last < text.length) parts.push(<span key={k++}>{text.slice(last)}</span>)
  return parts.length > 0 ? parts : text
}

// Code block with copy button
function CodeBlock({ lang, code }) {
  const [copied, setCopied] = useState(false)
  const copy = () => {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <div style={{ margin: '8px 0', borderRadius: '10px', border: '1px solid rgba(99,102,241,0.2)', overflow: 'hidden' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 12px', background: 'rgba(15,23,42,0.9)', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
        <span style={{ fontSize: '10px', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>{lang}</span>
        <button onClick={copy} style={{ background: 'none', border: 'none', color: copied ? '#22c55e' : '#64748b', cursor: 'pointer', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px', padding: '2px 6px' }}>
          {copied ? <><Check size={11} /> Copied</> : <><Copy size={11} /> Copy</>}
        </button>
      </div>
      <pre style={{ margin: 0, padding: '12px 14px', background: 'rgba(5,8,17,0.95)', overflowX: 'auto', fontSize: '11.5px', lineHeight: '1.65', color: '#a5b4fc', fontFamily: 'ui-monospace, SFMono-Regular, monospace', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
        <code>{code}</code>
      </pre>
    </div>
  )
}

// Simple table renderer
function TableBlock({ lines }) {
  const rows = lines
    .filter(l => !l.match(/^\|[\s\-|]+\|$/))  // skip separator rows
    .map(l => l.split('|').filter(c => c.trim()).map(c => c.trim()))
  if (!rows.length) return null
  const [header, ...body] = rows
  return (
    <div style={{ overflowX: 'auto', margin: '8px 0' }}>
      <table style={{ borderCollapse: 'collapse', fontSize: '12px', width: '100%' }}>
        <thead>
          <tr>{header.map((h, i) => <th key={i} style={{ padding: '6px 10px', background: 'rgba(99,102,241,0.12)', color: '#a5b4fc', fontWeight: 700, borderBottom: '1px solid rgba(255,255,255,0.08)', textAlign: 'left', whiteSpace: 'nowrap' }}>{h}</th>)}</tr>
        </thead>
        <tbody>
          {body.map((row, ri) => (
            <tr key={ri} style={{ background: ri % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)' }}>
              {row.map((cell, ci) => <td key={ci} style={{ padding: '5px 10px', color: '#cbd5e1', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>{inlineRender(cell)}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── Source citation badges ─────────────────────────────────────────────────────
const SOURCE_ICON = {
  evidence_file:    FileText,
  event_log:        AlertTriangle,
  mitre_technique:  ShieldAlert,
  graph_correlation: GitBranch,
  neo4j_graph:      Network,
  database_count:   Cpu,
  case_metadata:    FileText,
  system_guide:     Globe,
  default:          FileText,
}

const SOURCE_COLOR = {
  evidence_file:    '#3b82f6',
  event_log:        '#f59e0b',
  mitre_technique:  '#ef4444',
  graph_correlation: '#8b5cf6',
  neo4j_graph:      '#8b5cf6',
  database_count:   '#10b981',
  case_metadata:    '#64748b',
  system_guide:     '#64748b',
  default:          '#64748b',
}

function SourceBadge({ source }) {
  const type = source.type || 'default'
  const Icon = SOURCE_ICON[type] || SOURCE_ICON.default
  const color = SOURCE_COLOR[type] || SOURCE_COLOR.default
  const label = source.source_file || source.mitre_id || source.name || 'Source'
  const sub = source.event_id ? `Event ${source.event_id}` : source.mitre_id ? source.tactic : null

  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: '5px',
      padding: '4px 10px', borderRadius: '6px',
      background: `${color}12`, border: `1px solid ${color}30`,
      fontSize: '10.5px', color, fontWeight: 600,
      maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
      cursor: 'default',
    }}
      title={`${label}${sub ? ` — ${sub}` : ''}`}
    >
      <Icon size={11} style={{ flexShrink: 0 }} />
      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{label}</span>
      {sub && <span style={{ opacity: 0.6, fontSize: '9.5px' }}>· {sub}</span>}
    </div>
  )
}

// ── Confidence badge ──────────────────────────────────────────────────────────
function ConfidenceBadge({ confidence }) {
  const conf = (confidence || 'High').replace('Insufficient Evidence', 'Low')
  const color = conf === 'High' ? '#22c55e' : conf === 'Medium' ? '#f59e0b' : '#ef4444'
  return (
    <span style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '99px', background: `${color}18`, color, border: `1px solid ${color}35`, fontWeight: 700 }}>
      {conf} Confidence
    </span>
  )
}

// ── Animated typing dots ──────────────────────────────────────────────────────
export function TypingDots() {
  return (
    <div style={{ display: 'flex', gap: '4px', alignItems: 'center', padding: '4px 0' }}>
      {[0, 1, 2].map(i => (
        <div key={i} style={{
          width: '6px', height: '6px', borderRadius: '50%', background: '#60a5fa',
          animation: `bounce 1.2s infinite`,
          animationDelay: `${i * 0.2}s`,
          opacity: 0.7,
        }} />
      ))}
      <style>{`@keyframes bounce { 0%,80%,100% { transform: scale(0.7); opacity: 0.5; } 40% { transform: scale(1); opacity: 1; } }`}</style>
    </div>
  )
}

// ── Main ChatMessage component ────────────────────────────────────────────────
const ChatMessage = ({
  role,
  content,
  confidence,
  sources = [],
  isStreaming = false,
  timestamp,
  onCopy,
  onRegenerate,
}) => {
  const [copied, setCopied] = useState(false)
  const isUser = role === 'user'

  const handleCopy = () => {
    navigator.clipboard.writeText(content || '')
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
    onCopy?.()
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: isUser ? 'flex-end' : 'flex-start',
      gap: '6px',
      animation: 'fadeSlideIn 0.2s ease-out',
    }}>
      <style>{`
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(6px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      {/* Message bubble */}
      <div style={{
        maxWidth: isUser ? '75%' : '95%',
        padding: isUser ? '10px 14px' : '14px 16px',
        borderRadius: isUser ? '14px 14px 4px 14px' : '4px 14px 14px 14px',
        background: isUser
          ? 'linear-gradient(135deg, #3b82f6, #2563eb)'
          : 'rgba(15, 23, 42, 0.85)',
        border: isUser ? 'none' : '1px solid rgba(255,255,255,0.07)',
        boxShadow: isUser
          ? '0 2px 12px rgba(59,130,246,0.3)'
          : '0 2px 8px rgba(0,0,0,0.3)',
        position: 'relative',
      }}>
        {isUser ? (
          <p style={{ margin: 0, color: '#fff', fontSize: '13.5px', lineHeight: '1.55' }}>{content}</p>
        ) : isStreaming && !content ? (
          <TypingDots />
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
            {renderMarkdown(content || '')}
            {isStreaming && (
              <span style={{
                display: 'inline-block', width: '2px', height: '16px',
                background: '#60a5fa', marginLeft: '2px', verticalAlign: 'text-bottom',
                animation: 'blink 0.8s infinite',
              }} />
            )}
            <style>{`@keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0; } }`}</style>
          </div>
        )}
      </div>

      {/* Assistant message footer: confidence + sources + actions */}
      {!isUser && !isStreaming && content && (
        <div style={{ maxWidth: '95%', display: 'flex', flexDirection: 'column', gap: '8px' }}>

          {/* Source citations */}
          {sources && sources.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
              <span style={{ fontSize: '10px', color: '#475569', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Evidence Used
              </span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
                {sources.map((src, i) => <SourceBadge key={i} source={src} />)}
              </div>
            </div>
          )}

          {/* Action row */}
          <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
            {/* Copy */}
            <button
              onClick={handleCopy}
              style={{
                background: 'none', border: '1px solid rgba(255,255,255,0.07)',
                color: copied ? '#22c55e' : 'var(--forensic-text-muted)', cursor: 'pointer', fontSize: '10.5px', padding: '3px 9px', borderRadius: '6px',
                display: 'flex', alignItems: 'center', gap: '4px',
                transition: 'all 0.15s', fontFamily: 'inherit',
              }}
              onMouseEnter={e => { e.currentTarget.style.color = '#94a3b8'; e.currentTarget.style.background = 'rgba(255,255,255,0.04)' }}
              onMouseLeave={e => { if (!copied) { e.currentTarget.style.color = '#64748b'; e.currentTarget.style.background = 'none' } }}
            >
              {copied ? <><Check size={11} /> Copied</> : <><Copy size={11} /> Copy</>}
            </button>

            {/* Regenerate */}
            {onRegenerate && (
              <button
                onClick={onRegenerate}
                style={{
                  background: 'none', border: '1px solid rgba(255,255,255,0.07)',
                  color: 'var(--forensic-text-muted)', cursor: 'pointer', fontSize: '10.5px', padding: '3px 9px', borderRadius: '6px',
                  display: 'flex', alignItems: 'center', gap: '4px',
                  transition: 'all 0.15s', fontFamily: 'inherit',
                }}
                onMouseEnter={e => { e.currentTarget.style.color = '#94a3b8'; e.currentTarget.style.background = 'rgba(255,255,255,0.04)' }}
                onMouseLeave={e => { e.currentTarget.style.color = '#64748b'; e.currentTarget.style.background = 'none' }}
              >
                ↺ Regenerate
              </button>
            )}

            {/* Timestamp */}
            {timestamp && (
              <span style={{ fontSize: '10px', color: 'var(--forensic-text-muted)', marginLeft: 'auto' }}>
                {new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default ChatMessage
