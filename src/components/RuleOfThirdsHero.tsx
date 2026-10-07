import { useState } from "react"
import { Play, Terminal, BookOpen, ShieldCheck, Activity, RefreshCw, Zap, ExternalLink, Check, Copy } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { HeroBrandShield } from "@/components/HeroBrandShield"

interface RuleOfThirdsHeroProps {
  onWatchVideo: () => void
  onOpenPlayground: () => void
  onOpenSpecs: () => void
  onOpenLedger: () => void
}

export function RuleOfThirdsHero({
  onWatchVideo,
  onOpenPlayground,
  onOpenSpecs,
  onOpenLedger
}: RuleOfThirdsHeroProps) {
  // Interactive Drill State
  const [isSimulating, setIsSimulating] = useState(false)
  const [simStep, setSimStep] = useState<"idle" | "drift" | "drain" | "recovered">("idle")
  const [drillLatency, setDrillLatency] = useState<number | null>(null)
  const [copiedQuickstart, setCopiedQuickstart] = useState(false)

  const runSimulatedDrill = () => {
    if (isSimulating) return
    setIsSimulating(true)
    setSimStep("drift")

    // Step 1: Drift detected at 400ms
    setTimeout(() => {
      setSimStep("drain")
      setDrillLatency(120.4)
    }, 900)

    // Step 2: Drained & Fallback promoted
    setTimeout(() => {
      setSimStep("recovered")
    }, 2200)

    // Step 3: Return to idle
    setTimeout(() => {
      setSimStep("idle")
      setIsSimulating(false)
    }, 4500)
  }

  const handleCopyQuickstart = () => {
    navigator.clipboard.writeText("docker compose up -d")
    setCopiedQuickstart(true)
    setTimeout(() => setCopiedQuickstart(false), 2000)
  }

  return (
    <div className="relative pt-2 pb-6 sm:pb-12">
      {/* ── Rule of Thirds Asymmetric 2/3 + 1/3 Grid ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 items-center">
        {/* ══════════════════════════════════════════════════════════
            COLUMN 1 & 2: THE 2/3 PROPOSITION & ACTION CLUSTER
           ══════════════════════════════════════════════════════════ */}
        <div className="lg:col-span-7 xl:col-span-8 space-y-5 text-left">
          {/* Institutional VC & Grant Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900/90 border border-sky-500/30 text-[11px] font-mono text-zinc-300 shadow-sm">
            <span className="size-2 rounded-full bg-[#28A0F0] animate-pulse" />
            <span className="text-white font-semibold">ARBITRUM NITRO &amp; ORBIT</span>
            <span className="text-zinc-600">·</span>
            <span className="text-[#28A0F0]">L7 CONSENSUS RUNTIME SENTINEL</span>
          </div>

          {/* Primary High-Impact Headline */}
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-white leading-[1.12]">
            Deterministic Ingress &amp; Out-of-Band Consensus Guard
          </h1>

          {/* Strategic Value Proposition */}
          <p className="text-sm sm:text-base text-zinc-300 leading-relaxed max-w-2xl font-sans">
            Eliminates silent <span className="text-white font-medium">HTTP 200 OK</span> desyncs and sequencer queue stalls in Arbitrum Nitro and Orbit chains. Decouples EVM JSON-RPC transport with sub-130ms UNIX socket cutover and <span className="text-emerald-400 font-medium">zero TCP connection resets</span>.
          </p>

          {/* Rule of Thirds Action Links: Aligned along 1/3 focal line */}
          <div className="pt-2 flex flex-wrap items-center gap-2.5 sm:gap-3">
            {/* Primary Action Button (White / VC Spotlight) */}
            <Button
              onClick={onWatchVideo}
              className="bg-white hover:bg-zinc-200 text-black font-semibold h-10 sm:h-11 px-5 rounded-lg text-xs sm:text-sm transition-all flex items-center gap-2 shadow-lg shadow-white/5 active:scale-95"
            >
              <Play className="size-3.5 fill-current text-[#28A0F0]" />
              <span>Watch 1080p Explainer</span>
            </Button>

            {/* Secondary Action: Playground */}
            <Button
              variant="outline"
              onClick={onOpenPlayground}
              className="border border-zinc-700 bg-zinc-900/80 hover:bg-zinc-800 text-zinc-200 h-10 sm:h-11 px-4 rounded-lg text-xs sm:text-sm flex items-center gap-2 transition-all active:scale-95"
            >
              <Terminal className="size-3.5 text-[#28A0F0]" />
              <span>Gateway Playground</span>
            </Button>

            {/* Tertiary Action: Specs & RFC */}
            <Button
              variant="outline"
              onClick={onOpenSpecs}
              className="border border-zinc-800 bg-zinc-950/60 hover:bg-zinc-900 text-zinc-400 hover:text-white h-10 sm:h-11 px-4 rounded-lg text-xs sm:text-sm flex items-center gap-2 transition-all active:scale-95"
            >
              <BookOpen className="size-3.5" />
              <span>Architecture Specs</span>
            </Button>
          </div>

          {/* Quickstart Command Bar for Engineers & Reviewers */}
          <div className="pt-1 flex items-center gap-2 max-w-xl">
            <div className="flex-1 flex items-center justify-between px-3 py-1.5 rounded-lg bg-zinc-950/80 border border-zinc-800 font-mono text-xs text-zinc-300 min-w-0">
              <span className="text-zinc-500 mr-2 select-none">$</span>
              <span className="truncate flex-1 text-zinc-300">
                docker compose up -d <span className="text-zinc-500"># &lt;45MB RAM Sidecar</span>
              </span>
              <button
                onClick={handleCopyQuickstart}
                className="ml-2 text-zinc-400 hover:text-white p-1 rounded transition-colors"
                title="Copy Quickstart Command"
              >
                {copiedQuickstart ? <Check className="size-3.5 text-emerald-400" /> : <Copy className="size-3.5" />}
              </button>
            </div>
            <a
              href="https://github.com/maskalfreeup-glitch/driftguard"
              target="_blank"
              rel="noreferrer"
              className="px-3 py-2 rounded-lg bg-zinc-900/80 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 text-xs font-mono transition-colors flex items-center gap-1.5 shrink-0"
            >
              <span>GitHub</span>
              <ExternalLink className="size-3" />
            </a>
          </div>

          {/* Empirical Validation Proof Line */}
          <div className="pt-2 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs font-mono text-zinc-400 border-t border-zinc-800/80">
            <button
              onClick={onOpenLedger}
              className="inline-flex items-center gap-1.5 text-emerald-400 hover:underline cursor-pointer"
            >
              <ShieldCheck className="size-3.5 text-emerald-400" />
              <span>18 Production Desyncs Mitigated</span>
            </button>
            <span className="text-zinc-700 hidden sm:inline">•</span>
            <span className="inline-flex items-center gap-1.5 text-zinc-300">
              <Zap className="size-3 text-[#28A0F0]" />
              <span>&lt; 130ms Socket Cutover SLA</span>
            </span>
            <span className="text-zinc-700 hidden sm:inline">•</span>
            <a
              href="https://github.com/maskalfreeup-glitch/driftguard/blob/main/docs/PILOT_PARTNER_LOI.md"
              target="_blank"
              rel="noreferrer"
              className="text-cyan-400 hover:underline flex items-center gap-1"
            >
              <span>LOI-2026-ORBIT-001 Verified</span>
              <ExternalLink className="size-2.5" />
            </a>
          </div>
        </div>

        {/* ══════════════════════════════════════════════════════════
            COLUMN 3: THE 1/3 LIVE SENTINEL TELEMETRY HUD & SHIELD
           ══════════════════════════════════════════════════════════ */}
        <div className="lg:col-span-5 xl:col-span-4">
          <div className="relative rounded-2xl border border-sky-500/25 bg-gradient-to-b from-zinc-900/90 to-zinc-950/95 p-4 sm:p-5 shadow-2xl backdrop-blur-xl overflow-hidden specular-border">
            {/* Top Atmospheric Glow */}
            <div className="absolute top-0 right-0 w-36 h-36 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />

            {/* HUD Titlebar */}
            <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3 mb-3.5">
              <div className="flex items-center gap-2">
                <span className="relative flex size-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex rounded-full size-2.5 bg-emerald-500" />
                </span>
                <span className="font-mono text-xs font-semibold text-white tracking-wider uppercase">
                  SENTINEL TELEMETRY HUD
                </span>
              </div>
              <Badge variant="outline" className="border-sky-500/30 bg-sky-950/40 text-[#28A0F0] text-[10px] font-mono">
                CYCLE: 200MS
              </Badge>
            </div>

            {/* Shield Isometric Brand Graphic */}
            <div className="relative flex justify-center py-2">
              <HeroBrandShield />
            </div>

            {/* Live Telemetry Tickers */}
            <div className="space-y-2 mt-2 pt-2 border-t border-zinc-800/80 font-mono text-xs">
              <div className="flex items-center justify-between p-2 rounded-lg bg-zinc-950/80 border border-zinc-800/80">
                <span className="text-[11px] text-zinc-400">Consensus Tip Parity</span>
                <span className={`text-[11px] font-bold flex items-center gap-1.5 ${
                  simStep === "drift" ? "text-amber-400" : "text-emerald-400"
                }`}>
                  <span className={`size-1.5 rounded-full ${
                    simStep === "drift" ? "bg-amber-400 animate-ping" : "bg-emerald-400"
                  }`} />
                  {simStep === "drift" ? "6 BLOCKS LAG DETECTED" : "PARITY (0 BLOCK DRIFT)"}
                </span>
              </div>

              <div className="flex items-center justify-between p-2 rounded-lg bg-zinc-950/80 border border-zinc-800/80">
                <span className="text-[11px] text-zinc-400">HAProxy L7 Ingress</span>
                <span className="text-[11px] font-bold text-zinc-200">
                  {simStep === "drain" || simStep === "recovered" ? (
                    <span className="text-cyan-400">FALLBACK POOL (DRAINED)</span>
                  ) : (
                    <span>PRIMARY (arb1.arbitrum.io)</span>
                  )}
                </span>
              </div>

              <div className="flex items-center justify-between p-2 rounded-lg bg-zinc-950/80 border border-zinc-800/80">
                <span className="text-[11px] text-zinc-400">Cutover Latency (MTTC)</span>
                <span className="text-[11px] font-bold text-[#28A0F0]">
                  {drillLatency ? `${drillLatency} ms` : "119.8 ms (Target <130ms)"}
                </span>
              </div>

              <div className="flex items-center justify-between p-2 rounded-lg bg-zinc-950/80 border border-zinc-800/80">
                <span className="text-[11px] text-zinc-400">POSIX Socket Control</span>
                <span className="text-[10px] text-zinc-400 font-mono">/run/haproxy/admin.sock</span>
              </div>
            </div>

            {/* Interactive Chaos Drill Test Button */}
            <div className="mt-3.5 pt-3 border-t border-zinc-800/80">
              <button
                onClick={runSimulatedDrill}
                disabled={isSimulating}
                className={`w-full py-2 px-3 rounded-lg font-mono text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
                  isSimulating
                    ? "bg-amber-950/60 border border-amber-600/50 text-amber-300 cursor-wait"
                    : "bg-sky-500/10 hover:bg-sky-500/20 border border-sky-500/30 text-[#28A0F0] hover:text-sky-300"
                }`}
              >
                {isSimulating ? (
                  <>
                    <RefreshCw className="size-3.5 animate-spin" />
                    <span>
                      {simStep === "drift" && "Simulating 6-Block Sequencer Drift..."}
                      {simStep === "drain" && "Tripping Sub-130ms UNIX Socket Drain!"}
                      {simStep === "recovered" && "Cutover Complete · Zero Packet Drops"}
                    </span>
                  </>
                ) : (
                  <>
                    <Activity className="size-3.5 text-[#28A0F0]" />
                    <span>Trigger Live Failover Drill Simulation</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
