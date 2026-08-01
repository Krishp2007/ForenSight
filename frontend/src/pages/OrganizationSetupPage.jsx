import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createOrganization } from '../services/organizationService'
import { Shield, Building2 } from 'lucide-react'
import Spinner from '../components/ui/Spinner'

const OrganizationSetupPage = () => {
  const [name, setName] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await createOrganization(name)
      navigate('/register')
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to create organization')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
      <div className="w-full max-w-sm bg-gray-800 rounded-2xl shadow-2xl p-8">
        <div className="flex flex-col items-center gap-2 mb-8">
          <div className="p-3 bg-emerald-600/20 rounded-full">
            <Building2 size={28} className="text-emerald-400" />
          </div>
          <h1 className="text-white text-xl font-bold">Create Organization</h1>
          <p className="text-gray-400 text-sm text-center">Set up your forensics team workspace before registering users.</p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1 font-medium">Organization Name</label>
            <input
              value={name} onChange={(e) => setName(e.target.value)}
              required minLength={2}
              className="w-full px-3 py-2 rounded-lg bg-gray-700 border border-gray-600 text-white text-sm focus:outline-none focus:border-emerald-500"
              placeholder="e.g. DFIR Team Alpha"
            />
          </div>

          {error && (
            <p className="text-red-400 text-xs bg-red-900/20 border border-red-800 rounded-lg px-3 py-2">{error}</p>
          )}

          <button
            type="submit" disabled={loading}
            className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white text-sm font-semibold rounded-lg flex items-center justify-center gap-2 transition-colors"
          >
            {loading ? <Spinner size="sm" /> : <Shield size={15} />}
            Create & Continue
          </button>
        </form>
      </div>
    </div>
  )
}

export default OrganizationSetupPage
