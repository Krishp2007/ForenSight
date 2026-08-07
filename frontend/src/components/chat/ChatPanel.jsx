import { useState, useRef, useEffect, useCallback } from 'react'
import { Send, Bot, Trash2, Square, Search, RotateCcw, ChevronRight } from 'lucide-react'
import { streamCopilot, searchEvents } from '../../services/copilotService'
import ChatMessage, { TypingDots } from './ChatMessage'

// ── Suggested follow-up questions ────────────────────────────────────────────
const SUGGESTIONS = [
  { label: '📋 Summarize Case', q: 'Summarize this investigation case and key findings.' },
  { label: '⚠️ Anomalies', q: 'What anomalies were detected by the ML model?' },
  { label: '🔴 Suspicious Processes', q: 'Show all suspicious processes and why they were flagged.' },
  { label: '🌐 Network Connections', q: 'List all outbound network connections and IP addresses.' },
  { label: '🔑 Registry Persistence', q: 'Show registry modifications and persistence mechanisms.' },
  { label: '👤 User Logins', q: 'Which users logged in and from where?' },
  { label: '🗓️ Attack Timeline', q: 'Show the attack timeline in chronological order.' },
  { label: '📄 Incident Report', q: 'Generate a full incident response report for this case.' },
]

// ── Storage helpers ────────────────────────────────────────────────────────────
function loadHistory(caseId) {
  try {
    const saved = localStorage.getItem(`forensight_chat_${caseId}`)
    return saved ? JSON.parse(saved) : []
  } catch { return [] }
}

function saveHistory(caseId, messages) {
  try {
    // Store max 40 messages to prevent quota issues
    localStorage.setItem(`forensight_chat_${caseId}`, JSON.stringify(messages.slice(-40)))
  } catch (e) {
    console.warn('Chat history persist failed:', e)
  }
}

// ── Main ChatPanel Component ──────────────────────────────────────────────────
const ChatPanel = ({ caseId }) => {
  const [messages, setMessages]       = useState(() => loadHistory(caseId))
  const [input, setInput]             = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [mode, setMode]               = useState('copilot')
  const [streamingId, setStreamingId] = useState(null)  // message index being streamed

  const bottomRef    = useRef(null)
  const inputRef     = useRef(null)
  const abortRef     = useRef(null)   // AbortController for active stream
  const messagesRef  = useRef(messages)

  // Keep ref in sync for use inside closures
  messagesRef.current = messages

  // ── Reload history on case change ─────────────────────────────────────────
  useEffect(() => {
    const hist = loadHistory(caseId)
    setMessages(hist)
    setIsStreaming(false)
    setStreamingId(null)
    abortRef.current?.abort()
    inputRef.current?.focus()
  }, [caseId])

  // ── Persist history on message change ─────────────────────────────────────
  useEffect(() => {
    if (caseId) saveHistory(caseId, messages)
  }, [messages, caseId])

  // ── Auto-scroll ────────────────────────────────────────────────────────────
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isStreaming])

  // ── Global keyboard focus ─────────────────────────────────────────────────
  useEffect(() => {
    inputRef.current?.focus()
    const handleKey = (e) => {
      if (['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName)) return
      if (e.ctrlKey || e.altKey || e.metaKey || e.key === 'Tab' || e.key === 'Escape') return
      if (e.key.length === 1 || e.key === 'Backspace') inputRef.current?.focus()
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [])

  // ── Stop generation ───────────────────────────────────────────────────────
  const stopGeneration = () => {
    abortRef.current?.abort()
    abortRef.current = null
    setIsStreaming(false)
    setStreamingId(null)
  }

  // ── Clear chat ────────────────────────────────────────────────────────────
  const clearChat = () => {
    stopGeneration()
    setMessages([])
    if (caseId) localStorage.removeItem(`forensight_chat_${caseId}`)
  }

  // ── Core send logic ───────────────────────────────────────────────────────
  const send = useCallback(async (text) => {
    const q = (text || input).trim()
    if (!q || isStreaming) return
    setInput('')

    const userMsg = { role: 'user', content: q, timestamp: Date.now() }

    // ── Semantic search mode ───────────────────────────────────────────────
    if (mode === 'search') {
      setMessages(m => [...m, userMsg])
      setIsStreaming(true)
      try {
        const results = await searchEvents(caseId, q, 5)
        if (!results.length) {
          setMessages(m => [...m, {
            role: 'assistant',
            content: `No matching events found in the FAISS vector index for **"${q}"**. Try a broader search term.`,
            confidence: 'Low',
            sources: [],
            timestamp: Date.now(),
          }])
        } else {
          const items = results.map((ev, i) =>
            `${i + 1}. **${ev.event_type || 'Event'}** (\`${(ev.severity || 'info').toUpperCase()}\`) — *${new Date(ev.timestamp).toLocaleString()}*\n   \`${ev.subject || 'System'}\` → *${ev.action || 'acted'}* → \`${ev.object || 'Target'}\``
          ).join('\n\n')
          setMessages(m => [...m, {
            role: 'assistant',
            content: `**Semantic Search Results for "${q}":**\n\n${items}`,
            confidence: 'High',
            sources: results.slice(0, 3).map(ev => ({ type: 'event_log', source_file: ev.evidence_file || 'log', event_type: ev.event_type || '' })),
            timestamp: Date.now(),
          }])
        }
      } catch (e) {
        setMessages(m => [...m, { role: 'assistant', content: `⚠️ Search error: ${e.message}`, confidence: 'Low', sources: [], timestamp: Date.now() }])
      } finally {
        setIsStreaming(false)
      }
      return
    }

    // ── AI Copilot streaming mode ──────────────────────────────────────────
    // Build history for context (exclude streaming placeholder)
    const historyForApi = messagesRef.current
      .filter(m => m.role && m.content && !m._streaming)
      .slice(-10)
      .map(m => ({ role: m.role, content: m.content }))

    setMessages(m => [...m, userMsg])

    // Add streaming placeholder
    const streamIdx = messagesRef.current.length + 1
    setMessages(m => [...m, { role: 'assistant', content: '', sources: [], confidence: '', _streaming: true, timestamp: Date.now() }])
    setIsStreaming(true)
    setStreamingId(streamIdx)

    let accumulated = ''
    let finalSources = []
    let finalConfidence = 'High'

    const controller = streamCopilot(
      caseId,
      q,
      historyForApi,
      // onToken
      (chunk) => {
        accumulated += chunk
        setMessages(m => m.map((msg, idx) =>
          idx === streamIdx
            ? { ...msg, content: accumulated, _streaming: true }
            : msg
        ))
      },
      // onSources
      (srcs) => {
        finalSources = srcs
      },
      // onDone
      (conf) => {
        finalConfidence = conf || 'High'
        setMessages(m => m.map((msg, idx) =>
          idx === streamIdx
            ? { ...msg, content: accumulated, sources: finalSources, confidence: finalConfidence, _streaming: false }
            : msg
        ))
        setIsStreaming(false)
        setStreamingId(null)
        abortRef.current = null
      },
      // onError
      (errMsg) => {
        setMessages(m => m.map((msg, idx) =>
          idx === streamIdx
            ? { ...msg, content: errMsg || 'Sorry, I couldn\'t generate a response at this time. Please try again.', sources: [], confidence: 'Low', _streaming: false }
            : msg
        ))
        setIsStreaming(false)
        setStreamingId(null)
        abortRef.current = null
      },
    )

    abortRef.current = controller
  }, [caseId, input, isStreaming, mode])

  // ── Regenerate last response ───────────────────────────────────────────────
  const regenerate = useCallback(() => {
    // Find last user message
    const msgs = messagesRef.current
    let lastUserQ = null
    for (let i = msgs.length - 1; i >= 0; i--) {
      if (msgs[i].role === 'user') { lastUserQ = msgs[i].content; break }
    }
    if (!lastUserQ) return

    // Remove last assistant message and re-send
    setMessages(m => {
      const copy = [...m]
      for (let i = copy.length - 1; i >= 0; i--) {
        if (copy[i].role === 'assistant') { copy.splice(i, 1); break }
      }
      return copy
    })
    setTimeout(() => send(lastUserQ), 50)
  }, [send])

  const canSend = input.trim().length > 0 && !isStreaming

  return (
    <div style={{
      display: 'flex', flexDirection: 'column',
      height: '680px', maxHeight: 'calc(100vh - 120px)',
      background: 'var(--forensic-panel-bg, #070c1a)',
      borderRadius: '16px',
      border: '1px solid var(--forensic-border, rgba(255,255,255,0.08))',
      overflow: 'hidden',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      boxShadow: '0 20px 60px rgba(0,0,0,0.25)',
    }}>

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div style={{
        flexShrink: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '13px 18px',
        borderBottom: '1px solid var(--forensic-border, rgba(255,255,255,0.07))',
        background: 'var(--forensic-card-bg, #ffffff)',
        backdropFilter: 'blur(12px)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: 36, height: 36, borderRadius: '10px',
            background: 'linear-gradient(135deg, rgba(99,102,241,0.25), rgba(59,130,246,0.2))',
            border: '1px solid rgba(99,102,241,0.35)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Bot size={18} color="#818cf8" />
          </div>
          <div>
            <div style={{ fontSize: '13.5px', fontWeight: 700, color: 'var(--forensic-text-main, #0f172a)' }}>ForenSight Copilot</div>
            {isStreaming && (
              <div style={{ fontSize: '10.5px', color: '#22c55e', marginTop: '1px' }}>
                ● Generating response…
              </div>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {/* Mode toggle */}
          <div style={{ display: 'flex', border: '1px solid var(--forensic-border, #e2e8f0)', borderRadius: '8px', overflow: 'hidden' }}>
            {[
              { id: 'copilot', label: 'AI Copilot' },
              { id: 'search',  label: '🔍 Search'  },
            ].map(m => (
              <button key={m.id} onClick={() => setMode(m.id)} style={{
                padding: '5px 12px', fontSize: '11px', fontWeight: 600, border: 'none',
                background: mode === m.id ? '#3b82f6' : 'transparent',
                color: mode === m.id ? '#fff' : 'var(--forensic-text-muted, #64748b)',
                cursor: 'pointer', fontFamily: 'inherit', transition: 'all 0.15s',
              }}>
                {m.label}
              </button>
            ))}
          </div>

          {/* Clear */}
          {messages.length > 0 && !isStreaming && (
            <button onClick={clearChat} title="Clear Chat" style={{
              background: 'none', border: '1px solid var(--forensic-border, #e2e8f0)',
              color: 'var(--forensic-text-muted, #64748b)', cursor: 'pointer',
              padding: '5px 8px', borderRadius: '7px',
              display: 'flex', alignItems: 'center', gap: '4px',
              fontSize: '11px', transition: 'all 0.15s', fontFamily: 'inherit',
            }}
              onMouseEnter={e => { e.currentTarget.style.color = '#ef4444'; e.currentTarget.style.borderColor = 'rgba(239,68,68,0.3)' }}
              onMouseLeave={e => { e.currentTarget.style.color = 'var(--forensic-text-muted, #64748b)'; e.currentTarget.style.borderColor = 'var(--forensic-border, #e2e8f0)' }}
            >
              <Trash2 size={12} />
            </button>
          )}
        </div>
      </div>

      {/* ── Messages area ──────────────────────────────────────────────────── */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px 20px 8px', display: 'flex', flexDirection: 'column', gap: '16px', background: 'var(--forensic-bg-dark, #050a14)' }}>

        {/* Empty state */}
        {messages.length === 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '14px', marginTop: '28px', paddingBottom: '8px' }}>
            <div style={{
              width: 52, height: 52, borderRadius: '14px',
              background: 'rgba(99,102,241,0.12)',
              border: '1px solid rgba(99,102,241,0.25)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Bot size={26} color="#818cf8" />
            </div>
            <div style={{ textAlign: 'center' }}>
              <h4 style={{ color: 'var(--forensic-text-main, #0f172a)', fontSize: '15px', fontWeight: 700, margin: '0 0 6px' }}>ForenSight AI Investigation Assistant</h4>
              <p style={{ color: 'var(--forensic-text-muted, #64748b)', fontSize: '12.5px', margin: 0, maxWidth: '380px', lineHeight: '1.55' }}>
                Ask any question about the current case — evidence files, suspicious processes, network activity, anomalies, or attack timelines.
              </p>
            </div>

            {/* Quick-start suggestion grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '7px', width: '100%', maxWidth: '500px', marginTop: '6px' }}>
              {SUGGESTIONS.slice(0, 4).map(s => (
                <button
                  key={s.q}
                  onClick={() => send(s.q)}
                  style={{
                    padding: '9px 12px', textAlign: 'left',
                    background: 'var(--forensic-panel-bg, #f8fafc)',
                    border: '1px solid var(--forensic-border, #e2e8f0)',
                    borderRadius: '10px', color: 'var(--forensic-text-muted, #64748b)',
                    fontSize: '11.5px', fontWeight: 500,
                    cursor: 'pointer', fontFamily: 'inherit',
                    transition: 'all 0.15s', lineHeight: '1.4',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = 'rgba(99,102,241,0.4)'; e.currentTarget.style.color = 'var(--forensic-text-main, #0f172a)' }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--forensic-border, #e2e8f0)'; e.currentTarget.style.color = 'var(--forensic-text-muted, #64748b)' }}
                >
                  {s.label}
                  <div style={{ fontSize: '10px', color: 'var(--forensic-text-muted, #64748b)', opacity: 0.7, marginTop: '2px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {s.q.slice(0, 42)}…
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Message list */}
        {messages.map((m, i) => (
          <ChatMessage
            key={i}
            role={m.role}
            content={m.content}
            confidence={m.confidence}
            sources={m.sources}
            isStreaming={m._streaming || false}
            timestamp={m.timestamp}
            onRegenerate={
              !isStreaming && i === messages.length - 1 && m.role === 'assistant'
                ? regenerate
                : null
            }
          />
        ))}

        <div ref={bottomRef} />
      </div>

      {/* ── Suggestion pills (after first message) ───────────────────────── */}
      {messages.length > 0 && !isStreaming && (
        <div style={{
          flexShrink: 0, padding: '8px 16px 4px',
          display: 'flex', gap: '6px', overflowX: 'auto',
          scrollbarWidth: 'none',
        }}>
          {SUGGESTIONS.map(s => (
            <button
              key={s.q}
              onClick={() => send(s.q)}
              style={{
                flexShrink: 0,
                fontSize: '11px', fontWeight: 600,
                padding: '5px 11px',
                background: 'var(--forensic-panel-bg, #f8fafc)',
                border: '1px solid var(--forensic-border, #e2e8f0)',
                borderRadius: '20px', color: 'var(--forensic-text-muted, #64748b)',
                cursor: 'pointer', fontFamily: 'inherit',
                transition: 'all 0.15s', whiteSpace: 'nowrap',
              }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = 'rgba(99,102,241,0.4)'; e.currentTarget.style.background = 'rgba(99,102,241,0.08)'; e.currentTarget.style.color = '#6366f1' }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--forensic-border, #e2e8f0)'; e.currentTarget.style.background = 'var(--forensic-panel-bg, #f8fafc)'; e.currentTarget.style.color = 'var(--forensic-text-muted, #64748b)' }}
            >
              {s.label}
            </button>
          ))}
        </div>
      )}

      {/* ── Input row ──────────────────────────────────────────────────────── */}
      <div style={{
        flexShrink: 0,
        borderTop: '1px solid var(--forensic-border, #e2e8f0)',
        padding: '10px 14px 12px',
        background: 'var(--forensic-card-bg, #ffffff)',
        display: 'flex', alignItems: 'flex-end', gap: '8px',
      }}>
        {mode === 'search' && <Search size={14} color="var(--forensic-text-muted, #64748b)" style={{ flexShrink: 0, marginBottom: '11px' }} />}

        <textarea
          ref={inputRef}
          value={input}
          onChange={e => {
            setInput(e.target.value)
            e.target.style.height = 'auto'
            e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
          }}
          onKeyDown={e => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              send()
            }
          }}
          placeholder={
            isStreaming
              ? 'Generating response…'
              : mode === 'search'
              ? 'Semantic event search — enter keywords or description…'
              : 'Ask about evidence, processes, IPs, anomalies, attack chain… (Enter to send, Shift+Enter for newline)'
          }
          disabled={isStreaming}
          rows={1}
          style={{
            flex: 1,
            resize: 'none',
            background: 'var(--forensic-panel-bg, #f8fafc)',
            border: '1px solid var(--forensic-border, #e2e8f0)',
            borderRadius: '12px',
            color: isStreaming ? 'var(--forensic-text-muted, #94a3b8)' : 'var(--forensic-text-main, #0f172a)',
            fontSize: '13px',
            padding: '10px 14px',
            outline: 'none',
            fontFamily: 'inherit',
            lineHeight: '1.5',
            minHeight: '42px',
            maxHeight: '120px',
            transition: 'border-color 0.15s',
            scrollbarWidth: 'thin',
          }}
          onFocus={e => { e.target.style.borderColor = 'rgba(99,102,241,0.5)' }}
          onBlur={e => { e.target.style.borderColor = 'var(--forensic-border, #e2e8f0)' }}
        />

        {/* Stop / Send button */}
        {isStreaming ? (
          <button
            onClick={stopGeneration}
            title="Stop generation"
            style={{
              flexShrink: 0,
              width: 40, height: 40, borderRadius: '10px',
              background: 'rgba(239,68,68,0.15)',
              border: '1px solid rgba(239,68,68,0.35)',
              color: '#f87171', cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              transition: 'all 0.15s',
            }}
            onMouseEnter={e => { e.currentTarget.style.background = 'rgba(239,68,68,0.25)' }}
            onMouseLeave={e => { e.currentTarget.style.background = 'rgba(239,68,68,0.15)' }}
          >
            <Square size={14} />
          </button>
        ) : (
          <button
            onClick={() => send()}
            disabled={!canSend}
            title="Send (Enter)"
            style={{
              flexShrink: 0,
              width: 40, height: 40, borderRadius: '10px',
              background: canSend
                ? 'linear-gradient(135deg, #3b82f6, #2563eb)'
                : 'var(--forensic-border, #e2e8f0)',
              border: 'none',
              color: canSend ? '#fff' : 'var(--forensic-text-muted, #94a3b8)',
              cursor: canSend ? 'pointer' : 'not-allowed',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              transition: 'all 0.15s',
              boxShadow: canSend ? '0 2px 12px rgba(59,130,246,0.35)' : 'none',
            }}
            onMouseEnter={e => { if (canSend) e.currentTarget.style.transform = 'translateY(-1px)' }}
            onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)' }}
          >
            <Send size={15} />
          </button>
        )}
      </div>
    </div>
  )
}

export default ChatPanel
