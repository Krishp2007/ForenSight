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
    const a = document.createElement('a')
    a.href = URL.createObjectURL(new Blob([html], { type: 'text/html;charset=utf-8' }))
    a.download = `ForenSight_Report_${caseId}.html`
    a.click()
  }

  // Generate PDF by opening the report HTML in a new window and triggering browser print.
  // This is the only approach that is 100% reliable across all browsers:
  // html2canvas cannot capture off-screen elements (produces blank output),
  // and WeasyPrint requires native system DLLs unavailable on Windows.
  const downloadPdf = () => {
    if (!html) return
    setPdfLoading(true)

    // Inject a print-trigger script into the HTML so the new window auto-prints.
    // We also inject a small @media print override to hide the browser's default
    // header/footer and give the page a clean A4 appearance.
    const printReady = html.replace(
      '</head>',
      `<style>
        @media print {
          @page { size: A4; margin: 15mm 14mm 18mm 14mm; }
          body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
        }
      </style>
      </head>`
    ).replace(
      '</body>',
      `<script>
        window.onload = function() {
          setTimeout(function() { window.print(); }, 400);
        };
      </script>
      </body>`
    )

    const blob = new Blob([printReady], { type: 'text/html;charset=utf-8' })
    const url  = URL.createObjectURL(blob)
    const win  = window.open(url, '_blank', 'width=900,height=700')

    // Clean up the object URL after the window has had time to load
    if (win) {
      win.addEventListener('afterprint', () => {
        URL.revokeObjectURL(url)
      })
    } else {
      // Pop-up blocked — fall back to direct HTML download with instructions
      URL.revokeObjectURL(url)
      alert('Pop-up blocked. Use "Download HTML" and open the file in your browser, then press Ctrl+P → Save as PDF.')
    }

    setPdfLoading(false)
  }

  const btnBase = {
    display: 'flex', alignItems: 'center', gap: '8px',
    padding: '9px 18px', borderRadius: '8px', border: 'none',
    fontSize: '13px', fontWeight: '500', cursor: 'pointer',
    fontFamily: 'inherit', transition: 'all 0.2s',
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif' }}>

      {/* Warning: evidence not parsed */}
      {evidenceReady === false && (
        <div style={{ display: 'flex', gap: '10px', background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.35)', borderRadius: '10px', padding: '12px 16px' }}>
          <Clock size={16} color="#fbbf24" style={{ flexShrink: 0, marginTop: '1px' }} />
          <div>
            <p style={{ color: '#fbbf24', fontSize: '13px', fontWeight: '600', margin: '0 0 4px 0' }}>Evidence not fully processed yet</p>
            <p style={{ color: '#9aa8c0', fontSize: '12px', margin: 0, lineHeight: '1.5' }}>
              Wait for evidence status to show <strong style={{ color: '#34d399' }}>Parsed</strong> in the Evidence tab before generating a report.
            </p>
          </div>
        </div>
      )}

      {/* Buttons */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
        {/* Generate */}
        <button
          onClick={loadReport} disabled={loading || evidenceCount === 0}
          style={{ ...btnBase, background: '#4a7fe8', color: '#fff', opacity: (loading || evidenceCount === 0) ? 0.5 : 1, cursor: evidenceCount === 0 ? 'not-allowed' : 'pointer' }}
          onMouseEnter={e => { if (!loading && evidenceCount !== 0) e.currentTarget.style.background = '#3b6bc4' }}
          onMouseLeave={e => e.currentTarget.style.background = '#4a7fe8'}
        >
          {loading ? <Spinner size="sm" /> : <RefreshCw size={14} />}
          {loading ? 'Generating…' : 'Generate Report'}
        </button>

        {html && (
          <>
            {/* PDF Download */}
            <button
              onClick={downloadPdf} disabled={pdfLoading}
              style={{ ...btnBase, background: '#10b981', color: '#fff', opacity: pdfLoading ? 0.7 : 1 }}
              onMouseEnter={e => { if (!pdfLoading) e.currentTarget.style.background = '#059669' }}
              onMouseLeave={e => e.currentTarget.style.background = '#10b981'}
            >
              {pdfLoading ? <Spinner size="sm" /> : <FileDown size={14} />}
              {pdfLoading ? 'Opening…' : 'Print / Save PDF'}
            </button>

            {/* HTML Download */}
            <button
              onClick={downloadHtml}
              style={{ ...btnBase, background: 'transparent', border: '1px solid #3d4f6a', color: '#9aa8c0' }}
              onMouseEnter={e => { e.currentTarget.style.background = '#2a3347'; e.currentTarget.style.color = '#fff' }}
              onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = '#9aa8c0' }}
            >
              <FileText size={14} />
              Download HTML
            </button>
          </>
        )}
      </div>

      {/* Error */}
      {error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.35)', borderRadius: '8px', padding: '12px 16px', color: '#fca5a5', fontSize: '13px' }}>
          <AlertCircle size={15} style={{ flexShrink: 0 }} />
          {error}
        </div>
      )}

      {/* Report iframe preview */}
      {html && (
        <div style={{ borderRadius: '12px', border: '1px solid #3d4f6a', overflow: 'hidden', boxShadow: '0 4px 20px rgba(0,0,0,0.3)' }}>
          <div style={{ background: '#1e2a3d', borderBottom: '1px solid #3d4f6a', padding: '8px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ color: '#9aa8c0', fontSize: '12px' }}>Report Preview</span>
            <span style={{ color: '#34d399', fontSize: '11px' }}>✓ Generated</span>
          </div>
          <iframe
            ref={iframeRef}
            srcDoc={html}
            title="Case Report"
            style={{ width: '100%', height: '75vh', border: 'none', background: '#fff', display: 'block' }}
            onLoad={() => {
              // Ensure iframe is fully rendered before PDF button is active
              if (iframeRef.current) {
                iframeRef.current.contentDocument.body.style.fontFamily = 'Arial,sans-serif'
              }
            }}
          />
        </div>
      )}

      {/* Empty state */}
      {!html && !loading && !error && (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '64px 16px', gap: '12px', border: '1px dashed #3d4f6a', borderRadius: '12px' }}>
          <FileDown size={40} color="#3d4f6a" strokeWidth={1.2} />
          <p style={{ color: '#6b7fa3', fontSize: '15px', fontWeight: '500', margin: 0 }}>No report generated yet</p>
          <p style={{ color: '#4a5568', fontSize: '13px', textAlign: 'center', maxWidth: '340px', margin: 0, lineHeight: '1.6' }}>
            Click <strong style={{ color: '#9aa8c0' }}>Generate Report</strong> to compile an AI-powered forensic report with anomaly analysis, graph relationships, and MITRE technique mappings.
          </p>
        </div>
      )}
    </div>
  )
}

export default ReportPanel
