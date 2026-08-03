import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import { Shield, Building2 } from 'lucide-react'
import { Spinner } from '../components/ui'

// Inlined from deleted organizationService
const createOrganization = (name) => api.post('/organizations/', { name }).then(r => r.data)

const OrganizationSetupPage = () => {
  const [name, setName] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await createOrganization(name)
      navigate('/register')
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Failed to create organization. Please ensure the database is running.')
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
      padding: '24px',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    }}>
      <div style={{
        width: '100%',
        maxWidth: '400px',
        background: '#323d52',
        borderRadius: '16px',
        padding: '40px 36px',
        boxShadow: '0 25px 60px rgba(0,0,0,0.4)',
      }}>
        {/* Icon + heading */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px', marginBottom: '32px' }}>
          <div style={{
            width: '56px', height: '56px',
            background: 'rgba(16,185,129,0.15)',
            border: '1px solid rgba(16,185,129,0.35)',
            borderRadius: '14px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Building2 size={26} color="#10b981" />
          </div>
          <h1 style={{ color: '#ffffff', fontSize: '22px', fontWeight: '600', margin: 0 }}>
            Create Organization
          </h1>
          <p style={{ color: '#9aa8c0', fontSize: '13px', textAlign: 'center', margin: 0, lineHeight: '1.6' }}>
            Set up your forensics team workspace before registering users.
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{
              display: 'block',
              color: '#8a9ab8',
              fontSize: '11px',
              fontWeight: '600',
              letterSpacing: '1px',
              textTransform: 'uppercase',
              marginBottom: '7px',
            }}>
              Organization Name
            </label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              minLength={2}
              placeholder="e.g. DFIR Team Alpha"
              style={{
                width: '100%',
                boxSizing: 'border-box',
                padding: '11px 14px',
                background: '#2a3347',
                border: '1.5px solid #3d4f6a',
                borderRadius: '8px',
                color: '#ffffff',
                fontSize: '14px',
                outline: 'none',
                fontFamily: 'inherit',
              }}
              onFocus={e => e.target.style.borderColor = '#60a5fa'}
              onBlur={e => e.target.style.borderColor = '#3d4f6a'}
            />
          </div>

          {error && (
            <div style={{
              background: 'rgba(239,68,68,0.1)',
              border: '1px solid rgba(239,68,68,0.4)',
              borderRadius: '8px',
              padding: '10px 14px',
              color: '#fca5a5',
              fontSize: '13px',
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '12px',
              background: loading ? '#0d9166' : '#10b981',
              border: 'none',
              borderRadius: '8px',
              color: '#ffffff',
              fontSize: '14px',
              fontWeight: '600',
              cursor: loading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              transition: 'background 0.2s',
              fontFamily: 'inherit',
            }}
            onMouseEnter={e => { if (!loading) e.currentTarget.style.background = '#0d9166' }}
            onMouseLeave={e => { if (!loading) e.currentTarget.style.background = '#10b981' }}
          >
            {loading ? <Spinner size="sm" /> : <Shield size={15} />}
            Create &amp; Continue
          </button>
        </form>
      </div>
    </div>
  )
}

export default OrganizationSetupPage
