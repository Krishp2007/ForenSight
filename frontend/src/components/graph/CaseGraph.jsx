import React, { useState, useEffect, useRef } from 'react';
import apiClient from '../../services/apiClient';
import GraphToolbar from './GraphToolbar';
import GraphCanvas from './GraphCanvas';
import GraphEntityInspector from './GraphEntityInspector';

const CaseGraph = ({ caseId }) => {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // View transform states
  const [zoomScale, setZoomScale] = useState(1);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const panStart = useRef({ x: 0, y: 0 });

  // Physics drag tracking
  const [draggedNode, setDraggedNode] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);

  // SVG dimensions
  const svgWidth = 800;
  const svgHeight = 500;

  const fetchGraph = async () => {
    setLoading(true);
    setError('');
    setSelectedNode(null);
    try {
      const res = await apiClient.get(`/cases/${caseId}/graph`);
      const rawNodes = res.data.nodes || [];
      const rawEdges = res.data.edges || [];

      // Arrange nodes in a circular layout initially
      const initializedNodes = rawNodes.map((n, i) => {
        const angle = (i / Math.max(1, rawNodes.length)) * 2 * Math.PI;
        const radius = 150 + Math.random() * 50;
        return {
          ...n,
          x: svgWidth / 2 + Math.cos(angle) * radius,
          y: svgHeight / 2 + Math.sin(angle) * radius,
          vx: 0,
          vy: 0,
        };
      });

      // Aggregate duplicate node edges to prevent overlapping blinks and speed up canvas rendering
      const edgeMap = {};
      rawEdges.forEach((edge) => {
        const key = `${edge.source}->${edge.target}`;
        if (!edgeMap[key]) {
          edgeMap[key] = {
            ...edge,
            actions: [edge.action],
            count: 1
          };
        } else {
          edgeMap[key].count += 1;
          if (!edgeMap[key].actions.includes(edge.action)) {
            edgeMap[key].actions.push(edge.action);
          }
          if (edge.is_anomaly) {
            edgeMap[key].is_anomaly = true;
            edgeMap[key].anomaly_score = Math.max(edgeMap[key].anomaly_score || 0, edge.anomaly_score || 0);
          }
        }
      });

      // Construct finalized custom displaying label representing all events
      const aggregatedEdges = Object.values(edgeMap).map((link) => {
        const repLabel = link.actions.slice(0, 2).join(', ');
        const suffix = link.actions.length > 2 ? '...' : '';
        const countText = link.count > 1 ? ` (x${link.count})` : '';
        return {
          ...link,
          action: `${repLabel}${suffix}${countText}`
        };
      });

      setNodes(initializedNodes);
      setEdges(aggregatedEdges);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to retrieve case Neo4j threat graph.');
    } finally {
      setLoading(false);
    }
  };

  const clearGraph = async () => {
    if (!window.confirm("Are you sure you want to clear Neo4j graph nodes for this case?")) return;
    try {
      await apiClient.delete(`/cases/${caseId}/graph`);
      fetchGraph();
    } catch (err) {
      setError('Failed to clear graph nodes.');
    }
  };

  useEffect(() => {
    fetchGraph();
  }, [caseId]);

  // Force-Directed Physics Ticker Loop (Repulsion, Attraction, Center-Gravity)
  useEffect(() => {
    if (nodes.length === 0 || draggedNode) return;

    let animId;
    const tick = () => {
      setNodes((prevNodes) => {
        const nextNodes = prevNodes.map((n) => ({ ...n }));
        const nodeMap = {};
        nextNodes.forEach((n) => {
          nodeMap[n.id] = n;
        });

        // 1. Center Gravity force
        const centerX = svgWidth / 2;
        const centerY = svgHeight / 2;
        const gravityConst = 0.015;

        nextNodes.forEach((n) => {
          n.vx += (centerX - n.x) * gravityConst;
          n.vy += (centerY - n.y) * gravityConst;
        });

        // 2. Repulsion force between node pairs (Coulomb Repulsion)
        const repelStrength = 1800;
        for (let i = 0; i < nextNodes.length; i++) {
          for (let j = i + 1; j < nextNodes.length; j++) {
            const nodeA = nextNodes[i];
            const nodeB = nextNodes[j];
            const dx = nodeB.x - nodeA.x;
            const dy = nodeB.y - nodeA.y;
            const distSq = dx * dx + dy * dy || 1;
            const dist = Math.sqrt(distSq);

            if (dist < 320) {
              const repelForce = repelStrength / distSq;
              const forceX = (dx / dist) * repelForce;
              const forceY = (dy / dist) * repelForce;
              nodeA.vx -= forceX;
              nodeA.vy -= forceY;
              nodeB.vx += forceX;
              nodeB.vy += forceY;
            }
          }
        }

        // 3. Attraction forces along connecting edges (Hooke's Edge Spring)
        const springStrength = 0.082;
        const springLen = 120;
        edges.forEach((edge) => {
          const nodeA = nodeMap[edge.source];
          const nodeB = nodeMap[edge.target];
          if (!nodeA || !nodeB) return;

          const dx = nodeB.x - nodeA.x;
          const dy = nodeB.y - nodeA.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const extension = dist - springLen;
          const springForce = extension * springStrength;

          const forceX = (dx / dist) * springForce;
          const forceY = (dy / dist) * springForce;

          nodeA.vx += forceX;
          nodeA.vy += forceY;
          nodeB.vx -= forceX;
          nodeB.vy -= forceY;
        });

        // 4. Update velocity drag and positions
        const dragVal = 0.82;
        nextNodes.forEach((n) => {
          n.x += n.vx;
          n.y += n.vy;
          n.vx *= dragVal;
          n.vy *= dragVal;

          n.x = Math.max(25, Math.min(svgWidth - 25, n.x));
          n.y = Math.max(25, Math.min(svgHeight - 25, n.y));
        });

        return nextNodes;
      });

      animId = requestAnimationFrame(tick);
    };

    animId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animId);
  }, [nodes.length, edges, draggedNode]);

  // Click & Drag Node Position Handling
  const handleNodeMouseDown = (node, e) => {
    e.stopPropagation();
    setDraggedNode(node.id);
    setSelectedNode(node);
  };

  const handleSVGMouseMove = (e) => {
    if (draggedNode) {
      const rect = e.currentTarget.getBoundingClientRect();
      const x = (e.clientX - rect.left - panOffset.x) / zoomScale;
      const y = (e.clientY - rect.top - panOffset.y) / zoomScale;

      setNodes((prevNodes) =>
        prevNodes.map((n) =>
          n.id === draggedNode ? { ...n, x, y, vx: 0, vy: 0 } : n
        )
      );
    } else if (isPanning) {
      const dx = e.clientX - panStart.current.x;
      const dy = e.clientY - panStart.current.y;
      setPanOffset({ x: panOffset.x + dx, y: panOffset.y + dy });
      panStart.current = { x: e.clientX, y: e.clientY };
    }
  };

  const handleSVGMouseUp = () => {
    setDraggedNode(null);
    setIsPanning(false);
  };

  const handleSVGMouseDown = (e) => {
    setIsPanning(true);
    panStart.current = { x: e.clientX, y: e.clientY };
  };

  const getNodeColor = (type) => {
    switch (type) {
      case 'Process':
        return '#8b5cf6'; // Violet Purple
      case 'NetworkAddress':
        return '#06b6d4'; // Cyan Blue
      case 'File':
        return '#3b82f6'; // Royal Blue
      case 'RegistryKey':
        return '#eab308'; // Amber Yellow
      case 'User':
        return '#f97316'; // Vivid Orange
      default:
        return '#94a3b8'; // Slate Gray
    }
  };

  const handleResetView = () => {
    setZoomScale(1);
    setPanOffset({ x: 0, y: 0 });
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Visualizer Panel left 3 cols */}
      <div className="lg:col-span-3 space-y-4">
        <GraphToolbar
          zoomScale={zoomScale}
          setZoomScale={setZoomScale}
          onResetView={handleResetView}
          onReload={fetchGraph}
          onClearGraph={clearGraph}
        />

        {error && (
          <div className="p-3 bg-red-950/20 border border-red-900/30 text-red-400 text-xs rounded-xl">
            {error}
          </div>
        )}

        <GraphCanvas
          loading={loading}
          nodes={nodes}
          edges={edges}
          zoomScale={zoomScale}
          panOffset={panOffset}
          selectedNode={selectedNode}
          onNodeMouseDown={handleNodeMouseDown}
          onSVGMouseMove={handleSVGMouseMove}
          onSVGMouseUp={handleSVGMouseUp}
          onSVGMouseDown={handleSVGMouseDown}
          getNodeColor={getNodeColor}
          svgWidth={svgWidth}
          svgHeight={svgHeight}
        />
      </div>

      {/* Inspect Profile Sidebar right 1 col */}
      <div className="lg:col-span-1">
        <GraphEntityInspector
          selectedNode={selectedNode}
          getNodeColor={getNodeColor}
          edges={edges}
        />
      </div>
    </div>
  );
};

export default CaseGraph;
