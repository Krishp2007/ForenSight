import api from './api'

// GET /cases/:id/events
export const listEvents = async (caseId, { severity, event_type, limit = 100 } = {}) => {
  const params = { limit }
  if (severity) params.severity = severity
  if (event_type) params.event_type = event_type
  const res = await api.get(`/cases/${caseId}/events`, { params })
  return res.data
}
