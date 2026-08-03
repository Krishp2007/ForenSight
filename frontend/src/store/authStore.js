import { create } from 'zustand'
import { getMe } from '../services/authService'

// Rehydrate user from localStorage so the topbar renders immediately on mount
const _savedUser = (() => {
  try { return JSON.parse(localStorage.getItem('user') || 'null') } catch { return null }
})()

const useAuthStore = create((set, get) => ({
  user: _savedUser,
  token: localStorage.getItem('token') || null,
  isLoading: false,

  setToken: (token) => {
    localStorage.setItem('token', token)
    set({ token, user: null })
  },

  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    set({ user: null, token: null })
  },

  fetchMe: async () => {
    if (get().isLoading) return
    set({ isLoading: true })
    try {
      const user = await getMe()
      localStorage.setItem('user', JSON.stringify(user))
      set({ user, isLoading: false })
    } catch (err) {
      // Clear token on 401 — expired or invalid
      if (err?.response?.status === 401 || err?.response?.status === 422) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        set({ user: null, token: null, isLoading: false })
      } else {
        // Network error — keep token and cached user, just stop loading
        set({ isLoading: false })
      }
    }
  },
}))

// Inline useRole — role helpers derived from auth store
const useRole = () => {
  const { user } = useAuthStore()
  const role = user?.role || 'viewer'
  return {
    role,
    isAdmin:        role === 'admin',
    isInvestigator: role === 'admin' || role === 'investigator',
    isViewer:       true,
    canUpload:      role === 'admin' || role === 'investigator',
    canReprocess:   role === 'admin' || role === 'investigator',
    canDelete:      role === 'admin' || role === 'investigator',
    canEdit:        role === 'admin' || role === 'investigator',
    canRunRules:    role === 'admin' || role === 'investigator',
    canSyncGraph:   role === 'admin' || role === 'investigator',
    canClearGraph:  role === 'admin' || role === 'investigator',
    canManageUsers: role === 'admin',
  }
}

export { useRole }
export default useAuthStore
