import { useState } from 'react'
import { useNavigate, Link, NavLink, useLocation } from 'react-router-dom'
import { LogOut, LayoutDashboard, Users, Menu, X, User } from 'lucide-react'
import useAuth from '../../hooks/useAuth'
import { useRole } from '../../store/authStore'

import ThemeToggle from '../ui/ThemeToggle'
import BrandLogo from './BrandLogo'

const Topbar = () => {
  const { user, logout } = useAuth()
  const { canManageUsers } = useRole()
  const navigate = useNavigate()
  const location = useLocation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  // Derive initials for avatar
  const initials = (user?.username || '?').split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
  const hue = [...(user?.username || '')].reduce((a, c) => a + c.charCodeAt(0), 0) % 360

  const isDashboardActive = location.pathname === '/dashboard'
  const isProfileActive = location.pathname === '/profile'

  return (
    <>
      <header className="responsive-header" style={{
        height: '64px',
        padding: '0 28px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'var(--forensic-panel-bg, rgba(15, 23, 42, 0.85))',
        backdropFilter: 'blur(16px)',
        borderBottom: '1px solid var(--forensic-border, rgba(255, 255, 255, 0.08))',
        flexShrink: 0,
        position: 'sticky',
        top: 0,
        zIndex: 50,
      }}>
        {/* Left: Brand Logo & Desktop Navigation */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
          <Link to="/dashboard" style={{ display: 'flex', alignItems: 'center', textDecoration: 'none' }}>
            <BrandLogo height={32} />
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="desktop-only" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Link
              to="/dashboard"
              style={{
                display: 'flex', alignItems: 'center', gap: '8px',
                padding: '8px 16px', borderRadius: '12px',
                fontSize: '13px', fontWeight: '700', textDecoration: 'none',
                background: isDashboardActive ? 'var(--forensic-primary, #2563eb)' : 'rgba(99, 102, 241, 0.12)',
                border: isDashboardActive ? '1px solid var(--forensic-primary, #2563eb)' : '1px solid var(--forensic-border, rgba(99, 102, 241, 0.3))',
                color: isDashboardActive ? '#ffffff' : 'var(--forensic-text-main, #e2e8f0)',
              }}
            >
              <LayoutDashboard size={16} style={{ color: isDashboardActive ? '#ffffff' : 'var(--forensic-primary, #818cf8)' }} />
              <span>All Cases</span>
            </Link>

            {canManageUsers && (
              <NavLink
                to="/users"
                style={({ isActive }) => ({
                  display: 'flex', alignItems: 'center', gap: '8px',
                  padding: '8px 16px', borderRadius: '12px',
                  fontSize: '13px', fontWeight: isActive ? '600' : '500',
                  textDecoration: 'none',
                  background: isActive ? 'var(--forensic-primary, #2563eb)' : 'transparent',
                  color: isActive ? '#ffffff' : 'var(--forensic-text-muted, #94a3b8)',
                })}
              >
                <Users size={16} />
                <span>Users</span>
              </NavLink>
            )}
          </nav>
        </div>

        {/* Right Corner: Desktop User Actions & Theme Toggle */}
        <div className="desktop-only" style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '14px' }}>
          
          <ThemeToggle />

          <div style={{ width: '1px', height: '24px', background: 'var(--forensic-border, rgba(255, 255, 255, 0.1))' }} />

          {user && (
            <Link
              to="/profile"
              title="Profile & Account Settings"
              style={{
                display: 'flex', alignItems: 'center', gap: '10px',
                textDecoration: 'none', padding: '6px 14px', borderRadius: '12px',
                background: isProfileActive ? 'var(--forensic-primary, #2563eb)' : 'rgba(255, 255, 255, 0.05)',
                border: isProfileActive ? '1px solid var(--forensic-primary, #2563eb)' : '1px solid var(--forensic-border, rgba(255, 255, 255, 0.1))',
                color: isProfileActive ? '#ffffff' : 'var(--forensic-text-main, #f8fafc)',
              }}
            >
              <div style={{
                width: '28px', height: '28px', borderRadius: '50%',
                background: `hsl(${hue}, 60%, 45%)`,
                border: '2px solid rgba(129, 140, 248, 0.6)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '11px', fontWeight: '700', color: '#fff', flexShrink: 0,
              }}>
                {initials}
              </div>
              <div style={{ lineHeight: 1.2 }}>
                <div style={{ fontSize: '13px', fontWeight: '600' }}>Profile</div>
                <div style={{ fontSize: '9.5px', color: isProfileActive ? '#e0e7ff' : 'var(--forensic-text-muted, #94a3b8)', textTransform: 'capitalize' }}>
                  {user.username}
                </div>
              </div>
            </Link>
          )}

          <div style={{ width: '1px', height: '24px', background: 'var(--forensic-border, rgba(255, 255, 255, 0.1))' }} />

          <button
            onClick={handleLogout}
            className="logout-btn-theme"
            style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              fontSize: '12.5px', fontWeight: '600',
              cursor: 'pointer', padding: '7.5px 14px', borderRadius: '10px',
              fontFamily: 'inherit',
            }}
          >
            <LogOut size={15} />
            Logout
          </button>
        </div>

        {/* Mobile Hamburger Toggle Button */}
        <button
          className="mobile-only"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Toggle navigation menu"
          style={{
            background: 'rgba(255, 255, 255, 0.08)',
            border: '1px solid rgba(255, 255, 255, 0.15)',
            color: 'var(--forensic-text-main, #f8fafc)',
            padding: '8px',
            borderRadius: '10px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </header>

      {/* Mobile Menu Slide-Down Drawer */}
      {mobileMenuOpen && (
        <div
          className="mobile-only"
          style={{
            position: 'fixed',
            top: '64px',
            left: 0,
            right: 0,
            bottom: 0,
            background: 'var(--forensic-panel-bg, rgba(11, 15, 25, 0.96))',
            backdropFilter: 'blur(20px)',
            zIndex: 49,
            padding: '20px 16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
            borderBottom: '1px solid var(--forensic-border, rgba(255, 255, 255, 0.1))',
          }}
        >


          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 4px' }}>
            <span style={{ fontSize: '13px', fontWeight: '600', color: 'var(--forensic-text-muted, #94a3b8)' }}>Theme Mode</span>
            <ThemeToggle />
          </div>

          <Link
            to="/dashboard"
            onClick={() => setMobileMenuOpen(false)}
            style={{
              display: 'flex', alignItems: 'center', gap: '12px',
              padding: '12px 16px', borderRadius: '12px',
              background: isDashboardActive ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--forensic-border, rgba(255, 255, 255, 0.1))',
              color: 'var(--forensic-text-main, #ffffff)', textDecoration: 'none', fontWeight: '600',
            }}
          >
            <LayoutDashboard size={18} color="#818cf8" /> All Cases / Dashboard
          </Link>

          {canManageUsers && (
            <Link
              to="/users"
              onClick={() => setMobileMenuOpen(false)}
              style={{
                display: 'flex', alignItems: 'center', gap: '12px',
                padding: '12px 16px', borderRadius: '12px',
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid var(--forensic-border, rgba(255, 255, 255, 0.1))',
                color: 'var(--forensic-text-main, #ffffff)', textDecoration: 'none', fontWeight: '600',
              }}
            >
              <Users size={18} color="#818cf8" /> User Management
            </Link>
          )}

          <Link
            to="/profile"
            onClick={() => setMobileMenuOpen(false)}
            style={{
              display: 'flex', alignItems: 'center', gap: '12px',
              padding: '12px 16px', borderRadius: '12px',
              background: isProfileActive ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--forensic-border, rgba(255, 255, 255, 0.1))',
              color: 'var(--forensic-text-main, #ffffff)', textDecoration: 'none', fontWeight: '600',
            }}
          >
            <User size={18} color="#818cf8" /> Profile & Settings ({user?.username})
          </Link>

          <button
            onClick={() => { setMobileMenuOpen(false); handleLogout() }}
            className="logout-btn-theme"
            style={{
              marginTop: 'auto',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
              padding: '14px', borderRadius: '12px',
              fontWeight: '600', fontSize: '14px',
              cursor: 'pointer', fontFamily: 'inherit',
            }}
          >
            <LogOut size={16} /> Log Out
          </button>
        </div>
      )}
    </>
  )
}

export default Topbar
