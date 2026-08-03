import React from 'react';
import { User, ShieldAlert } from 'lucide-react';

const MarkdownText = ({ text }) => {
  if (!text) return null;

  // Split content by code blocks to isolate preformatted sections
  const parts = text.split(/(```[\s\S]*?```)/g);

  return (
    <div className="space-y-2 text-xs leading-relaxed font-sans text-gray-200">
      {parts.map((part, index) => {
        // Render Code block
        if (part.startsWith('```') && part.endsWith('```')) {
          const match = part.match(/```(\w*)\n([\s\S]*?)```/);
          const lang = match ? match[1] : '';
          const code = match ? match[2] : part.slice(3, -3);

          return (
            <pre key={index} className="bg-gray-950 p-4 rounded-xl border border-gray-800/80 font-mono text-[11px] text-green-400 overflow-x-auto my-3 shadow-inner leading-normal">
              {code.trim()}
            </pre>
          );
        }

        // Render ordinary prose text with inline markers replaced
        const lines = part.split('\n');
        return lines.map((line, lineIndex) => {
          let cleanLine = line.trim();
          if (!cleanLine) return <div key={`empty-${lineIndex}`} className="h-2" />;

          // Bullets
          if (cleanLine.startsWith('- ') || cleanLine.startsWith('* ')) {
            const listContent = cleanLine.slice(2);
            return (
              <ul key={`list-${lineIndex}`} className="list-disc pl-5 my-1 space-y-1">
                <li>{parseInlineMarkdown(listContent)}</li>
              </ul>
            );
          }

          // Numbered bullets
          const numMatch = cleanLine.match(/^(\d+)\.\s(.*)/);
          if (numMatch) {
            return (
              <ol key={`num-${lineIndex}`} className="list-decimal pl-5 my-1 space-y-1">
                <li value={parseInt(numMatch[1])}>{parseInlineMarkdown(numMatch[2])}</li>
              </ol>
            );
          }

          // Standard Header lines
          if (cleanLine.startsWith('### ')) {
            return (
              <h5 key={`h3-${lineIndex}`} className="text-white font-bold text-sm mt-3 mb-1">
                {parseInlineMarkdown(cleanLine.slice(4))}
              </h5>
            );
          }
          if (cleanLine.startsWith('## ')) {
            return (
              <h4 key={`h2-${lineIndex}`} className="text-accent font-bold text-sm mt-4 mb-2">
                {parseInlineMarkdown(cleanLine.slice(3))}
              </h4>
            );
          }
          if (cleanLine.startsWith('# ')) {
            return (
              <h3 key={`h1-${lineIndex}`} className="text-white font-extrabold text-base mt-4 mb-2">
                {parseInlineMarkdown(cleanLine.slice(2))}
              </h3>
            );
          }

          return (
            <p key={`p-${lineIndex}`} className="mb-2">
              {parseInlineMarkdown(line)}
            </p>
          );
        });
      })}
    </div>
  );
};

// Replace bold (**text**) and code (`code`) markers
const parseInlineMarkdown = (string) => {
  const parts = string.split(/(\*\*.*?\*\*|`.*?`)/g);

  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} className="text-white font-bold">{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code key={i} className="bg-gray-950 border border-gray-800 text-purple-400 font-mono text-[10px] px-1 py-0.5 rounded mx-0.5">
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
};

const ChatMessage = ({ msg }) => {
  const isCopilot = msg.sender === 'copilot';

  return (
    <div className={`flex gap-4 p-5 rounded-2xl border transition-all ${
      isCopilot 
        ? 'bg-gray-900/30 border-gray-850/60' 
        : 'bg-accent/5 border-accent/25'
    }`}>
      {/* Sender Avatar block */}
      <div className={`w-8 h-8 rounded-lg shrink-0 flex items-center justify-center border ${
        isCopilot
          ? 'bg-accent/20 border-accent/40 text-accent'
          : 'bg-gray-800 border-gray-700 text-gray-300'
      }`}>
        {isCopilot ? <ShieldAlert className="w-4 h-4 animate-pulse" /> : <User className="w-4 h-4" />}
      </div>

      {/* Message Output wrapper */}
      <div className="flex-1 min-w-0 space-y-1">
        <span className="text-[10px] font-bold tracking-wider uppercase text-gray-500">
          {isCopilot ? 'AI Copilot' : 'Investigator Analyst'}
        </span>
        <div className="mt-1">
          <MarkdownText text={msg.text} />
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
export { MarkdownText };
