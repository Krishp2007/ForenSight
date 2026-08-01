import api from './api'

// POST /organizations/
export const createOrganization = async (name) => {
  const res = await api.post('/organizations/', { name })
  return res.data
}

// GET /organizations/
export const listOrganizations = async () => {
  const res = await api.get('/organizations/')
  return res.data
}
