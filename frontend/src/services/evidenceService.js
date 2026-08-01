import api from './api'

export const uploadEvidence = async (caseId, file, onUploadProgress) => {
  const form = new FormData()
  form.append('file', file)
  const res = await api.post(`/cases/${caseId}/evidence`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress,
  })
  return res.data
}

export const listEvidence = async (caseId) => {
  const res = await api.get(`/cases/${caseId}/evidence`)
  return res.data
}

export const getEvidence = async (evidenceId) => {
  const res = await api.get(`/evidence/${evidenceId}`)
  return res.data
}

export const reprocessEvidence = async (caseId, evidenceId) => {
  const res = await api.post(`/cases/${caseId}/evidence/${evidenceId}/reprocess`)
  return res.data
}

export const deleteEvidence = async (caseId, evidenceId) => {
  await api.delete(`/cases/${caseId}/evidence/${evidenceId}`)
}

export const getEvidenceGraph = async (caseId, evidenceId) => {
  const res = await api.get(`/cases/${caseId}/evidence/${evidenceId}/graph`)
  return res.data
}

export const getEvidenceReport = async (caseId, evidenceId) => {
  const res = await api.get(`/cases/${caseId}/evidence/${evidenceId}/report/html`, {
    headers: { Accept: 'text/html' },
    responseType: 'text',
  })
  return res.data
}
