import api from './api'

// POST /auth/login  — form-encoded (OAuth2PasswordRequestForm)
export const login = async (email, password) => {
  const form = new URLSearchParams()
  form.append('username', email)   // FastAPI OAuth2 form uses "username"
  form.append('password', password)
  const res = await api.post('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return res.data // { access_token, token_type }
}

// POST /auth/register
export const register = async (payload) => {
  const res = await api.post('/auth/register', payload)
  return res.data
}

// GET /auth/me
export const getMe = async () => {
  const res = await api.get('/auth/me')
  return res.data
}

// PATCH /auth/me — update username, email, and/or password
export const updateMe = async (payload) => {
  const res = await api.patch('/auth/me', payload)
  return res.data
}
