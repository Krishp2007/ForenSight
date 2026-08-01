import { useState, useEffect, useRef } from 'react'
import cytoscape from 'cytoscape'
import { getEvidenceGraph, getEvidenceReport } from '../../services/evidenceService'
import Spinner from '../ui/Spinner'
import { X, GitBranch, FileText, RefreshCw, FileDown } from 'lucide-react'

const NODE_COLORS = {
  Process: '#3b82f6', File: '#10b981', NetworkAddress: '#f59e0b',
  RegistryKey: '#a855f7', User: '#ec4899', GenericEntity: '#6b7280', default: '#6b7280',
}

const Tab = ({ active, onClick, icon: Icon, label }) => (
  <button
    onClick={onClick}
    style={{
      display: 'flex', alignItems: 'center', gap: '6px',
      padding: '8px 16px', border: 'none', borderRadius: '6px 6px 0 0',
      background: active ? '#1a2234' : 'transparent',
      borderBottom: active ? '2px solid #4a7fe8' : '2px solid transparent',
      color: active ? '#fff' : '#9aa8c0',
      fontSize: '13px', fontWeight: '500', cursor: 'pointer',
      fontFamily: 'inherit', transition: 'all 0.15s',
    }}
  >
    <Icon size={13} />
    {label}
  </button>
)

export default function EvidenceDrawer({ evidence, caseId, onClose }) {
  const [tab, setTab] = useState('graph')

  // Graph state
  const containerRef = useRef(null)
  const cyRef        = useRef(null)
  const [graphLoading, setGraphLoading] = useState(false)
  const [graphData, setGraphData]       = useState(null)

  // Report state
  const [reportHtml,    setReportHtml]    = useState(null)
  const [reportLoading, setReportLoading] = useState(false)
  const [reportError,   setReportError]   = useState(null)
  const iframeRef = useRef(null)

  // ── Step 1: fetch graph data when tab=graph ────────────────────────────────
  useEffect(() => {
    if (tab !== 'graph' || !evidence) return
    setGraphLoading(true)
    setGraphData(null)
    if (cyRef.current) { cyRef.current.destroy(); cyRef.current = null }
    getEvidenceGraph(caseId, evidence.id)
      .then(data => setGraphData(data))
      .catch(console.error)
      .finally(() => setGraphLoading(false))
  }, [tab, evidence?.id])

  // ── Step 2: init Cytoscape once container is in DOM and data is ready ──────
  useEffect(() => {
    if (!graphData?.nodes?.length || !containerRef.current) return
    // Destroy previous instance if any
    if (cyRef.current) { cyRef.current.destroy(); cyRef.current = null }
    const elements = [
      ...graphData.nodes.map(n => ({
        data: { id: n.id, label: n.label || n.id, color: NODE_COLORS[n.type] || NODE_COLORS.default }
      })),
      ...graphData.edges.map(e => ({
        data: { id: `${e.source}--${e.target}--${Math.random()}`, source: e.source, target: e.target, label: e.action || '' }
      })),
    ]
    cyRef.current = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        { selector: 'node', style: { label: 'data(label)', 'background-color': 'data(color)', color: '#fff', 'font-size': '9px', 'text-valign': 'bottom', 'text-margin-y': 4, width: 26, height: 26, 'border-width': 2, 'border-color': '#1e2a3d' } },
        { selector: 'edge', style: { label: 'data(label)', 'font-size': '7px', color: '#6b7fa3', 'line-color': '#3d4f6a', 'target-arrow-color': '#3d4f6a', 'target-arrow-shape': 'triangle', 'curve-style': 'bezier', width: 1.5 } },
        { selector: 'node:selected', style: { 'border-color': '#60a5fa', 'border-width': 3 } },
      ],
      layout: { name: 'cose', animate: true, padding: 30, randomize: false },
      wheelSensitivity: 0.3,
    })
    return () => { if (cyRef.current) { cyRef.current.destroy(); cyRef.current = null } }
  }, [graphData])

  // Load report when tab = report
  const loadReport = () => {
    if (!evidence) return
    setReportLoading(true); setReportError(null)
    getEvidenceReport(caseId, evidence.id)
      .then(setReportHtml)
      .catch(e => setReportError(e.response?.data?.detail || 'Failed to generate report'))
      .finally(() => setReportLoading(false))
  }

  useEffect(() => {
    if (tab === 'report' && !reportHtml && !reportLoading) loadReport()
  }, [tab])

  const printReport = () => {
    if (!reportHtml) return
    const printReady = reportHtml
      .replace('</head>', `<style>@media print{@page{size:A4;margin:15mm 14mm 18mm 14mm}body{-webkit-print-color-adjust:exact;print-color-adjust:exact}}</style></head>`)
      .replace('</body>', `<script>window.onload=function(){setTimeout(function(){window.print()},400)}</script></body>`)
    const url = URL.createObjectURL(new Blob([printReady], { type: 'text/html;charset=utf-8' }))
    const win = window.open(url, '_blank', 'width=900,height=700')
    if (win) win.addEventListener('afterprint', () => URL.revokeObjectURL(url))
    else { URL.revokeObjectURL(url); alert('Pop-up blocked. Use Download HTML instead.') }
  }

  const downloadHtml = () => {
    if (!reportHtml) return
    const a = document.createElement('a')
    a.href = URL.createObjectURL(new Blob([reportHtml], { type: 'text/html;charset=utf-8' }))
    a.download = `ForenSight_${evidence.filename}_Report.html`
    a.click()
  }

  if (!evidence) return null

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 100,
      display: 'flex', alignItems: 'stretch', justifyContent: 'flex-end',
      background: 'rgba(0,0,0,0.6)',
    }} onClick={e => { if (e.target === e.currentTarget) onClose() }}>
      <div style={{
        width: '85vw', maxWidth: '1100px',
        background: '#1a2234', display: 'flex', flexDirection: 'column',
        boxShadow: '-8px 0 40px rgba(0,0,0,0.5)',
        animation: 'slideIn 0.2s ease',
      }}>
        <style>{`@keyframes slideIn{from{transform:translateX(60px);opacity:0}to{transform:translateX(0);opacity:1}}`}</style>

        {/* Header */}
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #2d3748', display: 'flex', alignItems: 'center', gap: '12px', background: '#1e2a3d', flexShrink: 0 }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ color: '#fff', fontWeight: '700', fontSize: '15px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {evidence.filename}
            </div>
            <div style={{ color: '#6b7fa3', fontSize: '12px', marginTop: '2px' }}>
              {evidence.file_type?.toUpperCase()} · {evidence.status}
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#6b7fa3', cursor: 'pointer', padding: '4px', display: 'flex', alignItems: 'center' }}
            onMouseEnter={e => e.currentTarget.style.color = '#fff'}
            onMouseLeave={e => e.currentTarget.style.color = '#6b7fa3'}>
            <X size={18} />
          </button>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: '2px', padding: '0 20px', borderBottom: '1px solid #2d3748', background: '#1e2a3d', flexShrink: 0 }}>
          <Tab active={tab === 'graph'} onClick={() => setTab('graph')} icon={GitBranch} label="Evidence Graph" />
          <Tab active={tab === 'report'} onClick={() => setTab('report')} icon={FileText} label="Evidence Report" />
        </div>

        {/* Body */}
        <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>

          {/* GRAPH TAB */}
          {tab === 'graph' && (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0 }}>
              {graphLoading && (
                <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#1a2234' }}>
                  <Spinner size="lg" />
                </div>
              )}
              {!graphLoading && graphData && !graphData.nodes?.length && (
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '12px', color: '#6b7fa3' }}>
                  <GitBranch size={40} strokeWidth={1.2} />
                  <p style={{ margin: 0, fontSize: '14px' }}>No graph data for this evidence file</p>
                  <p style={{ margin: 0, fontSize: '12px', color: '#4a5568', textAlign: 'center', maxWidth: '300px' }}>
                    Re-process this evidence to populate the graph. Neo4j must be running.
                  </p>
                </div>
              )}
              {!graphLoading && graphData?.nodes?.length > 0 && (
                <>
                  {/* Legend bar */}
                  <div style={{ padding: '8px 16px', background: '#1e2a3d', borderBottom: '1px solid #2d3748', fontSize: '12px', color: '#6b7fa3', flexShrink: 0 }}>
                    {graphData.nodes.length} nodes · {graphData.edges.length} edges
                    <span style={{ marginLeft: '16px' }}>
                      {['Process','File','NetworkAddress','RegistryKey','User','GenericEntity'].map(t => (
                        <span key={t} style={{ marginRight: '10px' }}>
                          <span style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', background: NODE_COLORS[t], marginRight: '4px' }} />
                          {t}
                        </span>
                      ))}
                    </span>
                  </div>
                  {/* Cytoscape container — must have explicit height, NOT flex:1 */}
                  <div
                    ref={containerRef}
                    style={{ width: '100%', height: 'calc(100vh - 180px)', background: '#1a2234' }}
                  />
                </>
              )}
            </div>
          )}

          {/* REPORT TAB */}
          {tab === 'report' && (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              <div style={{ padding: '10px 16px', background: '#1e2a3d', borderBottom: '1px solid #2d3748', display: 'flex', gap: '8px', alignItems: 'center', flexShrink: 0 }}>
                <button onClick={loadReport} disabled={reportLoading}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 14px', background: '#4a7fe8', border: 'none', borderRadius: '7px', color: '#fff', fontSize: '12px', fontWeight: '600', cursor: reportLoading ? 'not-allowed' : 'pointer', fontFamily: 'inherit', opacity: reportLoading ? 0.7 : 1 }}>
                  {reportLoading ? <Spinner size="sm" /> : <RefreshCw size={12} />}
                  {reportLoading ? 'Generating…' : 'Refresh Report'}
                </button>
                {reportHtml && (
                  <>
                    <button onClick={printReport}
                      style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 14px', background: '#10b981', border: 'none', borderRadius: '7px', color: '#fff', fontSize: '12px', fontWeight: '600', cursor: 'pointer', fontFamily: 'inherit' }}>
                      <FileDown size={12} /> Print / PDF
                    </button>
                    <button onClick={downloadHtml}
                      style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 14px', background: 'transparent', border: '1px solid #3d4f6a', borderRadius: '7px', color: '#9aa8c0', fontSize: '12px', fontWeight: '600', cursor: 'pointer', fontFamily: 'inherit' }}>
                      <FileText size={12} /> Download HTML
                    </button>
                  </>
                )}
              </div>
              {reportError && (
                <div style={{ padding: '12px 16px', background: 'rgba(239,68,68,0.1)', color: '#fca5a5', fontSize: '13px' }}>{reportError}</div>
              )}
              {reportHtml && (
                <iframe ref={iframeRef} srcDoc={reportHtml} title="Evidence Report"
                  style={{ flex: 1, width: '100%', border: 'none', background: '#fff' }} />
              )}
              {!reportHtml && !reportLoading && !reportError && (
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '12px', color: '#6b7fa3' }}>
                  <FileText size={40} strokeWidth={1.2} />
                  <p style={{ margin: 0, fontSize: '14px' }}>Click Refresh Report to generate</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
