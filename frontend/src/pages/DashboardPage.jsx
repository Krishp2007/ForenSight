import { useState, useEffect } from 'react'
import { listCases, createCase } from '../services/caseService'
import useCase from '../hooks/useCase'
import CaseCard from '../components/cases/CaseCard'
import CaseForm from '../components/cases/CaseForm'
import Spinner from '../components/ui/Spinner'
import EmptyState from '../components/ui/EmptyState'
import { CASE_STATUSES } from '../utils/constants'
import { humanize } from '../utils/formatters'
import { Plus, FolderOpen, X } from 'lucide-react'

const DashboardPage = () => {
  const { cases, setCases } = useCase()
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [creating, setCreating] = useState(false)
  const [statusFilter, setStatusFilter] = useState('')
  const [error, setError] = useState(null)

  const load = async () => {
    setLoading(true)
    try {
      const data = await listCases(statusFilter || null)
      setCases(data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load cases')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [statusFilter])

  const handleCreate = async (payload) => {
    setCreating(true)
    try {
      const c = await createCase(payload)
      setCases([c, ...cases])
      setShowForm(false)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to create case')
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="flex flex-col gap-6 max-w-5xl mx-auto">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-white text-xl font-bold">Cases</h2>
          <p className="text-gray-400 text-sm mt-0.5">{cases.length} case{cases.length !== 1 ? 's' : ''} in your organization</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition-colors"
        >
          <Plus size={16} />
          New Case
        </button>
      </div>

      {/* Create form modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
          <div className="bg-gray-800 rounded-2xl shadow-2xl p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-white font-semibold">New Case</h3>
              <button onClick={() => setShowForm(false)} className="text-gray-400 hover:text-white">
                <X size={18} />
              </button>
            </div>
            <CaseForm onSubmit={handleCreate} onCancel={() => setShowForm(false)} loading={creating} />
          </div>
        </div>
      )}

      {/* Filter row */}
      <div className="flex items-center gap-3">
        <span className="text-gray-400 text-xs">Status:</span>
        <button
          onClick={() => setStatusFilter('')}
          className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${!statusFilter ? 'bg-blue-600 border-blue-600 text-white' : 'border-gray-600 text-gray-400 hover:text-white'}`}
        >
          All
        </button>
        {CASE_STATUSES.map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${statusFilter === s ? 'bg-blue-600 border-blue-600 text-white' : 'border-gray-600 text-gray-400 hover:text-white'}`}
          >
            {humanize(s)}
          </button>
        ))}
      </div>

      {error && (
        <p className="text-red-400 text-sm bg-red-900/20 border border-red-800 rounded-lg px-4 py-3">{error}</p>
      )}

      {loading ? (
        <div className="flex justify-center py-16"><Spinner size="lg" /></div>
      ) : cases.length === 0 ? (
        <EmptyState icon={FolderOpen} title="No cases yet" description="Create your first forensic case to get started." />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {cases.map((c) => <CaseCard key={c.id} c={c} />)}
        </div>
      )}
    </div>
  )
}

export default DashboardPage
