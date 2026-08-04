import ReactMarkdown from 'react-markdown'
import { User, Shield } from 'lucide-react'

const ChatMessage = ({ role, content }) => {
  const isUser = role === 'user'
  return (
    <div style={{ display: 'flex', flexDirection: 'column', width: '100%', marginBottom: '4px' }}>
      <div style={{
        maxWidth: '92%',
        alignSelf: isUser ? 'flex-end' : 'flex-start',
        borderRadius: '12px',
        padding: '12px 16px',
        fontSize: '13px',
        lineHeight: '1.6',
        background: isUser ? 'rgba(30, 41, 59, 0.75)' : 'rgba(15, 23, 42, 0.85)',
        border: isUser ? '1px solid rgba(255, 255, 255, 0.08)' : '1px solid rgba(96, 165, 250, 0.25)',
        color: '#e2e8f0',
        wordBreak: 'break-word',
        overflowWrap: 'anywhere',
        boxSizing: 'border-box',
        boxShadow: isUser ? '0 2px 8px rgba(0, 0, 0, 0.2)' : '0 4px 12px rgba(0, 0, 0, 0.35)',
      }}>
        {/* Header Label */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
          {isUser ? (
            <>
              <User size={12} color="#94a3b8" />
              <span style={{ color: '#94a3b8', fontSize: '10px', fontWeight: '700', letterSpacing: '0.8px', textTransform: 'uppercase' }}>
                INVESTIGATOR ANALYST
              </span>
            </>
          ) : (
            <>
              <div style={{
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                width: '18px', height: '18px', borderRadius: '4px',
                background: 'rgba(96, 165, 250, 0.2)', border: '1px solid rgba(96, 165, 250, 0.4)'
              }}>
                <Shield size={11} color="#60a5fa" />
              </div>
              <span style={{ color: '#60a5fa', fontSize: '10px', fontWeight: '700', letterSpacing: '0.8px', textTransform: 'uppercase' }}>
                AI COPILOT
              </span>
            </>
          )}
        </div>

        {/* Message Content */}
        {isUser ? (
          <p style={{ margin: 0, wordBreak: 'break-word', overflowWrap: 'anywhere', color: '#f1f5f9' }}>{content}</p>
        ) : (
          <ReactMarkdown
            components={{
              p: ({ children }) => <p style={{ margin: '0 0 8px 0', wordBreak: 'break-word', overflowWrap: 'anywhere' }}>{children}</p>,
              a: ({ href, children }) => (
                <a
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    color: '#60a5fa',
                    wordBreak: 'break-all',
                    overflowWrap: 'anywhere',
                    textDecoration: 'underline',
                    textUnderlineOffset: '2px',
                  }}
                >
                  {children}
                </a>
              ),
              ul: ({ children }) => <ul style={{ margin: '0 0 8px 0', paddingLeft: '20px', wordBreak: 'break-word' }}>{children}</ul>,
              ol: ({ children }) => <ol style={{ margin: '0 0 8px 0', paddingLeft: '20px', wordBreak: 'break-word' }}>{children}</ol>,
              code: ({ inline, children }) => inline
                ? <code style={{
                    background: 'rgba(96, 165, 250, 0.15)',
                    border: '1px solid rgba(96, 165, 250, 0.3)',
                    color: '#bfdbfe',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    fontSize: '12px',
                    fontFamily: 'monospace',
                    fontWeight: '600',
                    wordBreak: 'break-all'
                  }}>{children}</code>
                : <pre style={{
                    background: 'rgba(2, 6, 23, 0.7)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '6px',
                    padding: '10px 12px',
                    fontSize: '11px',
                    overflowX: 'auto',
                    margin: '8px 0',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word'
                  }}><code style={{ fontFamily: 'monospace', color: '#cbd5e1' }}>{children}</code></pre>,
              h3: ({ children }) => <h3 style={{ color: '#93c5fd', fontWeight: '700', margin: '12px 0 4px 0', fontSize: '13px' }}>{children}</h3>,
              h4: ({ children }) => <h4 style={{ color: '#cbd5e1', fontWeight: '600', margin: '8px 0 4px 0', fontSize: '13px' }}>{children}</h4>,
              strong: ({ children }) => <strong style={{ color: '#ffffff', fontWeight: '600' }}>{children}</strong>,
              li: ({ children }) => <li style={{ marginBottom: '4px', wordBreak: 'break-word' }}>{children}</li>,
            }}
          >{content}</ReactMarkdown>
        )}
      </div>
    </div>
  )
}
export default ChatMessage
