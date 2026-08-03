import { useEffect, useRef, useState } from 'react'
import cytoscape from 'cytoscape'
import { getCaseGraph, getEvidenceGraph, clearCaseGraph, syncCaseGraph } from '../../services/graphService'
import { Spinner, EmptyState, ConfirmModal } from '../ui'
import { GitBranch, Trash2, RefreshCw, ChevronDown } from 'lucide-react'
import useRole from '../../hooks/useRole'

// Register fcose layout if available — guarantees zero node overlap
let fcoseAvailable = false
try {
  const fcose = require('cytoscape-fcose')
  cytoscape.use(fcose)
  fcoseAvailable = true
} catch {
  // cytoscape-fcose not installed yet — fallback to cose
}

// Entity-type colours (used when viewing a single file)
const TYPE_COLORS = {
  Process:        '#3b82f6',
  File:           '#10b981',
  NetworkAddress: '#f59e0b',
  RegistryKey:    '#a855f7',
  User:           '#ec4899',
  GenericEntity:  '#6b7280',
  default:        '#6b7280',
}

// Distinct palette for evidence files (used in "All files" mode)
const FILE_PALETTE = [
  '#60a5fa', '#34d399', '#fbbf24', '#f87171',
  '#a78bfa', '#fb923c', '#67e8f9', '#86efac',
  '#f9a8d4', '#fde68a', '#c4b5fd', '#6ee7b7',
]

const ALL = '__all__'

const GraphView = ({ caseId, evidence = [] }) => {
  const containerRef = useRef(null)
  const cyRef        = useRef(null)

  const [selectedId,   setSelectedId]   = useState(ALL)
  const [loading,      setLoading]      = useState(true)
  const [empty,        setEmpty]        = useState(false)
  const [error,        setError]        = useState(null)
  const [syncing,      setSyncing]      = useState(false)
  const [syncMsg,      setSyncMsg]      = useState(null)
  const [showConfirm,  setShowConfirm]  = useState(false)
  const [clearing,     setClearing]     = useState(false)
  const [nodeCount,    setNodeCount]    = useState(0)
  const [edgeCount,    setEdgeCount]    = useState(0)
  // legend items: [{ label, color }]
  const [legend,       setLegend]       = useState([])

  const { canClearGraph, canSyncGraph } = useRole()

  const parsedFiles = evidence.filter(e => e.status === 'parsed')

  const selectedLabel = selectedId === ALL
    ? 'All files'
    : (parsedFiles.find(e => e.id === selectedId)?.filename || 'Unknown')

  // Build evidence_id → { color, filename } map
  const buildFileColorMap = () => {
    const map = {}
    parsedFiles.forEach((ev, i) => {
      map[ev.id] = {
        color:    FILE_PALETTE[i % FILE_PALETTE.length],
        filename: ev.filename,
      }
    })
    return map
  }

  const loadGraph = async (evId) => {
    setLoading(true)
    setError(null)
    setSyncMsg(null)

    try {
      const data  = evId === ALL
        ? await getCaseGraph(caseId)
        : await getEvidenceGraph(caseId, evId)

      const nodes = data.nodes || []
      const edges = data.edges || []

      if (!nodes.length) {
        if (cyRef.current) { cyRef.current.destroy(); cyRef.current = null }
        setEmpty(true)
        setNodeCount(0)
        setEdgeCount(0)
        setLegend([])
        return
      }

      setEmpty(false)

      // ── Colour strategy ──────────────────────────────────────────────────
      // All files → colour nodes by which evidence file they came from
      // Single file → colour nodes by entity type
      const fileColorMap = buildFileColorMap()
      const isAllMode    = evId === ALL

      const cyElements = [
        ...nodes.map(n => ({
          data: {
            id:    n.id,
            label: n.label || n.id,
            color: isAllMode
              ? (fileColorMap[n.evidence_id]?.color || '#6b7280')
              : (TYPE_COLORS[n.type]  || TYPE_COLORS.default),
            evidence_id: n.evidence_id || '',
            node_type:   n.type || 'GenericEntity',
          },
        })),
        ...edges.map(e => ({
          data: {
            id:      `${e.source}__${e.target}__${e.action || ''}__${e.evidence_id || ''}`,
            source:  e.source,
            target:  e.target,
            label:   e.action || '',
            anomaly: e.is_anomaly || false,
            evidence_id: e.evidence_id || '',
          },
        })),
      ]

      // Wait one tick for container to be visible
      await new Promise(r => setTimeout(r, 0))
      if (!containerRef.current) return

      if (cyRef.current) { cyRef.current.destroy(); cyRef.current = null }

      cyRef.current = cytoscape({
        container: containerRef.current,
        elements:  cyElements,
        style: [
          {
            selector: 'node',
            style: {
              label:              'data(label)',
              'background-color': 'data(color)',
              color:              '#cbd5e1',
              'font-size':        '10px',
              'font-weight':      '600',
              'text-valign':      'bottom',
              'text-halign':      'center',
              'text-margin-y':    6,
              'text-max-width':   '90px',
              'text-wrap':        'ellipsis',
              width:              34,
              height:             34,
              'border-width':     2,
              'border-color':     '#1e2a3d',
              'min-zoomed-font-size': 7,
            },
          },
          {
            selector: 'edge',
            style: {
              label:                '',
              'font-size':          '8px',
              color:                '#94a3b8',
              'line-color':         '#3d4f6a',
              'target-arrow-color': '#3d4f6a',
              'target-arrow-shape': 'triangle',
              'arrow-scale':        1.2,
              'curve-style':        'bezier',
              'control-point-step-size': 50,
              width:                1.8,
            },
          },
          {
            selector: 'edge:active, edge.hover',
            style: {
              label:       'data(label)',
              'font-size': '9px',
              color:       '#e2e8f0',
              'text-background-color':   '#1e2a3d',
              'text-background-opacity': 1,
              'text-background-padding': '2px',
              'text-border-color':       '#3d4f6a',
              'text-border-opacity':     1,
              'text-border-width':       1,
            },
          },
          {
            selector: 'edge[?anomaly]',
            style: {
              'line-color':         '#f87171',
              'target-arrow-color': '#f87171',
              width:                2.8,
            },
          },
          {
            selector: 'node:selected',
            style: { 'border-width': 3.5, 'border-color': '#60a5fa' },
          },
        ],
        layout: {
          name:             'cose',
          animate:          true,
          animationDuration:750,
          padding:          80,
          fit:              true,
          randomize:        true,
          // High node repulsion — pushes nodes apart strongly to eliminate overlapping
          nodeRepulsion:    () => 3500000,
          // Ideal edge length — creates generous spacing between connected entities
          idealEdgeLength:  () => 200,
          edgeElasticity:   () => 100,
          gravity:          0.12,
          numIter:          2500,
          nodeOverlap:      0,
          componentSpacing: 150,
          coolingFactor:    0.99,
          minTemp:          1.0,
        },

        wheelSensitivity: 0.3,
      })

      // Counts from Cytoscape — accurate after dedup
      setNodeCount(cyRef.current.nodes().length)
      setEdgeCount(cyRef.current.edges().length)

      // Edge label on hover
      cyRef.current.on('mouseover', 'edge', e => e.target.addClass('hover'))
      cyRef.current.on('mouseout',  'edge', e => e.target.removeClass('hover'))

      // Build legend
      if (isAllMode) {
        // Group by evidence file
        const seenFiles = new Set()
        const items = []
        nodes.forEach(n => {
          const fid = n.evidence_id
          if (fid && !seenFiles.has(fid)) {
            seenFiles.add(fid)
            const info = fileColorMap[fid]
            if (info) items.push({ label: info.filename, color: info.color, type: 'file' })
          }
        })
        // Anomaly indicator
        const hasAnomaly = edges.some(e => e.is_anomaly)
        if (hasAnomaly) items.push({ label: 'Anomaly edge', color: '#f87171', type: 'edge' })
        setLegend(items)
      } else {
        // Entity type legend
        const seenTypes = new Set()
        const items = []
        nodes.forEach(n => {
          if (!seenTypes.has(n.type)) {
            seenTypes.add(n.type)
            items.push({ label: n.type || 'GenericEntity', color: TYPE_COLORS[n.type] || TYPE_COLORS.default, type: 'node' })
          }
        })
        const hasAnomaly = edges.some(e => e.is_anomaly)
        if (hasAnomaly) items.push({ label: 'Anomaly edge', color: '#f87171', type: 'edge' })
        setLegend(items)
      }

    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || 'Failed to load graph')
      setEmpty(false)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadGraph(selectedId)
    return () => { if (cyRef.current) { cyRef.current.destroy(); cyRef.current = null } }
  }, [caseId, selectedId]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleClear = async () => {
    setClearing(true)
    try {
      await clearCaseGraph(caseId)
      if (cyRef.current) { cyRef.current.destroy(); cyRef.current = null }
      setEmpty(true); setNodeCount(0); setEdgeCount(0); setLegend([])
    } finally { setClearing(false); setShowConfirm(false) }
  }

  const handleSync = async () => {
    setSyncing(true); setError(null)
    try {
      const res = await syncCaseGraph(caseId)
      setSyncMsg(`Synced ${res.synced} of ${res.total_events} events. Reloading…`)
      await loadGraph(selectedId)
    } catch (e) {
      setError(e?.response?.data?.detail || 'Sync failed')
    } finally { setSyncing(false) }
  }

  const showGraph = !loading && !empty && !error

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif' }}>

      {/* ── Toolbar ── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>

        {/* File dropdown */}
        <div style={{ position: 'relative', flexShrink: 0 }}>
          <select
            value={selectedId}
            onChange={e => setSelectedId(e.target.value)}
            style={{
              appearance: 'none', background: '#253347',
              border: '1px solid #3d4f6a', borderRadius: '8px',
              color: '#e2e8f0', fontSize: '12px', fontFamily: 'inherit',
              padding: '6px 32px 6px 12px', cursor: 'pointer',
              minWidth: '180px', maxWidth: '280px', outline: 'none',
            }}
          >
            <option value={ALL}>🗂 All files (mixed)</option>
            {parsedFiles.map((ev, i) => (
              <option key={ev.id} value={ev.id}>
                {ev.filename}
              </option>
            ))}
            {parsedFiles.length === 0 && <option disabled>No parsed files yet</option>}
          </select>
          <ChevronDown size={12} color="#6b7fa3"
            style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }} />
        </div>

        {/* Mode tag */}
        {selectedId === ALL ? (
          <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '4px', background: 'rgba(96,165,250,0.12)', color: '#60a5fa', border: '1px solid rgba(96,165,250,0.25)', fontWeight: '600' }}>
            All files — nodes coloured by source file
          </span>
        ) : (
          <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '4px', background: 'rgba(52,211,153,0.12)', color: '#34d399', border: '1px solid rgba(52,211,153,0.25)', fontWeight: '600' }}>
            {selectedLabel} — nodes coloured by entity type
          </span>
        )}

        {/* Spacer */}
        <div style={{ flex: 1 }} />

        {/* Stats */}
        {showGraph && (
          <span style={{ fontSize: '12px', color: '#9aa8c0' }}>
            <span style={{ color: '#e2e8f0', fontWeight: '600' }}>{nodeCount}</span> nodes
            {' · '}
            <span style={{ color: '#e2e8f0', fontWeight: '600' }}>{edgeCount}</span> edges
          </span>
        )}

        {/* Clear — investigator+, all-files only */}
        {canClearGraph && selectedId === ALL && (
          <button onClick={() => setShowConfirm(true)} style={{
            display: 'flex', alignItems: 'center', gap: '6px',
            padding: '6px 12px', background: 'transparent',
            border: '1px solid rgba(239,68,68,0.4)', borderRadius: '8px',
            color: '#fca5a5', fontSize: '12px', cursor: 'pointer', fontFamily: 'inherit', transition: 'all 0.15s',
          }}
          onMouseEnter={e => { e.currentTarget.style.background = 'rgba(239,68,68,0.1)'; e.currentTarget.style.borderColor = 'rgba(239,68,68,0.7)' }}
          onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.borderColor = 'rgba(239,68,68,0.4)' }}>
            <Trash2 size={12} /> Clear Graph
          </button>
        )}
      </div>

      {/* ── Canvas ── */}
      <div style={{ position: 'relative', minHeight: '480px', borderRadius: '12px', border: '1px solid #3d4f6a', background: '#1a2234', overflow: 'hidden' }}>

        {loading && (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(26,34,52,0.85)', zIndex: 10 }}>
            <Spinner size="lg" />
          </div>
        )}

        {!loading && empty && (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '16px', zIndex: 5, padding: '24px' }}>
            <EmptyState icon={GitBranch} title="No graph data"
              description={selectedId === ALL
                ? 'No nodes found. Parse evidence files then click Sync Graph.'
                : `No graph nodes for "${selectedLabel}". Re-parse this file to generate graph data.`} />
            {syncMsg && <p style={{ color: '#34d399', fontSize: '12px', textAlign: 'center', margin: 0 }}>{syncMsg}</p>}
            {canSyncGraph && selectedId === ALL && (
              <button onClick={handleSync} disabled={syncing} style={{
                display: 'flex', alignItems: 'center', gap: '6px',
                padding: '8px 18px', background: '#4a7fe8', border: 'none',
                borderRadius: '8px', color: '#fff', fontSize: '13px',
                fontWeight: '500', cursor: syncing ? 'not-allowed' : 'pointer',
                fontFamily: 'inherit', opacity: syncing ? 0.6 : 1,
              }}>
                <RefreshCw size={13} style={{ animation: syncing ? 'spin 1s linear infinite' : 'none' }} />
                {syncing ? 'Syncing…' : 'Sync Graph from Events'}
              </button>
            )}
          </div>
        )}

        {!loading && error && (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 5 }}>
            <div style={{ textAlign: 'center' }}>
              <p style={{ color: '#fca5a5', fontSize: '13px', marginBottom: '12px' }}>{error}</p>
              <button onClick={() => loadGraph(selectedId)}
                style={{ background: '#2a3347', border: '1px solid #3d4f6a', color: '#9aa8c0', borderRadius: '8px', padding: '7px 16px', cursor: 'pointer', fontSize: '12px', fontFamily: 'inherit' }}>
                Retry
              </button>
            </div>
          </div>
        )}

        {/* Cytoscape container — always in DOM to prevent className crash */}
        <div ref={containerRef} style={{ width: '100%', height: '100%', minHeight: '480px', visibility: showGraph ? 'visible' : 'hidden' }} />
      </div>

      {/* ── Legend ── */}
      {showGraph && legend.length > 0 && (
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', paddingLeft: '4px', alignItems: 'center' }}>
          <span style={{ color: '#4a5568', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: '600', flexShrink: 0 }}>
            {selectedId === ALL ? 'Source file' : 'Entity type'}
          </span>
          {legend.map(item => (
            <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              {item.type === 'edge' ? (
                <div style={{ width: '20px', height: '2px', background: item.color, flexShrink: 0, borderRadius: '1px' }} />
              ) : (
                <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: item.color, flexShrink: 0 }} />
              )}
              <span style={{
                color: '#9aa8c0', fontSize: '11px',
                maxWidth: '160px', overflow: 'hidden',
                textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              }} title={item.label}>
                {item.label}
              </span>
            </div>
          ))}
        </div>
      )}

      {showConfirm && (
        <ConfirmModal
          title="Clear Knowledge Graph"
          message="This deletes all nodes and edges for this case. Events stay in MongoDB but you'll need to re-parse to rebuild the graph."
          onConfirm={handleClear} onCancel={() => setShowConfirm(false)} loading={clearing}
        />
      )}

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

export default GraphView
