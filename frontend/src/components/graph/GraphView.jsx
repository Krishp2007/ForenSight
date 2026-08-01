import { useEffect, useRef, useState } from 'react'
import cytoscape from 'cytoscape'
import { getCaseGraph, clearCaseGraph } from '../../services/graphService'
import Spinner from '../ui/Spinner'
import EmptyState from '../ui/EmptyState'
import ConfirmModal from '../ui/ConfirmModal'
import { GitBranch, Trash2 } from 'lucide-react'

// Node color by type
const NODE_COLORS = {
  process: '#3b82f6',
  file: '#10b981',
  ip: '#f59e0b',
  registry: '#a855f7',
  user: '#ec4899',
  domain: '#f97316',
  default: '#6b7280',
}

const GraphView = ({ caseId }) => {
  const containerRef = useRef(null)
  const cyRef = useRef(null)
  const [loading, setLoading] = useState(true)
  const [empty, setEmpty] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [clearing, setClearing] = useState(false)
  const [nodeCount, setNodeCount] = useState(0)
  const [edgeCount, setEdgeCount] = useState(0)

  const loadGraph = async () => {
    setLoading(true)
    try {
      const data = await getCaseGraph(caseId)
      const nodes = data.nodes || []
      const edges = data.edges || []

      if (nodes.length === 0) { setEmpty(true); return }
      setNodeCount(nodes.length)
      setEdgeCount(edges.length)
      setEmpty(false)

      const elements = [
        ...nodes.map((n) => ({
          data: {
            id: n.id,
            label: n.label || n.id,
            type: n.type || 'default',
            color: NODE_COLORS[n.type] || NODE_COLORS.default,
          },
        })),
        ...edges.map((e) => ({
          data: {
            id: `${e.source}-${e.target}-${e.relation}`,
            source: e.source,
            target: e.target,
            label: e.relation || '',
          },
        })),
      ]

      if (cyRef.current) cyRef.current.destroy()

      cyRef.current = cytoscape({
        container: containerRef.current,
        elements,
        style: [
          {
            selector: 'node',
            style: {
              label: 'data(label)',
              'background-color': 'data(color)',
              color: '#fff',
              'font-size': '10px',
              'text-valign': 'bottom',
              'text-margin-y': 4,
              width: 30,
              height: 30,
              'border-width': 2,
              'border-color': '#1f2937',
            },
          },
          {
            selector: 'edge',
            style: {
              label: 'data(label)',
              'font-size': '9px',
              color: '#9ca3af',
              'line-color': '#374151',
              'target-arrow-color': '#374151',
              'target-arrow-shape': 'triangle',
              'curve-style': 'bezier',
              width: 1.5,
            },
          },
          {
            selector: 'node:selected',
            style: {
              'border-width': 3,
              'border-color': '#60a5fa',
            },
          },
        ],
        layout: { name: 'cose', animate: true, padding: 40 },
        wheelSensitivity: 0.3,
      })
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadGraph()
    return () => cyRef.current?.destroy()
  }, [caseId])

  const handleClear = async () => {
    setClearing(true)
    try {
      await clearCaseGraph(caseId)
      cyRef.current?.destroy()
      setEmpty(true)
      setNodeCount(0)
      setEdgeCount(0)
    } finally {
      setClearing(false)
      setShowConfirm(false)
    }
  }

  return (
    <div className="flex flex-col gap-3 h-full">
      <div className="flex items-center justify-between">
        <p className="text-gray-400 text-xs">{nodeCount} nodes · {edgeCount} edges</p>
        <button
          onClick={() => setShowConfirm(true)}
          className="flex items-center gap-1.5 text-xs text-red-400 hover:text-red-300 border border-red-800 hover:border-red-600 px-3 py-1.5 rounded-lg transition-colors"
        >
          <Trash2 size={12} />
          Clear Graph
        </button>
      </div>

      <div className="relative flex-1 min-h-[480px] rounded-xl border border-gray-700 bg-gray-900 overflow-hidden">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900/80 z-10">
            <Spinner size="lg" />
          </div>
        )}
        {!loading && empty ? (
          <EmptyState icon={GitBranch} title="No graph data" description="Parse evidence files to populate the knowledge graph." />
        ) : (
          <div ref={containerRef} className="w-full h-full" />
        )}
      </div>

      {showConfirm && (
        <ConfirmModal
          title="Clear Knowledge Graph"
          message="This will delete all nodes and edges for this case. The event data remains, but you'll need to re-parse to rebuild the graph."
          onConfirm={handleClear}
          onCancel={() => setShowConfirm(false)}
          loading={clearing}
        />
      )}
    </div>
  )
}

export default GraphView
