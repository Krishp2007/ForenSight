import { useState } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { resetPassword } from '../services/authService'
import { Spinner } from '../components/ui'
import { KeyRound, Eye, EyeOff, CheckCircle2, AlertCircle, Lock, Shield } from 'lucide-react'

export default function ResetPasswordPage() {
  const [searchParams]          = useSearchParams()
  const token                   = searchParams.get('token')
  const navigate                = useNavigate()

  const [password, setPassword]       = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPw, setShowPw]           = useState(false)
  const [showConfirmPw, setShowConfirmPw] = useState(false)
  const [loading, setLoading]         = useState(false)
  const [error, setError]             = useState(null)
  const [success, setSuccess]         = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    if (!token) {
      setError('Missing or invalid password reset token in URL. Please click the reset link in your email.')
      return
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long.')
      return
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match. Please re-enter your new password.')
      return
    }

    setLoading(true)
    try {
      await resetPassword(token, password)
      setSuccess(true)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to reset password. The link may have expired.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      width: '100vw',
      backgroundImage: `linear-gradient(135deg, rgba(3, 7, 18, 0.88) 0%, rgba(15, 23, 42, 0.92) 100%), url('https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=2070&auto=format&fit=crop')`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      padding: '24px',
      boxSizing: 'border-box',
    }}>
      <div style={{
        width: '100%',
        maxWidth: '460px',
        background: 'rgba(15, 23, 42, 0.85)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        borderRadius: '20px',
        border: '1px solid rgba(59, 130, 246, 0.3)',
        padding: '40px 36px',
        boxShadow: '0 30px 80px rgba(0, 0, 0, 0.7), 0 0 30px rgba(59, 130, 246, 0.15)',
        animation: 'dashboardFadeIn 0.4s ease-out',
      }}>
        {/* Header / Branding */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <img
            src="/logo.svg?v=7"
            alt="ForenSight AI"
            style={{ height: '44px', width: 'auto', marginBottom: '16px', objectFit: 'contain' }}
          />
          <h2 style={{ color: '#f8fafc', fontSize: '24px', fontWeight: '700', margin: '0 0 6px 0' }}>
            Set New Password
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '13px', margin: 0 }}>
            Enter your new secure password to update your account
          </p>
        </div>

        {/* Missing Token Warning */}
        {!token && !success && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            borderRadius: '10px', padding: '14px',
            color: '#fca5a5', fontSize: '13px', lineHeight: '1.5',
            display: 'flex', gap: '10px', alignItems: 'flex-start',
            marginBottom: '20px',
          }}>
            <AlertCircle size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <strong>Missing Token:</strong> No valid password reset token was detected in your link. Please check your email or request a new reset link on the sign in page.
            </div>
          </div>
        )}

        {/* Success State */}
        {success ? (
          <div style={{ textAlign: 'center', padding: '12px 0' }}>
            <div style={{ color: '#4ade80', display: 'flex', justifyContent: 'center', marginBottom: '16px' }}>
              <CheckCircle2 size={52} />
            </div>
            <h3 style={{ color: '#f8fafc', fontSize: '18px', fontWeight: '700', margin: '0 0 8px 0' }}>
              Password Reset Complete!
            </h3>
            <p style={{ color: '#94a3b8', fontSize: '13.5px', lineHeight: '1.6', margin: '0 0 24px 0' }}>
              Your account password has been permanently updated in the ForenSight vault. You can now log in with your new credentials.
            </p>
            <button
              onClick={() => navigate('/login', { replace: true })}
              style={{
                width: '100%', padding: '13px',
                background: '#3b82f6', border: 'none', borderRadius: '10px',
                color: '#ffffff', fontSize: '14px', fontWeight: '600',
                cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                boxShadow: '0 4px 14px rgba(59, 130, 246, 0.35)',
              }}
            >
              <KeyRound size={16} /> Proceed to Sign In
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>

            {/* New Password */}
            <div>
              <label style={{
                display: 'block', color: '#94a3b8',
                fontSize: '11px', fontWeight: '700',
                letterSpacing: '1px', textTransform: 'uppercase',
                marginBottom: '7px',
              }}>New Password</label>
              <div style={{ position: 'relative' }}>
                <input
                  type={showPw ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                  placeholder="At least 8 characters"
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

            {/* Confirm Password */}
            <div>
              <label style={{
                display: 'block', color: '#94a3b8',
                fontSize: '11px', fontWeight: '700',
                letterSpacing: '1px', textTransform: 'uppercase',
                marginBottom: '7px',
              }}>Confirm New Password</label>
              <div style={{ position: 'relative' }}>
                <input
                  type={showConfirmPw ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={e => setConfirmPassword(e.target.value)}
                  required
                  placeholder="Re-enter new password"
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
                  onClick={() => setShowConfirmPw(!showConfirmPw)}
                  style={{
                    position: 'absolute', right: '12px', top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'none', border: 'none',
                    color: '#64748b', cursor: 'pointer', display: 'flex', alignItems: 'center', padding: 0,
                  }}
                >
                  {showConfirmPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Error Banner */}
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

            {/* Reset Button */}
            <button
              type="submit"
              disabled={loading || !token}
              style={{
                width: '100%', padding: '13px',
                marginTop: '4px',
                background: (loading || !token) ? '#2563eb' : '#3b82f6',
                border: 'none', borderRadius: '10px',
                color: '#ffffff', fontSize: '14px', fontWeight: '600',
                cursor: (loading || !token) ? 'not-allowed' : 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                boxShadow: '0 4px 14px rgba(59, 130, 246, 0.35)',
                opacity: (!token) ? 0.6 : 1,
              }}
            >
              {loading ? <Spinner size="sm" /> : <Lock size={16} />}
              {loading ? 'Updating Password…' : 'Update Password'}
            </button>

            <div style={{ textAlign: 'center', marginTop: '12px' }}>
              <Link to="/login" style={{ color: '#60a5fa', fontSize: '13px', textDecoration: 'none', fontWeight: '600' }}>
                Cancel & Return to Sign In
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
