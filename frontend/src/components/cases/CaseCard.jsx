import { useNavigate } from 'react-router-dom'
import { FolderOpen, Calendar } from 'lucide-react'
import CaseStatusBadge from './CaseStatusBadge'
import { formatDateShort } from '../../utils/formatters'

const CaseCard = ({ c }) => {
  const navigate = useNavigate()

  return (
    <div
      onClick={() => navigate(`/cases/${c.id}/evidence`)}
      className="cursor-pointer bg-gray-800 hover:bg-gray-750 border border-gray-700 hover:border-blue-600 rounded-xl p-5 transition-all flex flex-col gap-3"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 text-white font-semibold text-sm">
          <FolderOpen size={16} className="text-blue-400 shrink-0" />
          <span className="truncate">{c.title}</span>
        </div>
        <CaseStatusBadge status={c.status} />
      </div>
      {c.description && (
        <p className="text-gray-400 text-xs leading-relaxed line-clamp-2">{c.description}</p>
      )}
      <div className="flex items-center gap-1 text-gray-500 text-xs mt-auto">
        <Calendar size={12} />
        {formatDateShort(c.created_at)}
      </div>
    </div>
  )
}

export default CaseCard
