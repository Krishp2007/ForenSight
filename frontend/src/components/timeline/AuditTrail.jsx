import { useState, useEffect } from 'react'
import { getCaseAuditLog } from '../../services/auditService'
import { formatDateTime, humanize } from '../../utils/formatters'
import Spinner from '../ui/Spinner'
import EmptyState from '../ui/EmptyState'
import { ShieldCheck, Hash } from 'lucide-react'

const ACTION_COLORS = {
  'case.create':       'text-emerald-400',
  'case.update':       'text-blue-400',
  'evidence.upload':   'text-yellow-400',
  'graph.clear':       'text-red-400',
  'correlations.run':  'text-purple-400',
  'report.generate':   'text-cyan-400',
}

const AuditTrail = ({ caseId }) => {
  const [rows, setRows]       = useState([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState(null)

  useEffect(() => {
    getCaseAuditLog(caseId, 200)
      .then(setRows)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [caseId])

  if (loading) return <div className="flex justify-center py-12"><Spinner size="lg" /></div>
  if (!rows.length) return (
    <EmptyState icon={ShieldCheck} title="No audit entries yet"
      description="Every case mutation is recorded here with a Merkle hash chain." />
  )

  return (
    <div className="flex flex-col gap-0 border border-gray-700 rounded-xl overflow-hidden">
      {[...rows].reverse().map((row, i) => {
        const color = ACTION_COLORS[row.action] || 'text-gray-400'
        const isOpen = expanded === i
        return (
          <div
            key={row.id || i}
            className="border-b border-gray-700 last:border-0 px-4 py-3 hover:bg-gray-700/30 transition-colors"
          >
            <div className="flex items-center gap-3 cursor-pointer" onClick={() => setExpanded(isOpen ? null : i)}>
              <ShieldCheck size={14} className={color} />
              <span className={`text-xs font-mono font-semibold ${color}`}>{row.action}</span>
              <span className="text-gray-400 text-xs flex-1 truncate">
                {humanize(row.entity_type)} · {row.entity_id?.slice(-8)}
              </span>
              <span className="text-gray-500 text-xs shrink-0">{formatDateTime(row.created_at)}</span>
            </div>

            {isOpen && (
              <div className="mt-2 ml-5 flex flex-col gap-1 text-xs text-gray-400">
                <div className="flex gap-2">
                  <Hash size={11} className="shrink-0 mt-0.5 text-gray-600" />
                  <span className="font-mono text-gray-500 break-all">
                    <span className="text-gray-600">prev:</span> {row.prev_hash?.slice(0, 32)}…
                  </span>
                </div>
                <div className="flex gap-2">
                  <Hash size={11} className="shrink-0 mt-0.5 text-gray-600" />
                  <span className="font-mono text-gray-500 break-all">
                    <span className="text-gray-600">self:</span> {row.self_hash?.slice(0, 32)}…
                  </span>
                </div>
                {row.metadata && Object.keys(row.metadata).length > 0 && (
                  <pre className="bg-gray-800 rounded p-2 text-xs overflow-x-auto mt-1 text-gray-300">
                    {JSON.stringify(row.metadata, null, 2)}
                  </pre>
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

export default AuditTrail
