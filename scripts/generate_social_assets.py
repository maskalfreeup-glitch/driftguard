#!/usr/bin/env python3
"""
DriftGuard Social Branding Asset Generator
Deterministically generates high-resolution vector and raster branding assets:
  - og-image.png       (1200x630 OpenGraph / Twitter Large Card)
  - twitter-card.png   (1200x630 Twitter Card)
  - banner.png         (1500x500 Twitter / GitHub Profile Banner)
  - avatar.png         (512x512 High-Res Profile Avatar)
  - icon-512.png       (512x512 PWA App Icon)
  - icon-192.png       (192x192 PWA Icon)
  - favicon.png        (32x32 Raster Favicon)
"""

import sys
from pathlib import Path

# Ensure dependencies are available
try:
    import cairosvg
    from PIL import Image
except ImportError:
    print("Error: Missing required packages. Run: pip install cairosvg pillow")
    sys.exit(1)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "public"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Reusable SVG Components
# ---------------------------------------------------------------------------

SHIELD_SVG = """
  <g id="shield-emblem">
    <defs>
      <linearGradient id="shield-rim" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#54B7F5" />
        <stop offset="50%" stop-color="#28A0F0" stop-opacity="0.8" />
        <stop offset="100%" stop-color="#0A2E4E" stop-opacity="0.4" />
      </linearGradient>
      <radialGradient id="shield-inner" cx="50%" cy="50%" r="50%">
        <stop offset="0%" stop-color="#0F172A" />
        <stop offset="100%" stop-color="#090D16" />
      </radialGradient>
      <linearGradient id="prism-cyan" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#7CCBFC" />
        <stop offset="45%" stop-color="#28A0F0" />
        <stop offset="100%" stop-color="#0B68AA" />
      </linearGradient>
      <linearGradient id="prism-white" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#FFFFFF" />
        <stop offset="60%" stop-color="#E2E8F0" />
        <stop offset="100%" stop-color="#94A3B8" />
      </linearGradient>
      <filter id="cyan-glow" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="0" dy="0" stdDeviation="6" flood-color="#28A0F0" flood-opacity="0.6"/>
      </filter>
    </defs>
    <!-- Outer Hexagonal Frame -->
    <polygon points="60,6 106,30 106,90 60,114 14,90 14,30"
             fill="url(#shield-inner)" stroke="url(#shield-rim)" stroke-width="3" stroke-linejoin="round"/>
    <!-- Inner Inset Frame -->
    <polygon points="60,14 98,34 98,86 60,106 22,86 22,34"
             fill="#0A1628" fill-opacity="0.6" stroke="#1E3A5F" stroke-width="1.5"/>
    <!-- Interlocking Prisms -->
    <g filter="url(#cyan-glow)">
      <!-- Left Cyan Prism -->
      <path d="M38 44 L60 30 L60 62 L38 76 Z" fill="url(#prism-cyan)" />
      <path d="M38 76 L60 62 L76 71 L54 85 Z" fill="#0A4C7E" />
      <!-- Right Platinum Prism -->
      <path d="M60 46 L82 32 L82 64 L60 78 Z" fill="url(#prism-white)" />
      <path d="M60 78 L82 64 L72 58 L50 72 Z" fill="#64748B" fill-opacity="0.9" />
      <!-- Center Nexus -->
      <circle cx="60" cy="60" r="3.5" fill="#38B0F8" />
      <circle cx="60" cy="60" r="1.5" fill="#FFFFFF" />
    </g>
  </g>
"""

# ---------------------------------------------------------------------------
# 1. OpenGraph Preview Image (1200 x 630)
# ---------------------------------------------------------------------------

def generate_og_image_svg() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">
  <defs>
    <radialGradient id="bg-glow" cx="25%" cy="50%" r="60%">
      <stop offset="0%" stop-color="#0E2A4A" stop-opacity="0.65" />
      <stop offset="50%" stop-color="#08101E" stop-opacity="0.9" />
      <stop offset="100%" stop-color="#060A12" stop-opacity="1" />
    </radialGradient>
    <radialGradient id="ambient-cyan" cx="220" cy="315" r="280">
      <stop offset="0%" stop-color="#28A0F0" stop-opacity="0.35" />
      <stop offset="70%" stop-color="#28A0F0" stop-opacity="0.05" />
      <stop offset="100%" stop-color="#28A0F0" stop-opacity="0" />
    </radialGradient>
    <linearGradient id="card-border" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#28A0F0" stop-opacity="0.4" />
      <stop offset="50%" stop-color="#1E3A5F" stop-opacity="0.3" />
      <stop offset="100%" stop-color="#0A2E4E" stop-opacity="0.1" />
    </linearGradient>
    <linearGradient id="accent-cyan" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#7CCBFC" />
      <stop offset="100%" stop-color="#28A0F0" />
    </linearGradient>
    <filter id="pill-glow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="0" stdDeviation="4" flood-color="#28A0F0" flood-opacity="0.35"/>
    </filter>
  </defs>

  <!-- Deep Obsidian Canvas -->
  <rect width="1200" height="630" fill="url(#bg-glow)" />

  <!-- Background Decorative Grid Lines -->
  <g opacity="0.07" stroke="#28A0F0" stroke-width="1">
    <line x1="0" y1="105" x2="1200" y2="105" />
    <line x1="0" y1="210" x2="1200" y2="210" />
    <line x1="0" y1="315" x2="1200" y2="315" />
    <line x1="0" y1="420" x2="1200" y2="420" />
    <line x1="0" y1="525" x2="1200" y2="525" />
    <line x1="200" y1="0" x2="200" y2="630" />
    <line x1="400" y1="0" x2="400" y2="630" />
    <line x1="600" y1="0" x2="600" y2="630" />
    <line x1="800" y1="0" x2="800" y2="630" />
    <line x1="1000" y1="0" x2="1000" y2="630" />
  </g>

  <!-- Outer Card Frame -->
  <rect x="24" y="24" width="1152" height="582" rx="20" fill="none" stroke="url(#card-border)" stroke-width="2" />

  <!-- Shield Ambient Glow Core -->
  <circle cx="230" cy="315" r="220" fill="url(#ambient-cyan)" />

  <!-- Pulsing Radar Rings Behind Shield -->
  <circle cx="230" cy="315" r="170" fill="none" stroke="#28A0F0" stroke-width="1.5" stroke-dasharray="4 8" opacity="0.4" />
  <circle cx="230" cy="315" r="135" fill="none" stroke="#28A0F0" stroke-width="1.5" opacity="0.6" />

  <!-- The Scaled Shield Emblem -->
  <g transform="translate(110, 195) scale(2.0)">
    {SHIELD_SVG}
  </g>

  <!-- Content Column -->
  <g transform="translate(450, 95)">
    <!-- Pill Badge -->
    <g filter="url(#pill-glow)">
      <rect x="0" y="0" width="310" height="34" rx="17" fill="#0A2E4E" fill-opacity="0.8" stroke="#28A0F0" stroke-width="1.5" />
      <circle cx="18" cy="17" r="4.5" fill="#28A0F0" />
      <text x="32" y="22" fill="#7CCBFC" font-family="Inter, 'DejaVu Sans', sans-serif" font-size="12" font-weight="700" letter-spacing="1.2">ARBITRUM NITRO CONSENSUS</text>
    </g>

    <!-- Main Title -->
    <text x="0" y="115" fill="#FFFFFF" font-family="Inter, 'DejaVu Sans', sans-serif" font-size="64" font-weight="800" letter-spacing="-1.5">
      Drift<tspan fill="url(#accent-cyan)">Guard</tspan>
    </text>

    <!-- Subtitle / Tagline -->
    <text x="0" y="165" fill="#93C5FD" font-family="Inter, 'DejaVu Sans', sans-serif" font-size="24" font-weight="600">
      Sub-130ms Failover Gateway &amp; Active-Passive RPC Sentry
    </text>

    <!-- Description -->
    <text x="0" y="215" fill="#94A3B8" font-family="Inter, 'DejaVu Sans', sans-serif" font-size="16" font-weight="400" line-height="1.5">
      Eliminating silent 250ms sequencer desync &amp; stale 200 OK reads across Arbitrum One &amp; Nova.
    </text>

    <!-- Metric Metric Badges -->
    <g transform="translate(0, 260)">
      <!-- Badge 1: Failover -->
      <rect x="0" y="0" width="155" height="68" rx="10" fill="#0D1A2D" stroke="#1E3A5F" stroke-width="1.5" />
      <text x="16" y="28" fill="#7CCBFC" font-family="'JetBrains Mono', 'DejaVu Sans Mono', monospace" font-size="18" font-weight="700">&lt;130ms</text>
      <text x="16" y="50" fill="#64748B" font-family="Inter, 'DejaVu Sans', sans-serif" font-size="11" font-weight="500">FAILOVER TIME</text>

      <!-- Badge 2: Tip Sync -->
      <rect x="170" y="0" width="155" height="68" rx="10" fill="#0D1A2D" stroke="#1E3A5F" stroke-width="1.5" />
      <text x="186" y="28" fill="#7CCBFC" font-family="'JetBrains Mono', 'DejaVu Sans Mono', monospace" font-size="18" font-weight="700">250ms</text>
      <text x="186" y="50" fill="#64748B" font-family="Inter, 'DejaVu Sans', sans-serif" font-size="11" font-weight="500">TIP SYNC GUARD</text>

      <!-- Badge 3: Memory -->
      <rect x="340" y="0" width="155" height="68" rx="10" fill="#0D1A2D" stroke="#1E3A5F" stroke-width="1.5" />
      <text x="356" y="28" fill="#7CCBFC" font-family="'JetBrains Mono', 'DejaVu Sans Mono', monospace" font-size="18" font-weight="700">42MB</text>
      <text x="356" y="50" fill="#64748B" font-family="Inter, 'DejaVu Sans', sans-serif" font-size="11" font-weight="500">MEMORY USAGE</text>

      <!-- Badge 4: Zero Drop -->
      <rect x="510" y="0" width="165" height="68" rx="10" fill="#0D1A2D" stroke="#1E3A5F" stroke-width="1.5" />
      <text x="526" y="28" fill="#34D399" font-family="'JetBrains Mono', 'DejaVu Sans Mono', monospace" font-size="18" font-weight="700">0% DROPS</text>
      <text x="526" y="50" fill="#64748B" font-family="Inter, 'DejaVu Sans', sans-serif" font-size="11" font-weight="500">SYNTHETIC SLA</text>
    </g>

    <!-- Footer Bar -->
    <g transform="translate(0, 365)">
      <circle cx="8" cy="8" r="4" fill="#34D399" />
      <text x="22" y="12" fill="#E2E8F0" font-family="'JetBrains Mono', 'DejaVu Sans Mono', monospace" font-size="14" font-weight="600">rpc.driftguard.live/arb</text>
      <text x="250" y="12" fill="#64748B" font-family="Inter, 'DejaVu Sans', sans-serif" font-size="14">•</text>
      <text x="270" y="12" fill="#93C5FD" font-family="Inter, 'DejaVu Sans', sans-serif" font-size="14">driftguard.live</text>
      <text x="400" y="12" fill="#64748B" font-family="Inter, 'DejaVu Sans', sans-serif" font-size="14">•</text>
      <text x="420" y="12" fill="#64748B" font-family="Inter, 'DejaVu Sans', sans-serif" font-size="14">MIT Open Source</text>
    </g>
  </g>
</svg>"""

# ---------------------------------------------------------------------------
# 2. Panoramic Banner (1500 x 500)
# ---------------------------------------------------------------------------

def generate_banner_svg() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1500 500" width="1500" height="500">
  <defs>
    <radialGradient id="banner-bg" cx="50%" cy="50%" r="70%">
      <stop offset="0%" stop-color="#0E233E" stop-opacity="0.7" />
      <stop offset="60%" stop-color="#080F1D" stop-opacity="0.95" />
      <stop offset="100%" stop-color="#050811" stop-opacity="1" />
    </radialGradient>
    <radialGradient id="banner-glow" cx="750" cy="250" r="350">
      <stop offset="0%" stop-color="#28A0F0" stop-opacity="0.25" />
      <stop offset="100%" stop-color="#28A0F0" stop-opacity="0" />
    </radialGradient>
    <linearGradient id="banner-cyan" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#7CCBFC" />
      <stop offset="100%" stop-color="#28A0F0" />
    </linearGradient>
  </defs>

  <rect width="1500" height="500" fill="url(#banner-bg)" />

  <!-- Ambient Glow -->
  <circle cx="750" cy="250" r="300" fill="url(#banner-glow)" />

  <!-- Geometric Grid Lines -->
  <g opacity="0.06" stroke="#28A0F0" stroke-width="1">
    <line x1="0" y1="125" x2="1500" y2="125" />
    <line x1="0" y1="250" x2="1500" y2="250" />
    <line x1="0" y1="375" x2="1500" y2="375" />
    <line x1="250" y1="0" x2="250" y2="500" />
    <line x1="500" y1="0" x2="500" y2="500" />
    <line x1="750" y1="0" x2="750" y2="500" />
    <line x1="1000" y1="0" x2="1000" y2="500" />
    <line x1="1250" y1="0" x2="1250" y2="500" />
  </g>

  <!-- Left Side: Center-Left Shield Icon -->
  <g transform="translate(180, 130) scale(2.0)">
    {SHIELD_SVG}
  </g>

  <!-- Brand Typography -->
  <g transform="translate(480, 140)">
    <!-- Pill Badge -->
    <rect x="0" y="0" width="280" height="30" rx="15" fill="#0A2E4E" stroke="#28A0F0" stroke-width="1.5" />
    <circle cx="16" cy="15" r="4" fill="#28A0F0" />
    <text x="28" y="20" fill="#7CCBFC" font-family="Inter, 'DejaVu Sans', sans-serif" font-size="11" font-weight="700" letter-spacing="1">ARBITRUM NITRO CONSENSUS</text>

    <!-- Main Title -->
    <text x="0" y="105" fill="#FFFFFF" font-family="Inter, 'DejaVu Sans', sans-serif" font-size="68" font-weight="800" letter-spacing="-1.5">
      Drift<tspan fill="url(#banner-cyan)">Guard</tspan>
    </text>

    <!-- Subtitle -->
    <text x="0" y="155" fill="#93C5FD" font-family="Inter, 'DejaVu Sans', sans-serif" font-size="22" font-weight="600">
      Sub-130ms Failover Gateway &amp; Active-Passive Sentinel
    </text>

    <!-- Metrics Row -->
    <g transform="translate(0, 185)">
      <text x="0" y="24" fill="#7CCBFC" font-family="'JetBrains Mono', 'DejaVu Sans Mono', monospace" font-size="15" font-weight="700">&lt;130ms Failover</text>
      <text x="170" y="24" fill="#64748B" font-family="Inter, 'DejaVu Sans', sans-serif" font-size="15">•</text>
      <text x="190" y="24" fill="#7CCBFC" font-family="'JetBrains Mono', 'DejaVu Sans Mono', monospace" font-size="15" font-weight="700">250ms Tip Sync</text>
      <text x="360" y="24" fill="#64748B" font-family="Inter, 'DejaVu Sans', sans-serif" font-size="15">•</text>
      <text x="380" y="24" fill="#7CCBFC" font-family="'JetBrains Mono', 'DejaVu Sans Mono', monospace" font-size="15" font-weight="700">42MB RAM</text>
      <text x="500" y="24" fill="#64748B" font-family="Inter, 'DejaVu Sans', sans-serif" font-size="15">•</text>
      <text x="520" y="24" fill="#34D399" font-family="'JetBrains Mono', 'DejaVu Sans Mono', monospace" font-size="15" font-weight="700">Zero Drops</text>
    </g>
  </g>
</svg>"""

# ---------------------------------------------------------------------------
# 3. Square Avatar & App Icon (512 x 512)
# ---------------------------------------------------------------------------

def generate_avatar_svg() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <radialGradient id="avatar-bg" cx="50%" cy="50%" r="65%">
      <stop offset="0%" stop-color="#0F243E" stop-opacity="0.8" />
      <stop offset="65%" stop-color="#080F1E" stop-opacity="0.95" />
      <stop offset="100%" stop-color="#060A14" stop-opacity="1" />
    </radialGradient>
    <radialGradient id="avatar-glow" cx="256" cy="256" r="180">
      <stop offset="0%" stop-color="#28A0F0" stop-opacity="0.35" />
      <stop offset="100%" stop-color="#28A0F0" stop-opacity="0" />
    </radialGradient>
  </defs>

  <rect width="512" height="512" fill="url(#avatar-bg)" rx="80" />

  <!-- Ambient Glow -->
  <circle cx="256" cy="256" r="160" fill="url(#avatar-glow)" />

  <!-- Outer Ring Accent -->
  <circle cx="256" cy="256" r="215" fill="none" stroke="#28A0F0" stroke-width="2" stroke-dasharray="6 10" opacity="0.3" />
  <circle cx="256" cy="256" r="185" fill="none" stroke="#28A0F0" stroke-width="1.5" opacity="0.5" />

  <!-- Centered Scaled Shield -->
  <g transform="translate(96, 96) scale(2.666)">
    {SHIELD_SVG}
  </g>
</svg>"""

# ---------------------------------------------------------------------------
# Generator Execution
# ---------------------------------------------------------------------------

def main():
    print("==================================================")
    print("  DriftGuard Deterministic Social Asset Generator")
    print("==================================================")
    print(f"Output Directory: {OUTPUT_DIR}\n")

    assets = [
        ("og-image.png", generate_og_image_svg(), 1200, 630),
        ("twitter-card.png", generate_og_image_svg(), 1200, 630),
        ("banner.png", generate_banner_svg(), 1500, 500),
        ("avatar.png", generate_avatar_svg(), 512, 512),
        ("icon-512.png", generate_avatar_svg(), 512, 512),
    ]

    for filename, svg_str, width, height in assets:
        target_path = OUTPUT_DIR / filename
        cairosvg.svg2png(
            bytestring=svg_str.encode("utf-8"),
            write_to=str(target_path),
            output_width=width,
            output_height=height,
        )
        size_kb = target_path.stat().st_size / 1024
        print(f"  ✓ Created {filename:<18} [{width}x{height}] ({size_kb:.1f} KB)")

    # Produce smaller icons via Pillow resizing from the 512x512 master
    master_icon_path = OUTPUT_DIR / "icon-512.png"
    with Image.open(master_icon_path) as img:
        # icon-192.png
        icon_192_path = OUTPUT_DIR / "icon-192.png"
        img.resize((192, 192), Image.Resampling.LANCZOS).save(icon_192_path, "PNG", optimize=True)
        print(f"  ✓ Created {'icon-192.png':<18} [192x192] ({icon_192_path.stat().st_size / 1024:.1f} KB)")

        # favicon.png
        favicon_path = OUTPUT_DIR / "favicon.png"
        img.resize((32, 32), Image.Resampling.LANCZOS).save(favicon_path, "PNG", optimize=True)
        print(f"  ✓ Created {'favicon.png':<18} [32x32] ({favicon_path.stat().st_size / 1024:.1f} KB)")

    print("\nAll social and web branding assets generated successfully!")

if __name__ == "__main__":
    main()
