interface DriftGuardLogoProps {
  className?: string
  iconSize?: number
  showText?: boolean
  showBadge?: boolean
}

export function DriftGuardLogo({
  className = "",
  iconSize = 34,
  showText = true,
  showBadge = true,
}: DriftGuardLogoProps) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* Code-Generated Pure SVG Geometric Hexagonal Shield with Interlocking Prisms */}
      <div className="relative flex items-center justify-center shrink-0">
        <svg
          width={iconSize}
          height={iconSize}
          viewBox="0 0 44 44"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="transition-transform hover:scale-105 duration-200"
        >
          <defs>
            {/* Ambient Cyan Glow Filter */}
            <filter id="dg-glow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow
                dx="0"
                dy="0"
                stdDeviation="2.5"
                floodColor="#28A0F0"
                floodOpacity="0.45"
              />
            </filter>

            {/* Cyan Gradient for Primary Prism */}
            <linearGradient id="prism-cyan" x1="6" y1="8" x2="38" y2="36" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#54B7F5" />
              <stop offset="60%" stopColor="#28A0F0" />
              <stop offset="100%" stopColor="#0C82D5" />
            </linearGradient>

            {/* White / Platinum Gradient for Interlocking Prism */}
            <linearGradient id="prism-white" x1="14" y1="6" x2="34" y2="34" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#FFFFFF" />
              <stop offset="100%" stopColor="#CBD5E1" />
            </linearGradient>

            {/* Shield Outline Gradient */}
            <linearGradient id="shield-rim" x1="22" y1="2" x2="22" y2="42" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#38B0F8" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#0A2E4E" stopOpacity="0.3" />
            </linearGradient>
          </defs>

          {/* Hexagonal Shield Background Frame */}
          <polygon
            points="22,3 39,12 39,32 22,41 5,32 5,12"
            fill="#090D16"
            stroke="url(#shield-rim)"
            strokeWidth="1.75"
            strokeLinejoin="round"
          />

          {/* Inner Accent Fill */}
          <polygon
            points="22,6 36,14 36,30 22,38 8,30 8,14"
            fill="#0F172A"
            fillOpacity="0.75"
          />

          {/* Dual Interlocking Offset Prisms (Arbitrum-style geometric facets) */}
          <g filter="url(#dg-glow)">
            {/* Primary Cyan Prism (Left-aligned & upward angled) */}
            <path
              d="M14 16 L22 11 L22 23 L14 28 Z"
              fill="url(#prism-cyan)"
            />
            <path
              d="M14 28 L22 23 L28 26.5 L20 31.5 Z"
              fill="#0B68AA"
            />

            {/* Interlocking White/Silver Prism (Offset & forward-facing) */}
            <path
              d="M22 17 L30 12 L30 24 L22 29 Z"
              fill="url(#prism-white)"
            />
            <path
              d="M22 29 L30 24 L26 21.5 L18 26.5 Z"
              fill="#94A3B8"
              fillOpacity="0.85"
            />

            {/* Central Convergence Node */}
            <circle cx="22" cy="22" r="1.5" fill="#28A0F0" />
          </g>
        </svg>
      </div>

      {/* Brand Typography & Arbitrum Nitro Pill Badge */}
      {showText && (
        <div className="flex items-center gap-2">
          <span className="font-semibold text-sm sm:text-base tracking-tight text-white">
            DriftGuard
          </span>
          {showBadge && (
            <span className="hidden md:inline-flex text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-zinc-900 border border-zinc-800 text-zinc-400">
              Arbitrum Nitro
            </span>
          )}
        </div>
      )}
    </div>
  )
}
