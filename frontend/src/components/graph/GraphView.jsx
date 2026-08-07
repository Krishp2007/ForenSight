import { useEffect, useRef, useState, useCallback } from 'react'
import cytoscape from 'cytoscape'
import { getCaseGraphSummary, syncCaseGraph } from '../../services/graphService'
import { Spinner, EmptyState } from '../ui'
import {
  GitBranch, RefreshCw, ZoomIn, ZoomOut, Maximize2,
  AlertTriangle, Network, Monitor, Globe, Shield, Eye, ChevronDown,
  Key, ShieldAlert, Cpu, Clipboard, Map, Search, EyeOff, LayoutGrid, SlidersHorizontal
} from 'lucide-react'
import useRole from '../../hooks/useRole'
import NodeDetailsPanel from './NodeDetailsPanel'

// ── Risk Palette ──────────────────────────────────────────────────────────────
const RISK = {
  critical: '#ef4444',
  high:     '#f97316',
  medium:   '#eab308',
  low:      '#22c55e',
  info:     '#64748b',
}

// ── Node Type Visual Style Configurations ──────────────────────────────────────
const NODE_STYLES = {
  Process:      { color: '#3b82f6', shape: 'ellipse',         size: 34 },
  User:         { color: '#a855f7', shape: 'hexagon',         size: 32 },
  Host:         { color: '#8b5cf6', shape: 'star',            size: 38 },
  File:         { color: '#10b981', shape: 'round-rectangle', size: 30 },
  IPAddress:    { color: '#f59e0b', shape: 'diamond',         size: 32 },
  Domain:       { color: '#06b6d4', shape: 'pentagon',        size: 32 },
  RegistryKey:  { color: '#ec4899', shape: 'rectangle',       size: 28 },
  Service:      { color: '#f97316', shape: 'tag',             size: 28 },
  BrowserVisit: { color: '#0ea5e9', shape: 'round-rectangle', size: 26 },
  Evidence:     { color: '#6366f1', shape: 'cut-rectangle',   size: 36 },
  Port:         { color: '#94a3b8', shape: 'ellipse',         size: 22 },
  default:      { color: '#475569', shape: 'ellipse',         size: 28 },
}

// ── Investigation Views Definition ───────────────────────────────────────────
const VIEWS = [
  { id: 'entity',       label: 'Entity Graph',     icon: GitBranch,     desc: 'Investigator-centric semantic entities, no raw events' },
  { id: 'process_tree', label: 'Process Lineage',  icon: Monitor,       desc: 'Parent-child process tree lineage & executions' },
  { id: 'attack_path',  label: 'Attack Paths',     icon: ShieldAlert,   desc: 'Suspicious execution chains, anomalies, & LOLBins' },
  { id: 'network',      label: 'Network View',     icon: Network,       desc: 'Process connections to public IPs & domains' },
  { id: 'browser',      label: 'Browser Activity',  icon: Globe,         desc: 'Web history, domains visited, & visits counts' },
  { id: 'registry',     label: 'Registry & Run',   icon: Key,           desc: 'Registry modifications, autostart run keys, & persistence' },
  { id: 'auth',         label: 'Authentication',   icon: Shield,        desc: 'Logon sessions, execution users, & privilege tracking' },
  { id: 'ioc',          label: 'IOC & Anomalies',  icon: AlertTriangle, desc: 'Flagged ML anomalies & suspicious indicators only' },
]

const ALL = '__all__'

function nodeRiskColor(nodeData) {
  if (nodeData.is_anomaly || nodeData.risk_level === 'critical') return RISK.critical
  if (nodeData.risk_level === 'high' || (nodeData.anomaly_score || 0) > 0.75) return RISK.high
  if (nodeData.risk_level === 'medium' || (nodeData.anomaly_score || 0) > 0.5) return RISK.medium
  const sev = (nodeData.severity || '').toLowerCase()
  return RISK[sev] || 'rgba(255,255,255,0.18)'
}

const GraphView = ({ caseId, evidence = [] }) => {
  const containerRef = useRef(null)
  const cyRef        = useRef(null)

  // View & Query filters
  const [activeView,     setActiveView]     = useState('entity')
  const [selectedEvId,   setSelectedEvId]   = useState(ALL)
  const [anomalyOnly,    setAnomalyOnly]    = useState(false)
  const [hideBenign,     setHideBenign]     = useState(true)
  const [selectedSeverity, setSelectedSeverity] = useState(ALL)
  const [searchQuery,    setSearchQuery]    = useState('')
  const [layoutName,     setLayoutName]     = useState('cose')
  const [clusterByHost,  setClusterByHost]  = useState(false)

  // Path finding
  const [pathSource,     setPathSource]     = useState('')
  const [pathTarget,     setPathTarget]     = useState('')
  const [isPathMode,     setIsPathMode]     = useState(false)

  // UI state
  const [loading,        setLoading]        = useState(true)
  const [empty,          setEmpty]          = useState(false)
  const [error,          setError]          = useState(null)
  const [syncing,        setSyncing]        = useState(false)
  const [nodeCount,      setNodeCount]      = useState(0)
  const [edgeCount,      setEdgeCount]      = useState(0)
  const [selectedNode,   setSelectedNode]   = useState(null)
  const [attackChainActive, setAttackChainActive] = useState(false)

  // Menus
  const [showViewMenu,   setShowViewMenu]   = useState(false)
  const [showFilters,    setShowFilters]    = useState(false)
  const [showPathBar,    setShowPathBar]    = useState(false)

  const { canSyncGraph } = useRole()

  // ── Build cytoscape elements from API data ──────────────────────────────────
  const buildElements = useCallback((nodes, edges) => {
    const cyNodes = nodes.map(n => {
      const style = NODE_STYLES[n.type] || NODE_STYLES.default
      const riskBorder = nodeRiskColor(n)
      const suspicious = n.suspicious || (n.type === 'Process' && n.label.toLowerCase().includes('powershell'))

      return {
        data: {
          id:            n.id,
          label:         truncateLabel(n.label, n.type),
          type:          n.type,
          color:         style.color,
          shape:         style.shape,
          size:          style.size,
          riskBorder:    suspicious ? '#f97316' : riskBorder,
          is_anomaly:    n.is_anomaly || false,
          anomaly_score: n.anomaly_score || 0,
          suspicious,
          properties:    n.properties || {},
          explanation:   n.explanation || '',
          mitre_attack:  n.mitre_attack || [],
          risk_level:    n.risk_level || 'low',
          raw:           n,
        },
      }
    })

    const cyEdges = edges.map((e, i) => ({
      data: {
        id:          e.id || `edge-${i}`,
        source:      e.source,
        target:      e.target,
        label:       formatRelLabel(e.type, e.count),
        type:        e.type,
        count:       e.count || 1,
        is_anomaly:  e.is_anomaly || false,
        properties:  e.properties || {},
      },
    }))

    return [...cyNodes, ...cyEdges]
  }, [])

  // ── Load Graph Data from Server ─────────────────────────────────────────────
  const loadGraph = useCallback(async (view, evId, anomaly, benign, severityVal, queryStr) => {
    setLoading(true)
    setError(null)
    setSelectedNode(null)
    setAttackChainActive(false)
    try {
      const params = {
        view,
        anomaly_only: anomaly,
        hide_benign: benign,
        limit: 2000,
      }
      if (evId !== ALL) params.evidence_id = evId
      if (severityVal !== ALL) params.severity = severityVal
      if (queryStr) params.search_query = queryStr

      const data = await getCaseGraphSummary(caseId, params)
      const nodes = data.nodes || []
      const edges = data.edges || []

      if (!nodes.length) {
        if (cyRef.current) { cyRef.current.destroy(); cyRef.current = null }
        setEmpty(true)
        setNodeCount(0)
        setEdgeCount(0)
        setLoading(false)
        return
      }

      setEmpty(false)
      setNodeCount(nodes.length)
      setEdgeCount(edges.length)

      const elements = buildElements(nodes, edges)

      await new Promise(r => setTimeout(r, 10))
      if (!containerRef.current) return
      if (cyRef.current) { cyRef.current.destroy(); cyRef.current = null }

      cyRef.current = cytoscape({
        container: containerRef.current,
        elements,
        wheelSensitivity: 0.25,
        style: getCyStyle(),
        layout: getLayout(layoutName, view, nodes.length),
      })

      // Add double click neighborhood expansion
      cyRef.current.on('dbltap', 'node', evt => {
        const node = evt.target
        const neighborhood = node.neighborhood().add(node)
        cyRef.current.elements().addClass('faded')
        neighborhood.removeClass('faded')
      })

      cyRef.current.on('tap', 'node', evt => {
        const d = evt.target.data()
        setSelectedNode({
          id:            d.id,
          label:         d.label,
          type:          d.type,
          is_anomaly:    d.is_anomaly,
          anomaly_score: d.anomaly_score,
          suspicious:    d.suspicious,
          properties:    d.properties,
          explanation:   d.explanation,
          mitre_attack:  d.mitre_attack,
          risk_level:    d.risk_level,
          raw:           d.raw,
        })
      })

      cyRef.current.on('tap', evt => {
        if (evt.target === cyRef.current) {
          setSelectedNode(null)
          cyRef.current.elements().removeClass('faded')
          cyRef.current.elements().removeClass('highlighted-path')
          setAttackChainActive(false)
        }
      })

      // Add anomaly classes
      cyRef.current.nodes('[?is_anomaly]').addClass('anomaly')
      cyRef.current.nodes('[?suspicious]').addClass('suspicious')

    } catch (e) {
      console.error('[GraphView] loadGraph failed:', e)
      setError(e.response?.data?.detail || e.message || 'Failed to fetch graph data')
    } finally {
      setLoading(false)
    }
  }, [caseId, buildElements, layoutName])

  useEffect(() => {
    loadGraph(activeView, selectedEvId, anomalyOnly, hideBenign, selectedSeverity, searchQuery)
  }, [activeView, selectedEvId, anomalyOnly, hideBenign, selectedSeverity, searchQuery, caseId, layoutName])

  // ── Sync Handler ────────────────────────────────────────────────────────────
  const handleSync = async () => {
    if (syncing) return
    setSyncing(true)
    try {
      await syncCaseGraph(caseId)
      await loadGraph(activeView, selectedEvId, anomalyOnly, hideBenign, selectedSeverity, searchQuery)
    } catch (e) {
      setError(e.message || 'Sync failed')
    } finally {
      setSyncing(false)
    }
  }

  // ── Shortest Pathfinding Logic ──────────────────────────────────────────────
  const handleFindPath = () => {
    if (!cyRef.current || !pathSource || !pathTarget) return
    const cy = cyRef.current

    // Reset styles first
    cy.elements().removeClass('faded')
    cy.elements().removeClass('highlighted-path')

    const sourceNode = cy.getElementById(pathSource)
    const targetNode = cy.getElementById(pathTarget)

    if (!sourceNode.length || !targetNode.length) {
      alert('Source or Target node not found in current graph view.')
      return
    }

    const aStar = cy.elements().aStar({
      root: sourceNode,
      goal: targetNode,
      directed: false
    })

    if (aStar.found) {
      const pathEles = aStar.distance === 0 ? sourceNode : aStar.path
      cy.elements().addClass('faded')
      pathEles.removeClass('faded').addClass('highlighted-path')
      cy.fit(pathEles, 50)
    } else {
      alert('No path discovered between these entities in the current view.')
    }
  }

  // ── Show Attack Chain Shortcut ──────────────────────────────────────────────
  const handleShowAttackChain = () => {
    if (!cyRef.current) return
    const cy = cyRef.current

    if (attackChainActive) {
      cy.elements().removeClass('faded')
      cy.elements().removeClass('highlighted-path')
      setAttackChainActive(false)
      return
    }

    cy.elements().removeClass('faded')
    cy.elements().removeClass('highlighted-path')

    // Collect all anomaly/suspicious nodes
    const suspiciousNodes = cy.nodes().filter(n => {
      return n.data('is_anomaly') || n.data('suspicious') || n.data('risk_level') === 'critical' || n.data('risk_level') === 'high'
    })

    if (suspiciousNodes.length === 0) {
      alert('No suspicious or anomalous entities detected in the current view.')
      return
    }

    // Sort nodes chronologically based on timestamp to establish logical flow
    const sortedNodes = suspiciousNodes.sort((a, b) => {
      const tsA = new Date(a.data('properties')?.timestamp || 0)
      const tsB = new Date(b.data('properties')?.timestamp || 0)
      return tsA - tsB
    })

    const pathElements = cy.collection()

    // Trace shortest path sequentially between chronological highlights
    for (let i = 0; i < sortedNodes.length - 1; i++) {
      const start = sortedNodes[i]
      const end = sortedNodes[i + 1]
      const aStar = cy.elements().aStar({
        root: start,
        goal: end,
        directed: false
      })
      if (aStar.found) {
        pathElements.merge(aStar.path)
      }
    }

    // Fallback: If no connecting path exists, highlight suspicious nodes and their neighbors
    if (pathElements.length === 0) {
      pathElements.merge(suspiciousNodes)
      pathElements.merge(suspiciousNodes.neighborhood())
    } else {
      pathElements.merge(suspiciousNodes)
    }

    cy.elements().addClass('faded')
    pathElements.removeClass('faded').addClass('highlighted-path')
    cy.fit(pathElements, 40)
    setAttackChainActive(true)
  }

  // ── Assign Path Node Helper ──────────────────────────────────────────────────
  const handleAssignPathNode = (role, nodeId) => {
    if (role === 'source') setPathSource(nodeId)
    if (role === 'target') setPathTarget(nodeId)
    setShowPathBar(true)
  }

  const handleZoomIn  = () => cyRef.current?.animate({ zoom: { level: cyRef.current.zoom() * 1.25 }, duration: 180 })
  const handleZoomOut = () => cyRef.current?.animate({ zoom: { level: cyRef.current.zoom() * 0.75 }, duration: 180 })
  const handleFit     = () => { if (cyRef.current) cyRef.current.animate({ fit: { eles: cyRef.current.elements(), padding: 40 }, duration: 250 }) }
  const handleReset   = () => {
    if (!cyRef.current) return
    cyRef.current.layout(getLayout(layoutName, activeView, cyRef.current.nodes().length)).run()
  }

  useEffect(() => {
    if (!showViewMenu) return
    const close = () => setShowViewMenu(false)
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [showViewMenu])

  const activeViewDef = VIEWS.find(v => v.id === activeView) || VIEWS[0]

  return (
    <div style={{ position: 'relative', width: '100%', height: '780px', background: '#050811', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.08)', display: 'flex', flexDirection: 'column' }}>

      {/* ── Main Toolbar ─────────────────────────────────────────────────────── */}
      <div style={{ padding: '12px 18px', borderBottom: '1px solid rgba(255,255,255,0.07)', background: 'rgba(9, 13, 26, 0.9)', backdropFilter: 'blur(12px)', display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap', zIndex: 30, position: 'relative', borderRadius: '16px 16px 0 0', overflow: 'visible' }}>

        {/* View selector dropdown */}
        <div style={{ position: 'relative' }} onMouseDown={e => e.stopPropagation()}>
          <button
            onClick={() => { setShowViewMenu(v => !v); setShowFilters(false); setShowPathBar(false) }}
            style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '7.5px 14px', borderRadius: '10px', background: 'rgba(99,102,241,0.14)', border: '1px solid rgba(99,102,241,0.35)', color: '#c7d2fe', cursor: 'pointer', fontSize: '13px', fontWeight: 600, fontFamily: 'inherit' }}
          >
            <activeViewDef.icon size={15} />
            {activeViewDef.label}
            <ChevronDown size={13} />
          </button>
          {showViewMenu && (
            <div style={{ position: 'absolute', top: 'calc(100% + 6px)', left: 0, zIndex: 50, background: 'rgba(9, 13, 26, 0.98)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', padding: '6px', minWidth: '240px', boxShadow: '0 16px 48px rgba(0,0,0,0.7)' }}>
              {VIEWS.map(v => (
                <button
                  key={v.id}
                  onClick={() => { setActiveView(v.id); setShowViewMenu(false) }}
                  className={`view-menu-item ${activeView === v.id ? 'view-menu-item-active' : ''}`}
                  style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', width: '100%', padding: '9px 12px', borderRadius: '8px', background: 'transparent', border: 'none', color: activeView === v.id ? '#a5b4fc' : '#94a3b8', cursor: 'pointer', textAlign: 'left', fontFamily: 'inherit' }}
                >
                  <v.icon size={15} style={{ marginTop: 2, flexShrink: 0 }} />
                  <div>
                    <div style={{ fontSize: '12.5px', fontWeight: 700, color: activeView === v.id ? '#fff' : '#cbd5e1' }}>{v.label}</div>
                    <div style={{ fontSize: '11px', color: '#576f93', marginTop: '1px', lineHeight: '1.3' }}>{v.desc}</div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Live Text Search */}
        <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
          <Search size={14} style={{ position: 'absolute', left: 10, color: '#475569' }} />
          <input
            type="text"
            placeholder="Search process, IP, user, host..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            style={{ padding: '7.5px 12px 7.5px 30px', borderRadius: '10px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', color: '#f8fafc', fontSize: '12.5px', outline: 'none', width: '220px', fontFamily: 'inherit', transition: 'all 0.15s' }}
            onFocus={e => e.target.style.borderColor = 'rgba(99,102,241,0.45)'}
            onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.08)'}
          />
        </div>

        {/* Filters Toggle Button */}
        <button
          onClick={() => { setShowFilters(f => !f); setShowViewMenu(false); setShowPathBar(false) }}
          style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '7.5px 12px', borderRadius: '10px', background: showFilters ? 'rgba(99,102,241,0.18)' : 'rgba(255,255,255,0.03)', border: showFilters ? '1px solid #6366f1' : '1px solid rgba(255,255,255,0.08)', color: showFilters ? '#a5b4fc' : '#94a3b8', fontSize: '12.5px', fontWeight: 500, cursor: 'pointer', fontFamily: 'inherit' }}
        >
          <SlidersHorizontal size={13} />
          Filters
        </button>

        {/* Pathfinding Toggle */}
        <button
          onClick={() => { setShowPathBar(p => !p); setShowViewMenu(false); setShowFilters(false) }}
          style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '7.5px 12px', borderRadius: '10px', background: showPathBar ? 'rgba(99,102,241,0.18)' : 'rgba(255,255,255,0.03)', border: showPathBar ? '1px solid #6366f1' : '1px solid rgba(255,255,255,0.08)', color: showPathBar ? '#a5b4fc' : '#94a3b8', fontSize: '12.5px', fontWeight: 500, cursor: 'pointer', fontFamily: 'inherit' }}
        >
          <Map size={13} />
          Path Finder
        </button>

        {/* Quick Attack Chain Button */}
        <button
          onClick={handleShowAttackChain}
          style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '6px', 
            padding: '7.5px 12px', 
            borderRadius: '10px', 
            background: attackChainActive ? '#ef4444' : 'rgba(239,68,68,0.15)', 
            border: attackChainActive ? '1px solid #f87171' : '1px solid rgba(239,68,68,0.35)', 
            color: attackChainActive ? '#fff' : '#f87171', 
            fontSize: '12.5px', 
            fontWeight: 600, 
            cursor: 'pointer', 
            fontFamily: 'inherit', 
            transition: 'all 0.15s',
            boxShadow: attackChainActive ? '0 0 14px rgba(239,68,68,0.45)' : 'none'
          }}
          title="Highlight suspicious activities chain"
        >
          {attackChainActive ? 'Hide Attack Chain' : 'Show Attack Chain'}
        </button>

        {/* Stats */}
        <span style={{ fontSize: '11px', color: '#475569', background: 'rgba(255,255,255,0.03)', padding: '4px 10px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.05)', whiteSpace: 'nowrap' }}>
          {nodeCount} nodes · {edgeCount} edges
        </span>

        <div style={{ flex: 1 }} />

        {/* Toolbar camera actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button onClick={() => loadGraph(activeView, selectedEvId, anomalyOnly, hideBenign, selectedSeverity, searchQuery)} className="graph-btn" title="Refresh">
            <RefreshCw size={13} />
          </button>
          {canSyncGraph && (
            <button onClick={handleSync} disabled={syncing} className="graph-btn" title="Sync Graph" style={{ opacity: syncing ? 0.5 : 1 }}>
              {syncing ? <Spinner size="xs" /> : <span style={{ fontSize: '11.5px', fontWeight: 700 }}>Sync Graph</span>}
            </button>
          )}
          <div style={{ width: 1, height: 16, background: 'rgba(255,255,255,0.08)' }} />
          <button onClick={handleZoomIn}  className="graph-btn" title="Zoom In"><ZoomIn size={13} /></button>
          <button onClick={handleZoomOut} className="graph-btn" title="Zoom Out"><ZoomOut size={13} /></button>
          <button onClick={handleFit}     className="graph-btn" title="Fit View"><Maximize2 size={13} /></button>
        </div>
      </div>

      {/* ── Advanced Filters Drawer ────────────────────────────────────────── */}
      {showFilters && (
        <div style={{ padding: '12px 18px', borderBottom: '1px solid rgba(255,255,255,0.06)', background: 'rgba(7, 10, 20, 0.95)', display: 'flex', gap: '14px', alignItems: 'center', flexWrap: 'wrap', zIndex: 29 }}>
          {/* Evidence selector */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <span style={{ fontSize: '10px', color: '#475569', fontWeight: 700, textTransform: 'uppercase' }}>Evidence Scope</span>
            <select
              value={selectedEvId}
              onChange={e => setSelectedEvId(e.target.value)}
              className="graph-select"
              style={{ padding: '5px 10px', fontSize: '12px', minWidth: '150px' }}
            >
              <option value={ALL}>All Evidence Scope</option>
              {evidence.map(ev => {
                const id = ev.id || ev._id
                return <option key={id} value={id}>{ev.filename || `Evidence (${id.slice(-6)})`}</option>
              })}
            </select>
          </div>

          {/* Severity selector */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <span style={{ fontSize: '10px', color: '#475569', fontWeight: 700, textTransform: 'uppercase' }}>Min Severity</span>
            <select
              value={selectedSeverity}
              onChange={e => setSelectedSeverity(e.target.value)}
              className="graph-select"
              style={{ padding: '5px 10px', fontSize: '12px', minWidth: '130px' }}
            >
              <option value={ALL}>All Severities</option>
              <option value="critical">Critical Only</option>
              <option value="high">High & Critical</option>
              <option value="medium">Medium +</option>
              <option value="low">Low +</option>
            </select>
          </div>

          {/* Layout Presets */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <span style={{ fontSize: '10px', color: '#475569', fontWeight: 700, textTransform: 'uppercase' }}>Layout Presets</span>
            <select
              value={layoutName}
              onChange={e => setLayoutName(e.target.value)}
              className="graph-select"
              style={{ padding: '5px 10px', fontSize: '12px', minWidth: '130px' }}
            >
              <option value="cose">Auto / Force-Directed</option>
              <option value="breadthfirst">Hierarchical Tree</option>
              <option value="concentric">Concentric Radial</option>
              <option value="circle">Circular Cluster</option>
            </select>
          </div>

          {/* Toggle Filters */}
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center', alignSelf: 'flex-end', height: '32px' }}>
            {/* Anomalies Only */}
            <button
              onClick={() => setAnomalyOnly(v => !v)}
              className={`graph-btn-anomaly ${anomalyOnly ? 'graph-btn-anomaly-active' : 'graph-btn-anomaly-inactive'}`}
              style={{ padding: '5px 12px', fontSize: '12px' }}
            >
              <AlertTriangle size={12} />
              Anomalies Only
            </button>

            {/* Hide Benign Activity */}
            <button
              onClick={() => setHideBenign(v => !v)}
              className={`graph-btn-anomaly ${hideBenign ? 'graph-btn-anomaly-active' : 'graph-btn-anomaly-inactive'}`}
              style={{ padding: '5px 12px', fontSize: '12px' }}
            >
              {hideBenign ? <EyeOff size={12} /> : <Eye size={12} />}
              Hide Benign Windows OS
            </button>
          </div>
        </div>
      )}

      {/* ── Path Finder Controls Drawer ────────────────────────────────────── */}
      {showPathBar && (
        <div style={{ padding: '10px 18px', borderBottom: '1px solid rgba(255,255,255,0.06)', background: 'rgba(7, 10, 20, 0.95)', display: 'flex', gap: '10px', alignItems: 'center', zIndex: 29 }}>
          <span style={{ fontSize: '11.5px', color: '#818cf8', fontWeight: 700 }}>A* Shortest Path:</span>

          <input
            type="text"
            placeholder="Select Start Node..."
            value={pathSource}
            onChange={e => setPathSource(e.target.value)}
            style={{ padding: '5px 10px', borderRadius: '6px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', fontSize: '11px', outline: 'none', width: '160px' }}
          />

          <span style={{ color: '#475569', fontSize: '11px' }}>→</span>

          <input
            type="text"
            placeholder="Select End Node..."
            value={pathTarget}
            onChange={e => setPathTarget(e.target.value)}
            style={{ padding: '5px 10px', borderRadius: '6px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', fontSize: '11px', outline: 'none', width: '160px' }}
          />

          <button
            onClick={handleFindPath}
            style={{ padding: '5px 12px', borderRadius: '6px', background: '#3b82f6', color: '#fff', border: 'none', fontSize: '11px', fontWeight: 600, cursor: 'pointer' }}
          >
            Find Path
          </button>

          <button
            onClick={() => { setPathSource(''); setPathTarget(''); if (cyRef.current) { cyRef.current.elements().removeClass('faded'); cyRef.current.elements().removeClass('highlighted-path') } }}
            style={{ padding: '5px 10px', borderRadius: '6px', background: 'rgba(255,255,255,0.05)', color: '#94a3b8', border: 'none', fontSize: '11px', cursor: 'pointer' }}
          >
            Clear
          </button>
        </div>
      )}

      {/* ── Main Panel (Sidebar Legend + Cytoscape Canvas) ────────────────────── */}
      <div style={{ flex: 1, position: 'relative', display: 'flex', overflow: 'hidden' }}>

        {/* Sidebar Legend */}
        <div style={{ width: '135px', flexShrink: 0, borderRight: '1px solid rgba(255,255,255,0.05)', padding: '14px 10px', overflowY: 'auto', background: 'rgba(7,11,20,0.6)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <div style={{ fontSize: '9px', color: '#475569', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: '6px', paddingLeft: '4px' }}>Node Types</div>
          {Object.entries(NODE_STYLES).filter(([k]) => k !== 'default').map(([type, style]) => (
            <div key={type} style={{ display: 'flex', alignItems: 'center', gap: '7px', padding: '4px', borderRadius: '6px' }}>
              <div style={{ width: 10, height: 10, borderRadius: type === 'Host' ? '50%' : '2px', background: style.color, flexShrink: 0 }} />
              <span style={{ fontSize: '10.5px', color: '#94a3b8', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{type}</span>
            </div>
          ))}
          <div style={{ marginTop: '12px', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '12px' }}>
            <div style={{ fontSize: '9px', color: '#475569', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: '8px', paddingLeft: '4px' }}>Risk levels</div>
            {[['Critical', RISK.critical], ['High', RISK.high], ['Medium', RISK.medium], ['Low', RISK.low]].map(([label, color]) => (
              <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '7px', padding: '3px 4px' }}>
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: color, flexShrink: 0 }} />
                <span style={{ fontSize: '10px', color: '#94a3b8' }}>{label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Canvas area */}
        <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>

          {/* Loading overlay */}
          {loading && (
            <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '12px', background: '#050811', zIndex: 10 }}>
              <Spinner />
              <span style={{ color: '#60a5fa', fontSize: '13px' }}>Aggregating {activeViewDef.label} Presets…</span>
            </div>
          )}

          {/* Error overlay */}
          {error && !loading && (
            <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '14px', background: '#050811', zIndex: 10 }}>
              <div style={{ color: '#ef4444', fontSize: '14px', textAlign: 'center', maxWidth: '400px', padding: '0 24px' }}>⚠ {error}</div>
              <button onClick={() => loadGraph(activeView, selectedEvId, anomalyOnly, hideBenign, selectedSeverity, searchQuery)} style={{ padding: '8px 20px', borderRadius: '8px', background: 'rgba(99,102,241,0.15)', border: '1px solid rgba(99,102,241,0.4)', color: '#a5b4fc', cursor: 'pointer', fontSize: '13px', fontFamily: 'inherit' }}>
                Retry
              </button>
            </div>
          )}

          {/* Empty overlay */}
          {empty && !loading && !error && (
            <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '16px', background: '#050811', zIndex: 10 }}>
              <EmptyState title="No graph data for this view" description="Try a different view, or sync if evidence has been processed." />
              {canSyncGraph && (
                <button onClick={handleSync} disabled={syncing} style={{ padding: '9px 22px', borderRadius: '10px', background: 'rgba(99,102,241,0.18)', border: '1px solid rgba(99,102,241,0.45)', color: '#a5b4fc', cursor: syncing ? 'wait' : 'pointer', fontSize: '13px', fontWeight: 600, fontFamily: 'inherit', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {syncing ? <><Spinner size="xs" /> Syncing…</> : 'Sync Graph'}
                </button>
              )}
            </div>
          )}

          {/* Cytoscape canvas */}
          <div ref={containerRef} style={{ position: 'absolute', inset: 0, visibility: (loading || empty || error) ? 'hidden' : 'visible' }} />

          {/* Node details panel */}
          {selectedNode && (
            <NodeDetailsPanel
              node={selectedNode}
              onClose={() => setSelectedNode(null)}
              onSetPathNode={handleAssignPathNode}
            onExpandNeighbors={(node, isActive) => {
                if (!cyRef.current) return
                if (isActive) {
                  // Cancel: restore all elements without moving the camera
                  cyRef.current.elements().removeClass('faded')
                  return
                }
                const cyNode = cyRef.current.getElementById(node.id)
                if (!cyNode.length) return
                cyRef.current.elements().removeClass('faded')
                const neighborhood = cyNode.neighborhood().add(cyNode)
                cyRef.current.elements().not(neighborhood).addClass('faded')
              }}
            />
          )}
        </div>
      </div>
    </div>
  )
}

// ── Label Helpers ─────────────────────────────────────────────────────────────
function truncateLabel(label, type) {
  if (!label) return '?'
  if (type === 'Process') {
    const parts = label.replace(/\\/g, '/').split('/')
    return parts[parts.length - 1] || label
  }
  if (label.length > 22) return label.slice(0, 20) + '…'
  return label
}

function formatRelLabel(type, count) {
  const nice = (type || '')
    .replace(/_/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, c => c.toUpperCase())
  return count > 1 ? `${nice} (${count})` : nice
}

// ── Cytoscape Layout Rules ─────────────────────────────────────────────────────
function getLayout(layoutPreset, view, nodeCount) {
  if (view === 'process_tree' || layoutPreset === 'breadthfirst') {
    return {
      name: 'breadthfirst',
      directed: true,
      padding: 30,
      spacingFactor: 1.35,
      animate: false,
    }
  }
  if (view === 'browser' || layoutPreset === 'concentric') {
    return {
      name: 'concentric',
      concentric: n => n.data('type') === 'Evidence' ? 3 : n.data('type') === 'Domain' ? 1 : 2,
      levelWidth: () => 2,
      padding: 35,
      animate: false,
    }
  }
  if (layoutPreset === 'circle' || nodeCount < 30) {
    return { name: 'circle', padding: 45, animate: false }
  }
  return {
    name: 'cose',
    animate: false,
    padding: 35,
    nodeRepulsion: () => 8500,
    idealEdgeLength: () => 85,
    edgeElasticity: () => 100,
    gravity: 0.25,
    numIter: 1000,
    coolingFactor: 0.95,
  }
}

// ── Cytoscape Styles Sheet ────────────────────────────────────────────────────
function getCyStyle() {
  return [
    {
      selector: 'node',
      style: {
        'background-color':   'data(color)',
        'shape':              'data(shape)',
        'width':              'data(size)',
        'height':             'data(size)',
        'label':              'data(label)',
        'color':              '#cbd5e1',
        'font-size':          '10px',
        'font-family':        'ui-monospace, SFMono-Regular, monospace',
        'text-valign':        'bottom',
        'text-margin-y':      5,
        'text-max-width':     '110px',
        'text-wrap':          'ellipsis',
        'border-width':       2,
        'border-color':       'data(riskBorder)',
        'border-opacity':     0.9,
      },
    },
    {
      selector: 'node.anomaly',
      style: {
        'border-width':   4.5,
        'border-color':   '#ef4444',
        'border-opacity': 1,
      },
    },
    {
      selector: 'node.suspicious',
      style: {
        'border-width':   4,
        'border-color':   '#f97316',
        'border-opacity': 1,
      },
    },
    {
      selector: 'node:selected',
      style: {
        'border-width':   4,
        'border-color':   '#f59e0b',
        'width':          'mapData(size, 22, 40, 26, 46)',
        'height':         'mapData(size, 22, 40, 26, 46)',
      },
    },
    {
      selector: 'node.faded',
      style: { opacity: 0.15 },
    },
    {
      selector: 'edge',
      style: {
        'width':                   'mapData(count, 1, 100, 1.5, 5)',
        'line-color':              'rgba(100, 116, 139, 0.55)',
        'target-arrow-color':      'rgba(100, 116, 139, 0.7)',
        'target-arrow-shape':      'triangle',
        'curve-style':             'bezier',
        'label':                   'data(label)',
        'font-size':               '9px',
        'font-family':             'ui-monospace, SFMono-Regular, monospace',
        'font-weight':             '600',
        'color':                   '#94a3b8',
        'text-rotation':           'autorotate',
        'text-margin-y':           -8,
        'text-background-color':   '#0f172a',
        'text-background-opacity': 0.92,
        'text-background-padding': '3px',
        'text-border-color':       'rgba(148,163,184,0.2)',
        'text-border-width':       1,
        'text-border-opacity':     1,
      },
    },
    {
      selector: 'edge.highlighted-path',
      style: {
        'line-color':         '#ef4444',
        'target-arrow-color': '#ef4444',
        'width':              4.5,
        'opacity':            1,
      },
    },
    {
      selector: 'node.highlighted-path',
      style: {
        'border-width':  4,
        'border-color':  '#10b981',
        'opacity':       1,
      },
    },
    {
      selector: 'edge[?is_anomaly]',
      style: {
        'line-color':         '#ef4444',
        'target-arrow-color': '#ef4444',
        'width':              3,
        'line-style':         'dashed',
      },
    },
    {
      selector: 'edge.faded',
      style: { opacity: 0.08 },
    },
  ]
}

export default GraphView
