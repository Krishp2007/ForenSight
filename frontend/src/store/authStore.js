import { create } from 'zustand'
import { getMe } from '../services/authService'

const useAuthStore = create((set, get) => ({
  user: null,
  token: localStorage.getItem('token') || null,
  isLoading: false,

  setToken: (token) => {
    localStorage.setItem('token', token)
    set({ token, user: null })
  },

  logout: () => {
    localStorage.removeItem('token')
    set({ user: null, token: null })
  },

  fetchMe: async () => {
    if (get().isLoading) return
    set({ isLoading: true })
    try {
      const user = await getMe()
      set({ user, isLoading: false })
    } catch (err) {
      // Clear token on 401 — expired or invalid
      if (err?.response?.status === 401 || err?.response?.status === 422) {
        localStorage.removeItem('token')
        set({ user: null, token: null, isLoading: false })
      } else {
        // Network error — keep token, just stop loading
        set({ isLoading: false })
      }
    }
  },
}))

export default useAuthStore
