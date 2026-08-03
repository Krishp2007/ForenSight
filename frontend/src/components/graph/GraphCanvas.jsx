import React from 'react';
import { Network } from 'lucide-react';

const GraphCanvas = ({
  loading,
  nodes,
  edges,
  zoomScale,
  panOffset,
  selectedNode,
  onNodeMouseDown,
  onSVGMouseMove,
  onSVGMouseUp,
  onSVGMouseDown,
  getNodeColor,
  svgWidth = 800,
  svgHeight = 500
}) => {
  return (
    <div className="relative border border-gray-805 bg-gray-950/50 rounded-2xl overflow-hidden aspect-video shadow-2xl backdrop-blur-md select-none group">
      {loading ? (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-950/40">
          <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mb-3" />
          <span className="text-gray-505 text-[10px] font-bold tracking-widest uppercase animate-pulse">
            Mapping Neo4j Cypher Nodes...
          </span>
        </div>
      ) : nodes.length === 0 ? (
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <Network className="w-12 h-12 text-gray-707 mb-3 animate-pulse" />
          <h4 className="text-gray-450 font-bold text-xs">No Graph Elements Parsed</h4>
          <p className="text-gray-505 text-[11px] mt-1">Upload EVTX logs to map parsed event relationships.</p>
        </div>
      ) : (
        <svg
          width="100%"
          height="100%"
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          onMouseMove={onSVGMouseMove}
          onMouseUp={onSVGMouseUp}
          onMouseDown={onSVGMouseDown}
          className="w-full h-full cursor-grab active:cursor-grabbing"
        >
          {/* Arrow Marker Definitions */}
          <defs>
            <marker
              id="arrow"
              viewBox="0 0 10 10"
              refX="23"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#334155" />
            </marker>
          </defs>

          {/* Viewport Scale Pan Transformations */}
          <g transform={`translate(${panOffset.x}, ${panOffset.y}) scale(${zoomScale})`}>
            {/* 1. Draw Connecting Edge/Relationship lines */}
            {edges.map((edge, index) => {
              const nodeSrc = nodes.find(n => n.id === edge.source);
              const nodeTgt = nodes.find(n => n.id === edge.target);
              if (!nodeSrc || !nodeTgt) return null;

              return (
                <g key={`edge-${index}`} className="group/edge">
                  <line
                    x1={nodeSrc.x}
                    y1={nodeSrc.y}
                    x2={nodeTgt.x}
                    y2={nodeTgt.y}
                    stroke="#334155"
                    strokeWidth="1.5"
                    markerEnd="url(#arrow)"
                    className="transition-colors hover:stroke-accent duration-100"
                  />
                  {/* Edge name center labels */}
                  <text
                    x={(nodeSrc.x + nodeTgt.x) / 2}
                    y={(nodeSrc.y + nodeTgt.y) / 2 - 4}
                    fill="#475569"
                    fontSize="9"
                    textAnchor="middle"
                    className="font-mono bg-gray-950/80 px-1 hidden group-hover/edge:block pointer-events-none"
                  >
                    {edge.action}
                  </text>
                </g>
              );
            })}

            {/* 2. Draw Node Entities circles */}
            {nodes.map((node) => (
              <g
                key={node.id}
                transform={`translate(${node.x}, ${node.y})`}
                onMouseDown={(e) => onNodeMouseDown(node, e)}
                className="cursor-pointer group/node"
              >
                {/* Ring highlight on select/hover */}
                <circle
                  r="14"
                  fill="transparent"
                  stroke={selectedNode?.id === node.id ? '#a855f7' : 'transparent'}
                  strokeWidth="2"
                  className="group-hover/node:stroke-accent/50"
                />

                {/* Core node solid fills */}
                <circle
                  r="9"
                  fill={getNodeColor(node.type)}
                  stroke="#0f172a"
                  strokeWidth="2"
                />

                {/* Node Text Label (Truncated with shadow) */}
                <text
                  y="22"
                  fill="#e2e8f0"
                  fontSize="9"
                  textAnchor="middle"
                  className="font-bold pointer-events-none select-none drop-shadow-[0_2px_2px_rgba(0,0,0,0.8)]"
                >
                  {node.label.length > 18 ? `${node.label.slice(0, 16)}...` : node.label}
                </text>
              </g>
            ))}
          </g>
        </svg>
      )}

      {/* Zoom guide helper overlay */}
      <div className="absolute bottom-4 left-4 p-2 bg-gray-900/80 border border-gray-800 rounded-lg text-[9px] text-gray-550 pointer-events-none">
        Zoom Scale: {Math.round(zoomScale * 100)}% | Drag nodes to explore.
      </div>
    </div>
  );
};

export default GraphCanvas;
