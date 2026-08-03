import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { register } from '../services/authService'
import api from '../services/api'
import { Spinner } from '../components/ui'
import { ShieldCheck, UserPlus, Eye, EyeOff, Check, AlertCircle, Building, Shield } from 'lucide-react'



const listOrganizations = () => api.get('/organizations/').then(r => r.data)

const getStrength = (pw) => {
  if (!pw) return { label: '', color: '#ccc', width: '0%' }
  let score = 0
  if (pw.length >= 8)          score++
  if (/[A-Z]/.test(pw))        score++
  if (/[0-9]/.test(pw))        score++
  if (/[^A-Za-z0-9]/.test(pw)) score++
  if (pw.length >= 12)         score++
  if (score <= 1) return { label: 'weak',   color: '#ef4444', width: '25%' }
  if (score === 2) return { label: 'fair',   color: '#f59e0b', width: '50%' }
  if (score === 3) return { label: 'good',   color: '#3b82f6', width: '75%' }
  return           { label: 'strong', color: '#22c55e', width: '100%' }
}

const inputStyle = {
  width: '100%', boxSizing: 'border-box',
  padding: '12px 14px',
  background: '#0f172a',
  border: '1.5px solid #334155',
  borderRadius: '10px',
  color: '#f8fafc', fontSize: '14px',
  outline: 'none',
  transition: 'border-color 0.2s',
  fontFamily: 'inherit',
}

const labelStyle = {
  display: 'block',
  color: '#94a3b8',
  fontSize: '11px',
  fontWeight: '700',
  letterSpacing: '1px',
  textTransform: 'uppercase',
  marginBottom: '7px',
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

  return (
    <div style={{
      minHeight: '100vh',
      width: '100vw',
      backgroundImage: `linear-gradient(135deg, rgba(3, 7, 18, 0.9) 0%, rgba(15, 23, 42, 0.92) 100%), url('https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?q=80&w=2070&auto=format&fit=crop')`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      padding: '32px 16px',
      boxSizing: 'border-box',
    }}>
      <div style={{
        width: '100%',
        maxWidth: '520px',
        background: 'rgba(15, 23, 42, 0.88)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        borderRadius: '20px',
        border: '1px solid rgba(59, 130, 246, 0.3)',
        padding: '44px 40px',
        boxShadow: '0 30px 80px rgba(0,0,0,0.7), 0 0 30px rgba(59, 130, 246, 0.15)',
        animation: 'dashboardModalPop 0.3s ease-out',
      }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>

          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '16px' }}>
            <img
              src="/logo.svg?v=7"
              alt="ForenSight AI"
              style={{ height: '48px', width: 'auto', objectFit: 'contain' }}
            />
          </div>











          <h1 style={{ color: '#f8fafc', fontSize: '26px', fontWeight: '700', margin: '0 0 6px 0' }}>
            Create Investigator Account
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '13px', margin: 0 }}>
            Already registered?{' '}
            <Link to="/login" style={{ color: '#60a5fa', textDecoration: 'none', fontWeight: '600' }}>
              Sign In
            </Link>
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

          {/* Full name */}
          <div>
            <label style={labelStyle}>Full Name</label>
            <div style={{ display: 'flex', gap: '10px' }}>
              <input
                value={firstName} onChange={e => setFirstName(e.target.value)}
                required placeholder="First name"
                style={{ ...inputStyle, flex: 1 }}
                onFocus={e => e.target.style.borderColor = '#3b82f6'}
                onBlur={e => e.target.style.borderColor = '#334155'}
              />
              <input
                value={lastName} onChange={e => setLastName(e.target.value)}
                required placeholder="Last name"
                style={{ ...inputStyle, flex: 1 }}
                onFocus={e => e.target.style.borderColor = '#3b82f6'}
                onBlur={e => e.target.style.borderColor = '#334155'}
              />
            </div>
          </div>

          {/* Email with validation tick */}
          <div>
            <label style={labelStyle}>Investigator Email</label>
            <div style={{ position: 'relative' }}>
              <input
                type="email" value={email} onChange={e => setEmail(e.target.value)}
                required placeholder="investigator@agency.gov"
                style={{
                  ...inputStyle,
                  borderColor: emailValid && email ? '#22c55e' : '#334155',
                  paddingRight: '44px',
                }}
                onFocus={e => e.target.style.borderColor = emailValid ? '#22c55e' : '#3b82f6'}
                onBlur={e => e.target.style.borderColor = emailValid && email ? '#22c55e' : '#334155'}
              />
              {emailValid && email && (
                <div style={{
                  position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)',
                  width: '22px', height: '22px', borderRadius: '50%',
                  background: '#22c55e',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: '#fff',
                }}>
                  <Check size={14} />
                </div>
              )}
            </div>
          </div>

          {/* Password */}
          <div>
            <label style={labelStyle}>Password</label>
            <div style={{ position: 'relative' }}>
              <input
                type={showPw ? 'text' : 'password'} value={password}
                onChange={e => setPassword(e.target.value)}
                required minLength={8} placeholder="Password (min 8 chars)"
                style={{ ...inputStyle, paddingRight: '110px' }}
                onFocus={e => e.target.style.borderColor = '#3b82f6'}
                onBlur={e => e.target.style.borderColor = '#334155'}
              />
              <div style={{
                position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)',
                display: 'flex', alignItems: 'center', gap: '8px',
              }}>
                {password && (
                  <span style={{ color: strength.color, fontSize: '11px', fontWeight: '700', textTransform: 'uppercase' }}>
                    {strength.label}
                  </span>
                )}
                <button type="button" onClick={() => setShowPw(!showPw)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b', display: 'flex', alignItems: 'center', padding: 0 }}>
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
            {password && (
              <div style={{ marginTop: '6px', height: '4px', background: '#1e293b', borderRadius: '99px', overflow: 'hidden' }}>
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
                required placeholder="Re-enter password"
                style={{
                  ...inputStyle, paddingRight: '110px',
                  borderColor: pwMatch ? '#22c55e' : pwMismatch ? '#dc2626' : '#334155',
                }}
                onFocus={e => e.target.style.borderColor = pwMatch ? '#22c55e' : '#3b82f6'}
                onBlur={e => e.target.style.borderColor = pwMatch ? '#22c55e' : pwMismatch ? '#dc2626' : '#334155'}
              />
              <div style={{
                position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)',
                display: 'flex', alignItems: 'center', gap: '8px',
              }}>
                {pwMatch && <span style={{ color: '#22c55e', fontSize: '11px', fontWeight: '700' }}>Match</span>}
                {pwMismatch && <span style={{ color: '#dc2626', fontSize: '11px', fontWeight: '700' }}>Mismatch</span>}
                <button type="button" onClick={() => setShowConfirm(!showConfirm)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b', display: 'flex', alignItems: 'center', padding: 0 }}>
                  {showConfirm ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
          </div>

          {/* Organization */}
          <div>
            <label style={labelStyle}>Assigned Agency / Organization</label>
            {orgs.length > 0 ? (
              <select value={orgId} onChange={e => setOrgId(e.target.value)} required
                style={{ ...inputStyle, appearance: 'none', cursor: 'pointer', color: orgId ? '#f8fafc' : '#64748b' }}>
                <option value="">Select forensic agency…</option>
                {orgs.map(o => <option key={o.id} value={o.id}>{o.name}</option>)}
              </select>
            ) : (
              <div style={{
                padding: '11px 14px',
                background: 'rgba(234, 179, 8, 0.1)',
                border: '1.5px solid rgba(234, 179, 8, 0.4)',
                borderRadius: '10px',
                color: '#fbbf24', fontSize: '13px',
                display: 'flex', alignItems: 'center', gap: '8px',
              }}>
                <Building size={16} /> No agencies found.{' '}
                <Link to="/setup" style={{ color: '#60a5fa', fontWeight: '600', textDecoration: 'none' }}>
                  Create agency →
                </Link>
              </div>
            )}
          </div>

          {/* Role */}
          <div>
            <label style={labelStyle}>Forensic Role</label>
            <select value={role} onChange={e => setRole(e.target.value)}
              style={{ ...inputStyle, appearance: 'none', cursor: 'pointer' }}>
              <option value="investigator">Investigator (Full Case Access)</option>
              <option value="admin">Admin (System & User Manager)</option>
              <option value="viewer">Viewer (Read-Only Forensic Audit)</option>
            </select>
          </div>

          {/* Error */}
          {error && (
            <div style={{
              background: 'rgba(220, 38, 38, 0.12)',
              border: '1px solid rgba(220, 38, 38, 0.4)',
              borderRadius: '10px', padding: '11px 14px',
              color: '#fca5a5', fontSize: '13px', fontWeight: '500',
              display: 'flex', alignItems: 'center', gap: '8px',
            }}>
              <AlertCircle size={16} /> {error}
            </div>
          )}

          {/* Submit button */}
          <button
            type="submit"
            disabled={loading}
            className="cyber-button-hover"
            style={{
              width: '100%', padding: '13px',
              marginTop: '6px',
              background: loading ? '#2563eb' : '#3b82f6',
              border: 'none', borderRadius: '10px',
              color: '#ffffff', fontSize: '14px', fontWeight: '600',
              cursor: loading ? 'not-allowed' : 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
              boxShadow: '0 4px 14px rgba(59, 130, 246, 0.35)',
              fontFamily: 'inherit',
            }}
          >
            {loading ? <Spinner size="sm" /> : <UserPlus size={16} />}
            {loading ? 'Creating Account…' : 'Create Account'}
          </button>
        </form>
      </div>
    </div>
  )
}
