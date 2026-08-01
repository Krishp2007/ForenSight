import Spinner from './Spinner'

const ConfirmModal = ({
  title, message, onConfirm, onCancel, loading,
  confirmLabel = 'Confirm',
  confirmColor = '#ef4444',
}) => (
  <div style={{
    position: 'fixed', inset: 0, zIndex: 200,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    background: 'rgba(0,0,0,0.65)', padding: '16px',
  }}>
    <div style={{
      background: '#323d52', borderRadius: '14px',
      boxShadow: '0 25px 60px rgba(0,0,0,0.5)',
      padding: '24px', width: '100%', maxWidth: '380px',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    }}>
      <h3 style={{ color: '#fff', fontSize: '15px', fontWeight: '600', margin: '0 0 8px 0' }}>{title}</h3>
      <p style={{ color: '#9aa8c0', fontSize: '13px', margin: '0 0 20px 0', lineHeight: '1.6' }}>{message}</p>
      <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
        <button onClick={onCancel} disabled={loading}
          style={{ padding: '8px 16px', fontSize: '13px', borderRadius: '8px', border: '1px solid #3d4f6a', background: 'transparent', color: '#9aa8c0', cursor: 'pointer', fontFamily: 'inherit' }}
          onMouseEnter={e => { e.currentTarget.style.background = '#2a3347'; e.currentTarget.style.color = '#fff' }}
          onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = '#9aa8c0' }}
        >Cancel</button>
        <button onClick={onConfirm} disabled={loading}
          style={{ padding: '8px 16px', fontSize: '13px', borderRadius: '8px', border: 'none', background: loading ? confirmColor + 'aa' : confirmColor, color: '#fff', cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.8 : 1, fontFamily: 'inherit', display: 'flex', alignItems: 'center', gap: '6px', transition: 'background 0.15s' }}
          onMouseEnter={e => { if (!loading) e.currentTarget.style.filter = 'brightness(0.85)' }}
          onMouseLeave={e => { e.currentTarget.style.filter = 'none' }}
        >
          {loading && <Spinner size="sm" />}
          {loading ? 'Working…' : confirmLabel}
        </button>
      </div>
    </div>
  </div>
)
export default ConfirmModal
