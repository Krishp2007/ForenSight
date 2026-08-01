const EmptyState = ({ icon: Icon, title, description }) => (
  <div className="flex flex-col items-center justify-center py-16 text-gray-400 gap-3">
    {Icon && <Icon size={40} strokeWidth={1.2} />}
    <p className="text-base font-medium text-gray-500">{title}</p>
    {description && <p className="text-sm text-center max-w-xs">{description}</p>}
  </div>
)

export default EmptyState
