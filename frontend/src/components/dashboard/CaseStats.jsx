import { useState, useEffect } from 'react'
import { listEvents } from '../../services/eventService'
import { listEvidence } from '../../services/evidenceService'
import Spinner from '../ui/Spinner'
import { AlertTriangle, Activity, FileText, Layers } from 'lucide-react'

const Stat = ({ icon: Icon, label, value, color }) => (
  <div className="bg-gray-800 border border-gray-700 rounded-xl p-4 flex items-center gap-4">
    <div className={`p-2 rounded-lg ${color}`}>
      <Icon size={18} className="text-white" />
    </div>
    <div>
      <p className="text-gray-400 text-xs">{label}</p>
      <p className="text-white text-xl font-bold">{value}</p>
    </div>
  </div>
)

const CaseStats = ({ caseId }) => {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const [events, evidence] = await Promise.all([
          listEvents(caseId, { limit: 2000 }),
          listEvidence(caseId),
        ])
        const anomalies = events.filter((e) => e.is_anomaly).length
        const critical = events.filter((e) => e.severity === 'critical').length
        setStats({ total: events.length, anomalies, critical, files: evidence.length })
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [caseId])

  if (loading) return <div className="flex justify-center py-6"><Spinner /></div>
  if (!stats) return null

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Stat icon={Activity} label="Total Events" value={stats.total} color="bg-blue-600" />
      <Stat icon={AlertTriangle} label="Anomalies" value={stats.anomalies} color="bg-orange-500" />
      <Stat icon={Layers} label="Critical Events" value={stats.critical} color="bg-red-600" />
      <Stat icon={FileText} label="Evidence Files" value={stats.files} color="bg-emerald-600" />
    </div>
  )
}

export default CaseStats
