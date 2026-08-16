import { useEffect, useState } from 'react'
import { Users, ShieldCheck, ShieldOff, UserPlus, Copy, Check, Trash2, Link as LinkIcon, X, Key } from 'lucide-react'
import api from '../services/api'
import useRole from '../hooks/useRole'
import { Spinner } from '../components/ui'

const ROLE_COLORS = {
  admin:        { bg: 'rgba(251,191,36,0.15)',  color: '#fbbf24' },
  investigator: { bg: 'rgba(96,165,250,0.15)',  color: '#60a5fa' },
  viewer:       { bg: 'rgba(107,127,163,0.15)', color: '#9aa8c0' },
}

const RoleBadge = ({ role }) => {
  const s = ROLE_COLORS[role] || ROLE_COLORS.viewer
  return (
    <span style={{ padding: '2px 8px', borderRadius: '99px', fontSize: '11px', fontWeight: '600', textTransform: 'capitalize', background: s.bg, color: s.color }}>
      {role}
    </span>
  )
}

const UsersPage = () => {
  const { canManageUsers } = useRole()
  const [users, setUsers]   = useState([])
  const [invites, setInvites] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError]   = useState(null)
  const [saving, setSaving] = useState({})

  // Modal State
  const [showInviteModal, setShowInviteModal] = useState(false)
  const [inviteRole, setInviteRole]           = useState('investigator')
  const [targetEmail, setTargetEmail]         = useState('')
  const [inviteLoading, setInviteLoading]     = useState(false)
  const [inviteError, setInviteError]         = useState(null)
  const [createdInvite, setCreatedInvite]     = useState(null)
  const [copiedToken, setCopiedToken]         = useState(null)

  const loadData = async () => {
    if (!canManageUsers) return
    setLoading(true)
    try {
      const [uRes, iRes] = await Promise.all([
        api.get('/users'),
        api.get('/invites/'),
      ])
      setUsers(uRes.data)
      setInvites(iRes.data)
    } catch (e) {
      setError(e?.response?.data?.detail || 'Failed to load users & invites')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [canManageUsers])

  const update = async (userId, patch) => {
    setSaving(p => ({ ...p, [userId]: true }))
    try {
      const res = await api.patch(`/users/${userId}`, patch)
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, ...res.data } : u))
    } catch (e) {
      alert(e?.response?.data?.detail || 'Update failed')
    } finally {
      setSaving(p => ({ ...p, [userId]: false }))
    }
  }

  const handleCreateInvite = async (e) => {
    e.preventDefault()
    setInviteLoading(true)
    setInviteError(null)
    setCreatedInvite(null)
    try {
      const res = await api.post('/invites/', {
        role: inviteRole,
        target_email: targetEmail.trim() || null,
      })
      setCreatedInvite(res.data)
      setInvites(prev => [res.data, ...prev])
      setTargetEmail('')
    } catch (err) {
      setInviteError(err?.response?.data?.detail || 'Failed to generate invite link')
    } finally {
      setInviteLoading(false)
    }
  }

  const handleRevokeInvite = async (inviteId) => {
    if (!window.confirm('Revoke this invite link? Users will no longer be able to register using it.')) return
    try {
      await api.delete(`/invites/${inviteId}`)
      setInvites(prev => prev.filter(inv => inv.id !== inviteId))
    } catch (e) {
      alert(e?.response?.data?.detail || 'Failed to revoke invite token')
    }
  }

  const copyToClipboard = (url, key) => {
    navigator.clipboard.writeText(url)
    setCopiedToken(key)
    setTimeout(() => setCopiedToken(null), 2500)
  }

  if (!canManageUsers) return (
    <div style={{ padding: '48px', textAlign: 'center', color: '#fca5a5', fontSize: '14px' }}>
      Access denied — admin only.
    </div>
  )

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', padding: '96px' }}><Spinner size="lg" /></div>
  if (error)   return <div style={{ padding: '32px', color: '#fca5a5', textAlign: 'center' }}>{error}</div>

  const thStyle = { padding: '10px 16px', textAlign: 'left', color: '#6b7fa3', fontSize: '10px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '1px', borderBottom: '1px solid #3d4f6a' }

  const activeInvites = invites.filter(inv => !inv.is_used && new Date(inv.expires_at) > new Date())

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '1000px', margin: '0 auto' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Users size={22} color="#60a5fa" />
          <h2 style={{ color: '#fff', fontSize: '20px', fontWeight: '700', margin: 0 }}>User Management</h2>
          <span style={{ color: '#6b7fa3', fontSize: '12px' }}>({users.length} members)</span>
        </div>

        <button
          onClick={() => { setShowInviteModal(true); setCreatedInvite(null); setInviteError(null); }}
          style={{
            padding: '9px 16px',
            background: '#3b82f6',
            border: 'none',
            borderRadius: '8px',
            color: '#fff',
            fontSize: '13px',
            fontWeight: '600',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)',
            fontFamily: 'inherit',
          }}
        >
          <UserPlus size={16} />
          Invite Team Member
        </button>
      </div>

      {/* Users Table */}
      <div style={{ borderRadius: '12px', border: '1px solid #3d4f6a', overflow: 'hidden', background: '#1e293b' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ background: '#0f172a' }}>
              <th style={thStyle}>User</th>
              <th style={thStyle}>Role</th>
              <th style={thStyle}>Status</th>
              <th style={thStyle}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u, i) => (
              <tr key={u.id} style={{ background: i % 2 === 0 ? '#1e293b' : '#0f172a', borderBottom: '1px solid #334155' }}>
                <td style={{ padding: '12px 16px' }}>
                  <div style={{ color: '#fff', fontWeight: '500' }}>{u.username}</div>
                  <div style={{ color: '#64748b', fontSize: '11px' }}>{u.email}</div>
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <RoleBadge role={u.role} />
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <span style={{ fontSize: '11px', fontWeight: '600', color: u.is_active ? '#34d399' : '#f87171' }}>
                    {u.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    <select
                      value={u.role}
                      disabled={saving[u.id]}
                      onChange={e => update(u.id, { role: e.target.value })}
                      style={{ background: '#0f172a', border: '1px solid #334155', color: '#cbd5e1', borderRadius: '6px', padding: '4px 8px', fontSize: '11px', cursor: 'pointer', fontFamily: 'inherit' }}
                    >
                      <option value="viewer">Viewer</option>
                      <option value="investigator">Investigator</option>
                      <option value="admin">Admin</option>
                    </select>

                    <button
                      disabled={saving[u.id]}
                      onClick={() => update(u.id, { is_active: !u.is_active })}
                      title={u.is_active ? 'Deactivate' : 'Reactivate'}
                      style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '4px 10px', borderRadius: '6px', border: `1px solid ${u.is_active ? '#f8717133' : '#34d39933'}`, background: u.is_active ? 'rgba(248,113,113,0.1)' : 'rgba(52,211,153,0.1)', color: u.is_active ? '#f87171' : '#34d399', fontSize: '11px', cursor: 'pointer', fontFamily: 'inherit', opacity: saving[u.id] ? 0.5 : 1 }}
                    >
                      {u.is_active ? <ShieldOff size={11} /> : <ShieldCheck size={11} />}
                      {u.is_active ? 'Deactivate' : 'Reactivate'}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Active Invites Section */}
      <div style={{ marginTop: '12px' }}>
        <h3 style={{ color: '#f8fafc', fontSize: '15px', fontWeight: '600', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Key size={16} color="#60a5fa" />
          Active Invite Tokens ({activeInvites.length})
        </h3>

        {activeInvites.length === 0 ? (
          <div style={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '10px', padding: '16px', color: '#64748b', fontSize: '13px', textAlign: 'center' }}>
            No active invite tokens. Click <strong>"Invite Team Member"</strong> above to generate a join code.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {activeInvites.map(inv => (
              <div key={inv.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', background: '#0f172a', border: '1px solid #334155', borderRadius: '10px', gap: '12px' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', overflow: 'hidden' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    <RoleBadge role={inv.role} />
                    {inv.target_email && (
                      <span style={{ color: '#94a3b8', fontSize: '12px' }}>Restricted: {inv.target_email}</span>
                    )}
                    <span style={{ color: '#64748b', fontSize: '11px' }}>
                      Expires: {new Date(inv.expires_at).toLocaleDateString()}
                    </span>
                  </div>
                  <div style={{ color: '#38bdf8', fontSize: '13px', fontFamily: 'monospace', fontWeight: '600', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                    Code: {inv.token}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
                  <button
                    onClick={() => copyToClipboard(inv.token, `code-${inv.id}`)}
                    title="Copy Invite Code"
                    style={{
                      display: 'flex', alignItems: 'center', gap: '6px',
                      padding: '6px 12px', background: '#1e293b', border: '1px solid #334155',
                      borderRadius: '6px', color: copiedToken === `code-${inv.id}` ? '#22c55e' : '#f8fafc',
                      fontSize: '12px', cursor: 'pointer', fontFamily: 'inherit'
                    }}
                  >
                    {copiedToken === `code-${inv.id}` ? <Check size={14} /> : <Copy size={14} />}
                    {copiedToken === `code-${inv.id}` ? 'Code Copied' : 'Copy Code'}
                  </button>

                  <button
                    onClick={() => copyToClipboard(inv.invite_url, `url-${inv.id}`)}
                    title="Copy Full URL"
                    style={{
                      display: 'flex', alignItems: 'center', gap: '6px',
                      padding: '6px 10px', background: '#0f172a', border: '1px solid #334155',
                      borderRadius: '6px', color: copiedToken === `url-${inv.id}` ? '#22c55e' : '#94a3b8',
                      fontSize: '12px', cursor: 'pointer', fontFamily: 'inherit'
                    }}
                  >
                    {copiedToken === `url-${inv.id}` ? <Check size={14} /> : <LinkIcon size={14} />}
                    {copiedToken === `url-${inv.id}` ? 'URL Copied' : 'Copy URL'}
                  </button>

                  <button
                    onClick={() => handleRevokeInvite(inv.id)}
                    title="Revoke Token"
                    style={{
                      padding: '6px', background: 'rgba(239, 68, 68, 0.1)',
                      border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '6px',
                      color: '#ef4444', cursor: 'pointer'
                    }}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Invite Modal */}
      {showInviteModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(3, 7, 18, 0.8)', backdropFilter: 'blur(6px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 1000, padding: '16px'
        }}>
          <div style={{
            width: '100%', maxWidth: '480px', background: '#0f172a',
            border: '1px solid #334155', borderRadius: '16px', padding: '24px',
            boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)', position: 'relative'
          }}>
            <button
              onClick={() => setShowInviteModal(false)}
              style={{ position: 'absolute', top: '16px', right: '16px', background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}
            >
              <X size={20} />
            </button>

            <h3 style={{ color: '#f8fafc', fontSize: '18px', fontWeight: '700', margin: '0 0 4px 0' }}>
              Generate Team Invite Code
            </h3>
            <p style={{ color: '#94a3b8', fontSize: '13px', margin: '0 0 20px 0' }}>
              Generate a secure invite code for new team members to enter during registration.
            </p>

            <form onSubmit={handleCreateInvite} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', color: '#94a3b8', fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', marginBottom: '6px' }}>
                  Assigned Forensic Role
                </label>
                <select
                  value={inviteRole} onChange={e => setInviteRole(e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f8fafc', fontSize: '13px' }}
                >
                  <option value="investigator">Investigator (Full Case Access)</option>
                  <option value="viewer">Viewer (Read-Only Audit)</option>
                  <option value="admin">Admin (Full System & User Management)</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', color: '#94a3b8', fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', marginBottom: '6px' }}>
                  Restrict to Email (Optional)
                </label>
                <input
                  type="email"
                  placeholder="e.g. analyst@agency.gov (leave blank for any email)"
                  value={targetEmail} onChange={e => setTargetEmail(e.target.value)}
                  style={{ width: '100%', boxSizing: 'border-box', padding: '10px 12px', background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f8fafc', fontSize: '13px' }}
                />
              </div>

              {inviteError && (
                <div style={{ padding: '10px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '8px', color: '#fca5a5', fontSize: '13px' }}>
                  {inviteError}
                </div>
              )}

              {createdInvite && (
                <div style={{ padding: '14px', background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.3)', borderRadius: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div style={{ color: '#4ade80', fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    Invite Code Generated!
                  </div>
                  
                  {/* Token Box */}
                  <div style={{
                    padding: '10px 12px', background: '#0f172a', border: '1px solid rgba(56, 189, 248, 0.4)',
                    borderRadius: '8px', color: '#38bdf8', fontSize: '13px', fontFamily: 'monospace',
                    fontWeight: '600', wordBreak: 'break-all', textAlign: 'center'
                  }}>
                    {createdInvite.token}
                  </div>

                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      type="button"
                      onClick={() => copyToClipboard(createdInvite.token, 'modal-code')}
                      style={{
                        flex: 1, padding: '9px', background: '#22c55e', border: 'none',
                        borderRadius: '8px', color: '#fff', fontSize: '12px', fontWeight: '600',
                        cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px'
                      }}
                    >
                      {copiedToken === 'modal-code' ? <Check size={14} /> : <Copy size={14} />}
                      {copiedToken === 'modal-code' ? 'Code Copied!' : 'Copy Invite Code'}
                    </button>

                    <button
                      type="button"
                      onClick={() => copyToClipboard(createdInvite.invite_url, 'modal-url')}
                      style={{
                        padding: '9px 12px', background: '#1e293b', border: '1px solid #334155',
                        borderRadius: '8px', color: copiedToken === 'modal-url' ? '#22c55e' : '#cbd5e1', fontSize: '12px', fontWeight: '600',
                        cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px'
                      }}
                    >
                      {copiedToken === 'modal-url' ? <Check size={14} /> : <LinkIcon size={14} />}
                      {copiedToken === 'modal-url' ? 'URL Copied' : 'Copy URL'}
                    </button>
                  </div>
                </div>
              )}

              <button
                type="submit"
                disabled={inviteLoading}
                style={{
                  width: '100%', padding: '11px', background: '#3b82f6', border: 'none',
                  borderRadius: '8px', color: '#fff', fontSize: '13px', fontWeight: '600',
                  cursor: inviteLoading ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px'
                }}
              >
                {inviteLoading ? <Spinner size="sm" /> : <Key size={16} />}
                Generate Invite Code
              </button>
            </form>
          </div>
        </div>
      )}

    </div>
  )
}

export default UsersPage
