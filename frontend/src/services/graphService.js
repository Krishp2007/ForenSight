import api from './api'

// GET /cases/:id/graph
export const getCaseGraph = async (caseId) => {
  const res = await api.get(`/cases/${caseId}/graph`)
  return res.data // { nodes: [], edges: [] }
}

// DELETE /cases/:id/graph
export const clearCaseGraph = async (caseId) => {
  await api.delete(`/cases/${caseId}/graph`)
}
