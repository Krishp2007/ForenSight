import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { login, forgotPassword } from '../services/authService'
import useAuth from '../hooks/useAuth'
import { Spinner } from '../components/ui'
import { Shield, FileCheck, Lock, HardDrive, KeyRound, Eye, EyeOff, Search, Mail, CheckCircle2, X } from 'lucide-react'

const features = [
  { icon: Shield, text: 'Cryptographic anti-tampering evidence chain' },
  { icon: FileCheck, text: 'Court-admissible certified forensic reports' },
  { icon: Lock, text: 'Chain of Custody SHA-256 audit logging' },
  { icon: HardDrive, text: 'Encrypted S3 & MongoDB evidence vault' },
]

export default function LoginPage() {
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [showPw, setShowPw]     = useState(false)
  const [error, setError]       = useState(null)
  const [loading, setLoading]   = useState(false)
  
  // Forgot password modal state
  const [showForgotModal, setShowForgotModal] = useState(false)
  const [forgotEmail, setForgotEmail]         = useState('')
  const [forgotLoading, setForgotLoading]     = useState(false)
  const [forgotMessage, setForgotMessage]     = useState(null)
  const [forgotError, setForgotError]         = useState(null)

  const { setToken, fetchMe }  = useAuth()
  const navigate                = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const data = await login(email, password)
      setToken(data.access_token)
      await fetchMe()
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(err.response?.data?.detail || 'Incorrect email or password.')
    } finally {
      setLoading(false)
    }
  }

  const handleForgotSubmit = async (e) => {
    e.preventDefault()
    setForgotError(null)
    setForgotMessage(null)
    setForgotLoading(true)
    try {
      const res = await forgotPassword(forgotEmail)
      setForgotMessage(res.message || 'If an account with that email exists, a password reset link has been sent.')
    } catch (err) {
      setForgotError(err.response?.data?.detail || 'Failed to send password reset request. Please try again.')
    } finally {
      setForgotLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      width: '100%',
      backgroundColor: '#030712',
      backgroundImage: `linear-gradient(135deg, rgba(3, 7, 18, 0.88) 0%, rgba(15, 23, 42, 0.92) 100%), url('https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=2070&auto=format&fit=crop')`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      backgroundRepeat: 'no-repeat',
      backgroundAttachment: 'fixed',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      padding: '24px 16px',
      boxSizing: 'border-box',
    }}>
      <div className="mobile-flex-col"
        style={{
          width: '100%',
          maxWidth: '920px',
          background: 'rgba(15, 23, 42, 0.85)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          borderRadius: '20px',
          border: '1px solid rgba(59, 130, 246, 0.3)',
          overflow: 'hidden',
          display: 'flex',
          boxShadow: '0 30px 80px rgba(0, 0, 0, 0.7), 0 0 30px rgba(59, 130, 246, 0.15)',
          animation: 'dashboardFadeIn 0.4s ease-out',
        }}>

        {/* ── LEFT PANEL: Forensic Branding ── */}
        <div className="desktop-only" style={{
          width: '45%',
          background: 'linear-gradient(180deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%)',
          padding: '48px 40px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          borderRight: '1px solid rgba(51, 65, 85, 0.6)',
        }}>
          {/* Logo */}
          <div>
            <div style={{ marginBottom: '20px' }}>
              <img
                src="/logo.svg?v=7"
                alt="ForenSight AI"
                style={{ height: '48px', width: 'auto', objectFit: 'contain' }}
              />
            </div>

            <div style={{
              display: 'inline-block',
              padding: '4px 10px',
              borderRadius: '20px',
              background: 'rgba(34, 197, 94, 0.12)',
              border: '1px solid rgba(34, 197, 94, 0.3)',
              color: '#4ade80',
              fontSize: '11px',
              fontWeight: '600',
            }}>
              ● Secure Investigator Portal
            </div>
          </div>


          {/* Description */}
          <div style={{ margin: '28px 0' }}>
            <p style={{ color: '#94a3b8', fontSize: '13.5px', lineHeight: '1.7', margin: 0 }}>
              Acquire, analyze, and certify electronic evidence with cryptographic court-admissible standards. 
              Built for digital forensics teams and cyber incident responders.
            </p>
          </div>

          {/* Features */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {features.map(({ icon: Icon, text }) => (
              <div key={text} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  width: '32px', height: '32px',
                  background: 'rgba(59, 130, 246, 0.12)',
                  border: '1px solid rgba(59, 130, 246, 0.25)',
                  borderRadius: '8px',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: '#60a5fa', flexShrink: 0,
                }}>
                  <Icon size={15} />
                </div>
                <span style={{ color: '#cbd5e1', fontSize: '13px', fontWeight: '500' }}>{text}</span>
              </div>
            ))}
          </div>

          <div style={{ color: '#64748b', fontSize: '11px', marginTop: '36px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Lock size={12} /> Encrypted Session · ISO 27001 Certified
          </div>
        </div>

        {/* ── RIGHT PANEL: Sign In Form ── */}
        <div style={{
          flex: 1,
          padding: '48px 44px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          background: 'rgba(15, 23, 42, 0.6)',
        }}>
          <div style={{ marginBottom: '24px' }}>
            <h2 style={{ color: '#f8fafc', fontSize: '26px', fontWeight: '700', margin: '0 0 6px 0' }}>
              Sign In
            </h2>
            <p style={{ color: '#94a3b8', fontSize: '13px', margin: 0 }}>
              Enter your credentials to access case evidence files
            </p>
          </div>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>

            {/* Email */}
            <div>
              <label style={{
                display: 'block', color: '#94a3b8',
                fontSize: '11px', fontWeight: '700',
                letterSpacing: '1px', textTransform: 'uppercase',
                marginBottom: '7px',
              }}>Investigator Email</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                placeholder="investigator@agency.gov"
                style={{
                  width: '100%', boxSizing: 'border-box',
                  padding: '12px 14px',
                  background: '#0f172a',
                  border: '1.5px solid #334155',
                  borderRadius: '10px',
                  color: '#f8fafc', fontSize: '14px',
                  outline: 'none', transition: 'all 0.2s',
                }}
                onFocus={e => e.target.style.borderColor = '#3b82f6'}
                onBlur={e => e.target.style.borderColor = '#334155'}
              />
            </div>

            {/* Password */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '7px' }}>
                <label style={{
                  color: '#94a3b8',
                  fontSize: '11px', fontWeight: '700',
                  letterSpacing: '1px', textTransform: 'uppercase',
                }}>Password</label>
                <button
                  type="button"
                  onClick={() => {
                    setForgotEmail(email)
                    setForgotMessage(null)
                    setForgotError(null)
                    setShowForgotModal(true)
                  }}
                  style={{
                    background: 'none', border: 'none',
                    color: '#60a5fa', fontSize: '12px', fontWeight: '600',
                    cursor: 'pointer', padding: 0,
                  }}
                >
                  Forgot Password?
                </button>
              </div>
              <div style={{ position: 'relative' }}>
                <input
                  type={showPw ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                  placeholder="••••••••••••"
                  style={{
                    width: '100%', boxSizing: 'border-box',
                    padding: '12px 42px 12px 14px',
                    background: '#0f172a',
                    border: '1.5px solid #334155',
                    borderRadius: '10px',
                    color: '#f8fafc', fontSize: '14px',
                    outline: 'none', transition: 'all 0.2s',
                  }}
                  onFocus={e => e.target.style.borderColor = '#3b82f6'}
                  onBlur={e => e.target.style.borderColor = '#334155'}
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  style={{
                    position: 'absolute', right: '12px', top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'none', border: 'none',
                    color: '#64748b', cursor: 'pointer', display: 'flex', alignItems: 'center', padding: 0,
                  }}
                >
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Error */}
            {error && (
              <div style={{
                background: 'rgba(220, 38, 38, 0.12)',
                border: '1px solid rgba(220, 38, 38, 0.4)',
                borderRadius: '10px', padding: '11px 14px',
                color: '#fca5a5', fontSize: '13px', fontWeight: '500',
              }}>
                {error}
              </div>
            )}

            {/* Sign in button */}
            <button
              type="submit"
              disabled={loading}
              className="cyber-button-hover"
              style={{
                width: '100%', padding: '13px',
                marginTop: '4px',
                background: loading ? '#2563eb' : '#3b82f6',
                border: 'none', borderRadius: '10px',
                color: '#ffffff', fontSize: '14px', fontWeight: '600',
                cursor: loading ? 'not-allowed' : 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                boxShadow: '0 4px 14px rgba(59, 130, 246, 0.35)',
              }}
            >
              {loading ? <Spinner size="sm" /> : <KeyRound size={16} />}
              {loading ? 'Authenticating…' : 'Sign In'}
            </button>
          </form>

          {/* Footer links */}
          <div style={{
            textAlign: 'center', color: '#94a3b8',
            fontSize: '13px', marginTop: '28px',
            paddingTop: '20px',
            borderTop: '1px solid rgba(51, 65, 85, 0.5)',
          }}>
            Need an account?{' '}
            <Link to="/register" style={{ color: '#60a5fa', textDecoration: 'none', fontWeight: '600' }}>
              Create Account
            </Link>
            <span style={{ margin: '0 8px', color: '#475569' }}>•</span>
            <Link to="/setup" style={{ color: '#60a5fa', textDecoration: 'none', fontWeight: '600' }}>
              Setup Agency
            </Link>
          </div>
        </div>

      </div>

      {/* ── FORGOT PASSWORD MODAL ── */}
      {showForgotModal && (
        <div style={{
          position: 'fixed', inset: 0,
          background: 'rgba(3, 7, 18, 0.8)',
          backdropFilter: 'blur(8px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 1000, padding: '20px',
        }}>
          <div style={{
            width: '100%', maxWidth: '440px',
            background: '#0f172a',
            border: '1px solid rgba(59, 130, 246, 0.3)',
            borderRadius: '16px', padding: '32px',
            boxShadow: '0 20px 50px rgba(0,0,0,0.8)',
            position: 'relative',
            animation: 'dashboardFadeIn 0.3s ease-out',
          }}>
            <button
              onClick={() => setShowForgotModal(false)}
              style={{
                position: 'absolute', top: '20px', right: '20px',
                background: 'none', border: 'none', color: '#64748b',
                cursor: 'pointer', padding: '4px', display: 'flex', alignItems: 'center',
              }}
            >
              <X size={20} />
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
              <div style={{
                width: '40px', height: '40px', borderRadius: '10px',
                background: 'rgba(59, 130, 246, 0.15)',
                border: '1px solid rgba(59, 130, 246, 0.3)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: '#60a5fa',
              }}>
                <Mail size={20} />
              </div>
              <div>
                <h3 style={{ color: '#f8fafc', margin: 0, fontSize: '18px', fontWeight: '700' }}>
                  Reset Password
                </h3>
                <p style={{ color: '#94a3b8', margin: 0, fontSize: '12px' }}>
                  Send a password recovery link to your email
                </p>
              </div>
            </div>

            {forgotMessage ? (
              <div style={{ textAlign: 'center', padding: '12px 0' }}>
                <div style={{ color: '#4ade80', display: 'flex', justifyContent: 'center', marginBottom: '12px' }}>
                  <CheckCircle2 size={44} />
                </div>
                <p style={{ color: '#e2e8f0', fontSize: '14px', lineHeight: '1.6', margin: '0 0 20px 0' }}>
                  {forgotMessage}
                </p>
                <button
                  onClick={() => setShowForgotModal(false)}
                  style={{
                    width: '100%', padding: '11px',
                    background: '#3b82f6', border: 'none', borderRadius: '8px',
                    color: '#fff', fontWeight: '600', cursor: 'pointer', fontSize: '14px',
                  }}
                >
                  Back to Sign In
                </button>
              </div>
            ) : (
              <form onSubmit={handleForgotSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div>
                  <label style={{
                    display: 'block', color: '#94a3b8',
                    fontSize: '11px', fontWeight: '700',
                    letterSpacing: '1px', textTransform: 'uppercase',
                    marginBottom: '6px',
                  }}>Registered Email</label>
                  <input
                    type="email"
                    value={forgotEmail}
                    onChange={e => setForgotEmail(e.target.value)}
                    required
                    placeholder="investigator@agency.gov"
                    style={{
                      width: '100%', boxSizing: 'border-box',
                      padding: '11px 14px',
                      background: '#1e293b',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      color: '#f8fafc', fontSize: '14px', outline: 'none',
                    }}
                  />
                </div>

                {forgotError && (
                  <div style={{
                    background: 'rgba(220, 38, 38, 0.12)',
                    border: '1px solid rgba(220, 38, 38, 0.4)',
                    borderRadius: '8px', padding: '10px 12px',
                    color: '#fca5a5', fontSize: '13px',
                  }}>
                    {forgotError}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={forgotLoading}
                  style={{
                    width: '100%', padding: '12px',
                    background: forgotLoading ? '#2563eb' : '#3b82f6',
                    border: 'none', borderRadius: '8px',
                    color: '#ffffff', fontSize: '14px', fontWeight: '600',
                    cursor: forgotLoading ? 'not-allowed' : 'pointer',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                  }}
                >
                  {forgotLoading ? <Spinner size="sm" /> : <Mail size={16} />}
                  {forgotLoading ? 'Sending Link…' : 'Send Reset Link'}
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
