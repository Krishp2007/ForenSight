// Date/time formatters — handles UTC conversion & local timezone
export const formatDateTime = (iso) => {
  if (!iso) return '—'
  let s = String(iso)
  // If ISO string lacks timezone offset or 'Z', append 'Z' to force UTC parsing
  if (s && !s.endsWith('Z') && !/[+-]\d{2}:?\d{2}$/.test(s)) {
    s += 'Z'
  }
  try {
    return new Date(s).toLocaleString(undefined, {
      year: 'numeric', month: 'short', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
      hour12: true,
    })
  } catch (e) {
    return String(iso)
  }
}

export const formatDateShort = (iso) => {
  if (!iso) return '—'
  let s = String(iso)
  if (s && !s.endsWith('Z') && !/[+-]\d{2}:?\d{2}$/.test(s)) {
    s += 'Z'
  }
  try {
    return new Date(s).toLocaleDateString(undefined, {
      year: 'numeric', month: 'short', day: '2-digit',
    })
  } catch (e) {
    return String(iso)
  }
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

// Case status → inline style object { background, color }
export const statusColor = (status) => {
  const map = {
    open:        { background: 'rgba(16,185,129,0.2)',  color: '#34d399' },
    in_progress: { background: 'rgba(96,165,250,0.2)',  color: '#60a5fa' },
    suspended:   { background: 'rgba(245,158,11,0.2)',  color: '#fbbf24' },
    resolved:    { background: 'rgba(107,127,163,0.2)', color: '#9aa8c0' },
  }
  return map[status] || { background: 'rgba(107,127,163,0.2)', color: '#9aa8c0' }
}

// Human-readable label
export const humanize = (str) =>
  str ? str.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()) : '—'

// Parse date string into UTC milliseconds safely (preventing local timezone offset shift)
export const parseUtcMs = (dateVal) => {
  if (!dateVal) return null
  if (typeof dateVal === 'number') return dateVal
  let str = String(dateVal).trim()
  if (!str) return null
  if (!str.endsWith('Z') && !/[+-]\d{2}:?\d{2}$/.test(str)) {
    str += 'Z'
  }
  const ms = new Date(str).getTime()
  return isNaN(ms) ? null : ms
}

// Duration formatter (0s, 47s, 1m 5s, 1h 1m 5s)
export const formatDuration = (totalSeconds) => {
  if (totalSeconds == null || isNaN(totalSeconds) || totalSeconds < 0) return '0s'
  const secs = Math.floor(totalSeconds)
  if (secs < 60) return `${secs}s`
  const mins = Math.floor(secs / 60)
  const remSecs = secs % 60
  if (mins < 60) return `${mins}m ${remSecs}s`
  const hours = Math.floor(mins / 60)
  const remMins = mins % 60
  return `${hours}h ${remMins}m ${remSecs}s`
}


