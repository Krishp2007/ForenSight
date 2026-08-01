import { useState, useEffect } from 'react'
import { listEvents } from '../../services/eventService'
import { listEvidence } from '../../services/evidenceService'
import Spinner from '../ui/Spinner'
import { AlertTriangle, Activity, FileText, Layers } from 'lucide-react'

const Stat = ({ icon: Icon, label, value, iconBg }) => (
  <div style={{
    background: '#2d3748',
    border: '1px solid #3d4f6a',
    borderRadius: '12px',
    padding: '16px',
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  }}>
    <div style={{
      width: '40px', height: '40px',
      borderRadius: '10px',
      background: iconBg,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      flexShrink: 0,
    }}>
      <Icon size={18} color="#ffffff" />
    </div>
    <div>
      <p style={{ color: '#9aa8c0', fontSize: '11px', margin: '0 0 4px 0', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        {label}
      </p>
      <p style={{ color: '#ffffff', fontSize: '22px', fontWeight: '700', margin: 0, lineHeight: 1 }}>
        {value}
      </p>
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

  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: '24px 0' }}>
      <Spinner />
    </div>
  )
  if (!stats) return null

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
      gap: '16px',
    }}>
      <Stat icon={Activity}      label="Total Events"   value={stats.total}     iconBg="#2563eb" />
      <Stat icon={AlertTriangle} label="Anomalies"      value={stats.anomalies} iconBg="#f97316" />
      <Stat icon={Layers}        label="Critical Events" value={stats.critical}  iconBg="#ef4444" />
      <Stat icon={FileText}      label="Evidence Files" value={stats.files}     iconBg="#10b981" />
    </div>
  )
}

export default CaseStats
