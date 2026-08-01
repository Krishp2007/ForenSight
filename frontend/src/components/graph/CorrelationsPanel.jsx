import { useState, useEffect } from 'react'
import { getCorrelations, runCorrelations } from '../../services/correlationService'
import Spinner from '../ui/Spinner'
import EmptyState from '../ui/EmptyState'
import Badge from '../ui/Badge'
import { Link2, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react'
import { humanize } from '../../utils/formatters'

const RULE_COLORS = {
  PROCESS_INITIATED_CONNECTION: 'bg-blue-600 text-white',
  REGISTRY_RUN_KEY_PERSISTENCE:  'bg-red-600 text-white',
  PARENT_OF:                     'bg-purple-600 text-white',
}

const CorrelationsPanel = ({ caseId }) => {
  const [data, setData]         = useState(null)
  const [loading, setLoading]   = useState(true)
  const [running, setRunning]   = useState(false)
  const [openRule, setOpenRule] = useState(null)
  const [error, setError]       = useState(null)

  const load = async () => {
    setLoading(true)
    try {
      const d = await getCorrelations(caseId)
      setData(d)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load correlations')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [caseId])

  const handleRun = async () => {
    setRunning(true)
    setError(null)
    try {
      await runCorrelations(caseId)
      await load()
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to run correlations')
    } finally {
      setRunning(false)
    }
  }

  const correlations = data?.correlations || []

  // Group by rule
  const groups = correlations.reduce((acc, c) => {
    const r = c.rule || 'UNKNOWN'
    acc[r] = acc[r] || []
    acc[r].push(c)
    return acc
  }, {})

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <p className="text-gray-400 text-sm">
          {correlations.length} derived relationships from 3 Cypher rules
        </p>
        <button
          onClick={handleRun} disabled={running}
          className="flex items-center gap-2 px-3 py-1.5 text-xs bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg transition-colors"
        >
          {running ? <Spinner size="sm" /> : <RefreshCw size={13} />}
          Re-run Rules
        </button>
      </div>

      {error && (
        <p className="text-red-400 text-xs bg-red-900/20 border border-red-800 rounded-lg px-3 py-2">{error}</p>
      )}

      {loading ? (
        <div className="flex justify-center py-12"><Spinner size="lg" /></div>
      ) : correlations.length === 0 ? (
        <EmptyState icon={Link2} title="No correlations yet"
          description="Click 'Re-run Rules' after parsing evidence to derive process, network and persistence relationships." />
      ) : (
        <div className="flex flex-col gap-3">
          {Object.entries(groups).map(([rule, items]) => {
            const isOpen = openRule === rule
            const colorCls = RULE_COLORS[rule] || 'bg-gray-600 text-white'
            return (
              <div key={rule} className="border border-gray-700 rounded-xl overflow-hidden">
                <button
                  onClick={() => setOpenRule(isOpen ? null : rule)}
                  className="w-full flex items-center justify-between px-4 py-3 bg-gray-800 hover:bg-gray-700 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <Badge label={humanize(rule)} colorClass={colorCls} />
                    <span className="text-gray-400 text-xs">{items.length} relationships</span>
                    {items[0]?.mitre && (
                      <span className="text-xs font-mono bg-purple-800/50 text-purple-300 px-2 py-0.5 rounded">
                        {items[0].mitre}
                      </span>
                    )}
                  </div>
                  {isOpen ? <ChevronUp size={14} className="text-gray-400" /> : <ChevronDown size={14} className="text-gray-400" />}
                </button>

                {isOpen && (
                  <div className="divide-y divide-gray-700/50">
                    {items.slice(0, 50).map((c, i) => (
                      <div key={i} className="px-4 py-2.5 flex items-center gap-2 text-sm bg-gray-800/40 hover:bg-gray-700/30">
                        <span className="text-blue-400 font-medium truncate max-w-[200px]">{c.source}</span>
                        <span className="text-gray-500 shrink-0">→</span>
                        <span className="text-green-400 font-medium truncate max-w-[200px]">{c.target}</span>
                        {c.technique && (
                          <span className="ml-auto text-xs text-gray-500 truncate">{c.technique}</span>
                        )}
                      </div>
                    ))}
                    {items.length > 50 && (
                      <p className="px-4 py-2 text-xs text-gray-500 bg-gray-800/40">
                        …and {items.length - 50} more
                      </p>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default CorrelationsPanel
