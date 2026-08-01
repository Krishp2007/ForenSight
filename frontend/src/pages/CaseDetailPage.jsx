import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getCase, updateCase } from '../services/caseService'
import { listEvidence } from '../services/evidenceService'
import useCase from '../hooks/useCase'
import CaseStatusBadge from '../components/cases/CaseStatusBadge'
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
import Spinner from '../components/ui/Spinner'
import { ArrowLeft, Pencil, X } from 'lucide-react'
import { formatDateShort } from '../utils/formatters'

const TABS = ['evidence', 'timeline', 'graph', 'correlations', 'chat', 'report', 'audit']

const CaseDetailPage = () => {
  const { caseId, tab } = useParams()
  const navigate = useNavigate()
  const { setActiveCase, updateCaseInList } = useCase()

  const [caseData, setCaseData] = useState(null)
  const [evidence, setEvidence] = useState([])
  const [loading, setLoading] = useState(true)
  const [editMode, setEditMode] = useState(false)
  const [updating, setUpdating] = useState(false)

  const activeTab = tab || 'evidence'

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

  const goTab = (t) => navigate(`/cases/${caseId}/${t}`)

  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: '96px 0' }}>
      <Spinner size="lg" />
    </div>
  )
  if (!caseData) return (
    <p style={{ color: '#9aa8c0', textAlign: 'center', padding: '96px 0' }}>Case not found.</p>
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Back + Case header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px' }}>
        <button
          onClick={() => navigate('/dashboard')}
          style={{
            marginTop: '4px',
            background: 'none', border: 'none',
            color: '#9aa8c0', cursor: 'pointer', padding: 0,
            transition: 'color 0.2s',
          }}
          onMouseEnter={e => e.currentTarget.style.color = '#ffffff'}
          onMouseLeave={e => e.currentTarget.style.color = '#9aa8c0'}
        >
          <ArrowLeft size={18} />
        </button>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <h2 style={{ color: '#ffffff', fontSize: '20px', fontWeight: '700', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {caseData.title}
            </h2>
            <CaseStatusBadge status={caseData.status} />
            <button
              onClick={() => setEditMode(true)}
              style={{
                marginLeft: 'auto', background: 'none', border: 'none',
                color: '#6b7fa3', cursor: 'pointer', padding: 0,
                transition: 'color 0.2s',
              }}
              onMouseEnter={e => e.currentTarget.style.color = '#ffffff'}
              onMouseLeave={e => e.currentTarget.style.color = '#6b7fa3'}
              title="Edit case"
            >
              <Pencil size={15} />
            </button>
          </div>
          {caseData.description && (
            <p style={{ color: '#9aa8c0', fontSize: '13px', margin: '6px 0 0 0' }}>{caseData.description}</p>
          )}
          <p style={{ color: '#6b7fa3', fontSize: '11px', margin: '4px 0 0 0' }}>
            Created {formatDateShort(caseData.created_at)}
          </p>
        </div>
      </div>

      {/* Stats summary */}
      <CaseStats caseId={caseId} />

      {/* Edit modal */}
      {editMode && (
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
              <h3 style={{ color: '#ffffff', fontWeight: '600', fontSize: '16px', margin: 0 }}>Edit Case</h3>
              <button
                onClick={() => setEditMode(false)}
                style={{ background: 'none', border: 'none', color: '#9aa8c0', cursor: 'pointer', padding: 0 }}
              >
                <X size={18} />
              </button>
            </div>
            <CaseForm initial={caseData} onSubmit={handleUpdate} onCancel={() => setEditMode(false)} loading={updating} />
          </div>
        </div>
      )}

      {/* Tabs */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid #3d4f6a',
        gap: '2px',
      }}>
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => goTab(t)}
            style={{
              padding: '8px 16px',
              fontSize: '13px',
              fontWeight: '500',
              textTransform: 'capitalize',
              background: activeTab === t ? '#323d52' : 'transparent',
              border: 'none',
              borderBottom: activeTab === t ? '2px solid #4a7fe8' : '2px solid transparent',
              color: activeTab === t ? '#ffffff' : '#9aa8c0',
              cursor: 'pointer',
              transition: 'color 0.15s, background 0.15s',
              borderRadius: '6px 6px 0 0',
              fontFamily: 'inherit',
            }}
            onMouseEnter={e => { if (activeTab !== t) e.currentTarget.style.color = '#ffffff' }}
            onMouseLeave={e => { if (activeTab !== t) e.currentTarget.style.color = '#9aa8c0' }}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Tab panels */}
      <div style={{ minHeight: '400px' }}>
        {activeTab === 'evidence' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <EvidenceUpload caseId={caseId} onUploaded={handleEvidenceUploaded} />
            <EvidenceList items={evidence} caseId={caseId} onItemUpdated={handleEvidenceUpdated} />
          </div>
        )}
        {activeTab === 'timeline'     && <EventTimeline caseId={caseId} />}
        {activeTab === 'graph'        && <GraphView caseId={caseId} />}
        {activeTab === 'correlations' && <CorrelationsPanel caseId={caseId} />}
        {activeTab === 'chat'         && <ChatPanel caseId={caseId} />}
        {activeTab === 'report'       && <ReportPanel caseId={caseId} />}
        {activeTab === 'audit'        && <AuditTrail caseId={caseId} />}
      </div>
    </div>
  )
}

export default CaseDetailPage
