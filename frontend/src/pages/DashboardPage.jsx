import { useState, useEffect, useMemo, useRef } from 'react'
import { listCases, createCase } from '../services/caseService'
import useCase from '../hooks/useCase'
import CaseCard from '../components/cases/CaseCard'
import CaseForm from '../components/cases/CaseForm'
import { Spinner, EmptyState } from '../components/ui'
import { CASE_STATUSES } from '../utils/constants'
import { humanize } from '../utils/formatters'
import { Plus, FolderOpen, X, Search, Briefcase, Clock, CheckCircle2, AlertCircle, PauseCircle, Sparkles, Command } from 'lucide-react'

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
      // Ignore keypresses if case creation modal is open
      if (showForm) return

      const activeTag = document.activeElement?.tagName?.toLowerCase()
      const isInputOrTextarea = activeTag === 'input' || activeTag === 'textarea' || document.activeElement?.isContentEditable

      // If user is already focused inside another input element (not our search bar), don't intercept
      if (isInputOrTextarea && document.activeElement !== searchInputRef.current) return

      // Handle Escape key to clear search & blur
      if (e.key === 'Escape') {
        setSearchQuery('')
        searchInputRef.current?.blur()
        return
      }

      // Handle Ctrl+K / Cmd+K or / shortcut to focus search
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

      // If user starts typing printable character (a-z, 0-9, space, etc.) anywhere without modifier keys
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

  // Calculate global status metric stats across ALL cases
  const caseStats = useMemo(() => {
    const total = cases.length
    const open = cases.filter(c => c.status === 'open').length
    const inProgress = cases.filter(c => c.status === 'in_progress').length
    const suspended = cases.filter(c => c.status === 'suspended').length
    const resolved = cases.filter(c => c.status === 'resolved').length
    return { total, open, inProgress, suspended, resolved }
  }, [cases])

  // Live filter cases by selected status and search query
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


  // Clickable Stat Filter Cards configuration (Dark Cybersecurity Theme)
  const filterCards = [
    {
      id: '',
      label: 'All Cases',
      count: caseStats.total,
      icon: Briefcase,
      color: '#818cf8',
      bgLight: 'rgba(99, 102, 241, 0.15)',
      borderActive: '#6366f1',
    },
    {
      id: 'open',
      label: 'Open',
      count: caseStats.open,
      icon: AlertCircle,
      color: '#34d399',
      bgLight: 'rgba(16, 185, 129, 0.15)',
      borderActive: '#10b981',
    },
    {
      id: 'in_progress',
      label: 'In Progress',
      count: caseStats.inProgress,
      icon: Clock,
      color: '#60a5fa',
      bgLight: 'rgba(59, 130, 246, 0.15)',
      borderActive: '#3b82f6',
    },
    {
      id: 'suspended',
      label: 'Suspended',
      count: caseStats.suspended,
      icon: PauseCircle,
      color: '#fbbf24',
      bgLight: 'rgba(245, 158, 11, 0.15)',
      borderActive: '#f59e0b',
    },
    {
      id: 'resolved',
      label: 'Resolved',
      count: caseStats.resolved,
      icon: CheckCircle2,
      color: '#cbd5e1',
      bgLight: 'rgba(148, 163, 184, 0.15)',
      borderActive: '#94a3b8',
    },
  ]

  return (
    <div style={{
      position: 'relative',
      display: 'flex',
      flexDirection: 'column',
      gap: '24px',
      maxWidth: '1200px',
      margin: '0 auto',
      width: '100%',
    }}>
      {/* Background Cyber Forensics Photo Trial */}
      <div className="dark-bg-overlay" style={{
        position: 'fixed',
        inset: 0,
        backgroundImage: 'url("https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?q=80&w=2000&auto=format&fit=crop")',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        opacity: 0.18,
        filter: 'contrast(1.1) brightness(0.65)',
        pointerEvents: 'none',
        zIndex: 0,
      }} />

      {/* Ambient gradient overlay */}
      <div className="dark-bg-overlay" style={{
        position: 'fixed',
        inset: 0,
        background: 'radial-gradient(ellipse at 50% 0%, rgba(99, 102, 241, 0.2) 0%, rgba(15, 23, 42, 0.85) 75%)',
        pointerEvents: 'none',
        zIndex: 0,
      }} />


      {/* Header Bar */}
      <div style={{ position: 'relative', zIndex: 1, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h2 style={{ color: '#ffffff', fontSize: '24px', fontWeight: '800', margin: 0, letterSpacing: '-0.5px' }}>
              {statusFilter ? `${humanize(statusFilter)} Cases` : 'All Cases'}
            </h2>

            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              padding: '3px 10px',
              borderRadius: '12px',
              fontSize: '11px',
              fontWeight: '600',
              background: 'rgba(99, 102, 241, 0.18)',
              color: '#818cf8',
              border: '1px solid rgba(99, 102, 241, 0.35)',
            }}>
              <Sparkles size={12} /> Active Workspace
            </span>
          </div>
        </div>


        {/* New Case CTA Button */}
        <button
          onClick={() => setShowForm(true)}
          style={{
            display: 'flex', alignItems: 'center', gap: '8px',
            padding: '10px 20px',
            background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
            border: 'none',
            borderRadius: '12px',
            color: '#ffffff',
            fontSize: '13.5px',
            fontWeight: '600',
            cursor: 'pointer',
            boxShadow: '0 4px 16px rgba(99, 102, 241, 0.4)',
            transition: 'all 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
            fontFamily: 'inherit',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.transform = 'translateY(-2px)'
            e.currentTarget.style.boxShadow = '0 8px 24px rgba(99, 102, 241, 0.6)'
          }}
          onMouseLeave={e => {
            e.currentTarget.style.transform = 'translateY(0)'
            e.currentTarget.style.boxShadow = '0 4px 16px rgba(99, 102, 241, 0.4)'
          }}
        >
          <Plus size={18} />
          New Case
        </button>
      </div>

      {/* Direct Interactive Clickable Metric Boxes */}
      <div style={{
        position: 'relative', zIndex: 1,
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '14px',
      }}>
        {filterCards.map((card) => {
          const IconComponent = card.icon
          const isSelected = statusFilter === card.id
          return (
            <div
              key={card.id || 'all'}
              onClick={() => setStatusFilter(card.id)}
              style={{
                cursor: 'pointer',
                background: isSelected 
                  ? 'linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(15, 23, 42, 0.95))' 
                  : 'rgba(30, 41, 59, 0.45)',
                backdropFilter: 'blur(16px)',
                WebkitBackdropFilter: 'blur(16px)',
                border: isSelected ? `2px solid ${card.borderActive}` : '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '16px',
                padding: '18px 20px',
                display: 'flex',
                alignItems: 'center',
                gap: '14px',
                position: 'relative',
                boxShadow: isSelected 
                  ? `0 8px 24px -4px ${card.borderActive}40, 0 0 20px ${card.borderActive}20` 
                  : '0 4px 14px rgba(0, 0, 0, 0.3)',
                transform: isSelected ? 'translateY(-3px)' : 'translateY(0)',
                transition: 'all 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
              }}
              onMouseEnter={e => {
                if (!isSelected) {
                  e.currentTarget.style.transform = 'translateY(-4px) scale(1.02)'
                  e.currentTarget.style.borderColor = card.borderActive
                  e.currentTarget.style.boxShadow = `0 8px 22px ${card.borderActive}35`
                  const iconBox = e.currentTarget.querySelector('.stat-icon-box')
                  if (iconBox) {
                    iconBox.style.transform = 'scale(1.08)'
                    iconBox.style.boxShadow = `0 0 14px ${card.borderActive}50`
                  }
                }
              }}
              onMouseLeave={e => {
                if (!isSelected) {
                  e.currentTarget.style.transform = 'translateY(0) scale(1)'
                  e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)'
                  e.currentTarget.style.boxShadow = '0 4px 14px rgba(0, 0, 0, 0.3)'
                  const iconBox = e.currentTarget.querySelector('.stat-icon-box')
                  if (iconBox) {
                    iconBox.style.transform = 'scale(1)'
                    iconBox.style.boxShadow = 'none'
                  }

                }
              }}
            >
              <div
                className="stat-icon-box"
                style={{
                  padding: '10px',
                  borderRadius: '12px',
                  background: card.bgLight,
                  color: card.color,
                  display: 'flex',
                  border: `1px solid ${card.color}30`,
                  transition: 'all 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
                }}
              >
                <IconComponent size={20} />
              </div>
              <div>
                <div style={{
                  color: isSelected ? card.color : '#94a3b8',
                  fontSize: '11.5px',
                  fontWeight: '600',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                  transition: 'color 0.2s ease',
                }}>
                  {card.label}
                </div>
                <div style={{ color: '#ffffff', fontSize: '22px', fontWeight: '800', marginTop: '2px' }}>
                  {card.count}
                </div>
              </div>
            </div>
          )
        })}

      </div>


      {/* Live Search Bar */}
      <div style={{
        position: 'relative', zIndex: 1,
        display: 'flex',
        alignItems: 'center',
        background: 'rgba(15, 23, 42, 0.65)',
        backdropFilter: 'blur(16px)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '16px',
        padding: '12px 18px',
        boxShadow: '0 4px 14px rgba(0, 0, 0, 0.3)',
      }}>
        <div style={{
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
          width: '100%',
        }}>
          <Search size={16} style={{ position: 'absolute', left: '14px', color: '#64748b', pointerEvents: 'none' }} />
          <input
            ref={searchInputRef}
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search cases by title or description..."
            style={{
              width: '100%',
              padding: '9px 80px 9px 40px',
              background: 'rgba(30, 41, 59, 0.6)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '10px',
              color: '#ffffff',
              fontSize: '13px',
              outline: 'none',
              transition: 'all 0.2s ease',
            }}
            onFocus={e => e.target.style.borderColor = '#6366f1'}
            onBlur={e => e.target.style.borderColor = 'rgba(255, 255, 255, 0.1)'}
          />
          {!searchQuery && (
            <div style={{
              position: 'absolute',
              right: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '2px 7px',
              borderRadius: '6px',
              background: 'rgba(255, 255, 255, 0.08)',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              color: '#94a3b8',
              fontSize: '10.5px',
              fontWeight: '600',
              pointerEvents: 'none',
            }}>
              <span>/</span>
            </div>
          )}
          {searchQuery && (

            <button
              onClick={() => setSearchQuery('')}
              style={{
                position: 'absolute', right: '12px', background: 'none', border: 'none',
                color: '#64748b', cursor: 'pointer', padding: 0, display: 'flex',
              }}
            >
              <X size={16} />
            </button>
          )}
        </div>
      </div>

      {/* Create Form Modal */}
      {showForm && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 100,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: 'rgba(3, 7, 18, 0.8)',
          backdropFilter: 'blur(12px)',
          padding: '16px',
        }}>
          <div
            className="animate-dashboard-modal"
            style={{
              background: 'rgba(24, 32, 47, 0.95)',
              border: '1px solid rgba(99, 102, 241, 0.4)',
              borderRadius: '20px',
              boxShadow: '0 25px 60px rgba(0, 0, 0, 0.7), 0 0 30px rgba(99, 102, 241, 0.2)',
              padding: '28px',
              width: '100%',
              maxWidth: '460px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{
                  padding: '8px',
                  borderRadius: '10px',
                  background: 'rgba(99, 102, 241, 0.2)',
                  color: '#818cf8',
                  display: 'flex',
                }}>
                  <Briefcase size={18} />
                </div>
                <h3 style={{ color: '#ffffff', fontWeight: '700', fontSize: '18px', margin: 0 }}>Create New Case</h3>
              </div>
              <button
                onClick={() => setShowForm(false)}
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#94a3b8',
                  cursor: 'pointer',
                  padding: '6px',
                  display: 'flex',
                  transition: 'all 0.2s ease',
                }}
                onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'; e.currentTarget.style.color = '#ffffff' }}
                onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)'; e.currentTarget.style.color = '#94a3b8' }}
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
          background: 'rgba(239, 68, 68, 0.12)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          borderRadius: '12px',
          padding: '14px 18px',
          color: '#fca5a5',
          fontSize: '13.5px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
        }}>
          <AlertCircle size={18} style={{ flexShrink: 0 }} />
          <span>{error}</span>
        </div>
      )}

      {/* Case Cards Grid */}
      <div style={{ position: 'relative', zIndex: 1 }}>
        {loading ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '80px 0', gap: '16px' }}>
            <Spinner size="lg" />
            <span style={{ color: '#94a3b8', fontSize: '13px' }}>Loading cases...</span>
          </div>
        ) : filteredCases.length === 0 ? (
          <div style={{
            background: 'rgba(15, 23, 42, 0.4)',
            backdropFilter: 'blur(12px)',
            border: '1px dashed rgba(255, 255, 255, 0.1)',
            borderRadius: '16px',
            padding: '48px 24px',
          }}>
            <EmptyState
              icon={FolderOpen}
              title={searchQuery ? "No matching cases found" : "No cases yet"}
              description={searchQuery ? `No cases match "${searchQuery}". Try a different term or clear filters.` : "Create your first forensic case to get started."}
            />
          </div>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
            gap: '18px',
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




