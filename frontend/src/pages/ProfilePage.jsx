import { useState } from 'react'
import { User, Mail, Lock, ShieldCheck, Save, CheckCircle, AlertCircle, Eye, EyeOff, Building } from 'lucide-react'
import useAuth from '../hooks/useAuth'
import { updateMe } from '../services/authService'
import { Spinner } from '../components/ui'

/* ── small reusable field ──────────────────────────────────────── */
const Field = ({ label, icon: Icon, children }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
    <label style={{
      display: 'flex', alignItems: 'center', gap: '6px',
      color: '#8a9ab8', fontSize: '11px', fontWeight: '600',
      letterSpacing: '1px', textTransform: 'uppercase',
    }}>
      <Icon size={12} color="#6b7fa3" />
      {label}
    </label>
    {children}
  </div>
)

const inputStyle = (focused) => ({
  width: '100%', boxSizing: 'border-box',
  padding: '10px 13px',
  background: '#1a2234',
  border: `1.5px solid ${focused ? '#60a5fa' : '#3d4f6a'}`,
  borderRadius: '8px',
  color: '#fff', fontSize: '14px',
  outline: 'none', transition: 'border-color 0.15s',
  fontFamily: 'inherit',
})

const Card = ({ title, subtitle, icon: Icon, children }) => (
  <div style={{
    background: '#1e2a3d', border: '1px solid #2d3748',
    borderRadius: '12px', overflow: 'hidden',
  }}>
    <div style={{
      padding: '16px 20px', borderBottom: '1px solid #2d3748',
      display: 'flex', alignItems: 'center', gap: '10px',
    }}>
      <div style={{
        width: '32px', height: '32px', borderRadius: '8px',
        background: 'rgba(96,165,250,0.12)', border: '1px solid rgba(96,165,250,0.25)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
      }}>
        <Icon size={15} color="#60a5fa" />
      </div>
      <div>
        <div style={{ color: '#fff', fontWeight: '600', fontSize: '14px' }}>{title}</div>
        {subtitle && <div style={{ color: '#6b7fa3', fontSize: '12px', marginTop: '1px' }}>{subtitle}</div>}
      </div>
    </div>
    <div style={{ padding: '20px' }}>
      {children}
    </div>
  </div>
)

/* ── Avatar initials ───────────────────────────────────────────── */
const Avatar = ({ name, size = 72 }) => {
  const initials = (name || '?').split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
  const hue = [...(name || '')].reduce((acc, c) => acc + c.charCodeAt(0), 0) % 360
  return (
    <div style={{
      width: size, height: size, borderRadius: '50%',
      background: `hsl(${hue},55%,35%)`,
      border: '3px solid rgba(96,165,250,0.35)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: size * 0.38, fontWeight: '700', color: '#fff',
      flexShrink: 0, userSelect: 'none',
    }}>
      {initials}
    </div>
  )
}

/* ── Role badge ────────────────────────────────────────────────── */
const roleMeta = {
  admin:        { bg: '#fee2e2', color: '#991b1b', label: 'Admin' },
  investigator: { bg: '#dbeafe', color: '#1d4ed8', label: 'Investigator' },
  viewer:       { bg: '#ecfdf5', color: '#065f46', label: 'Viewer' },
}
const RoleBadge = ({ role }) => {
  const m = roleMeta[role] || { bg: '#f1f5f9', color: '#475569', label: role }
  return (
    <span style={{
      background: m.bg, color: m.color,
      fontSize: '11px', fontWeight: '700', padding: '3px 10px',
      borderRadius: '12px', letterSpacing: '0.3px',
    }}>{m.label}</span>
  )
}

/* ── Toast ─────────────────────────────────────────────────────── */
const Toast = ({ type, msg }) => (
  <div style={{
    display: 'flex', alignItems: 'center', gap: '8px',
    padding: '10px 14px', borderRadius: '8px',
    background: type === 'success' ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
    border: `1px solid ${type === 'success' ? 'rgba(16,185,129,0.4)' : 'rgba(239,68,68,0.4)'}`,
    color: type === 'success' ? '#34d399' : '#fca5a5',
    fontSize: '13px',
  }}>
    {type === 'success'
      ? <CheckCircle size={15} style={{ flexShrink: 0 }} />
      : <AlertCircle size={15} style={{ flexShrink: 0 }} />}
    {msg}
  </div>
)

/* ═══════════════════════════════════════════════════════════════ */
/* MAIN PAGE                                                        */
/* ═══════════════════════════════════════════════════════════════ */
export default function ProfilePage() {
  const { user, fetchMe } = useAuth()

  /* ── profile form state ── */
  const [username,  setUsername]  = useState(user?.username  || '')
  const [email,     setEmail]     = useState(user?.email     || '')
  const [profileMsg, setProfileMsg] = useState(null)
  const [profileLoading, setProfileLoading] = useState(false)

  /* ── password form state ── */
  const [newPw,     setNewPw]     = useState('')
  const [confirmPw, setConfirmPw] = useState('')
  const [showPw,    setShowPw]    = useState(false)
  const [showCpw,   setShowCpw]   = useState(false)
  const [pwMsg,     setPwMsg]     = useState(null)
  const [pwLoading, setPwLoading] = useState(false)

  /* ── focus state ── */
  const [focused, setFocused] = useState({})
  const focus   = (k) => setFocused(p => ({ ...p, [k]: true  }))
  const unfocus = (k) => setFocused(p => ({ ...p, [k]: false }))

  /* ── save profile ── */
  const saveProfile = async (e) => {
    e.preventDefault()
    setProfileMsg(null)
    setProfileLoading(true)
    try {
      const payload = {}
      if (username !== user?.username) payload.username = username
      if (email    !== user?.email)    payload.email    = email
      if (!Object.keys(payload).length) {
        setProfileMsg({ type: 'success', msg: 'Nothing changed.' })
        return
      }
      await updateMe(payload)
      await fetchMe()
      setProfileMsg({ type: 'success', msg: 'Profile updated successfully.' })
    } catch (err) {
      setProfileMsg({ type: 'error', msg: err?.response?.data?.detail || 'Failed to update profile.' })
    } finally {
      setProfileLoading(false)
    }
  }

  /* ── change password ── */
  const changePassword = async (e) => {
    e.preventDefault()
    setPwMsg(null)
    if (newPw.length < 8) {
      setPwMsg({ type: 'error', msg: 'Password must be at least 8 characters.' })
      return
    }
    if (newPw !== confirmPw) {
      setPwMsg({ type: 'error', msg: 'Passwords do not match.' })
      return
    }
    setPwLoading(true)
    try {
      await updateMe({ password: newPw })
      setNewPw(''); setConfirmPw('')
      setPwMsg({ type: 'success', msg: 'Password changed successfully.' })
    } catch (err) {
      setPwMsg({ type: 'error', msg: err?.response?.data?.detail || 'Failed to change password.' })
    } finally {
      setPwLoading(false)
    }
  }

  const btnStyle = (loading, color = '#4a7fe8') => ({
    display: 'flex', alignItems: 'center', gap: '8px',
    padding: '10px 20px', borderRadius: '8px', border: 'none',
    background: loading ? '#3b6bc4' : color,
    color: '#fff', fontSize: '13px', fontWeight: '600',
    cursor: loading ? 'not-allowed' : 'pointer',
    fontFamily: 'inherit', transition: 'background 0.2s',
    opacity: loading ? 0.8 : 1,
  })

  return (
    <div style={{ maxWidth: '720px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>

      {/* ── Header ──────────────────────────────────────────────── */}
      <div>
        <h2 style={{ color: '#fff', fontWeight: '700', fontSize: '20px', margin: '0 0 4px 0' }}>
          Profile &amp; Settings
        </h2>
        <p style={{ color: '#6b7fa3', fontSize: '13px', margin: 0 }}>
          Manage your account details and security credentials.
        </p>
      </div>

      {/* ── Identity card ───────────────────────────────────────── */}
      <Card title="Account Overview" icon={User}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px', flexWrap: 'wrap' }}>
          <Avatar name={user?.username} size={68} />
          <div style={{ flex: 1, minWidth: '180px' }}>
            <div style={{ color: '#fff', fontSize: '18px', fontWeight: '700', marginBottom: '4px' }}>
              {user?.username}
            </div>
            <div style={{ color: '#9aa8c0', fontSize: '13px', marginBottom: '10px' }}>
              {user?.email}
            </div>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
              <RoleBadge role={user?.role} />
              <span style={{
                display: 'flex', alignItems: 'center', gap: '4px',
                background: user?.is_active ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                border: `1px solid ${user?.is_active ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}`,
                color: user?.is_active ? '#34d399' : '#fca5a5',
                fontSize: '11px', fontWeight: '600',
                padding: '3px 10px', borderRadius: '12px',
              }}>
                <span style={{ width: '6px', height: '6px', borderRadius: '50%',
                  background: user?.is_active ? '#34d399' : '#ef4444',
                  display: 'inline-block' }} />
                {user?.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
          </div>
          <div style={{
            background: '#1a2234', border: '1px solid #2d3748',
            borderRadius: '10px', padding: '14px 18px',
            fontSize: '12px', color: '#6b7fa3', minWidth: '200px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px', color: '#60a5fa', fontWeight: '700', fontSize: '13px' }}>
              <Building size={14} /> {user?.organization_name || 'Enterprise Forensics Org'}
            </div>
            <div style={{ color: '#cbd5e1', fontSize: '11px', wordBreak: 'break-all', marginBottom: '10px' }}>
              <span style={{ color: '#6b7fa3' }}>ID: </span>{user?.organization_id}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#9aa8c0', marginBottom: '3px' }}>
              <ShieldCheck size={12} /> Member since
            </div>
            <div style={{ color: '#cbd5e1', fontSize: '12px' }}>
              {user?.created_at
                ? new Date(user.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
                : '—'}
            </div>
          </div>
        </div>
      </Card>

      {/* ── Edit profile ────────────────────────────────────────── */}
      <Card title="Edit Profile" subtitle="Update your display name and email address" icon={User}>
        <form onSubmit={saveProfile} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <Field label="Display Name" icon={User}>
            <input
              value={username}
              onChange={e => setUsername(e.target.value)}
              onFocus={() => focus('username')}
              onBlur={() => unfocus('username')}
              placeholder="Your name"
              required minLength={3} maxLength={50}
              style={inputStyle(focused.username)}
            />
          </Field>

          <Field label="Email Address" icon={Mail}>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              onFocus={() => focus('email')}
              onBlur={() => unfocus('email')}
              placeholder="you@example.com"
              required
              style={inputStyle(focused.email)}
            />
          </Field>

          {profileMsg && <Toast type={profileMsg.type} msg={profileMsg.msg} />}

          <div>
            <button type="submit" disabled={profileLoading} style={btnStyle(profileLoading)}>
              {profileLoading ? <Spinner size="sm" /> : <Save size={14} />}
              {profileLoading ? 'Saving…' : 'Save Changes'}
            </button>
          </div>
        </form>
      </Card>

      {/* ── Change password ─────────────────────────────────────── */}
      <Card title="Change Password" subtitle="Choose a strong password of at least 8 characters" icon={Lock}>
        <form onSubmit={changePassword} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <Field label="New Password" icon={Lock}>
            <div style={{ position: 'relative' }}>
              <input
                type={showPw ? 'text' : 'password'}
                value={newPw}
                onChange={e => setNewPw(e.target.value)}
                onFocus={() => focus('newPw')}
                onBlur={() => unfocus('newPw')}
                placeholder="Min. 8 characters"
                minLength={8}
                required
                style={{ ...inputStyle(focused.newPw), paddingRight: '42px' }}
              />
              <button type="button" onClick={() => setShowPw(v => !v)} style={{
                position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)',
                background: 'none', border: 'none', color: '#6b7fa3', cursor: 'pointer', padding: 0,
                display: 'flex', alignItems: 'center',
              }}>
                {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </Field>

          <Field label="Confirm New Password" icon={Lock}>
            <div style={{ position: 'relative' }}>
              <input
                type={showCpw ? 'text' : 'password'}
                value={confirmPw}
                onChange={e => setConfirmPw(e.target.value)}
                onFocus={() => focus('cpw')}
                onBlur={() => unfocus('cpw')}
                placeholder="Repeat new password"
                minLength={8}
                required
                style={{
                  ...inputStyle(focused.cpw),
                  paddingRight: '42px',
                  borderColor: confirmPw && confirmPw !== newPw
                    ? '#ef4444'
                    : confirmPw && confirmPw === newPw
                    ? '#10b981'
                    : (focused.cpw ? '#60a5fa' : '#3d4f6a'),
                }}
              />
              <button type="button" onClick={() => setShowCpw(v => !v)} style={{
                position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)',
                background: 'none', border: 'none', color: '#6b7fa3', cursor: 'pointer', padding: 0,
                display: 'flex', alignItems: 'center',
              }}>
                {showCpw ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            {confirmPw && confirmPw !== newPw && (
              <span style={{ color: '#fca5a5', fontSize: '11px' }}>Passwords do not match</span>
            )}
          </Field>

          {pwMsg && <Toast type={pwMsg.type} msg={pwMsg.msg} />}

          <div>
            <button type="submit" disabled={pwLoading} style={btnStyle(pwLoading, '#7c3aed')}>
              {pwLoading ? <Spinner size="sm" /> : <Lock size={14} />}
              {pwLoading ? 'Updating…' : 'Update Password'}
            </button>
          </div>
        </form>
      </Card>

    </div>
  )
}
