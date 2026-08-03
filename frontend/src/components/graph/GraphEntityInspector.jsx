import React from 'react';
import { HelpCircle, Network } from 'lucide-react';

const GraphEntityInspector = ({ selectedNode, getNodeColor }) => {
  return (
    <div className="bg-gray-901 border border-gray-808 p-6 rounded-2xl h-full space-y-4 shadow-xl select-none">
      <div className="flex items-center gap-1.5 pb-3 border-b border-gray-808">
        <HelpCircle className="w-4 h-4 text-accent" />
        <h4 className="text-sm font-bold text-white">Entity Inspection</h4>
      </div>

      {selectedNode ? (
        <div className="space-y-4">
          <div>
            <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider block">
              Category Type
            </span>
            <span
              className="inline-block mt-1 text-[10px] px-2 py-0.5 border rounded-full font-mono uppercase font-bold"
              style={{
                backgroundColor: `${getNodeColor(selectedNode.type)}20`,
                borderColor: getNodeColor(selectedNode.type),
                color: getNodeColor(selectedNode.type)
              }}
            >
              {selectedNode.type}
            </span>
          </div>

          <div>
            <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider block">
              Identity/Name
            </span>
            <p className="text-xs text-white font-mono break-all bg-gray-950 p-3 rounded-lg border border-gray-850 mt-1 pb-3 pt-3">
              {selectedNode.label}
            </p>
          </div>

          <div className="p-3 bg-gray-950/40 border border-gray-850/60 rounded-xl space-y-1">
            <span className="text-[9px] text-gray-450 block leading-normal">
              Connected elements related to this entity can be mapped below in the timeline logs.
            </span>
          </div>
        </div>
      ) : (
        <div className="h-64 flex flex-col items-center justify-center text-center text-gray-500">
          <Network className="w-8 h-8 text-gray-705 mb-2 animate-none" />
          <p className="text-xs">Click any node to inspect details.</p>
        </div>
      )}
    </div>
  );
};

export default GraphEntityInspector;
