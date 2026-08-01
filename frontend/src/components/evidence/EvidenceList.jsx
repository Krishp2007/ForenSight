import { useEffect, useRef } from 'react'
import { getEvidence } from '../../services/evidenceService'
import EvidenceStatusBadge from './EvidenceStatusBadge'
import { formatBytes, formatDateTime } from '../../utils/formatters'
import { FileText, RefreshCw } from 'lucide-react'
import EmptyState from '../ui/EmptyState'

const POLLING_INTERVAL = 4000 // ms
const TERMINAL = ['parsed', 'failed']

const EvidenceList = ({ items, onItemUpdated }) => {
  const timerRef = useRef(null)

  // Poll non-terminal items
  useEffect(() => {
    const pending = items.filter((e) => !TERMINAL.includes(e.status))
    if (pending.length === 0) return

    timerRef.current = setInterval(async () => {
      for (const ev of pending) {
        try {
          const updated = await getEvidence(ev.id)
          if (updated.status !== ev.status) onItemUpdated(updated)
        } catch { /* silent */ }
      }
    }, POLLING_INTERVAL)

    return () => clearInterval(timerRef.current)
  }, [items])

  if (!items.length) {
    return <EmptyState icon={FileText} title="No evidence yet" description="Upload your first forensic file above." />
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-700">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-gray-400 text-xs uppercase bg-gray-800 border-b border-gray-700">
            <th className="px-4 py-3">Filename</th>
            <th className="px-4 py-3">Type</th>
            <th className="px-4 py-3">Size</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Uploaded</th>
            <th className="px-4 py-3">SHA-256</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-700">
          {items.map((e) => (
            <tr key={e.id} className="bg-gray-800/50 hover:bg-gray-700/50 transition-colors">
              <td className="px-4 py-3 text-white font-medium max-w-[200px] truncate">{e.filename}</td>
              <td className="px-4 py-3 text-gray-400 uppercase text-xs">{e.file_type}</td>
              <td className="px-4 py-3 text-gray-400">{formatBytes(e.size_bytes)}</td>
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <EvidenceStatusBadge status={e.status} />
                  {!TERMINAL.includes(e.status) && (
                    <RefreshCw size={12} className="text-gray-500 animate-spin" />
                  )}
                </div>
                {e.error_message && (
                  <p className="text-red-400 text-xs mt-1">{e.error_message}</p>
                )}
              </td>
              <td className="px-4 py-3 text-gray-400 text-xs">{formatDateTime(e.created_at)}</td>
              <td className="px-4 py-3 text-gray-500 text-xs font-mono truncate max-w-[120px]">
                {e.sha256?.slice(0, 12)}…
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default EvidenceList
