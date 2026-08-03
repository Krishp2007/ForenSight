import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

/**
 * Page route favicon SVG generators
 */
const favicons = {
  dashboard: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="#081320"/><path d="M16 4L26 8V16C26 22 20 26 16 28C12 26 6 22 6 16V8L16 4Z" fill="none" stroke="#18A0FB" stroke-width="2.2"/><circle cx="16" cy="15" r="3.5" fill="#FFFFFF"/></svg>`,
  cases: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="#0F172A"/><path d="M6 10H12L15 13H26V24H6V10Z" fill="none" stroke="#38BDF8" stroke-width="2.2" stroke-linejoin="round"/><circle cx="18" cy="17" r="3" fill="none" stroke="#FFFFFF" stroke-width="1.8"/><line x1="20" y1="19" x2="23" y2="22" stroke="#FFFFFF" stroke-width="1.8"/></svg>`,
  users: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="#180B28"/><circle cx="12" cy="12" r="3.5" fill="none" stroke="#A855F7" stroke-width="2"/><path d="M6 23C6 19 9 17 12 17C15 17 18 19 18 23" fill="none" stroke="#A855F7" stroke-width="2"/><circle cx="21" cy="14" r="2.5" fill="none" stroke="#C084FC" stroke-width="1.8"/><path d="M17 23C17 20.5 19 19 21 19C23 19 25 20.5 25 23" fill="none" stroke="#C084FC" stroke-width="1.8"/></svg>`,
  profile: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="#0D122B"/><circle cx="16" cy="12" r="4" fill="none" stroke="#6366F1" stroke-width="2.2"/><path d="M8 24C8 19.5 11.5 17.5 16 17.5C20.5 17.5 24 19.5 24 24" fill="none" stroke="#6366F1" stroke-width="2.2"/></svg>`,
  login: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="#042017"/><rect x="9" y="14" width="14" height="11" rx="2.5" fill="none" stroke="#10B981" stroke-width="2.2"/><path d="M12 14V10C12 7.8 13.8 6 16 6C18.2 6 20 7.8 20 10V14" fill="none" stroke="#10B981" stroke-width="2.2"/><circle cx="16" cy="19.5" r="1.5" fill="#34D399"/></svg>`,
  register: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="#0A182E"/><circle cx="14" cy="12" r="3.5" fill="none" stroke="#3B82F6" stroke-width="2"/><path d="M8 23C8 19.5 11 17.5 14 17.5C17 17.5 20 19.5 20 23" fill="none" stroke="#3B82F6" stroke-width="2"/><path d="M22 12H26M24 10V14" stroke="#60A5FA" stroke-width="2" stroke-linecap="round"/></svg>`,
  default: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="#081320"/><path d="M16 4L26 8V16C26 22 20 26 16 28C12 26 6 22 6 16V8L16 4Z" fill="none" stroke="#18A0FB" stroke-width="2.2"/><circle cx="16" cy="15" r="3.5" fill="#FFFFFF"/></svg>`,
}

const pageConfigs = {
  '/dashboard': { title: 'Dashboard | ForenSight AI', icon: favicons.dashboard },
  '/users': { title: 'User Management | ForenSight AI', icon: favicons.users },
  '/profile': { title: 'Investigator Profile | ForenSight AI', icon: favicons.profile },
  '/login': { title: 'Sign In | ForenSight AI', icon: favicons.login },
  '/register': { title: 'Create Account | ForenSight AI', icon: favicons.register },
  '/setup': { title: 'Organization Setup | ForenSight AI', icon: favicons.default },
}

export function useDynamicFavicon() {
  const location = useLocation()

  useEffect(() => {
    const path = location.pathname
    let config = pageConfigs[path]

    if (!config && path.startsWith('/cases/')) {
      config = { title: 'Case Investigation | ForenSight AI', icon: favicons.cases }
    }

    if (!config) {
      config = { title: 'ForenSight AI Digital Forensics', icon: favicons.default }
    }

    // 1. Update Document Title
    document.title = config.title

    // 2. Dynamically Update Browser Favicon Link
    let link = document.querySelector("link[rel*='icon']")
    if (!link) {
      link = document.createElement('link')
      link.rel = 'shortcut icon'
      document.getElementsByTagName('head')[0].appendChild(link)
    }

    // Convert SVG string to Data URI
    const encodedSvg = encodeURIComponent(config.icon)
    link.type = 'image/svg+xml'
    link.href = `data:image/svg+xml,${encodedSvg}`
  }, [location])
}
