import React from 'react';
import { Network, ZoomIn, ZoomOut, RefreshCw, Trash2 } from 'lucide-react';

const GraphToolbar = ({
  zoomScale,
  setZoomScale,
  onResetView,
  onReload,
  onClearGraph
}) => {
  return (
    <div className="flex justify-between items-center bg-gray-900 border border-gray-800 p-4 rounded-xl">
      <div className="flex items-center gap-2 text-xs font-bold text-gray-400">
        <Network className="w-4 h-4 text-accent" />
        Threat Connectivity Map
      </div>
      <div className="flex items-center gap-2">
        {/* Zoom Controls */}
        <button
          onClick={() => setZoomScale(z => Math.min(z + 0.15, 2.5))}
          className="p-1.5 border border-gray-808 bg-gray-955 hover:bg-gray-850 rounded text-gray-450 hover:text-white transition-colors cursor-pointer"
        >
          <ZoomIn className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => setZoomScale(z => Math.max(z - 0.15, 0.4))}
          className="p-1.5 border border-gray-808 bg-gray-955 hover:bg-gray-850 rounded text-gray-450 hover:text-white transition-colors cursor-pointer"
        >
          <ZoomOut className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={onResetView}
          className="px-2.5 py-1 border border-gray-808 bg-gray-955 hover:bg-gray-850 rounded text-[10px] font-bold text-gray-400 hover:text-white transition-colors cursor-pointer"
        >
          Reset view
        </button>
        
        {/* Action Controls */}
        <button
          onClick={onReload}
          className="p-1.5 border border-gray-808 bg-gray-955 hover:bg-gray-850 rounded text-gray-400 hover:text-white transition-colors cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={onClearGraph}
          className="p-1.5 border border-red-955/40 bg-red-955/20 hover:bg-red-900/30 rounded text-red-400 transition-colors cursor-pointer"
          title="Clear Database Graph nodes"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};

export default GraphToolbar;
