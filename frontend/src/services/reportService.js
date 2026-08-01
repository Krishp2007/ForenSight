import api from './api'

// GET /cases/:id/report/html  — returns raw HTML string
export const getHtmlReport = async (caseId) => {
  const res = await api.get(`/cases/${caseId}/report/html`, {
    headers: { Accept: 'text/html' },
    responseType: 'text',
  })
  return res.data
}

// GET /cases/:id/report/pdf  — triggers browser download
export const downloadPdfReport = async (caseId) => {
  const res = await api.get(`/cases/${caseId}/report/pdf`, {
    responseType: 'blob',
  })
  const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
  const a = document.createElement('a')
  a.href = url
  a.download = `ForenSight_Report_${caseId}.pdf`
  a.click()
  window.URL.revokeObjectURL(url)
}
