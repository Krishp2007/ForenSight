import React, { useState, useEffect, useRef } from 'react';
import apiClient from '../../services/apiClient';
import { X, FileText, Download, Printer, ExternalLink, ShieldAlert, Loader2 } from 'lucide-react';

const CaseReportModal = ({ caseId, caseTitle, onClose }) => {
  const [htmlContent, setHtmlContent] = useState('');
  const [loadingPreview, setLoadingPreview] = useState(true);
  const [previewError, setPreviewError] = useState('');
  
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [pdfError, setPdfError] = useState('');
  const [warningMessage, setWarningMessage] = useState('');

  const iframeRef = useRef(null);

  const fetchHtmlPreview = async () => {
    setLoadingPreview(true);
    setPreviewError('');
    try {
      const res = await apiClient.get(`/cases/${caseId}/report/html`);
      setHtmlContent(res.data);
    } catch (err) {
      setPreviewError(err.response?.data?.detail || 'Failed to generate HTML report preview.');
    } finally {
      setLoadingPreview(false);
    }
  };

  useEffect(() => {
    fetchHtmlPreview();
  }, [caseId]);

  const handleDownloadPdf = async () => {
    setDownloadingPdf(true);
    setPdfError('');
    setWarningMessage('');
    try {
      const res = await apiClient.get(`/cases/${caseId}/report/pdf`, {
        responseType: 'blob'
      });
      
      const file = new Blob([res.data], { type: 'application/pdf' });
      const fileURL = URL.createObjectURL(file);
      const link = document.createElement('a');
      link.href = fileURL;
      link.setAttribute('download', `ForenSight_Report_${caseId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch (err) {
      // Decode JSON error if response was sent with application/json
      if (err.response?.data instanceof Blob) {
        const text = await err.response.data.text();
        try {
          const parsed = JSON.parse(text);
          if (err.response.status === 424) {
            setWarningMessage(parsed.detail || 'WeasyPrint dependency missing.');
          } else {
            setPdfError(parsed.detail || 'Failed compiling PDF.');
          }
        } catch {
          setPdfError('Failed parsing PDF compilation response.');
        }
      } else {
        setPdfError(err.response?.data?.detail || 'Failed compiling PDF report.');
      }
    } finally {
      setDownloadingPdf(false);
    }
  };

  const handleBrowserPrint = () => {
    if (iframeRef.current) {
      iframeRef.current.contentWindow.focus();
      iframeRef.current.contentWindow.print();
    }
  };

  const handleOpenNewWindow = () => {
    const newWindow = window.open();
    if (newWindow) {
      newWindow.document.write(htmlContent);
      newWindow.document.close();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-950/80 backdrop-blur-sm">
      
      {/* Backdrop Click Dismiss */}
      <div className="absolute inset-0 cursor-default" onClick={onClose} />

      {/* Main Modal panel */}
      <div className="relative w-full max-w-5xl h-[90vh] bg-gray-900 border border-gray-808 rounded-3xl shadow-3xl flex flex-col overflow-hidden z-10 animate-in fade-in zoom-in duration-200">
        
        {/* Modal Header */}
        <div className="p-6 border-b border-gray-800 bg-gray-901 flex flex-col md:flex-row justify-between md:items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-accent/15 border border-accent/35 flex items-center justify-center text-accent">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Forensic Audit Summary Report</h3>
              <p className="text-[10px] text-gray-500 font-mono mt-0.5">Case: {caseTitle}</p>
            </div>
          </div>

          <div className="flex flex-wrap gap-2 items-center">
            {/* Direct Window Printer click */}
            <button
              onClick={handleBrowserPrint}
              disabled={loadingPreview || !!previewError}
              className="px-3.5 py-1.5 border border-gray-800 hover:border-gray-700 bg-gray-955 hover:bg-gray-850 text-gray-300 hover:text-white text-xs font-bold rounded-lg transition-colors cursor-pointer flex items-center gap-1.5 disabled:opacity-40"
            >
              <Printer className="w-3.5 h-3.5" />
              Print Report
            </button>

            {/* Open In New Tab */}
            <button
              onClick={handleOpenNewWindow}
              disabled={loadingPreview || !!previewError}
              className="px-3.5 py-1.5 border border-gray-800 hover:border-gray-700 bg-gray-955 hover:bg-gray-850 text-gray-305 hover:text-white text-xs font-bold rounded-lg transition-colors cursor-pointer flex items-center gap-1.5 disabled:opacity-40"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              New Window
            </button>

            {/* Compile PDF blob download */}
            <button
              onClick={handleDownloadPdf}
              disabled={downloadingPdf}
              className="px-4 py-1.5 bg-accent hover:bg-accent-hover text-white text-xs font-bold rounded-lg shadow-lg hover:shadow-accent/15 transition-all cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
            >
              {downloadingPdf ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Compiling...
                </>
              ) : (
                <>
                  <Download className="w-3.5 h-3.5" />
                  Download PDF
                </>
              )}
            </button>

            {/* Modal Close Dismiss */}
            <button
              onClick={onClose}
              className="p-1.5 border border-gray-800 bg-gray-955 hover:bg-gray-800 hover:text-white rounded-lg text-gray-400 transition-colors cursor-pointer md:ml-2"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Modal Info notices */}
        {(pdfError || warningMessage) && (
          <div className="px-6 py-3 border-b border-gray-800/80 bg-gray-950 flex flex-col gap-2">
            {pdfError && (
              <div className="text-xs text-red-400 font-semibold p-2 bg-red-950/20 border border-red-900/30 rounded-lg">
                {pdfError}
              </div>
            )}
            {warningMessage && (
              <div className="flex items-start gap-2.5 p-3 bg-purple-950/15 border border-purple-900/30 rounded-xl">
                <ShieldAlert className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
                <div className="text-[11px] text-gray-300 leading-normal font-medium">
                  <strong>WeasyPrint Note:</strong> {warningMessage}
                  <div className="mt-1 text-accent font-semibold">
                    💡 Tip: Click the "Print Report" or "New Window" button above and choose "Save as PDF" to compile locally.
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Dynamic iframe viewport */}
        <div className="flex-1 bg-gray-950 p-6">
          {loadingPreview ? (
            <div className="w-full h-full flex flex-col items-center justify-center">
              <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mb-3" />
              <span className="text-gray-505 text-[10px] font-bold tracking-widest uppercase animate-pulse">
                Assembling HTML Sections...
              </span>
            </div>
          ) : previewError ? (
            <div className="w-full h-full flex flex-col items-center justify-center text-center">
              <ShieldAlert className="w-10 h-10 text-red-500/80 mb-3 animate-none" />
              <h4 className="text-red-400 font-bold text-xs">{previewError}</h4>
            </div>
          ) : (
            <iframe
              ref={iframeRef}
              srcDoc={htmlContent}
              className="w-full h-full bg-white rounded-2xl shadow-inner border border-gray-800"
              title="Forensic PDF Preview Document"
            />
          )}
        </div>

      </div>

    </div>
  );
};

export default CaseReportModal;
