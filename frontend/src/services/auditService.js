import api from './api'

export const getCaseAuditLog  = (caseId, limit = 200) => api.get(`/cases/${caseId}/audit`, { params: { limit } }).then(r => r.data)
export const getOrgAuditLog   = (limit = 500) => api.get('/audit', { params: { limit } }).then(r => r.data)
export const verifyAuditChain = () => api.get('/audit/verify').then(r => r.data)
