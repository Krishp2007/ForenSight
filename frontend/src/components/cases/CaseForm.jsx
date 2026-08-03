import { useState } from 'react'
import { CASE_STATUSES } from '../../utils/constants'
import { humanize } from '../../utils/formatters'
import { Spinner } from '../ui'

const CaseForm = ({ initial = {}, onSubmit, onCancel, loading }) => {
  const [title, setTitle] = useState(initial.title || '')
  const [description, setDescription] = useState(initial.description || '')
  const [status, setStatus] = useState(initial.status || 'open')

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit({ title, description, status })
  }

  const inputStyle = {
    width: '100%',
    boxSizing: 'border-box',
    padding: '11px 15px',
    background: '#1e293b',
    border: '1.5px solid #334155',
    borderRadius: '10px',
    color: '#f8fafc',
    fontSize: '13.5px',
    outline: 'none',
    fontFamily: 'inherit',
    transition: 'all 0.2s ease',
    resize: 'none',
  }

  const labelStyle = {
    display: 'block',
    color: '#94a3b8',
    fontSize: '11.5px',
    fontWeight: '600',
    letterSpacing: '0.6px',
    textTransform: 'uppercase',
    marginBottom: '6px',
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div>
        <label style={labelStyle}>Title *</label>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required minLength={3} maxLength={150}
          placeholder="e.g. APT29 Phishing Investigation"
          style={inputStyle}
          onFocus={e => { e.target.style.borderColor = '#6366f1'; e.target.style.boxShadow = '0 0 12px rgba(99, 102, 241, 0.3)' }}
          onBlur={e => { e.target.style.borderColor = '#334155'; e.target.style.boxShadow = 'none' }}
        />
      </div>
      <div>
        <label style={labelStyle}>Description</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          placeholder="Optional case scope or incident details…"
          style={inputStyle}
          onFocus={e => { e.target.style.borderColor = '#6366f1'; e.target.style.boxShadow = '0 0 12px rgba(99, 102, 241, 0.3)' }}
          onBlur={e => { e.target.style.borderColor = '#334155'; e.target.style.boxShadow = 'none' }}
        />
      </div>
      {initial.id && (
        <div>
          <label style={labelStyle}>Status</label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            style={{ ...inputStyle, cursor: 'pointer', appearance: 'none' }}
            onFocus={e => { e.target.style.borderColor = '#6366f1'; e.target.style.boxShadow = '0 0 12px rgba(99, 102, 241, 0.3)' }}
            onBlur={e => { e.target.style.borderColor = '#334155'; e.target.style.boxShadow = 'none' }}
          >
            {CASE_STATUSES.map((s) => (
              <option key={s} value={s}>{humanize(s)}</option>
            ))}
          </select>
        </div>
      )}
      <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', paddingTop: '8px' }}>
        <button
          type="button"
          onClick={onCancel}
          style={{
            padding: '9px 18px',
            fontSize: '13px',
            fontWeight: '500',
            borderRadius: '10px',
            border: '1px solid #334155',
            background: 'rgba(255, 255, 255, 0.05)',
            color: '#cbd5e1',
            cursor: 'pointer',
            fontFamily: 'inherit',
            transition: 'all 0.15s ease',
          }}
          onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'; e.currentTarget.style.color = '#ffffff'; e.currentTarget.style.transform = 'translateY(-1px)' }}
          onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)'; e.currentTarget.style.color = '#cbd5e1'; e.currentTarget.style.transform = 'translateY(0)' }}
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={loading}
          style={{
            padding: '9px 20px',
            fontSize: '13px',
            fontWeight: '600',
            borderRadius: '10px',
            border: 'none',
            background: loading ? '#4f46e5' : 'linear-gradient(135deg, #6366f1, #4f46e5)',
            color: '#ffffff',
            cursor: loading ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontFamily: 'inherit',
            boxShadow: '0 4px 14px rgba(99, 102, 241, 0.4)',
            opacity: loading ? 0.7 : 1,
            transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
          }}
          onMouseEnter={e => { if (!loading) { e.currentTarget.style.boxShadow = '0 8px 24px rgba(99, 102, 241, 0.65)'; e.currentTarget.style.transform = 'translateY(-2px)' } }}
          onMouseLeave={e => { if (!loading) { e.currentTarget.style.boxShadow = '0 4px 14px rgba(99, 102, 241, 0.4)'; e.currentTarget.style.transform = 'translateY(0)' } }}
        >
          {loading && <Spinner size="sm" />}
          {initial.id ? 'Update Case' : 'Create Case'}
        </button>

      </div>
    </form>
  )
}

export default CaseForm


