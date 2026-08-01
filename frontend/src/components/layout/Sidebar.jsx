import { NavLink, useParams } from 'react-router-dom'
import {
  LayoutDashboard,
  Upload,
  GitBranch,
  Clock,
  MessageSquare,
  FileText,
  Shield,
  Link,
  ShieldCheck,
  UserCircle,
} from 'lucide-react'

const Sidebar = () => {
  const { caseId } = useParams()

  const navItemStyle = (isActive) => ({
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '8px 12px',
    borderRadius: '8px',
    fontSize: '13px',
    fontWeight: '500',
    textDecoration: 'none',
    transition: 'background 0.15s, color 0.15s',
    background: isActive ? '#4a7fe8' : 'transparent',
    color: isActive ? '#ffffff' : '#9aa8c0',
    cursor: 'pointer',
  })

  return (
    <aside style={{
      width: '220px',
      flexShrink: 0,
      background: '#1e2a3d',
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      padding: '16px',
      gap: '4px',
      borderRight: '1px solid #2d3748',
    }}>
      {/* Brand */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        marginBottom: '24px',
        padding: '4px 4px',
      }}>
        <div style={{
          width: '34px', height: '34px',
          background: 'rgba(96,165,250,0.15)',
          border: '1px solid rgba(96,165,250,0.35)',
          borderRadius: '8px',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0,
        }}>
          <Shield size={17} color="#60a5fa" />
        </div>
        <div>
          <div style={{ color: '#ffffff', fontWeight: '700', fontSize: '15px', letterSpacing: '-0.2px' }}>
            ForenSight
          </div>
          <div style={{ color: '#6b7fa3', fontSize: '9px', letterSpacing: '1.5px', textTransform: 'uppercase' }}>
            AI Forensics
          </div>
        </div>
      </div>

      {/* Global nav */}
      <NavLink
        to="/dashboard"
        style={({ isActive }) => navItemStyle(isActive)}
        onMouseEnter={e => { if (e.currentTarget.style.background !== 'rgb(74, 127, 232)') e.currentTarget.style.background = '#2a3347' }}
        onMouseLeave={e => { if (e.currentTarget.style.background !== 'rgb(74, 127, 232)') e.currentTarget.style.background = 'transparent' }}
      >
        <LayoutDashboard size={15} />
        Dashboard
      </NavLink>

      {/* Case-scoped nav — only visible when inside a case */}
      {caseId && (
        <>
          <div style={{
            marginTop: '16px',
            marginBottom: '4px',
            padding: '0 12px',
            fontSize: '10px',
            color: '#4a5568',
            textTransform: 'uppercase',
            letterSpacing: '2px',
            fontWeight: '600',
          }}>
            Current Case
          </div>
          <NavLink
            to={`/cases/${caseId}/evidence`}
            style={({ isActive }) => navItemStyle(isActive)}
            onMouseEnter={e => { if (e.currentTarget.style.background !== 'rgb(74, 127, 232)') e.currentTarget.style.background = '#2a3347' }}
            onMouseLeave={e => { if (e.currentTarget.style.background !== 'rgb(74, 127, 232)') e.currentTarget.style.background = 'transparent' }}
          >
            <Upload size={15} />
            Evidence
          </NavLink>
          <NavLink
            to={`/cases/${caseId}/timeline`}
            style={({ isActive }) => navItemStyle(isActive)}
            onMouseEnter={e => { if (e.currentTarget.style.background !== 'rgb(74, 127, 232)') e.currentTarget.style.background = '#2a3347' }}
            onMouseLeave={e => { if (e.currentTarget.style.background !== 'rgb(74, 127, 232)') e.currentTarget.style.background = 'transparent' }}
          >
            <Clock size={15} />
            Timeline
          </NavLink>
          <NavLink
            to={`/cases/${caseId}/graph`}
            style={({ isActive }) => navItemStyle(isActive)}
            onMouseEnter={e => { if (e.currentTarget.style.background !== 'rgb(74, 127, 232)') e.currentTarget.style.background = '#2a3347' }}
            onMouseLeave={e => { if (e.currentTarget.style.background !== 'rgb(74, 127, 232)') e.currentTarget.style.background = 'transparent' }}
          >
            <GitBranch size={15} />
            Graph
          </NavLink>
          <NavLink
            to={`/cases/${caseId}/correlations`}
            style={({ isActive }) => navItemStyle(isActive)}
            onMouseEnter={e => { if (e.currentTarget.style.background !== 'rgb(74, 127, 232)') e.currentTarget.style.background = '#2a3347' }}
            onMouseLeave={e => { if (e.currentTarget.style.background !== 'rgb(74, 127, 232)') e.currentTarget.style.background = 'transparent' }}
          >
            <Link size={15} />
            Correlations
          </NavLink>
          <NavLink
            to={`/cases/${caseId}/chat`}
            style={({ isActive }) => navItemStyle(isActive)}
            onMouseEnter={e => { if (e.currentTarget.style.background !== 'rgb(74, 127, 232)') e.currentTarget.style.background = '#2a3347' }}
            onMouseLeave={e => { if (e.currentTarget.style.background !== 'rgb(74, 127, 232)') e.currentTarget.style.background = 'transparent' }}
          >
            <MessageSquare size={15} />
            Copilot
          </NavLink>
          <NavLink
            to={`/cases/${caseId}/report`}
            style={({ isActive }) => navItemStyle(isActive)}
            onMouseEnter={e => { if (e.currentTarget.style.background !== 'rgb(74, 127, 232)') e.currentTarget.style.background = '#2a3347' }}
            onMouseLeave={e => { if (e.currentTarget.style.background !== 'rgb(74, 127, 232)') e.currentTarget.style.background = 'transparent' }}
          >
            <FileText size={15} />
            Report
          </NavLink>
          <NavLink
            to={`/cases/${caseId}/audit`}
            style={({ isActive }) => navItemStyle(isActive)}
            onMouseEnter={e => { if (e.currentTarget.style.background !== 'rgb(74, 127, 232)') e.currentTarget.style.background = '#2a3347' }}
            onMouseLeave={e => { if (e.currentTarget.style.background !== 'rgb(74, 127, 232)') e.currentTarget.style.background = 'transparent' }}
          >
            <ShieldCheck size={15} />
            Audit Trail
          </NavLink>
        </>
      )}
      {/* Profile link — pinned at bottom */}
      <div style={{ flex: 1 }} />
      <div style={{ borderTop: '1px solid #2d3748', paddingTop: '12px' }}>
        <NavLink
          to="/profile"
          style={({ isActive }) => navItemStyle(isActive)}
          onMouseEnter={e => { if (e.currentTarget.style.background !== 'rgb(74, 127, 232)') e.currentTarget.style.background = '#2a3347' }}
          onMouseLeave={e => { if (e.currentTarget.style.background !== 'rgb(74, 127, 232)') e.currentTarget.style.background = 'transparent' }}
        >
          <UserCircle size={15} />
          Profile &amp; Settings
        </NavLink>
      </div>
    </aside>
  )
}

export default Sidebar
