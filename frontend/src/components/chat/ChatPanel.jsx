import { useState, useRef, useEffect } from 'react'
import api from '../../services/api'
import ChatMessage from './ChatMessage'
import { Spinner } from '../ui'
import { Send, Search, Bot } from 'lucide-react'

// Inlined from chatService + similarityService
const askCopilot   = (caseId, question) => api.post(`/cases/${caseId}/copilot`, { question }).then(r => r.data)
const searchEvents = (caseId, query, limit = 10) => api.get(`/cases/${caseId}/search`, { params: { query, limit } }).then(r => r.data)

const SUGGESTIONS = [
  'Summarise the case timeline',
  'What anomalies were detected?',
  'Which MITRE techniques were observed?',
  'List all critical severity events',
  'What processes made network connections?',
]

const ChatPanel = ({ caseId }) => {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState('copilot')
  const bottomRef = useRef(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const send = async (text) => {
    const q = text || input.trim()
    if (!q || loading) return
    setInput('')
    setMessages(m => [...m, { role: 'user', content: q }])
    setLoading(true)
    try {
      if (mode === 'search') {
        const results = await searchEvents(caseId, q, 5)
        const formatted = results.length === 0
          ? 'No similar events found for that query.'
          : results.map((ev, i) => `**${i+1}. ${ev.event_type}** (${ev.severity})\n${ev.subject} → ${ev.action} → ${ev.object}\n*${new Date(ev.timestamp).toLocaleString()}*`).join('\n\n')
        setMessages(m => [...m, { role: 'assistant', content: formatted }])
      } else {
        const res = await askCopilot(caseId, q)
        setMessages(m => [...m, { role: 'assistant', content: res.analysis }])
      }
    } catch (e) {
      setMessages(m => [...m, { role: 'assistant', content: `⚠️ Error: ${e.response?.data?.detail || e.message}` }])
    } finally { setLoading(false) }
  }

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', minHeight: '540px',
      background: '#1e2a3d', borderRadius: '12px',
      border: '1px solid #3d4f6a', overflow: 'hidden',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '12px 16px', borderBottom: '1px solid #3d4f6a', background: '#253347',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#ffffff', fontSize: '13px', fontWeight: '600' }}>
          <Bot size={16} color="#60a5fa" />
          ForenSight Copilot
        </div>
        <div style={{ display: 'flex', border: '1px solid #3d4f6a', borderRadius: '8px', overflow: 'hidden' }}>
          {['copilot', 'search'].map(m => (
            <button key={m} onClick={() => setMode(m)} style={{
              padding: '5px 12px', fontSize: '11px', fontWeight: '500', border: 'none',
              background: mode === m ? '#4a7fe8' : 'transparent',
              color: mode === m ? '#ffffff' : '#9aa8c0',
              cursor: 'pointer', fontFamily: 'inherit', textTransform: 'capitalize',
              transition: 'background 0.15s',
            }}>
              {m === 'copilot' ? 'AI Copilot' : 'Semantic Search'}
            </button>
          ))}
        </div>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {messages.length === 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px', marginTop: '24px' }}>
            <p style={{ color: '#6b7fa3', fontSize: '13px', margin: 0 }}>Ask a question or choose a suggestion:</p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'center' }}>
              {SUGGESTIONS.map(s => (
                <button key={s} onClick={() => send(s)} style={{
                  fontSize: '12px', padding: '6px 12px',
                  background: '#2a3347', border: '1px solid #3d4f6a',
                  borderRadius: '99px', color: '#9aa8c0', cursor: 'pointer',
                  fontFamily: 'inherit', transition: 'all 0.15s',
                }}
                onMouseEnter={e => { e.currentTarget.style.background = '#323d52'; e.currentTarget.style.color = '#fff'; e.currentTarget.style.borderColor = '#4a7fe8' }}
                onMouseLeave={e => { e.currentTarget.style.background = '#2a3347'; e.currentTarget.style.color = '#9aa8c0'; e.currentTarget.style.borderColor = '#3d4f6a' }}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => <ChatMessage key={i} role={m.role} content={m.content} />)}
        {loading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div style={{ background: '#2d3748', borderRadius: '12px', padding: '10px 16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Spinner size="sm" />
              <span style={{ color: '#9aa8c0', fontSize: '13px' }}>Analysing…</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{
        borderTop: '1px solid #3d4f6a', padding: '12px 16px',
        display: 'flex', alignItems: 'center', gap: '10px', background: '#253347',
      }}>
        {mode === 'search' && <Search size={15} color="#6b7fa3" style={{ flexShrink: 0 }} />}
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
          placeholder={mode === 'search' ? 'Semantic event search…' : 'Ask about this case…'}
          disabled={loading}
          style={{
            flex: 1, background: 'transparent', border: 'none',
            color: '#ffffff', fontSize: '13px', outline: 'none',
            fontFamily: 'inherit',
          }}
        />
        <button
          onClick={() => send()}
          disabled={!input.trim() || loading}
          style={{
            padding: '7px 10px', background: '#4a7fe8', border: 'none',
            borderRadius: '8px', cursor: 'pointer', display: 'flex',
            alignItems: 'center', opacity: (!input.trim() || loading) ? 0.4 : 1,
            transition: 'opacity 0.15s',
          }}
          onMouseEnter={e => { if (input.trim() && !loading) e.currentTarget.style.background = '#3b6bc4' }}
          onMouseLeave={e => e.currentTarget.style.background = '#4a7fe8'}
        >
          <Send size={14} color="#ffffff" />
        </button>
      </div>
    </div>
  )
}
export default ChatPanel
