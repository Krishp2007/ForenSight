import { useState, useEffect } from 'react'
import api from '../../services/api'
import { listEvidence } from '../../services/evidenceService'
import { AlertTriangle, Activity, FileText, Layers } from 'lucide-react'

// Inlined from deleted eventService
const listEvents = (caseId, opts = {}) => {
  const params = { limit: opts.limit || 2000 }
  if (opts.severity)   params.severity   = opts.severity
  if (opts.event_type) params.event_type = opts.event_type
  return api.get(`/cases/${caseId}/events`, { params }).then(r => r.data)
}

const Stat = ({ icon: Icon, label, value, iconBg, loading }) => (
  <div style={{
    background: 'rgba(30, 41, 59, 0.55)',
    backdropFilter: 'blur(16px)',
    WebkitBackdropFilter: 'blur(16px)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '16px',
    padding: '18px 20px',
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    boxShadow: '0 4px 14px rgba(0, 0, 0, 0.25)',
    transition: 'all 0.2s ease',
  }}>
    <div style={{
      width: '42px', height: '42px',
      borderRadius: '12px',
      background: iconBg + '22',
      border: `1px solid ${iconBg}44`,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      flexShrink: 0,
      color: iconBg,
    }}>
      <Icon size={20} />
    </div>
    <div style={{ flex: 1 }}>
      <p style={{ color: '#94a3b8', fontSize: '11px', fontWeight: '600', margin: '0 0 4px 0', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        {label}
      </p>
      {loading ? (
        <div style={{
          width: '52px', height: '22px', borderRadius: '6px',
          background: 'rgba(255, 255, 255, 0.08)',
          animation: 'pulse 1.5s infinite ease-in-out',
        }} />
      ) : (
        <p style={{ color: '#ffffff', fontSize: '22px', fontWeight: '800', margin: 0, lineHeight: 1 }}>
          {value ?? 0}
        </p>
      )}
    </div>
  </div>
)

const CaseStats = ({ caseId, evidenceList, initialEvidenceCount }) => {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  const effectiveCount = Array.isArray(evidenceList) 
    ? evidenceList.length 
    : (initialEvidenceCount !== undefined ? initialEvidenceCount : null)

  const parsedCount = Array.isArray(evidenceList)
    ? evidenceList.filter(e => e.status === 'parsed').length
    : 0

  useEffect(() => {
    let isMounted = true
    const load = async () => {
      setLoading(true)
      try {
        let fileCount = effectiveCount
        if (fileCount === null) {
          const evs = await listEvidence(caseId)
          fileCount = evs.length
        }

        if (fileCount === 0) {
          if (isMounted) {
            setStats({ total: 0, anomalies: 0, critical: 0, files: 0 })
          }
          return
        }

        const resStats = await api.get(`/cases/${caseId}/stats`).then(r => r.data)
        if (isMounted) {
          setStats({ total: resStats.total, anomalies: resStats.anomalies, critical: resStats.critical, files: fileCount })
        }
      } catch (e) {
        if (isMounted) setStats({ total: 0, anomalies: 0, critical: 0, files: effectiveCount || 0 })
      } finally {
        if (isMounted) setLoading(false)
      }
    }
    load()
    return () => { isMounted = false }
  }, [caseId, effectiveCount, parsedCount])

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
      gap: '14px',
    }}>
      <Stat icon={Activity}      label="Total Events"   value={stats?.total}     iconBg="#60a5fa" loading={loading} />
      <Stat icon={AlertTriangle} label="Anomalies"      value={stats?.anomalies} iconBg="#fbbf24" loading={loading} />
      <Stat icon={Layers}        label="Critical Events" value={stats?.critical}  iconBg="#f87171" loading={loading} />
      <Stat icon={FileText}      label="Evidence Files" value={stats?.files ?? initialEvidenceCount} iconBg="#34d399" loading={loading && initialEvidenceCount === undefined} />
    </div>
  )
}

export default CaseStats
