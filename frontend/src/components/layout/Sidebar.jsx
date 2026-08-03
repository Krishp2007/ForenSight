import { NavLink, useParams, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Upload, GitBranch, Clock,
  MessageSquare, FileText, Shield, Link,
  ShieldCheck, UserCircle, Users, ArrowLeft,
} from 'lucide-react'
import useRole from '../../hooks/useRole'

const Sidebar = () => {
  const { caseId } = useParams()
  const navigate    = useNavigate()
  const { canManageUsers } = useRole()

  const nav = (isActive) => ({
    display: 'flex', alignItems: 'center', gap: '10px',
    padding: '8px 12px', borderRadius: '8px',
    fontSize: '13px', fontWeight: '500', textDecoration: 'none',
    transition: 'background 0.15s, color 0.15s',
    background: isActive ? '#4a7fe8' : 'transparent',
    color: isActive ? '#ffffff' : '#9aa8c0',
    cursor: 'pointer',
  })

  const hover = {
    onMouseEnter: e => { if (e.currentTarget.style.background !== 'rgb(74, 127, 232)') e.currentTarget.style.background = '#2a3347' },
    onMouseLeave: e => { if (e.currentTarget.style.background !== 'rgb(74, 127, 232)') e.currentTarget.style.background = 'transparent' },
  }

  return (
    <aside style={{
      width: '220px', flexShrink: 0, background: '#1e2a3d',
      minHeight: '100vh', display: 'flex', flexDirection: 'column',
      padding: '16px', gap: '4px', borderRight: '1px solid #2d3748',
    }}>
      {/* Brand */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px', padding: '4px' }}>
        <div style={{ width: '34px', height: '34px', background: 'rgba(96,165,250,0.15)', border: '1px solid rgba(96,165,250,0.35)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          <Shield size={17} color="#60a5fa" />
        </div>
        <div>
          <div style={{ color: '#ffffff', fontWeight: '700', fontSize: '15px', letterSpacing: '-0.2px' }}>ForenSight</div>
          <div style={{ color: '#6b7fa3', fontSize: '9px', letterSpacing: '1.5px', textTransform: 'uppercase' }}>AI Forensics</div>
        </div>
      </div>

      {caseId ? (
        /* ── Inside a case: show only case tabs ── */
        <>
          <div style={{ marginBottom: '8px', padding: '0 4px' }}>
            <button
              onClick={() => navigate('/dashboard')}
              style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 12px', borderRadius: '8px', fontSize: '13px', fontWeight: '500', background: 'transparent', border: 'none', color: '#9aa8c0', cursor: 'pointer', fontFamily: 'inherit', transition: 'background 0.15s, color 0.15s', width: '100%' }}
              onMouseEnter={e => { e.currentTarget.style.background = '#2a3347'; e.currentTarget.style.color = '#fff' }}
              onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = '#9aa8c0' }}
            >
              <ArrowLeft size={15} /> All Cases
            </button>
          </div>

          {[
            { to: 'evidence',     icon: <Upload size={15} />,        label: 'Evidence'     },
            { to: 'timeline',     icon: <Clock size={15} />,         label: 'Timeline'     },
            { to: 'graph',        icon: <GitBranch size={15} />,     label: 'Graph'        },
            { to: 'correlations', icon: <Link size={15} />,          label: 'Correlations' },
            { to: 'chat',         icon: <MessageSquare size={15} />, label: 'Copilot'      },
            { to: 'report',       icon: <FileText size={15} />,      label: 'Report'       },
            { to: 'audit',        icon: <ShieldCheck size={15} />,   label: 'Audit Trail'  },
          ].map(({ to, icon, label }) => (
            <NavLink key={to} to={`/cases/${caseId}/${to}`} style={({ isActive }) => nav(isActive)} {...hover}>
              {icon} {label}
            </NavLink>
          ))}
        </>
      ) : (
        /* ── Outside a case: show global nav only ── */
        <>
          <NavLink to="/dashboard" style={({ isActive }) => nav(isActive)} {...hover}>
            <LayoutDashboard size={15} /> Dashboard
          </NavLink>

          {canManageUsers && (
            <NavLink to="/users" style={({ isActive }) => nav(isActive)} {...hover}>
              <Users size={15} /> Users
            </NavLink>
          )}
        </>
      )}

      {/* Profile — always pinned at bottom */}
      <div style={{ flex: 1 }} />
      <div style={{ borderTop: '1px solid #2d3748', paddingTop: '12px' }}>
        <NavLink to="/profile" style={({ isActive }) => nav(isActive)} {...hover}>
          <UserCircle size={15} /> Profile &amp; Settings
        </NavLink>
      </div>
    </aside>
  )
}

export default Sidebar
