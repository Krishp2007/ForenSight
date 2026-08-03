import { useEffect, useState } from 'react'
import { Users, ShieldCheck, ShieldOff, UserX } from 'lucide-react'
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
  const [loading, setLoading] = useState(true)
  const [error, setError]   = useState(null)
  const [saving, setSaving] = useState({})

  useEffect(() => {
    if (!canManageUsers) return
    api.get('/users')
      .then(r => setUsers(r.data))
      .catch(e => setError(e?.response?.data?.detail || 'Failed to load users'))
      .finally(() => setLoading(false))
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

  const deactivate = async (userId) => {
    if (!window.confirm('Deactivate this user? They will no longer be able to log in.')) return
    setSaving(p => ({ ...p, [userId]: true }))
    try {
      await api.delete(`/users/${userId}`)
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, is_active: false } : u))
    } catch (e) {
      alert(e?.response?.data?.detail || 'Failed to deactivate user')
    } finally {
      setSaving(p => ({ ...p, [userId]: false }))
    }
  }

  if (!canManageUsers) return (
    <div style={{ padding: '48px', textAlign: 'center', color: '#fca5a5', fontSize: '14px' }}>
      Access denied — admin only.
    </div>
  )

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', padding: '96px' }}><Spinner size="lg" /></div>
  if (error)   return <div style={{ padding: '32px', color: '#fca5a5', textAlign: 'center' }}>{error}</div>

  const thStyle = { padding: '10px 16px', textAlign: 'left', color: '#6b7fa3', fontSize: '10px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '1px', borderBottom: '1px solid #3d4f6a' }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxWidth: '1000px', margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <Users size={20} color="#60a5fa" />
        <h2 style={{ color: '#fff', fontSize: '18px', fontWeight: '700', margin: 0 }}>User Management</h2>
        <span style={{ marginLeft: 'auto', color: '#6b7fa3', fontSize: '12px' }}>{users.length} users</span>
      </div>

      <div style={{ borderRadius: '12px', border: '1px solid #3d4f6a', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ background: '#1e2a3d' }}>
              <th style={thStyle}>User</th>
              <th style={thStyle}>Role</th>
              <th style={thStyle}>Status</th>
              <th style={thStyle}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u, i) => (
              <tr key={u.id} style={{ background: i % 2 === 0 ? '#2d3748' : '#283141', borderBottom: '1px solid #3d4f6a' }}>
                <td style={{ padding: '10px 16px' }}>
                  <div style={{ color: '#fff', fontWeight: '500' }}>{u.username}</div>
                  <div style={{ color: '#6b7fa3', fontSize: '11px' }}>{u.email}</div>
                </td>
                <td style={{ padding: '10px 16px' }}>
                  <RoleBadge role={u.role} />
                </td>
                <td style={{ padding: '10px 16px' }}>
                  <span style={{ fontSize: '11px', fontWeight: '600', color: u.is_active ? '#34d399' : '#f87171' }}>
                    {u.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td style={{ padding: '10px 16px' }}>
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                    {/* Role selector */}
                    <select
                      value={u.role}
                      disabled={saving[u.id]}
                      onChange={e => update(u.id, { role: e.target.value })}
                      style={{ background: '#1e2a3d', border: '1px solid #3d4f6a', color: '#9aa8c0', borderRadius: '6px', padding: '3px 8px', fontSize: '11px', cursor: 'pointer', fontFamily: 'inherit' }}
                    >
                      <option value="viewer">Viewer</option>
                      <option value="investigator">Investigator</option>
                      <option value="admin">Admin</option>
                    </select>

                    {/* Toggle active */}
                    <button
                      disabled={saving[u.id]}
                      onClick={() => update(u.id, { is_active: !u.is_active })}
                      title={u.is_active ? 'Deactivate' : 'Reactivate'}
                      style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '3px 9px', borderRadius: '6px', border: `1px solid ${u.is_active ? '#f8717133' : '#34d39933'}`, background: u.is_active ? 'rgba(248,113,113,0.1)' : 'rgba(52,211,153,0.1)', color: u.is_active ? '#f87171' : '#34d399', fontSize: '11px', cursor: 'pointer', fontFamily: 'inherit', opacity: saving[u.id] ? 0.5 : 1 }}
                    >
                      {u.is_active ? <ShieldOff size={10} /> : <ShieldCheck size={10} />}
                      {u.is_active ? 'Deactivate' : 'Reactivate'}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default UsersPage
