import { ArrowRight, Shield } from "lucide-react"

export function AnnouncementBanner() {
  return (
    <div className="relative z-30 bg-gradient-to-r from-sky-950/70 via-zinc-950 to-sky-950/70 border-b border-sky-500/20 text-xs px-3 sm:px-4 py-2">
      <div className="max-w-6xl mx-auto flex items-center justify-between gap-2 sm:gap-4 flex-wrap sm:flex-nowrap">
        <div className="flex items-center gap-2 text-zinc-300 min-w-0">
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-sky-500/10 border border-sky-400/30 text-[10px] font-mono font-semibold text-[#28A0F0] shrink-0">
            <span className="size-1.5 rounded-full bg-[#28A0F0] animate-pulse" />
            GRANT PROPOSAL
          </span>
          <span className="text-[11px] sm:text-xs text-zinc-300 truncate">
            Arbitrum Foundation Grant Candidate · Sub-130ms Consensus Sentinel for Nitro &amp; Orbit Rollups
          </span>
        </div>

        <div className="flex items-center gap-3 shrink-0 text-[11px] font-mono">
          <a
            href="https://github.com/maskalfreeup-glitch/driftguard/blob/main/ARBITRUM_GRANT_PROPOSAL.md"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-[#28A0F0] hover:text-sky-300 transition-colors font-medium group"
          >
            <span>Review Proposal</span>
            <ArrowRight className="size-3 group-hover:translate-x-0.5 transition-transform" />
          </a>
          <span className="text-zinc-700 hidden sm:inline">|</span>
          <span className="text-emerald-400 hidden sm:inline-flex items-center gap-1 text-[10px]">
            <Shield className="size-3" />
            100% Empirically Verified
          </span>
        </div>
      </div>
    </div>
  )
}
