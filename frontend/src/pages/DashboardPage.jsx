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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '1080px', margin: '0 auto' }}>
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ color: '#ffffff', fontSize: '20px', fontWeight: '700', margin: '0 0 4px 0' }}>Cases</h2>
          <p style={{ color: '#9aa8c0', fontSize: '13px', margin: 0 }}>
            {cases.length} case{cases.length !== 1 ? 's' : ''} in your organization
          </p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          style={{
            display: 'flex', alignItems: 'center', gap: '8px',
            padding: '8px 16px',
            background: '#4a7fe8',
            border: 'none',
            borderRadius: '8px',
            color: '#ffffff',
            fontSize: '13px',
            fontWeight: '600',
            cursor: 'pointer',
            transition: 'background 0.2s',
            fontFamily: 'inherit',
          }}
          onMouseEnter={e => e.currentTarget.style.background = '#3b6bc4'}
          onMouseLeave={e => e.currentTarget.style.background = '#4a7fe8'}
        >
          <Plus size={16} />
          New Case
        </button>
      </div>

      {/* Create form modal */}
      {showForm && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 50,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: 'rgba(0,0,0,0.6)',
          padding: '16px',
        }}>
          <div style={{
            background: '#323d52',
            borderRadius: '16px',
            boxShadow: '0 25px 60px rgba(0,0,0,0.5)',
            padding: '24px',
            width: '100%',
            maxWidth: '440px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
              <h3 style={{ color: '#ffffff', fontWeight: '600', fontSize: '16px', margin: 0 }}>New Case</h3>
              <button
                onClick={() => setShowForm(false)}
                style={{ background: 'none', border: 'none', color: '#9aa8c0', cursor: 'pointer', padding: 0 }}
              >
                <X size={18} />
              </button>
            </div>
            <CaseForm onSubmit={handleCreate} onCancel={() => setShowForm(false)} loading={creating} />
          </div>
        </div>
      )}

      {/* Filter row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
        <span style={{ color: '#9aa8c0', fontSize: '12px' }}>Status:</span>
        <button
          onClick={() => setStatusFilter('')}
          style={{
            fontSize: '12px', padding: '5px 12px',
            borderRadius: '99px',
            border: `1px solid ${!statusFilter ? '#4a7fe8' : '#3d4f6a'}`,
            background: !statusFilter ? '#4a7fe8' : 'transparent',
            color: !statusFilter ? '#ffffff' : '#9aa8c0',
            cursor: 'pointer',
            transition: 'all 0.15s',
            fontFamily: 'inherit',
          }}
        >
          All
        </button>
        {CASE_STATUSES.map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            style={{
              fontSize: '12px', padding: '5px 12px',
              borderRadius: '99px',
              border: `1px solid ${statusFilter === s ? '#4a7fe8' : '#3d4f6a'}`,
              background: statusFilter === s ? '#4a7fe8' : 'transparent',
              color: statusFilter === s ? '#ffffff' : '#9aa8c0',
              cursor: 'pointer',
              transition: 'all 0.15s',
              fontFamily: 'inherit',
            }}
          >
            {humanize(s)}
          </button>
        ))}
      </div>

      {error && (
        <div style={{
          background: 'rgba(239,68,68,0.1)',
          border: '1px solid rgba(239,68,68,0.4)',
          borderRadius: '8px',
          padding: '12px 16px',
          color: '#fca5a5',
          fontSize: '13px',
        }}>
          {error}
        </div>
      )}

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '64px 0' }}>
          <Spinner size="lg" />
        </div>
      ) : cases.length === 0 ? (
        <EmptyState icon={FolderOpen} title="No cases yet" description="Create your first forensic case to get started." />
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
          gap: '16px',
        }}>
          {cases.map((c) => <CaseCard key={c.id} c={c} />)}
        </div>
      )}
    </div>
  )
}

export default DashboardPage
