const EmptyState = ({ icon: Icon, title, description }) => (
  <div style={{
    display: 'flex', flexDirection: 'column', alignItems: 'center',
    justifyContent: 'center', padding: '64px 16px', gap: '12px',
  }}>
    {Icon && <Icon size={40} strokeWidth={1.2} color="#3d4f6a" />}
    <p style={{ color: '#6b7fa3', fontSize: '15px', fontWeight: '500', margin: 0 }}>{title}</p>
    {description && (
      <p style={{ color: '#4a5568', fontSize: '13px', textAlign: 'center', maxWidth: '280px', margin: 0, lineHeight: '1.6' }}>
        {description}
      </p>
    )}
  </div>
)
export default EmptyState
