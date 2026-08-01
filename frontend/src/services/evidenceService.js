import api from './api'

// POST /cases/:id/evidence  — multipart file upload
export const uploadEvidence = async (caseId, file, onUploadProgress) => {
  const form = new FormData()
  form.append('file', file)
  const res = await api.post(`/cases/${caseId}/evidence`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress,
  })
  return res.data
}

// GET /cases/:id/evidence
export const listEvidence = async (caseId) => {
  const res = await api.get(`/cases/${caseId}/evidence`)
  return res.data
}

// GET /evidence/:id
export const getEvidence = async (evidenceId) => {
  const res = await api.get(`/evidence/${evidenceId}`)
  return res.data
}
