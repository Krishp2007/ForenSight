import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { login } from '../services/authService'
import useAuth from '../hooks/useAuth'
import Spinner from '../components/ui/Spinner'

const features = [
  { emoji: '🛡️', text: 'Anti-tampering evidence chain' },
  { emoji: '📄', text: 'Forensic report with legal value' },
  { emoji: '🔐', text: 'Certified forensic audit trail' },
  { emoji: '💾', text: 'Secure encrypted evidence storage' },
]

export default function LoginPage() {
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [showPw, setShowPw]     = useState(false)
  const [error, setError]       = useState(null)
  const [loading, setLoading]   = useState(false)
  const { setToken }            = useAuth()
  const navigate                = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const data = await login(email, password)
      setToken(data.access_token)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(err.response?.data?.detail || 'Incorrect email or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: '#2a3347',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      padding: '24px',
    }}>
      <div style={{
        width: '100%',
        maxWidth: '860px',
        background: '#323d52',
        borderRadius: '16px',
        overflow: 'hidden',
        display: 'flex',
        boxShadow: '0 25px 60px rgba(0,0,0,0.4)',
      }}>

        {/* ── LEFT PANEL ── */}
        <div style={{
          width: '42%',
          background: '#2a3347',
          padding: '48px 40px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}>
          {/* Logo */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
              <div style={{
                width: '42px', height: '42px',
                background: 'rgba(96,165,250,0.15)',
                border: '1px solid rgba(96,165,250,0.4)',
                borderRadius: '10px',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '20px',
              }}>🔎</div>
              <div>
                <div style={{ color: '#fff', fontWeight: '700', fontSize: '18px', letterSpacing: '-0.3px' }}>
                  ForenSight
                </div>
                <div style={{ color: '#6b7fa3', fontSize: '10px', letterSpacing: '2px', textTransform: 'uppercase' }}>
                  AI Forensics
                </div>
              </div>
            </div>
          </div>

          {/* Description */}
          <div style={{ margin: '32px 0' }}>
            <p style={{ color: '#9aa8c0', fontSize: '13.5px', lineHeight: '1.7', margin: 0 }}>
              ForenSight AI allows investigators to acquire, parse and certify digital evidence
              with legal value. Each investigation produces a complete forensic evidence
              package — cryptographically signed and securely stored.
            </p>
          </div>

          {/* Features */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {features.map(({ emoji, text }) => (
              <div key={text} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  width: '30px', height: '30px',
                  background: 'rgba(96,165,250,0.12)',
                  borderRadius: '8px',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '14px', flexShrink: 0,
                }}>
                  {emoji}
                </div>
                <span style={{ color: '#9aa8c0', fontSize: '13px' }}>{text}</span>
              </div>
            ))}
          </div>

          <div style={{ color: '#4a5568', fontSize: '11px', marginTop: '40px' }}>
            © 2026 ForenSight AI
          </div>
        </div>

        {/* ── RIGHT PANEL ── */}
        <div style={{
          flex: 1,
          padding: '48px 44px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
        }}>
          <h2 style={{ color: '#fff', fontSize: '26px', fontWeight: '600', margin: '0 0 28px 0' }}>
            Sign in
          </h2>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>

            {/* Email */}
            <div>
              <label style={{
                display: 'block', color: '#8a9ab8',
                fontSize: '11px', fontWeight: '600',
                letterSpacing: '1px', textTransform: 'uppercase',
                marginBottom: '7px',
              }}>Email</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                placeholder="name@company.com"
                style={{
                  width: '100%', boxSizing: 'border-box',
                  padding: '11px 14px',
                  background: '#2a3347',
                  border: '1.5px solid #4a90e2',
                  borderRadius: '8px',
                  color: '#fff', fontSize: '14px',
                  outline: 'none',
                }}
                onFocus={e => e.target.style.borderColor = '#60a5fa'}
                onBlur={e => e.target.style.borderColor = '#4a90e2'}
              />
            </div>

            {/* Password */}
            <div>
              <label style={{
                display: 'block', color: '#8a9ab8',
                fontSize: '11px', fontWeight: '600',
                letterSpacing: '1px', textTransform: 'uppercase',
                marginBottom: '7px',
              }}>Password</label>
              <div style={{ position: 'relative' }}>
                <input
                  type={showPw ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                  placeholder="Password"
                  style={{
                    width: '100%', boxSizing: 'border-box',
                    padding: '11px 40px 11px 14px',
                    background: '#2a3347',
                    border: '1.5px solid #3d4f6a',
                    borderRadius: '8px',
                    color: '#fff', fontSize: '14px',
                    outline: 'none',
                  }}
                  onFocus={e => e.target.style.borderColor = '#60a5fa'}
                  onBlur={e => e.target.style.borderColor = '#3d4f6a'}
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  style={{
                    position: 'absolute', right: '12px', top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'none', border: 'none',
                    color: '#6b7fa3', cursor: 'pointer', fontSize: '15px', padding: 0,
                  }}
                >
                  {showPw ? '🙈' : '👁'}
                </button>
              </div>
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

            {/* Sign in button */}
            <button
              type="submit"
              disabled={loading}
              style={{
                width: '100%', padding: '12px',
                marginTop: '4px',
                background: loading ? '#3b6bc4' : '#4a7fe8',
                border: 'none', borderRadius: '8px',
                color: '#fff', fontSize: '14px', fontWeight: '600',
                cursor: loading ? 'not-allowed' : 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                transition: 'background 0.2s',
              }}
              onMouseEnter={e => { if (!loading) e.target.style.background = '#3b6bc4' }}
              onMouseLeave={e => { if (!loading) e.target.style.background = '#4a7fe8' }}
            >
              {loading && <Spinner size="sm" />}
              Sign in
            </button>
          </form>

          {/* Footer links */}
          <p style={{
            textAlign: 'center', color: '#6b7fa3',
            fontSize: '12px', marginTop: '28px',
          }}>
            Don't have an account?{' '}
            <Link to="/register" style={{ color: '#60a5fa', textDecoration: 'none', fontWeight: '500' }}>
              Create account
            </Link>
            {' · '}
            <Link to="/setup" style={{ color: '#60a5fa', textDecoration: 'none', fontWeight: '500' }}>
              Setup organization
            </Link>
          </p>
        </div>

      </div>
    </div>
  )
}
