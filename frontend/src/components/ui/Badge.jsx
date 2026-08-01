const Badge = ({ label, colorClass }) => (
  <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wide ${colorClass}`}>
    {label}
  </span>
)

export default Badge
