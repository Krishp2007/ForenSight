import api from './api'

export const getCorrelations  = (caseId) => api.get(`/cases/${caseId}/correlations`).then(r => r.data)
export const runCorrelations  = (caseId) => api.post(`/cases/${caseId}/correlations/run`).then(r => r.data)
