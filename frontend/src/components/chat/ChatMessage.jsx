import ReactMarkdown from 'react-markdown'

const ChatMessage = ({ role, content }) => {
  const isUser = role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] rounded-xl px-4 py-3 text-sm leading-relaxed
          ${isUser
            ? 'bg-blue-600 text-white rounded-br-none'
            : 'bg-gray-700 text-gray-100 rounded-bl-none'
          }`}
      >
        {isUser ? (
          <p>{content}</p>
        ) : (
          <ReactMarkdown
            components={{
              p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
              ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
              code: ({ inline, children }) =>
                inline
                  ? <code className="bg-gray-600 px-1 py-0.5 rounded text-xs font-mono">{children}</code>
                  : <pre className="bg-gray-800 rounded p-2 text-xs overflow-x-auto my-2"><code>{children}</code></pre>,
              h3: ({ children }) => <h3 className="font-bold text-blue-300 mb-1 mt-2">{children}</h3>,
              h4: ({ children }) => <h4 className="font-semibold text-gray-300 mb-1">{children}</h4>,
              strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
            }}
          >
            {content}
          </ReactMarkdown>
        )}
      </div>
    </div>
  )
}

export default ChatMessage
