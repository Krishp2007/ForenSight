import { NavLink, useParams } from 'react-router-dom'
import {
  LayoutDashboard,
  FolderOpen,
  Upload,
  GitBranch,
  Clock,
  MessageSquare,
  FileText,
  Shield,
  Link,
  ShieldCheck,
} from 'lucide-react'

const navBase =
  'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors'
const active = 'bg-blue-600 text-white'
const inactive = 'text-gray-400 hover:bg-gray-700 hover:text-white'

const Sidebar = () => {
  const { caseId } = useParams()

  return (
    <aside className="w-56 shrink-0 bg-gray-900 min-h-screen flex flex-col p-4 gap-1">
      {/* Brand */}
      <div className="flex items-center gap-2 mb-6 px-1">
        <Shield size={22} className="text-blue-500" />
        <span className="text-white font-bold text-base tracking-tight">ForenSight</span>
      </div>

      {/* Global nav */}
      <NavLink to="/dashboard" className={({ isActive }) => `${navBase} ${isActive ? active : inactive}`}>
        <LayoutDashboard size={16} />
        Dashboard
      </NavLink>

      {/* Case-scoped nav — only visible when inside a case */}
      {caseId && (
        <>
          <div className="mt-4 mb-1 px-3 text-xs text-gray-500 uppercase tracking-widest">
            Current Case
          </div>
          <NavLink
            to={`/cases/${caseId}/evidence`}
            className={({ isActive }) => `${navBase} ${isActive ? active : inactive}`}
          >
            <Upload size={16} />
            Evidence
          </NavLink>
          <NavLink
            to={`/cases/${caseId}/timeline`}
            className={({ isActive }) => `${navBase} ${isActive ? active : inactive}`}
          >
            <Clock size={16} />
            Timeline
          </NavLink>
          <NavLink
            to={`/cases/${caseId}/graph`}
            className={({ isActive }) => `${navBase} ${isActive ? active : inactive}`}
          >
            <GitBranch size={16} />
            Graph
          </NavLink>
          <NavLink
            to={`/cases/${caseId}/correlations`}
            className={({ isActive }) => `${navBase} ${isActive ? active : inactive}`}
          >
            <Link size={16} />
            Correlations
          </NavLink>
          <NavLink
            to={`/cases/${caseId}/chat`}
            className={({ isActive }) => `${navBase} ${isActive ? active : inactive}`}
          >
            <MessageSquare size={16} />
            Copilot
          </NavLink>
          <NavLink
            to={`/cases/${caseId}/report`}
            className={({ isActive }) => `${navBase} ${isActive ? active : inactive}`}
          >
            <FileText size={16} />
            Report
          </NavLink>
          <NavLink
            to={`/cases/${caseId}/audit`}
            className={({ isActive }) => `${navBase} ${isActive ? active : inactive}`}
          >
            <ShieldCheck size={16} />
            Audit Trail
          </NavLink>
        </>
      )}
    </aside>
  )
}

export default Sidebar
