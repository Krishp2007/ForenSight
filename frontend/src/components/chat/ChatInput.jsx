import React from 'react';
import { Send, Terminal } from 'lucide-react';

const ChatInput = ({ value, onChange, onSubmit, disabled, setPrompt }) => {
  const SUGGESTION_CHIPS = [
    { label: "Summarize Timeline", query: "Summarize the timeline events of this case." },
    { label: "Check Persistence", query: "Find registry persistence keys or modifications." },
    { label: "Anomalous Processes", query: "List suspicious process executions or outlier events." },
    { label: "Net Connections", query: "Identify suspicious network IP connect events." }
  ];

  const handleChipClick = (query) => {
    if (disabled) return;
    setPrompt(query);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSubmit(e);
    }
  };

  return (
    <div className="space-y-4">
      {/* Suggestions Row */}
      <div className="flex flex-wrap gap-2">
        {SUGGESTION_CHIPS.map((chip, index) => (
          <button
            key={index}
            type="button"
            disabled={disabled}
            onClick={() => handleChipClick(chip.query)}
            className="px-3 py-1.5 bg-gray-900 hover:bg-gray-850 hover:text-white border border-gray-805 text-[10px] font-bold text-gray-400 rounded-lg transition-colors cursor-pointer disabled:opacity-40"
          >
            {chip.label}
          </button>
        ))}
      </div>

      {/* Input Form field */}
      <form onSubmit={onSubmit} className="flex gap-3 relative items-end">
        <div className="relative flex-1">
          <Terminal className="absolute left-3.5 bottom-3.5 w-4 h-4 text-gray-500 pointer-events-none" />
          <textarea
            rows="2"
            disabled={disabled}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask Copilot: 'Explain payload run command lines' or request specific indicators..."
            className="w-full pl-10 pr-4 py-3 bg-gray-950 border border-gray-800 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent resize-none min-h-[48px] leading-relaxed"
          />
        </div>
        <button
          type="submit"
          disabled={disabled || !value.trim()}
          className="w-12 h-12 bg-accent hover:bg-accent-hover text-white border border-transparent rounded-xl flex items-center justify-center shrink-0 transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_0_12px_rgba(170,59,255,0.25)]"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};

export default ChatInput;
