import { useNavigate, Link, NavLink, useLocation } from 'react-router-dom'
import { LogOut, Shield, LayoutDashboard, Users } from 'lucide-react'
import useAuth from '../../hooks/useAuth'
import { useRole } from '../../store/authStore'


const Topbar = () => {
  const { user, logout } = useAuth()
  const { canManageUsers } = useRole()
  const navigate = useNavigate()
  const location = useLocation()

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
    <header style={{
      height: '64px',
      padding: '0 28px',
      display: 'flex',
      alignItems: 'center',
      justify: 'space-between',
      background: 'rgba(15, 23, 42, 0.85)',
      backdropFilter: 'blur(16px)',
      borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
      flexShrink: 0,
      position: 'sticky',
      top: 0,
      zIndex: 50,
    }}>
      {/* Left: Brand Logo & Main Navigation Links */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
        {/* Brand */}
        <Link to="/dashboard" style={{ display: 'flex', alignItems: 'center', textDecoration: 'none' }}>
          <img
            src="/logo.svg?v=7"
            alt="ForenSight"
            style={{ height: '36px', width: 'auto', objectFit: 'contain' }}
          />
        </Link>












        {/* Main Navigation Links */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {/* All Cases / Dashboard Link */}
          <Link
            to="/dashboard"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 16px',
              borderRadius: '12px',
              fontSize: '13px',
              fontWeight: '700',
              textDecoration: 'none',
              background: isDashboardActive 
                ? 'linear-gradient(135deg, #6366f1, #4f46e5)' 
                : 'rgba(99, 102, 241, 0.16)',
              border: isDashboardActive 
                ? '1px solid #6366f1' 
                : '1px solid rgba(99, 102, 241, 0.4)',
              color: isDashboardActive ? '#ffffff' : '#e2e8f0',
              boxShadow: isDashboardActive 
                ? '0 4px 14px rgba(99, 102, 241, 0.4)' 
                : '0 2px 10px rgba(99, 102, 241, 0.25)',
              transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
            }}
            onMouseEnter={e => {
              if (!isDashboardActive) {
                e.currentTarget.style.background = 'rgba(99, 102, 241, 0.28)'
                e.currentTarget.style.borderColor = 'rgba(99, 102, 241, 0.65)'
                e.currentTarget.style.transform = 'translateY(-1px)'
              }
            }}
            onMouseLeave={e => {
              if (!isDashboardActive) {
                e.currentTarget.style.background = 'rgba(99, 102, 241, 0.16)'
                e.currentTarget.style.borderColor = 'rgba(99, 102, 241, 0.4)'
                e.currentTarget.style.transform = 'translateY(0)'
              }
            }}
          >
            <LayoutDashboard size={16} style={{ color: isDashboardActive ? '#ffffff' : '#818cf8' }} />
            <span>All Cases</span>
          </Link>

          {canManageUsers && (
            <NavLink
              to="/users"
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 16px',
                borderRadius: '12px',
                fontSize: '13px',
                fontWeight: isActive ? '600' : '500',
                textDecoration: 'none',
                background: isActive ? 'linear-gradient(135deg, #6366f1, #4f46e5)' : 'transparent',
                color: isActive ? '#ffffff' : '#94a3b8',
                transition: 'all 0.2s ease',
              })}
            >
              <Users size={16} />
              <span>Users</span>
            </NavLink>
          )}
        </nav>
      </div>

      {/* Right Corner Actions: Profile & Logout */}
      <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '12px' }}>

        {user && (
          <Link
            to="/profile"
            title="Profile & Account Settings"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              textDecoration: 'none',
              padding: '6px 14px',
              borderRadius: '12px',
              background: isProfileActive 
                ? 'linear-gradient(135deg, #6366f1, #4f46e5)' 
                : 'rgba(255, 255, 255, 0.05)',
              border: isProfileActive 
                ? '1px solid #6366f1' 
                : '1px solid rgba(255, 255, 255, 0.1)',
              color: isProfileActive ? '#ffffff' : '#f8fafc',
              boxShadow: isProfileActive ? '0 4px 14px rgba(99, 102, 241, 0.4)' : 'none',
              transition: 'all 0.2s ease',
            }}
            onMouseEnter={e => {
              if (!isProfileActive) {
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'
                e.currentTarget.style.borderColor = 'rgba(99, 102, 241, 0.4)'
                e.currentTarget.style.transform = 'translateY(-1px)'
              }
            }}
            onMouseLeave={e => {
              if (!isProfileActive) {
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)'
                e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.1)'
                e.currentTarget.style.transform = 'translateY(0)'
              }
            }}
          >
            {/* Avatar */}
            <div style={{
              width: '28px', height: '28px', borderRadius: '50%',
              background: `hsl(${hue}, 60%, 45%)`,
              border: '2px solid rgba(129, 140, 248, 0.6)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '11px', fontWeight: '700', color: '#fff',
              flexShrink: 0,
            }}>
              {initials}
            </div>
            <div style={{ lineHeight: 1.2 }}>
              <div style={{ fontSize: '13px', fontWeight: '600' }}>
                Profile
              </div>
              <div style={{ fontSize: '9.5px', color: isProfileActive ? '#e0e7ff' : '#94a3b8', textTransform: 'capitalize' }}>
                {user.username}
              </div>
            </div>
          </Link>
        )}

        <div style={{ width: '1px', height: '24px', background: 'rgba(255, 255, 255, 0.1)' }} />

        <button
          onClick={handleLogout}
          title="Sign out"
          style={{
            display: 'flex', alignItems: 'center', gap: '6px',
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.25)',
            color: '#fca5a5', fontSize: '12.5px', fontWeight: '600',
            cursor: 'pointer', padding: '7.5px 14px',
            borderRadius: '10px', transition: 'all 0.2s ease',
            fontFamily: 'inherit',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = 'rgba(239, 68, 68, 0.25)'
            e.currentTarget.style.transform = 'translateY(-1px)'
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)'
            e.currentTarget.style.transform = 'translateY(0)'
          }}
        >
          <LogOut size={15} />
          Logout
        </button>
      </div>
    </header>
  )
}

export default Topbar
