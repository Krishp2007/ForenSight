import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FolderOpen, Calendar } from 'lucide-react'
import CaseStatusBadge from './CaseStatusBadge'
import { formatDateShort } from '../../utils/formatters'

const CaseCard = ({ c }) => {
  const navigate = useNavigate()
  const [hovered, setHovered] = useState(false)

  return (
    <div
      onClick={() => navigate(`/cases/${c.id}/evidence`)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        cursor: 'pointer',
        background: '#2d3748',
        border: `1px solid ${hovered ? '#4a7fe8' : '#3d4f6a'}`,
        borderRadius: '12px',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        transition: 'border-color 0.2s, box-shadow 0.2s',
        boxShadow: hovered ? '0 4px 20px rgba(74,127,232,0.15)' : 'none',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#ffffff', fontWeight: '600', fontSize: '13px', minWidth: 0 }}>
          <FolderOpen size={15} color="#60a5fa" style={{ flexShrink: 0 }} />
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.title}</span>
        </div>
        <CaseStatusBadge status={c.status} />
      </div>
      {c.description && (
        <p style={{
          color: '#9aa8c0',
          fontSize: '12px',
          lineHeight: '1.6',
          margin: 0,
          display: '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical',
          overflow: 'hidden',
        }}>
          {c.description}
        </p>
      )}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#6b7fa3', fontSize: '11px', marginTop: 'auto' }}>
        <Calendar size={11} />
        {formatDateShort(c.created_at)}
      </div>
    </div>
  )
}

export default CaseCard
