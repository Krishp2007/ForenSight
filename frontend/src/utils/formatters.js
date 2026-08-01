// Date/time
export const formatDateTime = (iso) => {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-GB', {
    year: 'numeric', month: 'short', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}

export const formatDateShort = (iso) => {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-GB', {
    year: 'numeric', month: 'short', day: '2-digit',
  })
}

// File size
export const formatBytes = (bytes) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let val = bytes
  while (val >= 1024 && i < units.length - 1) {
    val /= 1024
    i++
  }
  return `${val.toFixed(1)} ${units[i]}`
}

// Severity → Tailwind color classes
export const severityColor = (severity) => {
  const map = {
    critical: 'bg-red-600 text-white',
    high: 'bg-orange-500 text-white',
    medium: 'bg-yellow-400 text-black',
    low: 'bg-blue-400 text-white',
    info: 'bg-gray-400 text-white',
  }
  return map[severity] || 'bg-gray-300 text-black'
}

// Case status → color classes
export const statusColor = (status) => {
  const map = {
    open: 'bg-emerald-500 text-white',
    in_progress: 'bg-blue-500 text-white',
    suspended: 'bg-yellow-400 text-black',
    resolved: 'bg-gray-500 text-white',
  }
  return map[status] || 'bg-gray-300 text-black'
}

// Evidence status → color classes
export const evidenceStatusColor = (status) => {
  const map = {
    uploaded: 'bg-gray-400 text-white',
    queued: 'bg-blue-300 text-black',
    parsing: 'bg-yellow-400 text-black',
    parsed: 'bg-emerald-500 text-white',
    failed: 'bg-red-500 text-white',
  }
  return map[status] || 'bg-gray-300 text-black'
}

// Human-readable label
export const humanize = (str) =>
  str ? str.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()) : '—'
