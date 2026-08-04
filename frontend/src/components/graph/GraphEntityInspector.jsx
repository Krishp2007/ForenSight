import React from 'react';
import { HelpCircle, Network } from 'lucide-react';

const GraphEntityInspector = ({ selectedNode, getNodeColor, edges = [] }) => {
  // Filter for active relations linked to this node
  const connections = selectedNode
    ? edges.filter(e => e.source === selectedNode.id || e.target === selectedNode.id)
    : [];

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

          {connections.length > 0 && (
            <div className="space-y-2">
              <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider block">
                Active Connections ({connections.length})
              </span>
              <div className="space-y-2 mt-1.5 max-h-56 overflow-y-auto pr-1">
                {connections.map((c, idx) => {
                  const isSource = c.source === selectedNode.id;
                  const partner = isSource ? c.target : c.source;
                  return (
                    <div key={idx} className="p-2 bg-gray-950/60 border border-gray-850 rounded-lg text-[10px] text-gray-300 flex flex-col gap-1">
                      <div className="flex justify-between items-center">
                        <span className="font-mono text-[9px] text-[#a855f7] uppercase font-bold">
                          {isSource ? "Outbound ➔" : "◀ Inbound"}
                        </span>
                        <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold ${c.is_anomaly ? "bg-rose-950/40 border border-rose-800 text-rose-450" : "bg-gray-800 text-gray-400"}`}>
                          {c.is_anomaly ? "Anomaly" : "Normal"}
                        </span>
                      </div>
                      <div className="break-all font-mono">
                        {isSource ? (
                          <span>This Node <strong className="text-white">[{c.action}]</strong> ➔ {partner}</span>
                        ) : (
                          <span>{partner} <strong className="text-white">[{c.action}]</strong> ➔ This Node</span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          <div className="p-3 bg-gray-950/40 border border-gray-850/60 rounded-xl space-y-1">
            <span className="text-[9px] text-gray-450 block leading-normal">
              Select other nodes in the graph canvas to inspect threat chain linkages and correlations.
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
