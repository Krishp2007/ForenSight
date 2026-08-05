import api from './api'

// GET /cases/:id/graph  (all files — legacy raw graph)
export const getCaseGraph = async (caseId) => {
  const res = await api.get(`/cases/${caseId}/graph`)
  return res.data
}

// GET /cases/:id/graph/summary  (investigator-centric aggregated graph)
export const getCaseGraphSummary = async (caseId, params = {}) => {
  const res = await api.get(`/cases/${caseId}/graph/summary`, { params })
  return res.data
}

// GET /cases/:id/evidence/:evidenceId/graph  (single file)
export const getEvidenceGraph = async (caseId, evidenceId) => {
  const res = await api.get(`/cases/${caseId}/evidence/${evidenceId}/graph`)
  return res.data
}

// POST /cases/:id/graph/sync
export const syncCaseGraph = async (caseId) => {
  const res = await api.post(`/cases/${caseId}/graph/sync`)
  return res.data
}

// DELETE /cases/:id/graph
export const clearCaseGraph = async (caseId) => {
  await api.delete(`/cases/${caseId}/graph`)
}
