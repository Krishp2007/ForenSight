import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// NEVER redirect automatically — let the app handle auth state
// The 401 interceptor was the root cause of the redirect loop
api.interceptors.response.use(
  (res) => res,
  (err) => Promise.reject(err)
)

export default api
