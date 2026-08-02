import { useEffect, useRef, useState } from 'react'
import cytoscape from 'cytoscape'
import { getCaseGraph, clearCaseGraph, syncCaseGraph } from '../../services/graphService'
import Spinner from '../ui/Spinner'
import EmptyState from '../ui/EmptyState'
import ConfirmModal from '../ui/ConfirmModal'
import { GitBranch, Trash2, RefreshCw } from 'lucide-react'

const NODE_COLORS = {
  Process:'#3b82f6', File:'#10b981', NetworkAddress:'#f59e0b',
  RegistryKey:'#a855f7', User:'#ec4899', GenericEntity:'#6b7280', default:'#6b7280',
}

const GraphView = ({ caseId }) => {
  const containerRef = useRef(null)
  const cyRef        = useRef(null)
  const [loading, setLoading]         = useState(true)
  const [empty, setEmpty]             = useState(false)
  const [error, setError]             = useState(null)
  const [syncing, setSyncing]         = useState(false)
  const [syncMsg, setSyncMsg]         = useState(null)
  const [showConfirm, setShowConfirm] = useState(false)
  const [clearing, setClearing]       = useState(false)
  const [nodeCount, setNodeCount]     = useState(0)
  const [edgeCount, setEdgeCount]     = useState(0)

  const loadGraph = async () => {
    setLoading(true)
    try {
      const data  = await getCaseGraph(caseId)
      const nodes = data.nodes || []
      const edges = data.edges || []
      if (!nodes.length) { setEmpty(true); return }
      setNodeCount(nodes.length); setEdgeCount(edges.length); setEmpty(false)

      const elements = [
        ...nodes.map(n => ({ data: { id:n.id, label:n.label||n.id, color:NODE_COLORS[n.type]||NODE_COLORS.default } })),
        ...edges.map(e => ({ data: { id:`${e.source}-${e.target}`, source:e.source, target:e.target, label:e.action||'' } })),
      ]
      if (cyRef.current) cyRef.current.destroy()
      cyRef.current = cytoscape({
        container: containerRef.current, elements,
        style:[
          { selector:'node', style:{ label:'data(label)', 'background-color':'data(color)', color:'#fff', 'font-size':'10px', 'text-valign':'bottom', 'text-margin-y':4, width:28, height:28, 'border-width':2, 'border-color':'#1e2a3d' } },
          { selector:'edge', style:{ label:'data(label)', 'font-size':'8px', color:'#6b7fa3', 'line-color':'#3d4f6a', 'target-arrow-color':'#3d4f6a', 'target-arrow-shape':'triangle', 'curve-style':'bezier', width:1.5 } },
          { selector:'node:selected', style:{ 'border-width':3, 'border-color':'#60a5fa' } },
        ],
        layout:{ name:'cose', animate:true, padding:40 },
        wheelSensitivity:0.3,
      })
    } catch(e) {
      const msg = e?.response?.data?.detail || e?.message || 'Failed to load graph'
      setError(msg)
    }
    finally { setLoading(false) }
  }

  useEffect(() => { loadGraph(); return () => cyRef.current?.destroy() }, [caseId])

  const handleClear = async () => {
    setClearing(true)
    try { await clearCaseGraph(caseId); cyRef.current?.destroy(); setEmpty(true); setNodeCount(0); setEdgeCount(0) }
    finally { setClearing(false); setShowConfirm(false) }
  }

  const handleSync = async () => {
    setSyncing(true); setSyncMsg(null); setError(null)
    try {
      const res = await syncCaseGraph(caseId)
      setSyncMsg(`Synced ${res.synced} of ${res.total_events} events to Neo4j. Reloading…`)
      await loadGraph()
    } catch (e) {
      setError(e?.response?.data?.detail || 'Sync failed')
    } finally {
      setSyncing(false)
    }
  }

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:'12px', fontFamily:'-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif' }}>
      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between' }}>
        <p style={{ color:'#9aa8c0', fontSize:'12px', margin:0 }}>{nodeCount} nodes · {edgeCount} edges</p>
        <button onClick={() => setShowConfirm(true)} style={{
          display:'flex', alignItems:'center', gap:'6px',
          padding:'6px 12px', background:'transparent',
          border:'1px solid rgba(239,68,68,0.4)', borderRadius:'8px',
          color:'#fca5a5', fontSize:'12px', cursor:'pointer', fontFamily:'inherit',
          transition:'all 0.15s',
        }}
        onMouseEnter={e => { e.currentTarget.style.background='rgba(239,68,68,0.1)'; e.currentTarget.style.borderColor='rgba(239,68,68,0.7)' }}
        onMouseLeave={e => { e.currentTarget.style.background='transparent'; e.currentTarget.style.borderColor='rgba(239,68,68,0.4)' }}>
          <Trash2 size={12} /> Clear Graph
        </button>
      </div>

      <div style={{ position:'relative', minHeight:'480px', borderRadius:'12px', border:'1px solid #3d4f6a', background:'#1a2234', overflow:'hidden' }}>
        {loading && (
          <div style={{ position:'absolute', inset:0, display:'flex', alignItems:'center', justifyContent:'center', background:'rgba(26,34,52,0.8)', zIndex:10 }}>
            <Spinner size="lg" />
          </div>
        )}
      {!loading && empty
          ? <div style={{ display:'flex', alignItems:'center', justifyContent:'center', height:'100%', minHeight:'300px', flexDirection:'column', gap:'16px' }}>
              <EmptyState icon={GitBranch} title="No graph data" description="Neo4j has no nodes for this case. If you have parsed evidence, click Sync Graph to push events from MongoDB into Neo4j." />
              {syncMsg && <p style={{ color:'#34d399', fontSize:'12px', textAlign:'center' }}>{syncMsg}</p>}
              <button
                onClick={handleSync}
                disabled={syncing}
                style={{
                  display:'flex', alignItems:'center', gap:'6px',
                  padding:'8px 18px', background:'#4a7fe8', border:'none',
                  borderRadius:'8px', color:'#fff', fontSize:'13px',
                  fontWeight:'500', cursor: syncing ? 'not-allowed' : 'pointer',
                  fontFamily:'inherit', opacity: syncing ? 0.6 : 1,
                }}
              >
                <RefreshCw size={13} style={{ animation: syncing ? 'spin 1s linear infinite' : 'none' }} />
                {syncing ? 'Syncing…' : 'Sync Graph from Events'}
              </button>
            </div>
          : !loading && error
          ? <div style={{ display:'flex', alignItems:'center', justifyContent:'center', height:'100%', padding:'32px' }}>
              <div style={{ textAlign:'center' }}>
                <p style={{ color:'#fca5a5', fontSize:'13px', marginBottom:'12px' }}>{error}</p>
                <button onClick={loadGraph} style={{ background:'#2a3347', border:'1px solid #3d4f6a', color:'#9aa8c0', borderRadius:'8px', padding:'7px 16px', cursor:'pointer', fontSize:'12px', fontFamily:'inherit' }}>Retry</button>
              </div>
            </div>
          : <div ref={containerRef} style={{ width:'100%', height:'100%', minHeight:'480px' }} />
        }
      </div>

      {showConfirm && (
        <ConfirmModal
          title="Clear Knowledge Graph"
          message="This will delete all nodes and edges for this case. Events remain but you'll need to re-parse to rebuild the graph."
          onConfirm={handleClear} onCancel={() => setShowConfirm(false)} loading={clearing}
        />
      )}
    </div>
  )
}
export default GraphView
