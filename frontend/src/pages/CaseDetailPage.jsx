import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getCase, updateCase } from '../services/caseService'
import { listEvidence } from '../services/evidenceService'
import useCaseStore from '../store/caseStore'
import { useRole } from '../store/authStore'
import { statusColor, humanize, formatDateShort } from '../utils/formatters'
import CaseForm from '../components/cases/CaseForm'
import CaseStats from '../components/dashboard/CaseStats'
import EvidenceUpload from '../components/evidence/EvidenceUpload'
import EvidenceList from '../components/evidence/EvidenceList'
import EventTimeline from '../components/timeline/EventTimeline'
import GraphView from '../components/graph/GraphView'
import CorrelationsPanel from '../components/graph/CorrelationsPanel'
import ChatPanel from '../components/chat/ChatPanel'
import ReportPanel from '../components/reports/ReportPanel'
import AuditTrail from '../components/timeline/AuditTrail'
import { Spinner } from '../components/ui'
import {
  Pencil, X,
  LayoutDashboard, FileCheck, FileText, ShieldCheck,
  Briefcase, ArrowRight, Link,
  Clock, Share2, MessageSquare
} from 'lucide-react'

// Theme-aware status badge
const CaseStatusBadge = ({ status }) => {
  const s = statusColor(status)
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '5px',
      padding: '4px 12px', borderRadius: '99px',
      fontSize: '11px', fontWeight: '700', textTransform: 'uppercase',
      letterSpacing: '0.5px', background: s.background, color: s.color,
      whiteSpace: 'nowrap', border: `1px solid ${s.color}40`,
    }}>
      <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: s.color }} />
      {humanize(status)}
    </span>
  )
}

// Top head tab bar configuration
const TAB_CONFIG = [
  { id: 'dashboard',    label: 'Dashboard',    icon: LayoutDashboard },
  { id: 'correlations', label: 'Correlations', icon: Link },
  { id: 'report',       label: 'Report',       icon: FileText },
  { id: 'audit',        label: 'Audit Log',    icon: ShieldCheck },
]

const CaseDetailPage = () => {
  const { caseId, tab } = useParams()
  const navigate = useNavigate()
  const { setActiveCase, updateCaseInList } = useCaseStore()
  const { canEdit } = useRole()

  const [caseData, setCaseData] = useState(null)
  const [evidence, setEvidence] = useState([])
  const [loading, setLoading] = useState(true)
  const [editMode, setEditMode] = useState(false)
  const [updating, setUpdating] = useState(false)

  const activeTab = tab || 'dashboard'

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const [c, ev] = await Promise.all([getCase(caseId), listEvidence(caseId)])
        setCaseData(c)
        setActiveCase(c)
        setEvidence(ev)
      } finally {
        setLoading(false)
      }
    }
    load()
    return () => setActiveCase(null)
  }, [caseId])

  const handleUpdate = async (payload) => {
    setUpdating(true)
    try {
      const updated = await updateCase(caseId, payload)
      setCaseData(updated)
      updateCaseInList(updated)
      setEditMode(false)
    } finally {
      setUpdating(false)
    }
  }

  const handleEvidenceUploaded = (ev) => setEvidence((prev) => [ev, ...prev])
  const handleEvidenceUpdated = (updated) => {
    const uId = updated.id || updated._id
    setEvidence((prev) => prev.map((e) => ((e.id || e._id) === uId ? updated : e)))
  }
  const handleEvidenceDeleted = (deletedId) => {
    setEvidence((prev) => prev.filter((e) => (e.id || e._id) !== deletedId))
  }

  const goTab = (t) => navigate(`/cases/${caseId}/${t}`)

  if (loading) return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '96px 0', gap: '16px' }}>
      <Spinner size="lg" />
      <span style={{ color: 'var(--forensic-text-muted, #64748b)', fontSize: '13.5px', fontWeight: '500' }}>Loading case investigation details...</span>
    </div>
  )
  if (!caseData) return (
    <p style={{ color: 'var(--forensic-text-muted, #64748b)', textAlign: 'center', padding: '96px 0' }}>Case not found.</p>
  )

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '20px',
      maxWidth: '1280px',
      margin: '0 auto',
      width: '100%',
    }}>
      {/* Back button & Case Header */}
      <div style={{
        background: 'var(--forensic-card-bg, #ffffff)',
        border: '1px solid var(--forensic-border, #e2e8f0)',
        borderRadius: '20px',
        padding: '20px 24px',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '16px',
        boxShadow: '0 2px 10px rgba(0, 0, 0, 0.04)',
      }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <h2 style={{ color: 'var(--forensic-text-main, #0f172a)', fontSize: '24px', fontWeight: '800', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', letterSpacing: '-0.5px' }}>
              {caseData.title}
            </h2>
            <CaseStatusBadge status={caseData.status} />

            {canEdit && (
              <button
                onClick={() => setEditMode(true)}
                style={{
                  marginLeft: 'auto',
                  padding: '7px 14px',
                  background: 'var(--forensic-panel-bg, #f8fafc)',
                  border: '1px solid var(--forensic-border, #cbd5e1)',
                  borderRadius: '10px',
                  color: 'var(--forensic-text-main, #0f172a)',
                  cursor: 'pointer',
                  fontSize: '12.5px',
                  fontWeight: '600',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  transition: 'all 0.2s ease',
                  fontFamily: 'inherit',
                }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--forensic-primary, #2563eb)' }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--forensic-border, #cbd5e1)' }}
                title="Edit Case Details"
              >
                <Pencil size={13} /> Edit
              </button>
            )}
          </div>

          {caseData.description && (
            <p style={{ color: 'var(--forensic-text-muted, #475569)', fontSize: '13.5px', margin: '8px 0 0 0', lineHeight: '1.5' }}>{caseData.description}</p>
          )}

          <p style={{ color: 'var(--forensic-text-muted, #64748b)', fontSize: '12px', margin: '6px 0 0 0' }}>
            Created {formatDateShort(caseData.created_at)}
          </p>
        </div>
      </div>

      {/* Edit Modal */}
      {editMode && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 100,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: 'rgba(15, 23, 42, 0.7)',
          backdropFilter: 'blur(10px)',
          padding: '16px',
        }}>
          <div style={{
            background: 'var(--forensic-card-bg, #ffffff)',
            border: '1px solid var(--forensic-border, #e2e8f0)',
            borderRadius: '24px',
            boxShadow: '0 25px 60px rgba(0, 0, 0, 0.25)',
            padding: '28px',
            width: '100%',
            maxWidth: '460px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
              <h3 style={{ color: 'var(--forensic-text-main, #0f172a)', fontWeight: '800', fontSize: '18px', margin: 0 }}>Edit Case</h3>
              <button
                onClick={() => setEditMode(false)}
                style={{ background: 'none', border: 'none', color: 'var(--forensic-text-muted, #64748b)', cursor: 'pointer', padding: 0 }}
              >
                <X size={18} />
              </button>
            </div>
            <CaseForm initial={caseData} onSubmit={handleUpdate} onCancel={() => setEditMode(false)} loading={updating} />
          </div>
        </div>
      )}

      {/* Top Head Tab Bar */}
      <div className="touch-horizontal-scroll" style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        padding: '6px',
        background: 'var(--forensic-card-bg, #ffffff)',
        border: '1px solid var(--forensic-border, #e2e8f0)',
        borderRadius: '16px',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)',
      }}>
        {TAB_CONFIG.map((t) => {
          const IconComp = t.icon
          const isActive = activeTab === t.id
          return (
            <button
              key={t.id}
              onClick={() => goTab(t.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '9px 18px',
                fontSize: '13px',
                fontWeight: isActive ? '700' : '600',
                background: isActive ? 'var(--forensic-primary, #2563eb)' : 'transparent',
                border: 'none',
                borderRadius: '12px',
                color: isActive ? '#ffffff' : 'var(--forensic-text-muted, #64748b)',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                boxShadow: isActive ? '0 4px 14px rgba(37, 99, 235, 0.35)' : 'none',
                transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
                fontFamily: 'inherit',
              }}
              onMouseEnter={e => {
                if (!isActive) {
                  e.currentTarget.style.color = 'var(--forensic-text-main, #0f172a)'
                  e.currentTarget.style.background = 'var(--forensic-panel-bg, #f1f5f9)'
                  e.currentTarget.style.transform = 'translateY(-1px)'
                }
              }}
              onMouseLeave={e => {
                if (!isActive) {
                  e.currentTarget.style.color = 'var(--forensic-text-muted, #64748b)'
                  e.currentTarget.style.background = 'transparent'
                  e.currentTarget.style.transform = 'translateY(0)'
                }
              }}
            >
              <IconComp size={15} style={{ color: isActive ? '#ffffff' : 'var(--forensic-primary, #2563eb)' }} />
              {t.label}
            </button>

          )
        })}
      </div>

      {/* Tab Panel Content Area */}
      <div style={{ minHeight: '450px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {/* 1. DASHBOARD TAB */}
        {activeTab === 'dashboard' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Event & Evidence Statistics */}
            <CaseStats caseId={caseId} evidenceList={evidence} />

            {/* Case Overview Highlights & Interactive Shortcut Cards */}
            <div style={{
              background: 'var(--forensic-card-bg, #ffffff)',
              border: '1px solid var(--forensic-border, #e2e8f0)',
              borderRadius: '20px',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '18px',
              boxShadow: '0 2px 10px rgba(0, 0, 0, 0.04)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ padding: '8px', borderRadius: '10px', background: 'rgba(99, 102, 241, 0.15)', color: 'var(--forensic-primary, #2563eb)', display: 'flex' }}>
                    <Briefcase size={18} />
                  </div>
                  <h3 style={{ color: 'var(--forensic-text-main, #0f172a)', fontSize: '16px', fontWeight: '700', margin: 0 }}>Case Overview</h3>
                </div>
                <span style={{ color: 'var(--forensic-text-muted, #64748b)', fontSize: '12.5px', fontWeight: '600' }}>{evidence.length} Evidence File{evidence.length !== 1 ? 's' : ''}</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
                <div
                  onClick={() => goTab('evidence')}
                  style={{
                    cursor: 'pointer', padding: '16px', borderRadius: '14px',
                    background: 'var(--forensic-panel-bg, #f8fafc)', border: '1px solid var(--forensic-border, #e2e8f0)',
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    transition: 'all 0.2s ease',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--forensic-primary, #2563eb)'; e.currentTarget.style.transform = 'translateY(-2px)' }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--forensic-border, #e2e8f0)'; e.currentTarget.style.transform = 'translateY(0)' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <FileCheck size={18} style={{ color: 'var(--forensic-primary, #2563eb)' }} />
                    <span style={{ color: 'var(--forensic-text-main, #0f172a)', fontSize: '13px', fontWeight: '600' }}>Manage Evidence</span>
                  </div>
                  <ArrowRight size={14} style={{ color: 'var(--forensic-primary, #2563eb)' }} />
                </div>

                <div
                  onClick={() => goTab('timeline')}
                  style={{
                    cursor: 'pointer', padding: '16px', borderRadius: '14px',
                    background: 'var(--forensic-panel-bg, #f8fafc)', border: '1px solid var(--forensic-border, #e2e8f0)',
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    transition: 'all 0.2s ease',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = '#2563eb'; e.currentTarget.style.transform = 'translateY(-2px)' }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--forensic-border, #e2e8f0)'; e.currentTarget.style.transform = 'translateY(0)' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <Clock size={18} style={{ color: '#2563eb' }} />
                    <span style={{ color: 'var(--forensic-text-main, #0f172a)', fontSize: '13px', fontWeight: '600' }}>View Timeline</span>
                  </div>
                  <ArrowRight size={14} style={{ color: '#2563eb' }} />
                </div>

                <div
                  onClick={() => goTab('graph')}
                  style={{
                    cursor: 'pointer', padding: '16px', borderRadius: '14px',
                    background: 'var(--forensic-panel-bg, #f8fafc)', border: '1px solid var(--forensic-border, #e2e8f0)',
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    transition: 'all 0.2s ease',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = '#059669'; e.currentTarget.style.transform = 'translateY(-2px)' }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--forensic-border, #e2e8f0)'; e.currentTarget.style.transform = 'translateY(0)' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <Share2 size={18} style={{ color: '#059669' }} />
                    <span style={{ color: 'var(--forensic-text-main, #0f172a)', fontSize: '13px', fontWeight: '600' }}>Knowledge Graph</span>
                  </div>
                  <ArrowRight size={14} style={{ color: '#059669' }} />
                </div>

                <div
                  onClick={() => goTab('chat')}
                  style={{
                    cursor: 'pointer', padding: '16px', borderRadius: '14px',
                    background: 'var(--forensic-panel-bg, #f8fafc)', border: '1px solid var(--forensic-border, #e2e8f0)',
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    transition: 'all 0.2s ease',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = '#d97706'; e.currentTarget.style.transform = 'translateY(-2px)' }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--forensic-border, #e2e8f0)'; e.currentTarget.style.transform = 'translateY(0)' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <MessageSquare size={18} style={{ color: '#d97706' }} />
                    <span style={{ color: 'var(--forensic-text-main, #0f172a)', fontSize: '13px', fontWeight: '600' }}>Ask AI Assistant</span>
                  </div>
                  <ArrowRight size={14} style={{ color: '#d97706' }} />
                </div>
              </div>
            </div>

            {/* Evidence Summary */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <h3 style={{ color: 'var(--forensic-text-main, #0f172a)', fontSize: '16px', fontWeight: '700', margin: 0 }}>Evidence Summary</h3>
              <EvidenceList items={evidence} caseId={caseId} isDashboard={true} onItemUpdated={handleEvidenceUpdated} onItemDeleted={handleEvidenceDeleted} />
            </div>
          </div>
        )}

        {/* OTHER TABS */}
        {activeTab === 'evidence' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <EvidenceUpload caseId={caseId} onUploaded={handleEvidenceUploaded} />
            <EvidenceList items={evidence} caseId={caseId} isDashboard={false} onItemUpdated={handleEvidenceUpdated} onItemDeleted={handleEvidenceDeleted} />
          </div>
        )}
        {activeTab === 'timeline'     && <EventTimeline caseId={caseId} />}
        {activeTab === 'graph'        && <GraphView caseId={caseId} evidence={evidence} />}
        {activeTab === 'correlations' && <CorrelationsPanel caseId={caseId} evidenceCount={evidence.length} />}
        {activeTab === 'chat'         && <ChatPanel caseId={caseId} />}
        {activeTab === 'report'       && <ReportPanel caseId={caseId} evidenceCount={evidence.length} />}
        {activeTab === 'audit'        && <AuditTrail caseId={caseId} />}
      </div>
    </div>
  )
}

export default CaseDetailPage
