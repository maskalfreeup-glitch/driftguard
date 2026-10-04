export function HeroBrandShield() {
  return (
    <div className="relative rounded-2xl border border-sky-500/20 bg-sky-950/10 p-8 backdrop-blur-sm flex flex-col items-center justify-center overflow-hidden shadow-[0_0_50px_-10px_rgba(40,160,240,0.18)] transition-all hover:border-sky-500/40 duration-300">
      {/* Outer ambient radial glow in Arbitrum Cyan */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(40,160,240,0.18)_0%,transparent_70%)] pointer-events-none" />

      {/* Pulsing radar ping ring around the shield */}
      <div className="relative flex items-center justify-center">
        <div className="absolute size-44 rounded-full border border-sky-400/20 animate-ping opacity-30 pointer-events-none" />
        <div className="absolute size-36 rounded-full border border-[#28A0F0]/30 animate-pulse pointer-events-none" />

        {/* Luminous High-Resolution SVG Shield */}
        <svg
          width="160"
          height="160"
          viewBox="0 0 120 120"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="relative z-10 drop-shadow-[0_0_25px_rgba(40,160,240,0.4)]"
        >
          <defs>
            {/* Ambient Cyan Filter Glow */}
            <filter id="hero-shield-glow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow
                dx="0"
                dy="0"
                stdDeviation="4"
                floodColor="#28A0F0"
                floodOpacity="0.5"
              />
            </filter>

            {/* Gradient for Primary Nitro Prism */}
            <linearGradient id="hero-prism-cyan" x1="20" y1="20" x2="100" y2="100" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#7CCBFC" />
              <stop offset="45%" stopColor="#28A0F0" />
              <stop offset="100%" stopColor="#0B68AA" />
            </linearGradient>

            {/* Gradient for Interlocking Platinum Prism */}
            <linearGradient id="hero-prism-white" x1="40" y1="15" x2="95" y2="95" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#FFFFFF" />
              <stop offset="60%" stopColor="#E2E8F0" />
              <stop offset="100%" stopColor="#94A3B8" />
            </linearGradient>

            {/* Outer Hexagon Shield Rim Gradient */}
            <linearGradient id="hero-rim-gradient" x1="60" y1="4" x2="60" y2="116" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#54B7F5" />
              <stop offset="50%" stopColor="#28A0F0" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#0A2E4E" stopOpacity="0.4" />
            </linearGradient>

            {/* Inner Facet Gradient */}
            <radialGradient id="hero-inner-facet" cx="60" cy="60" r="50" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#0F172A" />
              <stop offset="100%" stopColor="#090D16" />
            </radialGradient>
          </defs>

          {/* Outer Geometric Hexagonal Frame */}
          <polygon
            points="60,6 106,30 106,90 60,114 14,90 14,30"
            fill="url(#hero-inner-facet)"
            stroke="url(#hero-rim-gradient)"
            strokeWidth="3.5"
            strokeLinejoin="round"
          />

          {/* Isometric Inner Cutouts & Circuit Accents */}
          <polygon
            points="60,14 98,34 98,86 60,106 22,86 22,34"
            fill="#0A1628"
            fillOpacity="0.6"
            stroke="#1E3A5F"
            strokeWidth="1.5"
          />

          {/* Dual Interlocking Nitro Prisms (Arbitrum-style isometric geometry) */}
          <g filter="url(#hero-shield-glow)">
            {/* Primary Cyan Prism (Left-aligned & upward angled) */}
            <path
              d="M38 44 L60 30 L60 62 L38 76 Z"
              fill="url(#hero-prism-cyan)"
            />
            <path
              d="M38 76 L60 62 L76 71 L54 85 Z"
              fill="#0A4C7E"
            />

            {/* Interlocking Platinum/Silver Prism (Offset & forward-facing) */}
            <path
              d="M60 46 L82 32 L82 64 L60 78 Z"
              fill="url(#hero-prism-white)"
            />
            <path
              d="M60 78 L82 64 L72 58 L50 72 Z"
              fill="#64748B"
              fillOpacity="0.9"
            />

            {/* Center Consensus Nexus Core */}
            <circle cx="60" cy="60" r="3.5" fill="#38B0F8" />
            <circle cx="60" cy="60" r="1.5" fill="#FFFFFF" />
          </g>
        </svg>
      </div>

      {/* Connectivity Status Label */}
      <div className="mt-5 relative z-10 flex items-center gap-2 px-3 py-1 rounded-full bg-[#0A2E4E]/50 border border-[#28A0F0]/30 text-[#28A0F0] text-xs font-mono">
        <span className="relative flex size-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#28A0F0] opacity-75"></span>
          <span className="relative inline-flex rounded-full size-2 bg-[#28A0F0]"></span>
        </span>
        <span className="font-semibold tracking-wide">Arbitrum Nitro Consensus</span>
      </div>
    </div>
  )
}
