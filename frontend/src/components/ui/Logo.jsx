import React from 'react'

export default function Logo({ size = 'md', className = '' }) {
  const heightMap = { sm: '28px', md: '36px', lg: '48px', xl: '56px' }
  const h = heightMap[size] || '36px'

  return (
    <img
      src="/logo.svg?v=7"
      alt="ForenSight"
      className={className}
      style={{ height: h, width: 'auto', objectFit: 'contain', display: 'block' }}
    />
  )
}
