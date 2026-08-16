import { useState, useEffect } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { register } from '../services/authService'
import api from '../services/api'
import { Spinner } from '../components/ui'
import {
  ShieldCheck, UserPlus, Eye, EyeOff, Check, AlertCircle,
  Building, Shield, Lock, Link as LinkIcon, Key, ArrowRight
} from 'lucide-react'

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
  width: '100%',
  boxSizing: 'border-box',
  padding: '12px 14px',
  background: '#0f172a',
  border: '1.5px solid #334155',
  borderRadius: '10px',
  color: '#f8fafc',
  fontSize: '14px',
  outline: 'none',
  transition: 'all 0.2s ease',
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
  const [searchParams, setSearchParams] = useSearchParams()
  const inviteToken = searchParams.get('invite') || ''

  const [manualToken, setManualToken] = useState('')
  const [firstName, setFirstName]     = useState('')
  const [lastName, setLastName]       = useState('')
  const [email, setEmail]             = useState('')
  const [password, setPassword]       = useState('')
  const [confirm, setConfirm]         = useState('')

  const [inviteData, setInviteData]             = useState(null)
  const [validatingInvite, setValidatingInvite] = useState(false)
  const [inviteError, setInviteError]           = useState(null)

  const [showPw, setShowPw]           = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [error, setError]             = useState(null)
  const [loading, setLoading]         = useState(false)
  const navigate                      = useNavigate()

  const strength   = getStrength(password)
  const pwMatch    = confirm.length > 0 && password === confirm
  const pwMismatch = confirm.length > 0 && password !== confirm
  const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)

  // Validate invite token whenever it changes
  useEffect(() => {
    if (!inviteToken) {
      setInviteData(null)
      setInviteError(null)
      setValidatingInvite(false)
      return
    }

    setValidatingInvite(true)
    setInviteError(null)

    api.get(`/invites/validate?token=${encodeURIComponent(inviteToken)}`)
      .then(r => {
        if (r.data.valid) {
          setInviteData(r.data)
          setInviteError(null)
          if (r.data.target_email) {
            setEmail(r.data.target_email)
          }
        } else {
          setInviteData(null)
          setInviteError(r.data.error || 'Invite link is invalid or expired.')
        }
      })
      .catch(err => {
        setInviteData(null)
        setInviteError(err?.response?.data?.detail || 'Failed to validate invite link.')
      })
      .finally(() => setValidatingInvite(false))
  }, [inviteToken])

  const handleApplyManualToken = (e) => {
    e.preventDefault()
    if (!manualToken.trim()) return
    setSearchParams({ invite: manualToken.trim() })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (password !== confirm) {
      setError('Passwords do not match.')
      return
    }
    if (!inviteData) {
      setError('A valid Admin Invite Link is required to register.')
      return
    }

    setError(null)
    setLoading(true)
    try {
      await register({
        email,
        username: `${firstName} ${lastName}`.trim(),
        password,
        invite_token: inviteToken,
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
      width: '100%',
      backgroundColor: '#030712',
      backgroundImage: `linear-gradient(135deg, rgba(3, 7, 18, 0.92) 0%, rgba(15, 23, 42, 0.95) 100%), url('https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?q=80&w=2070&auto=format&fit=crop')`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      backgroundRepeat: 'no-repeat',
      backgroundAttachment: 'fixed',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      padding: '32px 16px',
      boxSizing: 'border-box',
    }}>
      <div style={{
        width: '100%',
        maxWidth: '500px',
        background: 'rgba(15, 23, 42, 0.9)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderRadius: '24px',
        border: '1px solid rgba(59, 130, 246, 0.25)',
        padding: '40px 36px',
        boxShadow: '0 30px 80px rgba(0,0,0,0.75), 0 0 40px rgba(59, 130, 246, 0.12)',
        animation: 'dashboardModalPop 0.3s ease-out',
      }}>
        {/* Top Header */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '16px' }}>
            <img
              src="/logo.svg?v=7"
              alt="ForenSight AI"
              style={{ height: '46px', width: 'auto', objectFit: 'contain' }}
            />
          </div>

          <h1 style={{ color: '#f8fafc', fontSize: '24px', fontWeight: '700', margin: '0 0 6px 0', letterSpacing: '-0.3px' }}>
            {inviteData ? 'Join ForenSight Agency' : 'Investigator Registration'}
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '13px', margin: 0 }}>
            Already have an account?{' '}
            <Link to="/login" style={{ color: '#60a5fa', textDecoration: 'none', fontWeight: '600' }}>
              Sign In
            </Link>
          </p>
        </div>

        {/* ── CASE 1: Validating Token Loader ── */}
        {validatingInvite && (
          <div style={{
            padding: '32px',
            background: 'rgba(30, 41, 59, 0.5)',
            borderRadius: '16px',
            border: '1px solid rgba(59, 130, 246, 0.2)',
            textAlign: 'center',
            color: '#94a3b8',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '12px',
            marginBottom: '20px'
          }}>
            <Spinner size="md" />
            <span style={{ fontSize: '13.5px', fontWeight: '500' }}>Validating Admin invite link…</span>
          </div>
        )}

        {/* ── CASE 2: Verified Invite Banner ── */}
        {!validatingInvite && inviteData && (
          <div style={{
            background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.15) 0%, rgba(30, 58, 138, 0.25) 100%)',
            border: '1px solid rgba(59, 130, 246, 0.4)',
            borderRadius: '16px',
            padding: '16px 20px',
            marginBottom: '24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px',
            boxShadow: '0 4px 20px rgba(37, 99, 235, 0.15)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
              <div style={{
                width: '42px', height: '42px', borderRadius: '12px',
                background: 'rgba(59, 130, 246, 0.2)',
                border: '1px solid rgba(59, 130, 246, 0.4)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: '#60a5fa', flexShrink: 0
              }}>
                <Building size={22} />
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#60a5fa', fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  <ShieldCheck size={13} /> Verified Organization
                </div>
                <div style={{ color: '#ffffff', fontSize: '15px', fontWeight: '700', marginTop: '2px' }}>
                  {inviteData.organization_name}
                </div>
              </div>
            </div>
            <div style={{
              background: 'rgba(56, 189, 248, 0.15)',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              borderRadius: '20px',
              padding: '4px 12px',
              color: '#38bdf8',
              fontSize: '12px',
              fontWeight: '700',
              textTransform: 'capitalize',
              whiteSpace: 'nowrap'
            }}>
              {inviteData.role}
            </div>
          </div>
        )}

        {/* ── CASE 3: Invalid / Expired Invite Error ── */}
        {!validatingInvite && inviteError && (
          <div style={{
            background: 'rgba(220, 38, 38, 0.1)',
            border: '1px solid rgba(220, 38, 38, 0.35)',
            borderRadius: '16px',
            padding: '18px 20px',
            color: '#fca5a5',
            fontSize: '13px',
            marginBottom: '24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '10px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: '700', fontSize: '14px', color: '#ef4444' }}>
              <AlertCircle size={18} /> Invalid or Expired Invite Link
            </div>
            <div style={{ color: '#cbd5e1', lineHeight: '1.5' }}>
              {inviteError}
            </div>
            <div style={{ borderTop: '1px solid rgba(220, 38, 38, 0.2)', paddingTop: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <button
                onClick={() => setSearchParams({})}
                style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: '12px', cursor: 'pointer', padding: 0, textDecoration: 'underline' }}
              >
                Clear Token
              </button>
              <Link to="/setup" style={{ color: '#60a5fa', textDecoration: 'none', fontWeight: '600', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                Register New Agency <ArrowRight size={13} />
              </Link>
            </div>
          </div>
        )}

        {/* ── CASE 4: No Token in URL (Prompt to Enter Code or Create Agency) ── */}
        {!validatingInvite && !inviteToken && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '18px', marginBottom: '24px' }}>
            {/* Invite Token Code Input */}
            <div style={{
              background: 'rgba(30, 41, 59, 0.6)',
              border: '1px solid rgba(51, 65, 85, 0.8)',
              borderRadius: '16px',
              padding: '20px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#f8fafc', fontSize: '14px', fontWeight: '600', marginBottom: '6px' }}>
                <Key size={16} color="#60a5fa" /> Have an Invite Code?
              </div>
              <p style={{ color: '#94a3b8', fontSize: '12.5px', margin: '0 0 14px 0', lineHeight: '1.5' }}>
                Paste the invite token provided by your agency administrator to unlock registration.
              </p>
              <form onSubmit={handleApplyManualToken} style={{ display: 'flex', gap: '8px' }}>
                <input
                  type="text"
                  value={manualToken}
                  onChange={e => setManualToken(e.target.value)}
                  placeholder="Paste invite token here..."
                  style={{ ...inputStyle, flex: 1, padding: '10px 12px', fontSize: '13px' }}
                />
                <button
                  type="submit"
                  disabled={!manualToken.trim()}
                  style={{
                    padding: '10px 16px',
                    background: manualToken.trim() ? '#3b82f6' : '#1e293b',
                    border: 'none',
                    borderRadius: '10px',
                    color: '#ffffff',
                    fontSize: '13px',
                    fontWeight: '600',
                    cursor: manualToken.trim() ? 'pointer' : 'not-allowed',
                    whiteSpace: 'nowrap',
                    transition: 'background 0.2s',
                    opacity: manualToken.trim() ? 1 : 0.6
                  }}
                >
                  Verify Token
                </button>
              </form>
            </div>

            {/* Create Agency Option */}
            <div style={{
              background: 'rgba(15, 23, 42, 0.5)',
              border: '1px dashed rgba(99, 102, 241, 0.3)',
              borderRadius: '16px',
              padding: '18px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '12px'
            }}>
              <div>
                <div style={{ color: '#f8fafc', fontSize: '13.5px', fontWeight: '600' }}>
                  Starting a new forensic agency?
                </div>
                <div style={{ color: '#94a3b8', fontSize: '12px', marginTop: '2px' }}>
                  Create your workspace and receive an Admin invite.
                </div>
              </div>
              <Link
                to="/setup"
                style={{
                  padding: '9px 14px',
                  background: 'rgba(99, 102, 241, 0.15)',
                  border: '1px solid rgba(99, 102, 241, 0.4)',
                  borderRadius: '10px',
                  color: '#818cf8',
                  fontSize: '12.5px',
                  fontWeight: '600',
                  textDecoration: 'none',
                  whiteSpace: 'nowrap',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                Create Agency <ArrowRight size={14} />
              </Link>
            </div>
          </div>
        )}

        {/* ── REGISTRATION FORM (Only shown when invite is valid) ── */}
        {!validatingInvite && inviteData && (
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

            {/* Full Name */}
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

            {/* Email Address */}
            <div>
              <label style={labelStyle}>Email Address</label>
              <div style={{ position: 'relative' }}>
                <input
                  type="email" value={email} onChange={e => setEmail(e.target.value)}
                  required placeholder="investigator@agency.gov"
                  disabled={!!inviteData?.target_email}
                  style={{
                    ...inputStyle,
                    borderColor: emailValid && email ? '#22c55e' : '#334155',
                    paddingRight: '44px',
                    opacity: inviteData?.target_email ? 0.75 : 1
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

            {/* Confirm Password */}
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

            {/* Form Error Message */}
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

            {/* Submit Button */}
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
                transition: 'background 0.2s',
              }}
            >
              {loading ? <Spinner size="sm" /> : <UserPlus size={16} />}
              {loading ? 'Creating Account…' : 'Complete Account Registration'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
