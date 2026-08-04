import api from './api'

// GET /cases/
export const listCases = async (statusFilter = null) => {
  const params = statusFilter ? { status_filter: statusFilter } : {}
  const res = await api.get('/cases', { params })
  return res.data
}

// GET /cases/:id
export const getCase = async (caseId) => {
  const res = await api.get(`/cases/${caseId}`)
  return res.data
}

// POST /cases/
export const createCase = async (payload) => {
  const res = await api.post('/cases/', payload)
  return res.data
}

// PUT /cases/:id
export const updateCase = async (caseId, payload) => {
  const res = await api.put(`/cases/${caseId}`, payload)
  return res.data
}
