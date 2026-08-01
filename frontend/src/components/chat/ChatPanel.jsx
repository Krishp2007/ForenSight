import { useState, useRef, useEffect } from 'react'
import { askCopilot } from '../../services/chatService'
import { searchEvents } from '../../services/similarityService'
import ChatMessage from './ChatMessage'
import Spinner from '../ui/Spinner'
import { Send, Search, Bot } from 'lucide-react'

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
  const [mode, setMode] = useState('copilot') // 'copilot' | 'search'
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async (text) => {
    const q = text || input.trim()
    if (!q || loading) return
    setInput('')
    setMessages((m) => [...m, { role: 'user', content: q }])
    setLoading(true)
    try {
      if (mode === 'search') {
        const results = await searchEvents(caseId, q, 5)
        const formatted = results.length === 0
          ? 'No similar events found for that query.'
          : results.map((ev, i) =>
              `**${i + 1}. ${ev.event_type}** (${ev.severity})\n` +
              `${ev.subject} → ${ev.action} → ${ev.object}\n` +
              `*${new Date(ev.timestamp).toLocaleString()}*`
            ).join('\n\n')
        setMessages((m) => [...m, { role: 'assistant', content: formatted }])
      } else {
        const res = await askCopilot(caseId, q)
        setMessages((m) => [...m, { role: 'assistant', content: res.analysis }])
      }
    } catch (e) {
      setMessages((m) => [...m, {
        role: 'assistant',
        content: `⚠️ Error: ${e.response?.data?.detail || e.message}`,
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full min-h-[540px] bg-gray-900 rounded-xl border border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700 bg-gray-800">
        <div className="flex items-center gap-2 text-white text-sm font-semibold">
          <Bot size={16} className="text-blue-400" />
          ForenSight Copilot
        </div>
        <div className="flex text-xs rounded-lg overflow-hidden border border-gray-600">
          <button
            onClick={() => setMode('copilot')}
            className={`px-3 py-1.5 transition-colors ${mode === 'copilot' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'}`}
          >
            AI Copilot
          </button>
          <button
            onClick={() => setMode('search')}
            className={`px-3 py-1.5 transition-colors ${mode === 'search' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'}`}
          >
            Semantic Search
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
        {messages.length === 0 && (
          <div className="flex flex-col items-center gap-4 mt-6">
            <p className="text-gray-500 text-sm">Ask a question or choose a suggestion:</p>
            <div className="flex flex-wrap gap-2 justify-center">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="text-xs bg-gray-700 hover:bg-gray-600 text-gray-300 hover:text-white px-3 py-1.5 rounded-full border border-gray-600 transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => <ChatMessage key={i} role={m.role} content={m.content} />)}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-700 rounded-xl px-4 py-3 flex items-center gap-2">
              <Spinner size="sm" />
              <span className="text-gray-400 text-sm">Analysing…</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-700 px-4 py-3 flex items-center gap-2 bg-gray-800">
        {mode === 'search' && <Search size={15} className="text-gray-500 shrink-0" />}
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && send()}
          placeholder={mode === 'search' ? 'Semantic event search…' : 'Ask about this case…'}
          className="flex-1 bg-transparent text-white text-sm placeholder-gray-500 focus:outline-none"
          disabled={loading}
        />
        <button
          onClick={() => send()}
          disabled={!input.trim() || loading}
          className="p-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 rounded-lg transition-colors"
        >
          <Send size={14} className="text-white" />
        </button>
      </div>
    </div>
  )
}

export default ChatPanel
