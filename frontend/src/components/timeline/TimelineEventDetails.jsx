import React from 'react';

const TimelineEventDetails = ({ searchSentence, details }) => {
  return (
    <div className="px-5 pb-5 border-t border-gray-850/65 bg-gray-955/30 pt-4 space-y-4">
      {/* Semantic Sentence Summary */}
      {searchSentence && (
        <div className="p-3 bg-gray-905 border border-gray-850 rounded-xl">
          <span className="text-[10px] text-accent font-bold uppercase tracking-wider block mb-1">
            Semantic Normalized Summary
          </span>
          <p className="text-xs text-gray-300 leading-relaxed font-sans">{searchSentence}</p>
        </div>
      )}

      {/* Raw Details JSON Tree */}
      <div>
        <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider block mb-2">
          Parser Parameters & Properties
        </span>
        <pre className="p-4 bg-gray-950 border border-gray-800 rounded-xl overflow-x-auto text-[11px] font-mono text-green-400 shadow-inner max-w-full leading-normal">
          {JSON.stringify(details, null, 2)}
        </pre>
      </div>
    </div>
  );
};

export default TimelineEventDetails;
