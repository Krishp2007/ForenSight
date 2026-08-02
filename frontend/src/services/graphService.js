import api from './api'

// GET /cases/:id/graph
export const getCaseGraph = async (caseId) => {
  const res = await api.get(`/cases/${caseId}/graph`)
  return res.data // { nodes: [], edges: [] }
}

// POST /cases/:id/graph/sync  — push MongoDB events → Neo4j
export const syncCaseGraph = async (caseId) => {
  const res = await api.post(`/cases/${caseId}/graph/sync`)
  return res.data
}

// DELETE /cases/:id/graph
export const clearCaseGraph = async (caseId) => {
  await api.delete(`/cases/${caseId}/graph`)
}
