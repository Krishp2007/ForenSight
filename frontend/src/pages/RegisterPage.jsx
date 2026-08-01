import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { register, login } from '../services/authService'
import useAuth from '../hooks/useAuth'
import { listOrganizations } from '../services/organizationService'
import { Shield, UserPlus } from 'lucide-react'
import Spinner from '../components/ui/Spinner'
import { USER_ROLES } from '../utils/constants'
import { humanize } from '../utils/formatters'

const RegisterPage = () => {
  const [orgs, setOrgs] = useState([])
  const [form, setForm] = useState({ email: '', username: '', password: '', organization_id: '', role: 'investigator' })
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const { setToken, fetchMe } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    listOrganizations().then(setOrgs).catch(() => {})
  }, [])

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await register(form)
      // Auto-login after successful registration
      const { access_token } = await login(form.email, form.password)
      setToken(access_token)
      await fetchMe()
      navigate('/dashboard', { replace: true })
    } catch (e) {
      setError(e.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const inputCls = 'w-full px-3 py-2 rounded-lg bg-gray-700 border border-gray-600 text-white text-sm focus:outline-none focus:border-blue-500'
  const labelCls = 'block text-xs text-gray-400 mb-1 font-medium'

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
      <div className="w-full max-w-sm bg-gray-800 rounded-2xl shadow-2xl p-8">
        <div className="flex flex-col items-center gap-2 mb-6">
          <div className="p-3 bg-blue-600/20 rounded-full">
            <Shield size={28} className="text-blue-400" />
          </div>
          <h1 className="text-white text-xl font-bold">Create Account</h1>
          <p className="text-gray-400 text-sm">ForenSight AI</p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <div>
            <label className={labelCls}>Email</label>
            <input type="email" value={form.email} onChange={set('email')} required className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Username</label>
            <input value={form.username} onChange={set('username')} required minLength={3} className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Password</label>
            <input type="password" value={form.password} onChange={set('password')} required minLength={8} className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Organization</label>
            {orgs.length > 0 ? (
              <select value={form.organization_id} onChange={set('organization_id')} required className={inputCls}>
                <option value="">Select organization…</option>
                {orgs.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
              </select>
            ) : (
              <div className="text-xs text-yellow-400 bg-yellow-900/20 border border-yellow-800 rounded-lg px-3 py-2">
                No organizations found.{' '}
                <Link to="/setup" className="underline">Create one first</Link>
              </div>
            )}
          </div>
          <div>
            <label className={labelCls}>Role</label>
            <select value={form.role} onChange={set('role')} className={inputCls}>
              {USER_ROLES.map((r) => <option key={r} value={r}>{humanize(r)}</option>)}
            </select>
          </div>

          {error && (
            <p className="text-red-400 text-xs bg-red-900/20 border border-red-800 rounded-lg px-3 py-2">{error}</p>
          )}

          <button
            type="submit" disabled={loading}
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-semibold rounded-lg flex items-center justify-center gap-2 mt-1 transition-colors"
          >
            {loading ? <Spinner size="sm" /> : <UserPlus size={15} />}
            Register
          </button>
        </form>

        <p className="text-center text-gray-500 text-xs mt-5">
          Already have an account?{' '}
          <Link to="/login" className="text-blue-400 hover:text-blue-300">Sign in</Link>
        </p>
      </div>
    </div>
  )
}

export default RegisterPage
