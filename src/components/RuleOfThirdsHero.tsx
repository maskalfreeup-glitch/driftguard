import { Terminal, Github, ArrowRight } from "lucide-react"

interface RuleOfThirdsHeroProps {
  onOpenPlayground: () => void
}

export function RuleOfThirdsHero({
  onOpenPlayground
}: RuleOfThirdsHeroProps) {
  return (
    <div className="py-16 md:py-24 max-w-4xl mx-auto space-y-8 text-center md:text-left">
      <div className="inline-flex items-center gap-2 text-xs font-mono text-zinc-400">
        <span className="size-2 rounded-full bg-emerald-400" />
        <span>v0.4.2 · MIT License · Arbitrum Nitro &amp; Orbit</span>
      </div>

      <h1 className="text-4xl sm:text-6xl font-bold tracking-tight text-white leading-[1.12]">
        Out-of-band consensus sentinel &amp; L7 failover for Arbitrum Nitro.
      </h1>

      <p className="text-lg sm:text-xl text-zinc-300 leading-relaxed font-sans max-w-3xl">
        When an Arbitrum sequencer stalls, upstream RPC nodes keep returning HTTP 200 with stale state roots. DriftGuard runs as an out-of-band HAProxy sidecar—polling canonical anchors every 200ms and draining desynced nodes in &lt;130ms without dropping active TCP connections.
      </p>

      {/* Two Main CTA Buttons */}
      <div className="pt-2 flex flex-wrap items-center justify-center md:justify-start gap-4">
        <button
          onClick={onOpenPlayground}
          className="bg-white hover:bg-zinc-200 text-black text-sm font-semibold px-6 py-3.5 rounded-lg transition-colors flex items-center gap-2 shadow-sm"
        >
          <Terminal className="size-4 text-[#28A0F0]" />
          <span>Launch RPC Playground</span>
          <ArrowRight className="size-4 text-zinc-600" />
        </button>

        <a
          href="https://github.com/maskalfreeup-glitch/driftguard"
          target="_blank"
          rel="noreferrer"
          className="border border-zinc-700 hover:border-zinc-500 bg-zinc-900/60 hover:bg-zinc-900 text-zinc-200 hover:text-white text-sm font-medium px-6 py-3.5 rounded-lg transition-colors flex items-center gap-2"
        >
          <Github className="size-4 text-zinc-300" />
          <span>View GitHub Repository</span>
        </a>
      </div>
    </div>
  )
}
