import ReactMarkdown from 'react-markdown'
import { User, Shield } from 'lucide-react'

const ChatMessage = ({ role, content, confidence = 'High', sources = [] }) => {
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
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
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

          {!isUser && confidence && (
            <span style={{
              fontSize: '10px', fontWeight: '700', padding: '2px 8px', borderRadius: '99px',
              background: confidence === 'High' ? 'rgba(52, 211, 153, 0.15)' : confidence === 'Medium' ? 'rgba(251, 191, 36, 0.15)' : 'rgba(248, 113, 113, 0.15)',
              color: confidence === 'High' ? '#34d399' : confidence === 'Medium' ? '#fbbf24' : '#f87171',
              border: `1px solid ${confidence === 'High' ? 'rgba(52, 211, 153, 0.3)' : confidence === 'Medium' ? 'rgba(251, 191, 36, 0.3)' : 'rgba(248, 113, 113, 0.3)'}`,
            }}>
              Confidence: {confidence}
            </span>
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
              code: ({ inline, className, children, ...props }) => {
                const match = /language-(\w+)/.exec(className || '')
                const isBlock = match || (children && String(children).includes('\n'))
                return !isBlock ? (
                  <code style={{
                    background: 'rgba(96, 165, 250, 0.15)',
                    border: '1px solid rgba(96, 165, 250, 0.3)',
                    color: '#bfdbfe',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    fontSize: '12px',
                    fontFamily: 'monospace',
                    fontWeight: '600',
                    display: 'inline-block',
                    wordBreak: 'break-all'
                  }} {...props}>{children}</code>
                ) : (
                  <pre style={{
                    background: 'rgba(2, 6, 23, 0.7)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '6px',
                    padding: '10px 12px',
                    fontSize: '11px',
                    overflowX: 'auto',
                    margin: '8px 0',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word'
                  }}><code style={{ fontFamily: 'monospace', color: '#cbd5e1' }} {...props}>{children}</code></pre>
                )
              },
              h3: ({ children }) => <h3 style={{ color: '#93c5fd', fontWeight: '700', margin: '12px 0 4px 0', fontSize: '13px' }}>{children}</h3>,
              h4: ({ children }) => <h4 style={{ color: '#cbd5e1', fontWeight: '600', margin: '8px 0 4px 0', fontSize: '13px' }}>{children}</h4>,
              strong: ({ children }) => <strong style={{ color: '#ffffff', fontWeight: '600' }}>{children}</strong>,
              li: ({ children }) => <li style={{ marginBottom: '4px', wordBreak: 'break-word' }}>{children}</li>,
            }}
          >{content}</ReactMarkdown>
        )}

        {/* Source Citations Badges */}
        {!isUser && Array.isArray(sources) && sources.length > 0 && (
          <div style={{
            marginTop: '10px', paddingTop: '8px', borderTop: '1px solid rgba(255, 255, 255, 0.08)',
            display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'center'
          }}>
            <span style={{ color: '#94a3b8', fontSize: '10px', fontWeight: '700', textTransform: 'uppercase' }}>Sources Cited:</span>
            {sources.map((s, idx) => (
              <span key={idx} style={{
                fontSize: '10px', padding: '2px 8px', borderRadius: '4px',
                background: 'rgba(30, 41, 59, 0.9)', border: '1px solid rgba(255, 255, 255, 0.12)',
                color: '#cbd5e1', fontFamily: 'monospace'
              }}>
                📄 {s.source_file || s.mitre_id || s.type || 'Evidence'}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
export default ChatMessage
