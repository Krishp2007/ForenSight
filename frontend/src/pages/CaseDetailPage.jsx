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
  LayoutDashboard, FileCheck, Clock, Share2,
  MessageSquare, FileText, ShieldCheck, Briefcase, ArrowRight
} from 'lucide-react'

// Dark cyber status badge
const CaseStatusBadge = ({ status }) => {
  const s = statusColor(status)
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '5px',
      padding: '3px 10px', borderRadius: '99px',
      fontSize: '11px', fontWeight: '600', textTransform: 'uppercase',
      letterSpacing: '0.6px', background: s.background, color: s.color,
      whiteSpace: 'nowrap', border: `1px solid ${s.color}40`,
      boxShadow: `0 0 10px ${s.background}`,
    }}>
      <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: s.color }} />
      {humanize(status)}
    </span>
  )
}

// Top head tab bar configuration — includes Dashboard, Report, and Audit Log
const TAB_CONFIG = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'report',    label: 'Report',    icon: FileText },
  { id: 'audit',     label: 'Audit Log', icon: ShieldCheck },
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
  const handleEvidenceUpdated = (updated) =>
    setEvidence((prev) => prev.map((e) => (e.id === updated.id ? updated : e)))
  const handleEvidenceDeleted = (deletedId) =>
    setEvidence((prev) => prev.filter((e) => e.id !== deletedId))

  const goTab = (t) => navigate(`/cases/${caseId}/${t}`)

  if (loading) return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '96px 0', gap: '16px' }}>
      <Spinner size="lg" />
      <span style={{ color: '#94a3b8', fontSize: '13px' }}>Loading case details...</span>
    </div>
  )
  if (!caseData) return (
    <p style={{ color: '#94a3b8', textAlign: 'center', padding: '96px 0' }}>Case not found.</p>
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
        background: 'rgba(30, 41, 59, 0.55)',
        backdropFilter: 'blur(16px)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '20px',
        padding: '20px 24px',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '16px',
        boxShadow: '0 4px 14px rgba(0, 0, 0, 0.25)',
      }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <h2 style={{ color: '#ffffff', fontSize: '22px', fontWeight: '800', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {caseData.title}
            </h2>
            <CaseStatusBadge status={caseData.status} />

            {canEdit && (
              <button
                onClick={() => setEditMode(true)}
                style={{
                  marginLeft: 'auto',
                  padding: '6px 12px',
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '8px',
                  color: '#94a3b8',
                  cursor: 'pointer',
                  fontSize: '12px',
                  fontWeight: '500',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  transition: 'all 0.2s ease',
                }}
                onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'; e.currentTarget.style.color = '#ffffff' }}
                onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)'; e.currentTarget.style.color = '#94a3b8' }}
                title="Edit Case Details"
              >
                <Pencil size={13} /> Edit
              </button>
            )}
          </div>

          {caseData.description && (
            <p style={{ color: '#cbd5e1', fontSize: '13px', margin: '6px 0 0 0', lineHeight: '1.5' }}>{caseData.description}</p>
          )}

          <p style={{ color: '#64748b', fontSize: '11.5px', margin: '6px 0 0 0' }}>
            Created {formatDateShort(caseData.created_at)}
          </p>
        </div>
      </div>

      {/* Edit Modal */}
      {editMode && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 100,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: 'rgba(3, 7, 18, 0.8)',
          backdropFilter: 'blur(12px)',
          padding: '16px',
        }}>
          <div style={{
            background: 'rgba(24, 32, 47, 0.95)',
            border: '1px solid rgba(99, 102, 241, 0.4)',
            borderRadius: '20px',
            boxShadow: '0 25px 60px rgba(0, 0, 0, 0.7), 0 0 30px rgba(99, 102, 241, 0.2)',
            padding: '28px',
            width: '100%',
            maxWidth: '460px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
              <h3 style={{ color: '#ffffff', fontWeight: '700', fontSize: '18px', margin: 0 }}>Edit Case</h3>
              <button
                onClick={() => setEditMode(false)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: 0 }}
              >
                <X size={18} />
              </button>
            </div>
            <CaseForm initial={caseData} onSubmit={handleUpdate} onCancel={() => setEditMode(false)} loading={updating} />
          </div>
        </div>
      )}

      {/* Top Head Tab Bar — contains remaining tabs */}
      <div className="touch-horizontal-scroll" style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        padding: '6px',
        background: 'rgba(15, 23, 42, 0.65)',
        backdropFilter: 'blur(16px)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '16px',
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
                fontSize: '12.5px',
                fontWeight: isActive ? '600' : '500',
                background: isActive ? 'linear-gradient(135deg, #6366f1, #4f46e5)' : 'transparent',
                border: 'none',
                borderRadius: '12px',
                color: isActive ? '#ffffff' : '#94a3b8',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                boxShadow: isActive ? '0 4px 14px rgba(99, 102, 241, 0.35)' : 'none',
                transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
                fontFamily: 'inherit',
              }}
              onMouseEnter={e => {
                if (!isActive) {
                  e.currentTarget.style.color = '#ffffff'
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)'
                  e.currentTarget.style.transform = 'translateY(-1px)'
                }
              }}
              onMouseLeave={e => {
                if (!isActive) {
                  e.currentTarget.style.color = '#94a3b8'
                  e.currentTarget.style.background = 'transparent'
                  e.currentTarget.style.transform = 'translateY(0)'
                }
              }}
            >
              <IconComp size={15} style={{ color: isActive ? '#ffffff' : '#818cf8' }} />
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
            <CaseStats caseId={caseId} initialEvidenceCount={evidence.length} />


            {/* Case Overview Highlights & Interactive Shortcut Cards */}
            <div style={{
              background: 'rgba(30, 41, 59, 0.55)',
              backdropFilter: 'blur(16px)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '20px',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '18px',
              boxShadow: '0 4px 14px rgba(0, 0, 0, 0.25)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ padding: '8px', borderRadius: '10px', background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8', display: 'flex' }}>
                    <Briefcase size={18} />
                  </div>
                  <h3 style={{ color: '#ffffff', fontSize: '16px', fontWeight: '700', margin: 0 }}>Case Overview</h3>
                </div>
                <span style={{ color: '#94a3b8', fontSize: '12px' }}>{evidence.length} Evidence File{evidence.length !== 1 ? 's' : ''}</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
                <div
                  onClick={() => goTab('evidence')}
                  style={{
                    cursor: 'pointer',
                    padding: '16px',
                    borderRadius: '14px',
                    background: 'rgba(15, 23, 42, 0.5)',
                    border: '1px solid rgba(255, 255, 255, 0.06)',
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    transition: 'all 0.2s ease',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = '#6366f1'; e.currentTarget.style.transform = 'translateY(-2px)' }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = 'rgba(255,255,255,0.06)'; e.currentTarget.style.transform = 'translateY(0)' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <FileCheck size={18} style={{ color: '#818cf8' }} />
                    <span style={{ color: '#ffffff', fontSize: '13px', fontWeight: '600' }}>Manage Evidence</span>
                  </div>
                  <ArrowRight size={14} style={{ color: '#818cf8' }} />
                </div>

                <div
                  onClick={() => goTab('timeline')}
                  style={{
                    cursor: 'pointer',
                    padding: '16px',
                    borderRadius: '14px',
                    background: 'rgba(15, 23, 42, 0.5)',
                    border: '1px solid rgba(255, 255, 255, 0.06)',
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    transition: 'all 0.2s ease',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = '#3b82f6'; e.currentTarget.style.transform = 'translateY(-2px)' }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = 'rgba(255,255,255,0.06)'; e.currentTarget.style.transform = 'translateY(0)' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <Clock size={18} style={{ color: '#60a5fa' }} />
                    <span style={{ color: '#ffffff', fontSize: '13px', fontWeight: '600' }}>View Timeline</span>
                  </div>
                  <ArrowRight size={14} style={{ color: '#60a5fa' }} />
                </div>

                <div
                  onClick={() => goTab('graph')}
                  style={{
                    cursor: 'pointer',
                    padding: '16px',
                    borderRadius: '14px',
                    background: 'rgba(15, 23, 42, 0.5)',
                    border: '1px solid rgba(255, 255, 255, 0.06)',
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    transition: 'all 0.2s ease',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = '#10b981'; e.currentTarget.style.transform = 'translateY(-2px)' }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = 'rgba(255,255,255,0.06)'; e.currentTarget.style.transform = 'translateY(0)' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <Share2 size={18} style={{ color: '#34d399' }} />
                    <span style={{ color: '#ffffff', fontSize: '13px', fontWeight: '600' }}>Knowledge Graph</span>
                  </div>
                  <ArrowRight size={14} style={{ color: '#34d399' }} />
                </div>

                <div
                  onClick={() => goTab('chat')}
                  style={{
                    cursor: 'pointer',
                    padding: '16px',
                    borderRadius: '14px',
                    background: 'rgba(15, 23, 42, 0.5)',
                    border: '1px solid rgba(255, 255, 255, 0.06)',
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    transition: 'all 0.2s ease',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = '#f59e0b'; e.currentTarget.style.transform = 'translateY(-2px)' }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = 'rgba(255,255,255,0.06)'; e.currentTarget.style.transform = 'translateY(0)' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <MessageSquare size={18} style={{ color: '#fbbf24' }} />
                    <span style={{ color: '#ffffff', fontSize: '13px', fontWeight: '600' }}>Ask AI Assistant</span>
                  </div>
                  <ArrowRight size={14} style={{ color: '#fbbf24' }} />
                </div>
              </div>
            </div>

            {/* Evidence Summary */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <h3 style={{ color: '#ffffff', fontSize: '15px', fontWeight: '700', margin: 0 }}>Evidence Summary</h3>
              <EvidenceList items={evidence} caseId={caseId} onItemUpdated={handleEvidenceUpdated} onItemDeleted={handleEvidenceDeleted} />
            </div>
          </div>
        )}

        {/* OTHER TABS */}
        {activeTab === 'evidence' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <EvidenceUpload caseId={caseId} onUploaded={handleEvidenceUploaded} />
            <EvidenceList items={evidence} caseId={caseId} onItemUpdated={handleEvidenceUpdated} onItemDeleted={handleEvidenceDeleted} />
          </div>
        )}
        {activeTab === 'timeline'     && <EventTimeline caseId={caseId} />}
        {activeTab === 'graph'        && <GraphView caseId={caseId} evidence={evidence} />}
        {activeTab === 'correlations' && <CorrelationsPanel caseId={caseId} />}
        {activeTab === 'chat'         && <ChatPanel caseId={caseId} />}
        {activeTab === 'report'       && <ReportPanel caseId={caseId} />}
        {activeTab === 'audit'        && <AuditTrail caseId={caseId} />}
      </div>
    </div>
  )
}

export default CaseDetailPage
