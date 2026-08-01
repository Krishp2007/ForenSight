const Spinner = ({ size = 'md' }) => {
  const sz = size === 'sm' ? 'h-4 w-4' : size === 'lg' ? 'h-10 w-10' : 'h-6 w-6'
  return (
    <div className={`inline-block ${sz} animate-spin rounded-full border-2 border-gray-300 border-t-blue-600`} />
  )
}

export default Spinner
