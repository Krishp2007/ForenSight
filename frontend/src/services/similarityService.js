import api from './api'

// GET /cases/:id/search?query=...&limit=10
export const searchEvents = async (caseId, query, limit = 10) => {
  const res = await api.get(`/cases/${caseId}/search`, {
    params: { query, limit },
  })
  return res.data // EventResponse[]
}
