import { useState, useEffect, useMemo, useRef } from 'react'
import { listCases, createCase } from '../services/caseService'
import useCase from '../hooks/useCase'
import CaseCard from '../components/cases/CaseCard'
import CaseForm from '../components/cases/CaseForm'
import { Spinner, EmptyState } from '../components/ui'
import { humanize } from '../utils/formatters'
import { 
  Plus, FolderOpen, X, Search, Briefcase, Clock, 
  CheckCircle2, AlertCircle, PauseCircle, Sparkles
} from 'lucide-react'

const DashboardPage = () => {
  const { cases, setCases } = useCase()
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [creating, setCreating] = useState(false)
  const [statusFilter, setStatusFilter] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [error, setError] = useState(null)
  const searchInputRef = useRef(null)

  const load = async () => {
    setLoading(true)
    try {
      const data = await listCases(null)
      setCases(data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load cases')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  // Auto-focus search bar when user starts typing on keyboard anywhere on Dashboard
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (showForm) return
      const activeTag = document.activeElement?.tagName?.toLowerCase()
      const isInputOrTextarea = activeTag === 'input' || activeTag === 'textarea' || document.activeElement?.isContentEditable
      if (isInputOrTextarea && document.activeElement !== searchInputRef.current) return

      if (e.key === 'Escape') {
        setSearchQuery('')
        searchInputRef.current?.blur()
        return
      }

      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        searchInputRef.current?.focus()
        return
      }

      if (e.key === '/' && document.activeElement !== searchInputRef.current) {
        e.preventDefault()
        searchInputRef.current?.focus()
        return
      }

      if (
        !e.ctrlKey &&
        !e.altKey &&
        !e.metaKey &&
        e.key.length === 1 &&
        document.activeElement !== searchInputRef.current
      ) {
        searchInputRef.current?.focus()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [showForm])

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

  // Metric stats
  const caseStats = useMemo(() => {
    const total = cases.length
    const open = cases.filter(c => c.status === 'open').length
    const inProgress = cases.filter(c => c.status === 'in_progress').length
    const suspended = cases.filter(c => c.status === 'suspended').length
    const resolved = cases.filter(c => c.status === 'resolved').length
    return { total, open, inProgress, suspended, resolved }
  }, [cases])

  // Filtered cases
  const filteredCases = useMemo(() => {
    let result = cases
    if (statusFilter) {
      result = result.filter(c => c.status === statusFilter)
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      result = result.filter(c => 
        c.title?.toLowerCase().includes(q) || 
        c.description?.toLowerCase().includes(q)
      )
    }
    return result
  }, [cases, statusFilter, searchQuery])

  // Interactive Stat Filter Cards
  const filterCards = [
    {
      id: '',
      label: 'All Cases',
      count: caseStats.total,
      icon: Briefcase,
      color: 'var(--forensic-primary, #2563eb)',
      bgLight: 'rgba(99, 102, 241, 0.14)',
      borderActive: 'var(--forensic-primary, #2563eb)',
    },
    {
      id: 'open',
      label: 'Open',
      count: caseStats.open,
      icon: AlertCircle,
      color: '#16a34a',
      bgLight: 'rgba(22, 163, 74, 0.14)',
      borderActive: '#16a34a',
    },
    {
      id: 'in_progress',
      label: 'In Progress',
      count: caseStats.inProgress,
      icon: Clock,
      color: '#6366f1',
      bgLight: 'rgba(99, 102, 241, 0.14)',
      borderActive: '#6366f1',
    },
    {
      id: 'suspended',
      label: 'Suspended',
      count: caseStats.suspended,
      icon: PauseCircle,
      color: '#d97706',
      bgLight: 'rgba(217, 119, 6, 0.14)',
      borderActive: '#d97706',
    },
    {
      id: 'resolved',
      label: 'Resolved',
      count: caseStats.resolved,
      icon: CheckCircle2,
      color: '#64748b',
      bgLight: 'rgba(100, 116, 139, 0.14)',
      borderActive: '#64748b',
    },
  ]

  return (
    <div style={{
      position: 'relative',
      display: 'flex',
      flexDirection: 'column',
      gap: '24px',
      maxWidth: '1240px',
      margin: '0 auto',
      width: '100%',
    }}>
      {/* ── HEADER BAR ── */}
      <div style={{ position: 'relative', zIndex: 1, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <h1 style={{ color: 'var(--forensic-text-main, #0f172a)', fontSize: '28px', fontWeight: '800', margin: 0, letterSpacing: '-0.6px' }}>
              {statusFilter ? `${humanize(statusFilter)} Cases` : 'Forensic Case Dashboard'}
            </h1>

            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 12px',
              borderRadius: '20px',
              fontSize: '11.5px',
              fontWeight: '700',
              background: 'rgba(99, 102, 241, 0.15)',
              color: 'var(--forensic-primary, #2563eb)',
              border: '1px solid var(--forensic-border, #bfdbfe)',
            }}>
              <Sparkles size={13} /> Active Workspace
            </span>
          </div>
          <p style={{ color: 'var(--forensic-text-muted, #64748b)', fontSize: '13.5px', margin: '4px 0 0 0' }}>
            Acquire, analyze, and manage electronic evidence with certified forensic standards.
          </p>
        </div>

        {/* New Case CTA Button */}
        <button
          onClick={() => setShowForm(true)}
          className="cyber-button-hover"
          style={{
            display: 'flex', alignItems: 'center', gap: '9px',
            padding: '12px 24px',
            background: 'var(--forensic-primary, #2563eb)',
            border: 'none',
            borderRadius: '14px',
            color: '#ffffff',
            fontSize: '14px',
            fontWeight: '700',
            cursor: 'pointer',
            boxShadow: '0 4px 14px rgba(37, 99, 235, 0.35)',
            transition: 'all 0.25s ease',
            fontFamily: 'inherit',
          }}
        >
          <Plus size={19} />
          New Case
        </button>
      </div>

      {/* ── INTERACTIVE STAT CARDS GRID ── */}
      <div style={{
        position: 'relative', zIndex: 1,
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))',
        gap: '16px',
      }}>
        {filterCards.map((card) => {
          const IconComponent = card.icon
          const isSelected = statusFilter === card.id
          return (
            <div
              key={card.id || 'all'}
              onClick={() => setStatusFilter(isSelected ? '' : card.id)}
              style={{
                cursor: 'pointer',
                background: 'var(--forensic-card-bg, #ffffff)',
                border: isSelected ? `2px solid ${card.borderActive}` : '1px solid var(--forensic-border, #e2e8f0)',
                borderRadius: '18px',
                padding: '20px 22px',
                display: 'flex',
                alignItems: 'center',
                gap: '16px',
                position: 'relative',
                boxShadow: isSelected 
                  ? `0 8px 24px -4px rgba(37, 99, 235, 0.2)` 
                  : '0 2px 8px rgba(0, 0, 0, 0.04)',
                transform: isSelected ? 'translateY(-3px)' : 'translateY(0)',
                transition: 'all 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
              }}
              onMouseEnter={e => {
                if (!isSelected) {
                  e.currentTarget.style.transform = 'translateY(-3px)'
                  e.currentTarget.style.borderColor = card.borderActive
                  e.currentTarget.style.boxShadow = '0 6px 16px rgba(0, 0, 0, 0.08)'
                }
              }}
              onMouseLeave={e => {
                if (!isSelected) {
                  e.currentTarget.style.transform = 'translateY(0)'
                  e.currentTarget.style.borderColor = 'var(--forensic-border, #e2e8f0)'
                  e.currentTarget.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.04)'
                }
              }}
            >
              <div
                style={{
                  padding: '11px',
                  borderRadius: '14px',
                  background: card.bgLight,
                  color: card.color,
                  display: 'flex',
                  border: `1px solid ${card.borderActive}30`,
                }}
              >
                <IconComponent size={22} />
              </div>
              <div>
                <div style={{
                  color: isSelected ? card.color : 'var(--forensic-text-muted, #64748b)',
                  fontSize: '12px',
                  fontWeight: '700',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                }}>
                  {card.label}
                </div>
                <div style={{ color: 'var(--forensic-text-main, #0f172a)', fontSize: '26px', fontWeight: '800', marginTop: '2px', letterSpacing: '-0.5px' }}>
                  {card.count}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* ── LIVE SEARCH BAR (CLEAN & MINIMAL) ── */}
      <div style={{
        position: 'relative', zIndex: 1,
        display: 'flex',
        alignItems: 'center',
        background: 'var(--forensic-card-bg, #ffffff)',
        border: '1px solid var(--forensic-border, #e2e8f0)',
        borderRadius: '16px',
        padding: '12px 18px',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)',
      }}>
        <div style={{
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
          width: '100%',
        }}>
          <Search size={18} style={{ position: 'absolute', left: '16px', color: 'var(--forensic-text-muted, #94a3b8)', pointerEvents: 'none' }} />
          <input
            ref={searchInputRef}
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search cases by title, description or tag..."
            style={{
              width: '100%',
              padding: '10px 40px 10px 46px',
              background: 'var(--forensic-panel-bg, #f8fafc)',
              border: '1px solid var(--forensic-border, #cbd5e1)',
              borderRadius: '12px',
              color: 'var(--forensic-text-main, #0f172a)',
              fontSize: '14px',
              outline: 'none',
              transition: 'all 0.2s ease',
            }}
            onFocus={e => e.target.style.borderColor = 'var(--forensic-primary, #2563eb)'}
            onBlur={e => e.target.style.borderColor = 'var(--forensic-border, #cbd5e1)'}
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              style={{
                position: 'absolute', right: '14px', background: 'none', border: 'none',
                color: 'var(--forensic-text-muted, #64748b)', cursor: 'pointer', padding: 0, display: 'flex',
              }}
            >
              <X size={18} />
            </button>
          )}
        </div>
      </div>

      {/* ── CREATE FORM MODAL ── */}
      {showForm && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 100,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: 'rgba(15, 23, 42, 0.7)',
          backdropFilter: 'blur(10px)',
          padding: '16px',
        }}>
          <div
            className="animate-dashboard-modal"
            style={{
              background: 'var(--forensic-card-bg, #ffffff)',
              border: '1px solid var(--forensic-border, #e2e8f0)',
              borderRadius: '24px',
              boxShadow: '0 25px 60px rgba(0, 0, 0, 0.3)',
              padding: '32px',
              width: '100%',
              maxWidth: '480px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '22px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  padding: '10px',
                  borderRadius: '12px',
                  background: 'rgba(99, 102, 241, 0.15)',
                  color: 'var(--forensic-primary, #2563eb)',
                  display: 'flex',
                }}>
                  <Briefcase size={20} />
                </div>
                <div>
                  <h3 style={{ color: 'var(--forensic-text-main, #0f172a)', fontWeight: '800', fontSize: '20px', margin: 0 }}>Create New Case</h3>
                  <p style={{ color: 'var(--forensic-text-muted, #64748b)', fontSize: '12px', margin: '2px 0 0 0' }}>Initialize a court-certified evidence file</p>
                </div>
              </div>
              <button
                onClick={() => setShowForm(false)}
                style={{
                  background: 'rgba(148, 163, 184, 0.15)',
                  border: 'none',
                  borderRadius: '10px',
                  color: 'var(--forensic-text-muted, #64748b)',
                  cursor: 'pointer',
                  padding: '8px',
                  display: 'flex',
                  transition: 'all 0.2s ease',
                }}
              >
                <X size={18} />
              </button>
            </div>
            <CaseForm onSubmit={handleCreate} onCancel={() => setShowForm(false)} loading={creating} />
          </div>
        </div>
      )}

      {error && (
        <div style={{
          position: 'relative', zIndex: 1,
          background: 'rgba(220, 38, 38, 0.12)',
          border: '1px solid rgba(220, 38, 38, 0.4)',
          borderRadius: '14px',
          padding: '14px 20px',
          color: '#dc2626',
          fontSize: '14px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
        }}>
          <AlertCircle size={20} style={{ flexShrink: 0 }} />
          <span>{error}</span>
        </div>
      )}

      {/* ── CASE CARDS GRID ── */}
      <div style={{ position: 'relative', zIndex: 1 }}>
        {loading ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '90px 0', gap: '18px' }}>
            <Spinner size="lg" />
            <span style={{ color: 'var(--forensic-text-muted, #64748b)', fontSize: '14px', fontWeight: '500' }}>Loading forensic cases...</span>
          </div>
        ) : filteredCases.length === 0 ? (
          <div style={{
            background: 'var(--forensic-card-bg, #ffffff)',
            border: '1px dashed var(--forensic-border, #cbd5e1)',
            borderRadius: '20px',
            padding: '56px 24px',
          }}>
            <EmptyState
              icon={FolderOpen}
              title={searchQuery ? "No matching cases found" : "No cases active yet"}
              description={searchQuery ? `No cases match "${searchQuery}". Try a different search term or clear your filters.` : "Create your first forensic case to begin analyzing digital evidence."}
            />
          </div>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
            gap: '20px',
          }}>
            {filteredCases.map((c, index) => (
              <CaseCard key={c.id} c={c} index={index} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default DashboardPage
