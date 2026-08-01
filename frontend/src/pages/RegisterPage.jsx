import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { register } from '../services/authService'
import { listOrganizations } from '../services/organizationService'
import Spinner from '../components/ui/Spinner'

// Password strength checker
const getStrength = (pw) => {
  if (!pw) return { label: '', color: '#ccc', width: '0%' }
  let score = 0
  if (pw.length >= 8)            score++
  if (/[A-Z]/.test(pw))          score++
  if (/[0-9]/.test(pw))          score++
  if (/[^A-Za-z0-9]/.test(pw))   score++
  if (pw.length >= 12)           score++
  if (score <= 1) return { label: 'weak',   color: '#ef4444', width: '25%' }
  if (score === 2) return { label: 'fair',   color: '#f59e0b', width: '50%' }
  if (score === 3) return { label: 'good',   color: '#4a7fe8', width: '75%' }
  return                         { label: 'strong', color: '#10b981', width: '100%' }
}

const inputStyle = {
  width: '100%', boxSizing: 'border-box',
  padding: '11px 14px',
  background: '#2a3347',
  border: '1.5px solid #3d4f6a',
  borderRadius: '8px',
  color: '#ffffff', fontSize: '14px',
  outline: 'none',
  transition: 'border-color 0.2s',
  fontFamily: 'inherit',
}

export default function RegisterPage() {
  const [firstName, setFirstName]       = useState('')
  const [lastName, setLastName]         = useState('')
  const [email, setEmail]               = useState('')
  const [password, setPassword]         = useState('')
  const [confirm, setConfirm]           = useState('')
  const [orgId, setOrgId]               = useState('')
  const [role, setRole]                 = useState('investigator')
  const [showPw, setShowPw]             = useState(false)
  const [showConfirm, setShowConfirm]   = useState(false)
  const [orgs, setOrgs]                 = useState([])
  const [error, setError]               = useState(null)
  const [loading, setLoading]           = useState(false)
  const navigate                        = useNavigate()

  const strength    = getStrength(password)
  const pwMatch     = confirm.length > 0 && password === confirm
  const pwMismatch  = confirm.length > 0 && password !== confirm
  const emailValid  = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)

  useEffect(() => {
    listOrganizations().then(setOrgs).catch(() => {})
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (password !== confirm) { setError('Passwords do not match.'); return }
    setError(null)
    setLoading(true)
    try {
      await register({
        email,
        username: `${firstName} ${lastName}`.trim(),
        password,
        organization_id: orgId,
        role,
      })
      navigate('/login')
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed.')
    } finally {
      setLoading(false)
    }
  }

  const labelStyle = {
    display: 'block',
    color: '#8a9ab8',
    fontSize: '11px',
    fontWeight: '600',
    letterSpacing: '1px',
    textTransform: 'uppercase',
    marginBottom: '7px',
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: '#2a3347',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      padding: '32px 16px',
    }}>
      <div style={{
        width: '100%',
        maxWidth: '480px',
        background: '#323d52',
        borderRadius: '16px',
        padding: '44px 40px',
        boxShadow: '0 25px 60px rgba(0,0,0,0.4)',
      }}>
        {/* Logo + Title */}
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px', marginBottom: '16px' }}>
            <div style={{
              width: '42px', height: '42px',
              background: 'rgba(96,165,250,0.15)',
              border: '1px solid rgba(96,165,250,0.4)',
              borderRadius: '10px',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '20px',
            }}>🔎</div>
            <div style={{ textAlign: 'left' }}>
              <div style={{ color: '#ffffff', fontWeight: '700', fontSize: '18px', letterSpacing: '-0.3px' }}>
                ForenSight
              </div>
              <div style={{ color: '#6b7fa3', fontSize: '10px', letterSpacing: '2px', textTransform: 'uppercase' }}>
                AI Forensics
              </div>
            </div>
          </div>
          <h1 style={{ color: '#ffffff', fontSize: '26px', fontWeight: '600', margin: '0 0 8px 0' }}>
            Create Account
          </h1>
          <p style={{ color: '#9aa8c0', fontSize: '13px', margin: 0 }}>
            Have an account already?{' '}
            <Link to="/login" style={{ color: '#60a5fa', textDecoration: 'none', fontWeight: '600' }}>
              Sign in
            </Link>
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

          {/* First + Last name row */}
          <div>
            <label style={labelStyle}>Full Name</label>
            <div style={{ display: 'flex', gap: '10px' }}>
              <input
                value={firstName} onChange={e => setFirstName(e.target.value)}
                required placeholder="First name"
                style={{ ...inputStyle, flex: 1 }}
                onFocus={e => e.target.style.borderColor = '#60a5fa'}
                onBlur={e => e.target.style.borderColor = '#3d4f6a'}
              />
              <input
                value={lastName} onChange={e => setLastName(e.target.value)}
                required placeholder="Last name"
                style={{ ...inputStyle, flex: 1 }}
                onFocus={e => e.target.style.borderColor = '#60a5fa'}
                onBlur={e => e.target.style.borderColor = '#3d4f6a'}
              />
            </div>
          </div>

          {/* Email with green tick */}
          <div>
            <label style={labelStyle}>Email</label>
            <div style={{ position: 'relative' }}>
              <input
                type="email" value={email} onChange={e => setEmail(e.target.value)}
                required placeholder="name@company.com"
                style={{
                  ...inputStyle,
                  borderColor: emailValid && email ? '#10b981' : '#3d4f6a',
                  paddingRight: '44px',
                }}
                onFocus={e => e.target.style.borderColor = emailValid ? '#10b981' : '#60a5fa'}
                onBlur={e => e.target.style.borderColor = emailValid && email ? '#10b981' : '#3d4f6a'}
              />
              {emailValid && email && (
                <div style={{
                  position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)',
                  width: '22px', height: '22px', borderRadius: '50%',
                  background: '#10b981',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: '#fff', fontSize: '12px',
                }}>✓</div>
              )}
            </div>
          </div>

          {/* Password with strength */}
          <div>
            <label style={labelStyle}>Password</label>
            <div style={{ position: 'relative' }}>
              <input
                type={showPw ? 'text' : 'password'} value={password}
                onChange={e => setPassword(e.target.value)}
                required minLength={8} placeholder="Password"
                style={{ ...inputStyle, paddingRight: '110px' }}
                onFocus={e => e.target.style.borderColor = '#60a5fa'}
                onBlur={e => e.target.style.borderColor = '#3d4f6a'}
              />
              <div style={{
                position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)',
                display: 'flex', alignItems: 'center', gap: '8px',
              }}>
                {password && (
                  <span style={{ color: strength.color, fontSize: '11px', fontWeight: '700' }}>
                    {strength.label}
                  </span>
                )}
                <button type="button" onClick={() => setShowPw(!showPw)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#6b7fa3', fontSize: '15px', padding: 0 }}>
                  {showPw ? '🙈' : '👁'}
                </button>
              </div>
            </div>
            {password && (
              <div style={{ marginTop: '6px', height: '3px', background: '#2a3347', borderRadius: '99px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: strength.width, background: strength.color, borderRadius: '99px', transition: 'width 0.3s, background 0.3s' }} />
              </div>
            )}
          </div>

          {/* Confirm password */}
          <div>
            <label style={labelStyle}>Confirm Password</label>
            <div style={{ position: 'relative' }}>
              <input
                type={showConfirm ? 'text' : 'password'} value={confirm}
                onChange={e => setConfirm(e.target.value)}
                required placeholder="Confirm password"
                style={{
                  ...inputStyle, paddingRight: '110px',
                  borderColor: pwMatch ? '#10b981' : pwMismatch ? '#ef4444' : '#3d4f6a',
                }}
                onFocus={e => e.target.style.borderColor = pwMatch ? '#10b981' : '#60a5fa'}
                onBlur={e => e.target.style.borderColor = pwMatch ? '#10b981' : pwMismatch ? '#ef4444' : '#3d4f6a'}
              />
              <div style={{
                position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)',
                display: 'flex', alignItems: 'center', gap: '8px',
              }}>
                {pwMatch && <span style={{ color: '#10b981', fontSize: '11px', fontWeight: '700' }}>correct</span>}
                {pwMismatch && <span style={{ color: '#ef4444', fontSize: '11px', fontWeight: '700' }}>mismatch</span>}
                <button type="button" onClick={() => setShowConfirm(!showConfirm)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#6b7fa3', fontSize: '15px', padding: 0 }}>
                  {showConfirm ? '🙈' : '👁'}
                </button>
              </div>
            </div>
          </div>

          {/* Organization */}
          <div>
            <label style={labelStyle}>Organization</label>
            {orgs.length > 0 ? (
              <select value={orgId} onChange={e => setOrgId(e.target.value)} required
                style={{ ...inputStyle, appearance: 'none', cursor: 'pointer', color: orgId ? '#ffffff' : '#6b7fa3' }}>
                <option value="">Select organization…</option>
                {orgs.map(o => <option key={o.id} value={o.id}>{o.name}</option>)}
              </select>
            ) : (
              <div style={{
                padding: '11px 14px',
                background: 'rgba(245,158,11,0.1)',
                border: '1.5px solid rgba(245,158,11,0.4)',
                borderRadius: '8px',
                color: '#f59e0b', fontSize: '13px',
              }}>
                No organizations found.{' '}
                <Link to="/setup" style={{ color: '#60a5fa', fontWeight: '600', textDecoration: 'none' }}>
                  Create one first →
                </Link>
              </div>
            )}
          </div>

          {/* Role */}
          <div>
            <label style={labelStyle}>Role</label>
            <select value={role} onChange={e => setRole(e.target.value)}
              style={{ ...inputStyle, appearance: 'none', cursor: 'pointer' }}>
              <option value="investigator">Investigator</option>
              <option value="admin">Admin</option>
              <option value="viewer">Viewer</option>
            </select>
          </div>

          {/* Error */}
          {error && (
            <div style={{
              background: 'rgba(239,68,68,0.1)',
              border: '1px solid rgba(239,68,68,0.4)',
              borderRadius: '8px', padding: '10px 14px',
              color: '#fca5a5', fontSize: '13px',
            }}>
              {error}
            </div>
          )}

          {/* Sign up button */}
          <button type="submit" disabled={loading}
            style={{
              width: '100%', padding: '12px',
              marginTop: '4px',
              background: loading ? '#3b6bc4' : '#4a7fe8',
              border: 'none', borderRadius: '8px',
              color: '#fff', fontSize: '14px', fontWeight: '600',
              cursor: loading ? 'not-allowed' : 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
              transition: 'background 0.2s',
              opacity: loading ? 0.8 : 1,
              fontFamily: 'inherit',
            }}
            onMouseEnter={e => { if (!loading) e.currentTarget.style.background = '#3b6bc4' }}
            onMouseLeave={e => { if (!loading) e.currentTarget.style.background = '#4a7fe8' }}
          >
            {loading && <Spinner size="sm" />}
            Sign up
          </button>
        </form>
      </div>
    </div>
  )
}
