import { useNavigate, Link } from 'react-router-dom'
import { LogOut, Settings } from 'lucide-react'
import useAuth from '../../hooks/useAuth'

const Topbar = ({ title }) => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  // Derive initials for avatar
  const initials = (user?.username || '?').split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
  const hue = [...(user?.username || '')].reduce((a, c) => a + c.charCodeAt(0), 0) % 360

  return (
    <header style={{
      height: '56px',
      padding: '0 24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      background: '#1e2a3d',
      borderBottom: '1px solid #2d3748',
      flexShrink: 0,
    }}>
      <h1 style={{ color: '#ffffff', fontWeight: '600', fontSize: '14px', margin: 0 }}>
        {title}
      </h1>

      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {user && (
          <Link
            to="/profile"
            style={{
              display: 'flex', alignItems: 'center', gap: '9px',
              textDecoration: 'none',
              padding: '5px 10px', borderRadius: '8px',
              transition: 'background 0.15s',
            }}
            onMouseEnter={e => e.currentTarget.style.background = '#2a3347'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
          >
            {/* Avatar */}
            <div style={{
              width: '28px', height: '28px', borderRadius: '50%',
              background: `hsl(${hue},55%,35%)`,
              border: '2px solid rgba(96,165,250,0.4)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '11px', fontWeight: '700', color: '#fff',
              flexShrink: 0,
            }}>
              {initials}
            </div>
            <div style={{ lineHeight: 1.2 }}>
              <div style={{ color: '#e2e8f0', fontSize: '13px', fontWeight: '500' }}>
                {user.username}
              </div>
              <div style={{ color: '#4a5568', fontSize: '10px', textTransform: 'capitalize' }}>
                {user.role}
              </div>
            </div>
            <Settings size={13} color="#4a5568" />
          </Link>
        )}

        <div style={{ width: '1px', height: '24px', background: '#2d3748' }} />

        <button
          onClick={handleLogout}
          title="Sign out"
          style={{
            display: 'flex', alignItems: 'center', gap: '6px',
            background: 'none', border: 'none',
            color: '#9aa8c0', fontSize: '13px',
            cursor: 'pointer', padding: '6px 10px',
            borderRadius: '6px', transition: 'color 0.15s, background 0.15s',
            fontFamily: 'inherit',
          }}
          onMouseEnter={e => { e.currentTarget.style.color = '#fca5a5'; e.currentTarget.style.background = 'rgba(239,68,68,0.1)' }}
          onMouseLeave={e => { e.currentTarget.style.color = '#9aa8c0'; e.currentTarget.style.background = 'none' }}
        >
          <LogOut size={15} />
          Logout
        </button>
      </div>
    </header>
  )
}

export default Topbar
