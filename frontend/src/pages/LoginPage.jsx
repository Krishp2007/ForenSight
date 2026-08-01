import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { login } from '../services/authService'
import useAuth from '../hooks/useAuth'
import { Shield, LogIn } from 'lucide-react'
import Spinner from '../components/ui/Spinner'

const LoginPage = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const { setToken } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const data = await login(email, password)
      // Store token — this is the ONLY thing we do before navigating
      setToken(data.access_token)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  const inputCls = 'w-full px-3 py-2 rounded-lg bg-gray-700 border border-gray-600 text-white text-sm focus:outline-none focus:border-blue-500'

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
      <div className="w-full max-w-sm bg-gray-800 rounded-2xl shadow-2xl p-8">
        <div className="flex flex-col items-center gap-2 mb-8">
          <div className="p-3 bg-blue-600/20 rounded-full">
            <Shield size={28} className="text-blue-400" />
          </div>
          <h1 className="text-white text-xl font-bold">ForenSight AI</h1>
          <p className="text-gray-400 text-sm">Forensic Investigation Copilot</p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1 font-medium">Email</label>
            <input
              type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              required className={inputCls} placeholder="analyst@forensight.org"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1 font-medium">Password</label>
            <input
              type="password" value={password} onChange={(e) => setPassword(e.target.value)}
              required className={inputCls} placeholder="••••••••"
            />
          </div>

          {error && (
            <p className="text-red-400 text-xs bg-red-900/20 border border-red-800 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit" disabled={loading}
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-semibold rounded-lg flex items-center justify-center gap-2 transition-colors"
          >
            {loading ? <Spinner size="sm" /> : <LogIn size={15} />}
            Sign In
          </button>
        </form>

        <p className="text-center text-gray-500 text-xs mt-6">
          Don't have an account?{' '}
          <Link to="/register" className="text-blue-400 hover:text-blue-300">Register</Link>
        </p>
      </div>
    </div>
  )
}

export default LoginPage
