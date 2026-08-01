import ReactMarkdown from 'react-markdown'

const ChatMessage = ({ role, content }) => {
  const isUser = role === 'user'
  return (
    <div style={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
      <div style={{
        maxWidth: '85%',
        borderRadius: isUser ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
        padding: '10px 14px',
        fontSize: '13px',
        lineHeight: '1.6',
        background: isUser ? '#4a7fe8' : '#2d3748',
        color: '#ffffff',
      }}>
        {isUser ? (
          <p style={{ margin: 0 }}>{content}</p>
        ) : (
          <ReactMarkdown
            components={{
              p: ({ children }) => <p style={{ margin: '0 0 8px 0' }}>{children}</p>,
              ul: ({ children }) => <ul style={{ margin: '0 0 8px 0', paddingLeft: '20px' }}>{children}</ul>,
              ol: ({ children }) => <ol style={{ margin: '0 0 8px 0', paddingLeft: '20px' }}>{children}</ol>,
              code: ({ inline, children }) => inline
                ? <code style={{ background: 'rgba(0,0,0,0.3)', padding: '1px 5px', borderRadius: '4px', fontSize: '12px', fontFamily: 'monospace' }}>{children}</code>
                : <pre style={{ background: 'rgba(0,0,0,0.3)', borderRadius: '6px', padding: '10px', fontSize: '11px', overflow: 'auto', margin: '8px 0' }}><code style={{ fontFamily: 'monospace' }}>{children}</code></pre>,
              h3: ({ children }) => <h3 style={{ color: '#93c5fd', fontWeight: '700', margin: '12px 0 4px 0', fontSize: '13px' }}>{children}</h3>,
              h4: ({ children }) => <h4 style={{ color: '#cbd5e1', fontWeight: '600', margin: '8px 0 4px 0', fontSize: '13px' }}>{children}</h4>,
              strong: ({ children }) => <strong style={{ color: '#ffffff', fontWeight: '600' }}>{children}</strong>,
              li: ({ children }) => <li style={{ marginBottom: '4px' }}>{children}</li>,
            }}
          >{content}</ReactMarkdown>
        )}
      </div>
    </div>
  )
}
export default ChatMessage
