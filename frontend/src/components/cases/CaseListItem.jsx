import React from 'react';
import { ChevronRight } from 'lucide-react';

const CaseListItem = ({ c, onClick }) => {
  return (
    <div
      onClick={onClick}
      className="p-6 hover:bg-gray-800/40 flex items-center justify-between cursor-pointer transition-colors duration-150 group"
    >
      <div className="space-y-1.5 min-w-0 pr-8">
        <div className="flex items-center gap-3">
          <h4 className="text-sm font-bold text-white group-hover:text-accent transition-colors truncate">
            {c.title}
          </h4>
          <span
            className={`text-[9px] px-2 py-0.5 border rounded-full font-mono uppercase tracking-wider font-semibold ${
              c.status === 'open'
                ? 'bg-red-950/30 border-red-500/40 text-red-400'
                : c.status === 'in_progress'
                  ? 'bg-amber-950/30 border-amber-500/40 text-amber-400'
                  : 'bg-green-950/30 border-green-500/40 text-green-400'
            }`}
          >
            {c.status}
          </span>
        </div>
        <p className="text-gray-400 text-xs truncate max-w-2xl">{c.description || 'No description provided.'}</p>
        <p className="text-gray-500 text-[10px] font-medium font-sans">
          Created at {new Date(c.created_at).toLocaleString()}
        </p>
      </div>
      <div className="text-gray-500 group-hover:text-white transition-colors pl-4">
        <ChevronRight className="w-5 h-5" />
      </div>
    </div>
  );
};

export default CaseListItem;
