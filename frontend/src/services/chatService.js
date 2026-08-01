import api from './api'

// POST /cases/:id/copilot
export const askCopilot = async (caseId, question = null) => {
  const res = await api.post(`/cases/${caseId}/copilot`, { question })
  return res.data // { analysis: "..." }
}
