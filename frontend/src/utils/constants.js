export const SEVERITY_LEVELS = ['info', 'low', 'medium', 'high', 'critical']

export const EVENT_TYPES = [
  'process_creation',
  'network_connection',
  'file_modification',
  'registry_change',
  'auth_event',
  'browser_history',
  'browser_download',
  'browser_credential',
  'hash_record',
  'generic',
]

export const CASE_STATUSES = ['open', 'in_progress', 'suspended', 'resolved']

export const EVIDENCE_STATUSES = ['uploaded', 'queued', 'parsing', 'parsed', 'failed']

export const EVIDENCE_TYPES = ['evtx', 'pcap', 'browser_sqlite', 'csv', 'json', 'text']

export const USER_ROLES = ['admin', 'investigator', 'viewer']
