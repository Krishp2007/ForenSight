import { useState, useEffect } from 'react'

export const THEMES = [
  { id: 'light', label: 'Light Mode', icon: 'Sun' },
  { id: 'dark', label: 'Dark Mode', icon: 'Moon' },
  { id: 'cyber', label: 'Cyber DFIR', icon: 'Zap' },
]

export function useTheme() {
  const [theme, setThemeState] = useState(() => {
    return localStorage.getItem('forensic_theme') || 'dark'
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('forensic_theme', theme)

    const handleStorage = (e) => {
      if (e.key === 'forensic_theme' && e.newValue) {
        setThemeState(e.newValue)
      }
    }
    window.addEventListener('storage', handleStorage)
    return () => window.removeEventListener('storage', handleStorage)
  }, [theme])

  const setTheme = (newTheme) => {
    setThemeState(newTheme)
    document.documentElement.setAttribute('data-theme', newTheme)
    localStorage.setItem('forensic_theme', newTheme)
    window.dispatchEvent(new Event('themeChange'))
  }

  const toggleTheme = () => {
    const nextTheme = theme === 'light' ? 'dark' : theme === 'dark' ? 'cyber' : 'light'
    setTheme(nextTheme)
  }

  return { theme, setTheme, toggleTheme, THEMES }
}

export default useTheme
