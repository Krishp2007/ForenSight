import { Sun, Moon, Zap } from 'lucide-react'
import useTheme from '../../hooks/useTheme'

export const ThemeToggle = ({ compact = false }) => {
  const { theme, setTheme } = useTheme()

  const modes = [
    { id: 'light', label: 'Light', icon: Sun },
    { id: 'dark', label: 'Dark', icon: Moon },
    { id: 'cyber', label: 'Cyber', icon: Zap },
  ]

  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      padding: '3px',
      borderRadius: '12px',
      background: 'var(--forensic-card-bg, rgba(30, 41, 59, 0.6))',
      border: '1px solid var(--forensic-border, rgba(255, 255, 255, 0.12))',
      gap: '3px',
    }}>
      {modes.map((m) => {
        const Icon = m.icon
        const isActive = theme === m.id
        return (
          <button
            key={m.id}
            onClick={() => setTheme(m.id)}
            title={`Switch to ${m.label} theme`}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: compact ? '0' : '5px',
              padding: compact ? '6px' : '5px 10px',
              borderRadius: '9px',
              border: 'none',
              fontSize: '11.5px',
              fontWeight: '700',
              cursor: 'pointer',
              background: isActive 
                ? 'var(--forensic-primary, #2563eb)' 
                : 'transparent',
              color: isActive ? '#ffffff' : 'var(--forensic-text-muted, #94a3b8)',
              boxShadow: isActive ? '0 2px 8px rgba(37, 99, 235, 0.3)' : 'none',
              transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
              fontFamily: 'inherit',
            }}
          >
            <Icon size={14} />
            {!compact && <span>{m.label}</span>}
          </button>
        )
      })}
    </div>
  )
}

export default ThemeToggle
