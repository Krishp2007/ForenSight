import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FolderOpen, Calendar, ArrowRight } from 'lucide-react'
import { humanize, formatDateShort } from '../../utils/formatters'

// Dark cyber status badge color mapping
const darkStatusStyle = (status) => {
  switch (status) {
    case 'open':
      return { background: 'rgba(16, 185, 129, 0.18)', color: '#34d399', border: 'rgba(16, 185, 129, 0.35)' }
    case 'in_progress':
      return { background: 'rgba(59, 130, 246, 0.18)', color: '#60a5fa', border: 'rgba(59, 130, 246, 0.35)' }
    case 'suspended':
      return { background: 'rgba(245, 158, 11, 0.18)', color: '#fbbf24', border: 'rgba(245, 158, 11, 0.35)' }
    case 'resolved':
    default:
      return { background: 'rgba(148, 163, 184, 0.18)', color: '#cbd5e1', border: 'rgba(148, 163, 184, 0.35)' }
  }
}

const CaseStatusBadge = ({ status, hovered }) => {
  const s = darkStatusStyle(status)
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '5px',
      padding: '3px 10px', borderRadius: '99px',
      fontSize: '11px', fontWeight: '600', textTransform: 'uppercase',
      letterSpacing: '0.6px', background: s.background, color: s.color,
      whiteSpace: 'nowrap', border: `1px solid ${hovered ? s.color : s.border}`,
      boxShadow: hovered ? `0 0 14px ${s.background}` : `0 0 8px ${s.background}`,
      transition: 'all 0.3s ease',
    }}>
      <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: s.color }} />
      {humanize(status)}
    </span>
  )
}

const CaseCard = ({ c, index = 0 }) => {
  const navigate = useNavigate()
  const [hovered, setHovered] = useState(false)

  return (
    <div
      onClick={() => navigate(`/cases/${c.id}/dashboard`)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className="animate-dashboard-card"
      style={{
        animationDelay: `${index * 0.05}s`,
        cursor: 'pointer',
        background: hovered
          ? 'linear-gradient(145deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.85))'
          : 'rgba(30, 41, 59, 0.55)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        border: hovered ? '1px solid rgba(99, 102, 241, 0.7)' : '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '16px',
        padding: '22px',
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
        position: 'relative',
        overflow: 'hidden',
        transform: hovered ? 'translateY(-6px) scale(1.01)' : 'translateY(0) scale(1)',
        transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
        boxShadow: hovered 
          ? '0 14px 32px -6px rgba(99, 102, 241, 0.35), 0 0 24px rgba(6, 182, 212, 0.2)' 
          : '0 4px 14px rgba(0, 0, 0, 0.3)',
      }}
    >
      {/* Top glowing accent line */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: '3px',
        background: 'linear-gradient(90deg, #6366f1, #06b6d4, #818cf8)',
        opacity: hovered ? 1 : 0,
        transition: 'opacity 0.3s ease',
      }} />

      {/* Card Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0 }}>
          <div style={{
            padding: '9px',
            borderRadius: '12px',
            background: hovered ? 'rgba(99, 102, 241, 0.28)' : 'rgba(99, 102, 241, 0.15)',
            border: hovered ? '1px solid rgba(99, 102, 241, 0.5)' : '1px solid rgba(99, 102, 241, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justify: 'center',
            color: hovered ? '#ffffff' : '#818cf8',
            transform: hovered ? 'scale(1.08)' : 'scale(1)',

            boxShadow: hovered ? '0 0 14px rgba(99, 102, 241, 0.4)' : 'none',
            transition: 'all 0.3s ease',
            flexShrink: 0,
          }}>
            <FolderOpen size={17} />
          </div>
          <span style={{
            color: '#ffffff',
            fontWeight: '700',
            fontSize: '14.5px',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            textShadow: hovered ? '0 0 10px rgba(255, 255, 255, 0.3)' : 'none',
            transition: 'all 0.2s ease',
          }}>
            {c.title}
          </span>
        </div>
        <CaseStatusBadge status={c.status} hovered={hovered} />
      </div>

      {c.description && (
        <p style={{
          color: hovered ? '#cbd5e1' : '#94a3b8',
          fontSize: '12.5px',
          lineHeight: '1.6',
          margin: 0,
          display: '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical',
          overflow: 'hidden',
          transition: 'color 0.2s ease',
        }}>
          {c.description}
        </p>
      )}

      {/* Clean Date Footer with subtle sliding arrow indicator */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justify: 'space-between',
        color: hovered ? '#cbd5e1' : '#64748b',
        fontSize: '11.5px',
        marginTop: 'auto',
        paddingTop: '12px',
        borderTop: hovered ? '1px solid rgba(99, 102, 241, 0.25)' : '1px solid rgba(255, 255, 255, 0.06)',
        transition: 'all 0.3s ease',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Calendar size={13} style={{ color: hovered ? '#818cf8' : '#64748b', transition: 'color 0.2s ease' }} />
          <span>Created {formatDateShort(c.created_at)}</span>
        </div>
        <ArrowRight
          size={14}
          style={{
            color: '#818cf8',
            opacity: hovered ? 1 : 0,
            transform: hovered ? 'translateX(0)' : 'translateX(-6px)',
            transition: 'all 0.3s ease',
          }}
        />
      </div>
    </div>
  )
}

export default CaseCard
