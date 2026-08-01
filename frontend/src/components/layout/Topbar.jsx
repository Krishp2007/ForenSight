import { useNavigate } from 'react-router-dom'
import { LogOut, User } from 'lucide-react'
import useAuth from '../../hooks/useAuth'

const Topbar = ({ title }) => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="h-14 px-6 flex items-center justify-between bg-gray-800 border-b border-gray-700 shrink-0">
      <h1 className="text-white font-semibold text-sm">{title}</h1>
      <div className="flex items-center gap-4">
        {user && (
          <div className="flex items-center gap-2 text-gray-300 text-sm">
            <User size={15} />
            <span>{user.username}</span>
            <span className="text-gray-500 text-xs">({user.role})</span>
          </div>
        )}
        <button
          onClick={handleLogout}
          className="flex items-center gap-1 text-gray-400 hover:text-red-400 text-sm transition-colors"
        >
          <LogOut size={15} />
          Logout
        </button>
      </div>
    </header>
  )
}

export default Topbar
