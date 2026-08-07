import React from 'react'

export const BrandLogo = ({ height = 32, className = '' }) => {
  return (
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      viewBox="0 0 460 155" 
      style={{ height: `${height}px`, width: 'auto', display: 'block' }}
      className={className}
    >
      <defs>
        {/* Neon Violet to Electric Indigo Gradient for NSIGHT */}
        <linearGradient id="violetIndigoGrad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#A855F7" />
          <stop offset="100%" stopColor="#6366F1" />
        </linearGradient>

        {/* Underline Gradient */}
        <linearGradient id="violetLineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#A855F7" strokeOpacity="0.9" />
          <stop offset="70%" stopColor="#6366F1" strokeOpacity="1" />
          <stop offset="100%" stopColor="#4F46E5" strokeOpacity="1" />
        </linearGradient>
      </defs>

      <g transform="translate(15, 12)">
        {/* Wordmark Group */}
        <g transform="translate(0, 0)">
          {/* F (Theme Adaptive FORE text color) */}
          <path d="M 10 10 H 42 V 22 H 24 V 38 H 38 V 50 H 24 V 80 H 10 V 10 Z" fill="var(--logo-fore-color, currentColor)" />

          {/* O */}
          <path d="M 48 10 H 84 V 80 H 48 V 10 Z M 62 22 V 68 H 70 V 22 H 62 Z" fill="var(--logo-fore-color, currentColor)" />

          {/* R */}
          <path d="M 90 10 H 126 V 46 H 114 L 128 80 H 112 L 100 48 H 104 V 80 H 90 V 10 Z M 104 22 V 36 H 112 V 22 H 104 Z" fill="var(--logo-fore-color, currentColor)" />

          {/* E (Stylized Triple Horizontal Bars) */}
          <rect x="132" y="10" width="30" height="11" fill="var(--logo-fore-color, currentColor)" rx="2" />
          <rect x="132" y="34.5" width="25" height="11" fill="var(--logo-fore-color, currentColor)" rx="2" />
          <rect x="132" y="59" width="30" height="11" fill="var(--logo-fore-color, currentColor)" rx="2" />

          {/* N (Violet to Indigo) */}
          <path d="M 172 10 H 184 L 206 55 V 10 H 218 V 80 H 206 L 184 35 V 80 H 172 V 10 Z" fill="url(#violetIndigoGrad)" />

          {/* S (Violet to Indigo) */}
          <path d="M 224 10 H 260 V 25 H 238 V 36 H 260 V 80 H 224 V 65 H 246 V 51 H 224 V 10 Z" fill="url(#violetIndigoGrad)" />

          {/* I (Violet to Indigo) */}
          <path d="M 266 10 H 278 V 80 H 266 V 10 Z" fill="url(#violetIndigoGrad)" />

          {/* G (Violet to Indigo) */}
          <path d="M 284 10 H 320 V 25 H 298 V 65 H 320 V 48 H 308 V 36 H 332 V 80 H 284 V 10 Z" fill="url(#violetIndigoGrad)" />

          {/* H (Violet to Indigo) */}
          <path d="M 338 10 H 350 V 39 H 368 V 10 H 380 V 80 H 368 V 51 H 350 V 80 H 338 V 10 Z" fill="url(#violetIndigoGrad)" />

          {/* T (Violet to Indigo) */}
          <path d="M 386 10 H 428 V 22 H 413 V 80 H 401 V 22 H 386 V 10 Z" fill="url(#violetIndigoGrad)" />
        </g>

        {/* Underline Trace with Node Terminal */}
        <g transform="translate(10, 94)">
          <line x1="0" y1="0" x2="390" y2="0" stroke="url(#violetLineGrad)" strokeWidth="3" strokeLinecap="round" />
          <line x1="390" y1="0" x2="402" y2="0" stroke="#6366F1" strokeWidth="2.5" />
          <circle cx="402" cy="0" r="4.5" fill="#6366F1" />
          <line x1="402" y1="0" x2="415" y2="0" stroke="#6366F1" strokeWidth="2.5" />
          <circle cx="419" cy="0" r="6" fill="var(--forensic-bg-dark, #0F172A)" stroke="#6366F1" strokeWidth="3" />
        </g>

        {/* Tagline */}
        <text
          x="220"
          y="126"
          fill="#A855F7"
          fontFamily="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
          fontSize="12"
          fontWeight="700"
          letterSpacing="3.5"
          textAnchor="middle"
        >
          FORENSICS. INTELLIGENCE. IMPACT.
        </text>
      </g>
    </svg>
  )
}

export default BrandLogo
