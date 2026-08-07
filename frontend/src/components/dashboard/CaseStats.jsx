import { useState, useEffect } from 'react'
import api from '../../services/api'
import { listEvidence } from '../../services/evidenceService'
import { Activity, AlertTriangle, FileText, Layers, GitBranch } from 'lucide-react'

const Stat = ({ icon: Icon, label, value, iconBg, loading }) => (
  <div style={{
    background: 'var(--forensic-card-bg, #ffffff)',
    backdropFilter: 'blur(16px)',
    WebkitBackdropFilter: 'blur(16px)',
    border: '1px solid var(--forensic-border, #e2e8f0)',
    borderRadius: '16px',
    padding: '18px 20px',
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)',
    transition: 'all 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
  }}>
    <div style={{
      width: '42px', height: '42px',
      borderRadius: '12px',
      background: iconBg + '18',
      border: `1px solid ${iconBg}40`,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      flexShrink: 0,
      color: iconBg,
    }}>
      <Icon size={20} />
    </div>
    <div style={{ flex: 1 }}>
      <p style={{ color: 'var(--forensic-text-muted, #64748b)', fontSize: '11px', fontWeight: '700', margin: '0 0 4px 0', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        {label}
      </p>
      {loading ? (
        <div style={{
          width: '52px', height: '22px', borderRadius: '6px',
          background: 'rgba(148, 163, 184, 0.2)',
          animation: 'pulse 1.5s infinite ease-in-out',
        }} />
      ) : (
        <p style={{ color: 'var(--forensic-text-main, #0f172a)', fontSize: '22px', fontWeight: '800', margin: 0, lineHeight: 1 }}>
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
          if (isMounted) setStats({ total: 0, anomalies: 0, critical: 0, correlations: 0, files: 0 })
          return
        }

        // Fetch event stats and graph correlations in parallel.
        // The /stats endpoint always returns graph_correlations=0 (by design — too expensive
        // to run Neo4j on every stats poll). We call /correlations separately for the real count.
        const [resStats, resCorr] = await Promise.allSettled([
          api.get(`/cases/${caseId}/stats`).then(r => r.data),
          api.get(`/cases/${caseId}/correlations`).then(r => r.data),
        ])

        if (isMounted) {
          const s = resStats.status === 'fulfilled' ? resStats.value : {}
          const c = resCorr.status === 'fulfilled' ? resCorr.value : {}
          setStats({
            total:        s.total        ?? 0,
            anomalies:    s.anomalies    ?? 0,
            critical:     s.critical     ?? 0,
            // Use total_correlations from the Neo4j correlations endpoint — authoritative count
            correlations: c.total_correlations ?? c.total ?? 0,
            files:        fileCount,
          })
        }
      } catch (e) {
        if (isMounted) setStats({ total: 0, anomalies: 0, critical: 0, correlations: 0, files: effectiveCount || 0 })
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
      gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
      gap: '14px',
    }}>
      <Stat icon={Activity}      label="Total Events"        value={stats?.total}        iconBg="#2563eb" loading={loading} />
      <Stat icon={AlertTriangle} label="ML Anomalies"        value={stats?.anomalies}    iconBg="#d97706" loading={loading} />
      <Stat icon={Layers}        label="Critical Events"     value={stats?.critical}     iconBg="#dc2626" loading={loading} />
      <Stat icon={GitBranch}     label="Graph Correlations"  value={stats?.correlations} iconBg="#7c3aed" loading={loading} />
      <Stat icon={FileText}      label="Evidence Files"      value={stats?.files ?? initialEvidenceCount} iconBg="#059669" loading={loading && initialEvidenceCount === undefined} />
    </div>
  )
}

export default CaseStats
