import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FolderOpen, Calendar, ArrowRight } from 'lucide-react'
import { humanize, formatDateShort } from '../../utils/formatters'

// Theme-aware status badge configuration
const statusBadgeConfig = (status) => {
  switch (status) {
    case 'open':
      return { 
        bg: 'rgba(16, 185, 129, 0.16)', 
        color: '#10b981', 
        border: 'rgba(16, 185, 129, 0.35)',
        label: 'Open Case'
      }
    case 'in_progress':
      return { 
        bg: 'rgba(99, 102, 241, 0.16)', 
        color: '#6366f1', 
        border: 'rgba(99, 102, 241, 0.35)',
        label: 'In Progress'
      }
    case 'suspended':
      return { 
        bg: 'rgba(245, 158, 11, 0.16)', 
        color: '#f59e0b', 
        border: 'rgba(245, 158, 11, 0.35)',
        label: 'Suspended'
      }
    case 'resolved':
    default:
      return { 
        bg: 'rgba(148, 163, 184, 0.16)', 
        color: '#64748b', 
        border: 'rgba(148, 163, 184, 0.35)',
        label: 'Resolved'
      }
  }
}

const CaseStatusBadge = ({ status, hovered }) => {
  const cfg = statusBadgeConfig(status)
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '6px',
      padding: '5px 12px', borderRadius: '20px',
      fontSize: '11px', fontWeight: '700', textTransform: 'uppercase',
      letterSpacing: '0.5px', background: cfg.bg, color: cfg.color,
      whiteSpace: 'nowrap', border: `1px solid ${cfg.border}`,
      boxShadow: hovered ? `0 2px 8px ${cfg.border}` : 'none',
      transition: 'all 0.25s ease',
    }}>
      <span style={{ 
        width: '6px', height: '6px', borderRadius: '50%', 
        background: cfg.color,
      }} />
      {cfg.label}
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
        animationDelay: `${index * 0.04}s`,
        cursor: 'pointer',
        background: 'var(--forensic-card-bg, #ffffff)',
        border: hovered ? '1px solid var(--forensic-primary, #2563eb)' : '1px solid var(--forensic-border, #e2e8f0)',
        borderRadius: '20px',
        padding: '24px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        position: 'relative',
        overflow: 'hidden',
        transform: hovered ? 'translateY(-4px)' : 'translateY(0)',
        transition: 'all 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
        boxShadow: hovered 
          ? '0 16px 32px -8px rgba(37, 99, 235, 0.25), 0 4px 12px rgba(0, 0, 0, 0.08)' 
          : '0 2px 10px rgba(0, 0, 0, 0.04)',
      }}
    >
      {/* Shimmer top gradient line */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: '3.5px',
        background: 'linear-gradient(90deg, var(--forensic-primary, #2563eb), #06b6d4)',
        opacity: hovered ? 1 : 0,
        transition: 'opacity 0.25s ease',
      }} />

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0 }}>
          <div style={{
            padding: '10px',
            borderRadius: '12px',
            background: 'rgba(99, 102, 241, 0.15)',
            border: '1px solid rgba(99, 102, 241, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--forensic-primary, #2563eb)',
            transform: hovered ? 'scale(1.05)' : 'scale(1)',
            transition: 'all 0.25s ease',
            flexShrink: 0,
          }}>
            <FolderOpen size={18} />
          </div>
          <h3 style={{
            color: 'var(--forensic-text-main, #0f172a)',
            fontWeight: '700',
            fontSize: '15.5px',
            margin: 0,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            letterSpacing: '-0.3px',
          }}>
            {c.title}
          </h3>
        </div>
        <CaseStatusBadge status={c.status} hovered={hovered} />
      </div>

      {/* Description */}
      {c.description ? (
        <p style={{
          color: 'var(--forensic-text-muted, #64748b)',
          fontSize: '13px',
          lineHeight: '1.65',
          margin: 0,
          display: '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical',
          overflow: 'hidden',
        }}>
          {c.description}
        </p>
      ) : (
        <p style={{ color: 'var(--forensic-text-muted, #94a3b8)', fontSize: '13px', fontStyle: 'italic', margin: 0 }}>
          No description provided for this case file.
        </p>
      )}

      {/* Footer */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        color: 'var(--forensic-text-muted, #64748b)',
        fontSize: '12px',
        marginTop: 'auto',
        paddingTop: '14px',
        borderTop: '1px solid var(--forensic-border, #e2e8f0)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Calendar size={13.5} style={{ color: 'var(--forensic-text-muted, #94a3b8)' }} />
          <span>Created {formatDateShort(c.created_at)}</span>
        </div>

        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          color: 'var(--forensic-primary, #2563eb)',
          fontWeight: '700',
          fontSize: '12px',
        }}>
          <span>Open Case</span>
          <ArrowRight
            size={14}
            style={{
              transform: hovered ? 'translateX(4px)' : 'translateX(0)',
              transition: 'transform 0.25s ease',
            }}
          />
        </div>
      </div>
    </div>
  )
}

export default CaseCard
