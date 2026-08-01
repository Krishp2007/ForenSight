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
    } catch {
      // on any error just stop loading — don't clear token, don't redirect
      set({ isLoading: false })
    }
  },
}))

export default useAuthStore
