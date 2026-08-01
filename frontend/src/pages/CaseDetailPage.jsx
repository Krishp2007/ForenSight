import { useState, useEffect } from 'react'
import { useParams, useLocation, useNavigate } from 'react-router-dom'
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

  if (loading) return <div className="flex justify-center py-24"><Spinner size="lg" /></div>
  if (!caseData) return <p className="text-gray-400 text-center py-24">Case not found.</p>

  return (
    <div className="flex flex-col gap-5 max-w-6xl mx-auto">
      {/* Back + Case header */}
      <div className="flex items-start gap-4">
        <button
          onClick={() => navigate('/dashboard')}
          className="mt-1 text-gray-400 hover:text-white transition-colors"
        >
          <ArrowLeft size={18} />
        </button>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 flex-wrap">
            <h2 className="text-white text-xl font-bold truncate">{caseData.title}</h2>
            <CaseStatusBadge status={caseData.status} />
            <button
              onClick={() => setEditMode(true)}
              className="text-gray-500 hover:text-white ml-auto"
              title="Edit case"
            >
              <Pencil size={15} />
            </button>
          </div>
          {caseData.description && (
            <p className="text-gray-400 text-sm mt-1">{caseData.description}</p>
          )}
          <p className="text-gray-600 text-xs mt-1">Created {formatDateShort(caseData.created_at)}</p>
        </div>
      </div>

      {/* Stats summary */}
      <CaseStats caseId={caseId} />

      {/* Edit modal */}
      {editMode && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
          <div className="bg-gray-800 rounded-2xl shadow-2xl p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-white font-semibold">Edit Case</h3>
              <button onClick={() => setEditMode(false)} className="text-gray-400 hover:text-white">
                <X size={18} />
              </button>
            </div>
            <CaseForm initial={caseData} onSubmit={handleUpdate} onCancel={() => setEditMode(false)} loading={updating} />
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-gray-700 gap-1">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => goTab(t)}
            className={`px-4 py-2 text-sm font-medium capitalize rounded-t-lg transition-colors
              ${activeTab === t
                ? 'text-white border-b-2 border-blue-500 bg-gray-800'
                : 'text-gray-400 hover:text-white'}`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Tab panels */}
      <div className="min-h-[400px]">
        {activeTab === 'evidence' && (
          <div className="flex flex-col gap-5">
            <EvidenceUpload caseId={caseId} onUploaded={handleEvidenceUploaded} />
            <EvidenceList items={evidence} onItemUpdated={handleEvidenceUpdated} />
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
