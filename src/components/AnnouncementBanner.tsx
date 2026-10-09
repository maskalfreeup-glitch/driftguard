import { ArrowRight, Shield } from "lucide-react"

export function AnnouncementBanner() {
  return (
    <div className="relative z-30 bg-zinc-950 border-b border-zinc-800/90 text-xs px-3 sm:px-4 py-2">
      <div className="max-w-6xl mx-auto flex items-center justify-between gap-2 sm:gap-4 flex-wrap sm:flex-nowrap">
        <div className="flex items-center gap-2 text-zinc-300 min-w-0">
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-zinc-900 border border-zinc-750 text-[10px] font-mono font-medium text-zinc-300 shrink-0">
            <span className="size-1.5 rounded-full bg-[#28A0F0]" />
            SPECIFICATION
          </span>
          <span className="text-[11px] sm:text-xs text-zinc-300 truncate font-sans">
            DriftGuard v0.4.2 • Open Source Consensus Ingress Gateway (MIT License)
          </span>
        </div>

        <div className="flex items-center gap-3 shrink-0 text-[11px] font-mono">
          <a
            href="https://github.com/maskalfreeup-glitch/driftguard"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-[#28A0F0] hover:text-sky-300 transition-colors font-medium group"
          >
            <span>Architecture RFC</span>
            <ArrowRight className="size-3 group-hover:translate-x-0.5 transition-transform" />
          </a>
          <span className="text-zinc-800 hidden sm:inline">|</span>
          <span className="text-zinc-400 hidden sm:inline-flex items-center gap-1 text-[10px]">
            <Shield className="size-3 text-emerald-400" />
            Open Source (MIT)
          </span>
        </div>
      </div>
    </div>
  )
}
