import { useState } from 'react'
import { getHtmlReport, downloadPdfReport } from '../../services/reportService'
import Spinner from '../ui/Spinner'
import { FileDown, RefreshCw } from 'lucide-react'

const ReportPanel = ({ caseId }) => {
  const [html, setHtml] = useState(null)
  const [loading, setLoading] = useState(false)
  const [pdfLoading, setPdfLoading] = useState(false)
  const [error, setError] = useState(null)

  const loadReport = async () => {
    setLoading(true)
    setError(null)
    try {
      const content = await getHtmlReport(caseId)
      setHtml(content)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to generate report')
    } finally {
      setLoading(false)
    }
  }

  const handlePdf = async () => {
    setPdfLoading(true)
    try {
      await downloadPdfReport(caseId)
    } catch (e) {
      const detail = e.response?.data?.detail || ''
      if (e.response?.status === 424) {
        alert(detail) // WeasyPrint not available — show the hint
      } else {
        alert('PDF generation failed: ' + detail)
      }
    } finally {
      setPdfLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-3">
        <button
          onClick={loadReport}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm rounded-lg transition-colors"
        >
          {loading ? <Spinner size="sm" /> : <RefreshCw size={14} />}
          Generate Report
        </button>
        {html && (
          <button
            onClick={handlePdf}
            disabled={pdfLoading}
            className="flex items-center gap-2 px-4 py-2 border border-gray-600 hover:border-blue-500 text-gray-300 hover:text-white text-sm rounded-lg transition-colors"
          >
            {pdfLoading ? <Spinner size="sm" /> : <FileDown size={14} />}
            Download PDF
          </button>
        )}
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg px-4 py-3 text-red-300 text-sm">
          {error}
        </div>
      )}

      {html && (
        <div className="rounded-xl border border-gray-700 overflow-hidden">
          <iframe
            srcDoc={html}
            title="Case Report"
            className="w-full"
            style={{ height: '70vh', border: 'none', background: '#fff' }}
          />
        </div>
      )}

      {!html && !loading && !error && (
        <p className="text-gray-500 text-sm">
          Click "Generate Report" to compile an AI-powered incident report for this case.
        </p>
      )}
    </div>
  )
}

export default ReportPanel
