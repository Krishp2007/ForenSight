import { useState } from 'react'
import { CASE_STATUSES } from '../../utils/constants'
import { humanize } from '../../utils/formatters'
import Spinner from '../ui/Spinner'

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
    padding: '10px 14px',
    background: '#2a3347',
    border: '1.5px solid #3d4f6a',
    borderRadius: '8px',
    color: '#ffffff',
    fontSize: '13px',
    outline: 'none',
    fontFamily: 'inherit',
    transition: 'border-color 0.2s',
    resize: 'none',
  }

  const labelStyle = {
    display: 'block',
    color: '#8a9ab8',
    fontSize: '11px',
    fontWeight: '600',
    letterSpacing: '0.8px',
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
          onFocus={e => e.target.style.borderColor = '#60a5fa'}
          onBlur={e => e.target.style.borderColor = '#3d4f6a'}
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
          onFocus={e => e.target.style.borderColor = '#60a5fa'}
          onBlur={e => e.target.style.borderColor = '#3d4f6a'}
        />
      </div>
      {initial.id && (
        <div>
          <label style={labelStyle}>Status</label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            style={{ ...inputStyle, cursor: 'pointer', appearance: 'none' }}
            onFocus={e => e.target.style.borderColor = '#60a5fa'}
            onBlur={e => e.target.style.borderColor = '#3d4f6a'}
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
            padding: '8px 16px',
            fontSize: '13px',
            borderRadius: '8px',
            border: '1px solid #3d4f6a',
            background: 'transparent',
            color: '#9aa8c0',
            cursor: 'pointer',
            fontFamily: 'inherit',
            transition: 'background 0.15s, color 0.15s',
          }}
          onMouseEnter={e => { e.currentTarget.style.background = '#2a3347'; e.currentTarget.style.color = '#ffffff' }}
          onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = '#9aa8c0' }}
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={loading}
          style={{
            padding: '8px 16px',
            fontSize: '13px',
            borderRadius: '8px',
            border: 'none',
            background: loading ? '#3b6bc4' : '#4a7fe8',
            color: '#ffffff',
            cursor: loading ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontFamily: 'inherit',
            opacity: loading ? 0.7 : 1,
            transition: 'background 0.2s',
          }}
          onMouseEnter={e => { if (!loading) e.currentTarget.style.background = '#3b6bc4' }}
          onMouseLeave={e => { if (!loading) e.currentTarget.style.background = '#4a7fe8' }}
        >
          {loading && <Spinner size="sm" />}
          {initial.id ? 'Update Case' : 'Create Case'}
        </button>
      </div>
    </form>
  )
}

export default CaseForm
