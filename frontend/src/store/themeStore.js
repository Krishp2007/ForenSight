import { create } from 'zustand'

const initialTheme = localStorage.getItem('forensight_theme') || 'dark'
if (initialTheme === 'light') {
  document.documentElement.setAttribute('data-theme', 'light')
} else {
  document.documentElement.setAttribute('data-theme', 'dark')
}

const useThemeStore = create((set) => ({
  theme: initialTheme,
  toggleTheme: () => set((state) => {
    const nextTheme = state.theme === 'dark' ? 'light' : 'dark'
    localStorage.setItem('forensight_theme', nextTheme)
    document.documentElement.setAttribute('data-theme', nextTheme)
    return { theme: nextTheme }
  }),
  setTheme: (newTheme) => set(() => {
    localStorage.setItem('forensight_theme', newTheme)
    document.documentElement.setAttribute('data-theme', newTheme)
    return { theme: newTheme }
  }),
}))

export default useThemeStore
