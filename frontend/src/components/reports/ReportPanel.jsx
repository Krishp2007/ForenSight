import { useState, useEffect, useRef } from 'react'
import api from '../../services/api'
import { listEvidence } from '../../services/evidenceService'
import { Spinner } from '../ui'
import { RefreshCw, FileDown, AlertCircle, Clock, FileText } from 'lucide-react'

// Inline from reportService
const getHtmlReport = (caseId) => api.get(`/cases/${caseId}/report/html`, { headers: { Accept: 'text/html' }, responseType: 'text' }).then(r => r.data)

const ReportPanel = ({ caseId, evidenceCount }) => {
  const [html, setHtml]                 = useState(null)
  const [loading, setLoading]           = useState(false)
  const [pdfLoading, setPdfLoading]     = useState(false)
  const [error, setError]               = useState(null)
  const [evidenceReady, setEvidenceReady] = useState(null)
  const iframeRef                       = useRef(null)

  useEffect(() => {
    setHtml(null)
    const check = async () => {
      try {
        if (evidenceCount === 0) {
          setEvidenceReady(false)
          return
        }
        const ev = await listEvidence(caseId)
        if (!ev || !ev.length) {
          setEvidenceReady(false)
          setHtml(null)
          return
        }
        setEvidenceReady(ev.some(e => e.status === 'parsed'))
      } catch {
        setEvidenceReady(false)
        setHtml(null)
      }
    }
    check()
  }, [caseId, evidenceCount])

  const loadReport = async () => {
    setLoading(true); setError(null)
    try { setHtml(await getHtmlReport(caseId)) }
    catch (e) { setError(e.response?.data?.detail || 'Failed to generate report.') }
    finally { setLoading(false) }
  }

  // Download as .html file — always works
  const downloadHtml = () => {
    if (!html) return
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = `Forensic_Report_${caseId.slice(-6)}.html`
    a.click()
    URL.revokeObjectURL(url)
  }

  // Print/Save PDF using browser native print dialog
  const downloadPdf = () => {
    if (!html) return
    setPdfLoading(true)

    const printReady = html.replace(
      '</head>',
      `<style>
        @media print {
          body { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
          .no-print { display: none !important; }
        }
      </style>
      <script>
        window.onload = function() {
          setTimeout(function() { window.print(); }, 400);
        };
      </script>
      </head>`
    )

    const blob = new Blob([printReady], { type: 'text/html;charset=utf-8' })
    const url  = URL.createObjectURL(blob)
    const win  = window.open(url, '_blank', 'width=900,height=700')

    if (win) {
      win.addEventListener('afterprint', () => {
        URL.revokeObjectURL(url)
      })
    } else {
      URL.revokeObjectURL(url)
      alert('Pop-up blocked. Use "Download HTML" and open the file in your browser, then press Ctrl+P → Save as PDF.')
    }

    setPdfLoading(false)
  }

  const btnBase = {
    display: 'flex', alignItems: 'center', gap: '8px',
    padding: '9px 18px', borderRadius: '10px', border: 'none',
    fontSize: '13px', fontWeight: '600', cursor: 'pointer',
    fontFamily: 'inherit', transition: 'all 0.2s ease',
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', fontFamily: 'inherit' }}>

      {/* Warning: evidence not parsed */}
      {evidenceReady === false && (
        <div style={{ display: 'flex', gap: '10px', background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.35)', borderRadius: '12px', padding: '12px 16px' }}>
          <Clock size={16} color="#d97706" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <p style={{ color: '#d97706', fontSize: '13px', fontWeight: '700', margin: '0 0 4px 0' }}>Evidence not fully processed yet</p>
            <p style={{ color: 'var(--forensic-text-muted, #64748b)', fontSize: '12px', margin: 0, lineHeight: '1.5' }}>
              Wait for evidence status to show <strong style={{ color: '#059669' }}>Parsed</strong> in the Evidence tab before generating a report.
            </p>
          </div>
        </div>
      )}

      {/* Buttons */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
        <button
          onClick={loadReport} disabled={loading || evidenceCount === 0}
          style={{ ...btnBase, background: 'var(--forensic-primary, #2563eb)', color: '#ffffff', opacity: (loading || evidenceCount === 0) ? 0.5 : 1, cursor: evidenceCount === 0 ? 'not-allowed' : 'pointer' }}
          onMouseEnter={e => { if (!loading && evidenceCount !== 0) e.currentTarget.style.background = '#1d4ed8' }}
          onMouseLeave={e => e.currentTarget.style.background = 'var(--forensic-primary, #2563eb)'}
        >
          {loading ? <Spinner size="sm" /> : <RefreshCw size={14} />}
          {loading ? 'Generating…' : 'Generate Report'}
        </button>

        {html && (
          <>
            <button
              onClick={downloadPdf} disabled={pdfLoading}
              style={{ ...btnBase, background: '#059669', color: '#ffffff', opacity: pdfLoading ? 0.7 : 1 }}
              onMouseEnter={e => { if (!pdfLoading) e.currentTarget.style.background = '#047857' }}
              onMouseLeave={e => e.currentTarget.style.background = '#059669'}
            >
              {pdfLoading ? <Spinner size="sm" /> : <FileDown size={14} />}
              {pdfLoading ? 'Opening…' : 'Print / Save PDF'}
            </button>

            <button
              onClick={downloadHtml}
              style={{ ...btnBase, background: 'var(--forensic-panel-bg, #f8fafc)', border: '1px solid var(--forensic-border, #cbd5e1)', color: 'var(--forensic-text-main, #0f172a)' }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--forensic-primary, #2563eb)' }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--forensic-border, #cbd5e1)' }}
            >
              <FileText size={14} />
              Download HTML
            </button>
          </>
        )}
      </div>

      {error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.35)', borderRadius: '10px', padding: '12px 16px', color: '#dc2626', fontSize: '13px', fontWeight: '500' }}>
          <AlertCircle size={15} style={{ flexShrink: 0 }} />
          {error}
        </div>
      )}

      {/* Report iframe preview */}
      {html && (
        <div style={{ borderRadius: '16px', border: '1px solid var(--forensic-border, #e2e8f0)', overflow: 'hidden', boxShadow: '0 2px 10px rgba(0,0,0,0.04)', background: 'var(--forensic-card-bg, #ffffff)' }}>
          <div style={{ background: 'var(--forensic-panel-bg, #f8fafc)', borderBottom: '1px solid var(--forensic-border, #e2e8f0)', padding: '10px 18px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--forensic-text-main, #0f172a)', fontSize: '13px', fontWeight: '700' }}>Report Preview</span>
            <span style={{ color: '#059669', fontSize: '11.5px', fontWeight: '700' }}>✓ Generated</span>
          </div>
          <iframe
            ref={iframeRef}
            srcDoc={html}
            title="Case Report"
            style={{ width: '100%', height: '75vh', border: 'none', background: '#ffffff', display: 'block' }}
          />
        </div>
      )}

      {/* Empty state */}
      {!html && !loading && !error && (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '64px 16px', gap: '12px', border: '1px dashed var(--forensic-border, #cbd5e1)', borderRadius: '16px', background: 'var(--forensic-card-bg, #ffffff)' }}>
          <FileDown size={40} style={{ color: 'var(--forensic-text-muted, #94a3b8)' }} strokeWidth={1.2} />
          <p style={{ color: 'var(--forensic-text-main, #0f172a)', fontSize: '15px', fontWeight: '700', margin: 0 }}>No report generated yet</p>
          <p style={{ color: 'var(--forensic-text-muted, #64748b)', fontSize: '13px', textAlign: 'center', maxWidth: '380px', margin: 0, lineHeight: '1.6' }}>
            Click <strong style={{ color: 'var(--forensic-primary, #2563eb)' }}>Generate Report</strong> to compile an AI-powered forensic report with anomaly analysis, graph relationships, and MITRE technique mappings.
          </p>
        </div>
      )}
    </div>
  )
}

export default ReportPanel
