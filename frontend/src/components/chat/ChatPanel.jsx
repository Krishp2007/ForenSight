import { useState, useRef, useEffect } from 'react'
import api from '../../services/api'
import ChatMessage from './ChatMessage'
import { Spinner } from '../ui'
import { Send, Search, Bot, Trash2 } from 'lucide-react'

// Inlined from chatService + similarityService
const askCopilot   = (caseId, question, history = []) => api.post(`/cases/${caseId}/copilot`, { question, history }).then(r => r.data)
const searchEvents = (caseId, query, limit = 10) => api.get(`/cases/${caseId}/search`, { params: { query, limit } }).then(r => r.data)

const SUGGESTIONS = [
  'Summarize Timeline',
  'Check Persistence',
  'Anomalous Processes',
  'Net Connections',
]

const ChatPanel = ({ caseId }) => {
  // Load persisted chat history for this specific case
  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem(`forensight_chat_${caseId}`)
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  })
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState('copilot')
  const [cooldown, setCooldown] = useState(0)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  // Auto-focus input field on mount and whenever user starts typing on keyboard
  useEffect(() => {
    inputRef.current?.focus()

    const handleGlobalKeyDown = (e) => {
      if (['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName)) return
      if (e.ctrlKey || e.altKey || e.metaKey || e.key === 'Tab' || e.key === 'Escape') return

      if (e.key.length === 1 || e.key === 'Backspace') {
        inputRef.current?.focus()
      }
    }

    window.addEventListener('keydown', handleGlobalKeyDown)
    return () => window.removeEventListener('keydown', handleGlobalKeyDown)
  }, [])

  // Rate limit cooldown countdown timer (4s safety window for 15 RPM limit)
  useEffect(() => {
    if (cooldown <= 0) return
    const timer = setInterval(() => {
      setCooldown(c => Math.max(0, c - 1))
    }, 1000)
    return () => clearInterval(timer)
  }, [cooldown])

  // Reload history if caseId changes
  useEffect(() => {
    try {
      const saved = localStorage.getItem(`forensight_chat_${caseId}`)
      setMessages(saved ? JSON.parse(saved) : [])
      inputRef.current?.focus()
    } catch {
      setMessages([])
    }
  }, [caseId])

  // Persist messages to localStorage whenever messages change
  useEffect(() => {
    if (caseId) {
      try {
        localStorage.setItem(`forensight_chat_${caseId}`, JSON.stringify(messages))
      } catch (e) {
        console.error('Failed to persist chat messages:', e)
      }
    }
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, caseId])

  const clearChat = () => {
    setMessages([])
    if (caseId) {
      localStorage.removeItem(`forensight_chat_${caseId}`)
    }
  }

  const send = async (text) => {
    const q = text || input.trim()
    if (!q || loading || cooldown > 0) return
    setInput('')
    setMessages(m => [...m, { role: 'user', content: q }])
    setLoading(true)
    setCooldown(1) // 1-second safety cooldown between questions
    try {
      if (mode === 'search') {
        const results = await searchEvents(caseId, q, 5)
        if (results.length === 0) {
          setMessages(m => [...m, { role: 'assistant', content: `Hello! I performed a semantic search across your case logs for **"${q}"**, but did not find matching events in the vector index.` }])
        } else {
          const intro = `Hello! Based on a semantic vector search for **"${q}"**, here are the top matching events from your case logs:\n\n`
          const items = results.map((ev, i) =>
            `${i+1}. **${ev.event_type || 'Event'}** (\`${(ev.severity || 'info').toUpperCase()}\`) — *${new Date(ev.timestamp).toLocaleString()}*\n   \`${ev.subject || 'System'}\` → *${ev.action || 'acted'}* → \`${ev.object || 'Target'}\``
          ).join('\n\n')
          setMessages(m => [...m, { role: 'assistant', content: intro + items + '\n\nLet me know if you would like me to analyze any of these specific log entries!' }])
        }
      } else {
        const res = await askCopilot(caseId, q, messages)
        setMessages(m => [...m, {
          role: 'assistant',
          content: res.analysis,
          confidence: res.confidence || 'High',
          sources: res.sources || []
        }])
      }
    } catch (e) {
      setMessages(m => [...m, { role: 'assistant', content: `⚠️ Error: ${e.response?.data?.detail || e.message}` }])
    } finally { setLoading(false) }
  }

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', height: '620px', maxHeight: 'calc(100vh - 140px)',
      background: '#0f172a', borderRadius: '14px',
      border: '1px solid rgba(255, 255, 255, 0.1)', overflow: 'hidden',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
    }}>
      {/* Fixed Top Header */}
      <div style={{
        flexShrink: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '14px 18px', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', background: '#1e293b',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#ffffff', fontSize: '13px', fontWeight: '700' }}>
          <Bot size={18} color="#60a5fa" />
          ForenSight Copilot
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {messages.length > 0 && (
            <button
              onClick={clearChat}
              title="Clear Chat History"
              style={{
                background: 'transparent', border: 'none', color: '#94a3b8',
                cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px',
                fontSize: '11px', padding: '4px 8px', borderRadius: '6px',
                transition: 'all 0.15s',
              }}
              onMouseEnter={e => { e.currentTarget.style.color = '#ef4444'; e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)' }}
              onMouseLeave={e => { e.currentTarget.style.color = '#94a3b8'; e.currentTarget.style.background = 'transparent' }}
            >
              <Trash2 size={13} />
              Clear
            </button>
          )}
          <div style={{ display: 'flex', border: '1px solid rgba(255, 255, 255, 0.12)', borderRadius: '8px', overflow: 'hidden' }}>
            {['copilot', 'search'].map(m => (
              <button key={m} onClick={() => setMode(m)} style={{
                padding: '5px 12px', fontSize: '11px', fontWeight: '600', border: 'none',
                background: mode === m ? '#3b82f6' : 'transparent',
                color: mode === m ? '#ffffff' : '#94a3b8',
                cursor: 'pointer', fontFamily: 'inherit', textTransform: 'capitalize',
                transition: 'background 0.15s',
              }}>
                {m === 'copilot' ? 'AI Copilot' : 'Semantic Search'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Scrollable Messages Container (Inside the Box) */}
      <div style={{ flex: 1, overflowY: 'auto', overflowX: 'hidden', padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {messages.length === 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px', marginTop: '36px' }}>
            <div style={{
              width: '44px', height: '44px', borderRadius: '12px',
              background: 'rgba(96, 165, 250, 0.15)', border: '1px solid rgba(96, 165, 250, 0.3)',
              display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <Bot size={24} color="#60a5fa" />
            </div>
            <h4 style={{ color: '#f8fafc', fontSize: '15px', fontWeight: '700', margin: 0 }}>ForenSight AI Assistant</h4>
            <p style={{ color: '#94a3b8', fontSize: '13px', margin: 0, textAlign: 'center', maxWidth: '420px' }}>
              Ask a question about case evidence, anomaly clusters, graph correlations, or select a quick action below.
            </p>
          </div>
        )}
        {messages.map((m, i) => (
          <ChatMessage
            key={i}
            role={m.role}
            content={m.content}
            confidence={m.confidence}
            sources={m.sources}
          />
        ))}
        {loading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div style={{ background: 'rgba(15, 23, 42, 0.85)', border: '1px solid rgba(96, 165, 250, 0.3)', borderRadius: '12px', padding: '10px 16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Spinner size="sm" />
              <span style={{ color: '#94a3b8', fontSize: '13px', fontWeight: '500' }}>Analysing evidence & graph context…</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Fixed Bottom Suggestions Pills Bar */}
      <div style={{ flexShrink: 0, padding: '8px 16px 4px 16px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        {SUGGESTIONS.map(s => (
          <button
            key={s}
            onClick={() => send(s)}
            disabled={loading}
            style={{
              fontSize: '11px', fontWeight: '600', padding: '5px 12px',
              background: 'rgba(30, 41, 59, 0.8)', border: '1px solid rgba(255, 255, 255, 0.12)',
              borderRadius: '8px', color: '#cbd5e1', cursor: 'pointer',
              fontFamily: 'inherit', transition: 'all 0.15s',
            }}
            onMouseEnter={e => { e.currentTarget.style.background = 'rgba(51, 65, 85, 0.9)'; e.currentTarget.style.color = '#ffffff'; e.currentTarget.style.borderColor = '#60a5fa' }}
            onMouseLeave={e => { e.currentTarget.style.background = 'rgba(30, 41, 59, 0.8)'; e.currentTarget.style.color = '#cbd5e1'; e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.12)' }}
          >
            {s}
          </button>
        ))}
      </div>

      {/* Fixed Bottom Input Row */}
      <div style={{
        flexShrink: 0,
        borderTop: '1px solid rgba(255, 255, 255, 0.08)', padding: '12px 16px',
        display: 'flex', alignItems: 'center', gap: '10px', background: '#1e293b',
      }}>
        {mode === 'search' && <Search size={15} color="#94a3b8" style={{ flexShrink: 0 }} />}
        <input
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
          placeholder={mode === 'search' ? 'Semantic event search…' : "Ask Copilot: 'Explain payload run command lines' or request specific indicators..."}
          disabled={loading}
          style={{
            flex: 1, background: 'transparent', border: 'none',
            color: '#ffffff', fontSize: '13px', outline: 'none',
            fontFamily: 'inherit',
          }}
        />
        <button
          onClick={() => send()}
          disabled={!input.trim() || loading || cooldown > 0}
          style={{
            padding: '7px 12px', background: cooldown > 0 ? '#475569' : '#3b82f6', border: 'none',
            borderRadius: '8px', cursor: (cooldown > 0 || loading || !input.trim()) ? 'not-allowed' : 'pointer',
            display: 'flex', alignItems: 'center', gap: '6px',
            opacity: (!input.trim() || loading || cooldown > 0) ? 0.6 : 1,
            transition: 'all 0.15s', color: '#ffffff',
          }}
          onMouseEnter={e => { if (input.trim() && !loading && cooldown === 0) e.currentTarget.style.background = '#2563eb' }}
          onMouseLeave={e => { if (cooldown === 0) e.currentTarget.style.background = '#3b82f6' }}
        >
          {cooldown > 0 ? (
            <span style={{ fontSize: '11px', fontWeight: '600' }}>Wait {cooldown}s</span>
          ) : (
            <Send size={14} color="#ffffff" />
          )}
        </button>
      </div>
    </div>
  )
}
export default ChatPanel
