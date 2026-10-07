import { useState, useRef } from "react"
import { Film, Terminal, Download, ExternalLink, BookOpen, Layers, Server, Activity, ShieldCheck } from "lucide-react"
import { Badge } from "@/components/ui/badge"

export function ExplainerShowcase() {
  const [mediaMode, setMediaMode] = useState<"video" | "terminal">("video")
  const [activeChapter, setActiveChapter] = useState(0)
  const videoRef = useRef<HTMLVideoElement>(null)

  const chapters = [
    { label: "00:00 Intro", time: 0 },
    { label: "00:02 Overview", time: 2 },
    { label: "00:23 Problem", time: 23 },
    { label: "00:43 Architecture", time: 43 },
    { label: "01:04 QuickStart", time: 64 },
    { label: "01:21 Failover Drill", time: 81 },
    { label: "01:38 Ecosystem", time: 98 },
    { label: "01:53 Open Source", time: 113 },
  ]

  const seekToChapter = (seconds: number, index: number) => {
    setActiveChapter(index)
    setMediaMode("video")
    if (videoRef.current) {
      videoRef.current.currentTime = seconds
      videoRef.current.play().catch(() => {})
    }
  }

  return (
    <div id="explainer-video" className="space-y-4 pt-2">
      {/* Header with Title and Mode Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-1">
        <div className="flex items-center gap-2">
          <Film className="size-4 text-[#28A0F0]" />
          <h2 className="text-sm font-mono tracking-tight font-semibold text-white uppercase">
            Architectural Explainer &amp; Failover Walkthrough
          </h2>
        </div>

        {/* Media Switcher: Video vs Asciinema Terminal */}
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <div className="flex items-center bg-zinc-900/90 p-1 rounded-lg border border-zinc-800 text-xs font-mono">
            <button
              onClick={() => setMediaMode("video")}
              className={`px-3 py-1 rounded-md transition-all flex items-center gap-1.5 ${
                mediaMode === "video"
                  ? "bg-zinc-800 text-white font-medium shadow-sm"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              <Film className="size-3 text-[#28A0F0]" />
              <span>1080p Video</span>
            </button>
            <button
              onClick={() => setMediaMode("terminal")}
              className={`px-3 py-1 rounded-md transition-all flex items-center gap-1.5 ${
                mediaMode === "terminal"
                  ? "bg-zinc-800 text-white font-medium shadow-sm"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              <Terminal className="size-3 text-emerald-400" />
              <span>Terminal Drill</span>
            </button>
          </div>

          <Badge variant="outline" className="border-sky-800/80 bg-sky-950/40 text-[#28A0F0] text-[10px] font-mono tracking-wider hidden md:inline-flex">
            1080P MASTER
          </Badge>
        </div>
      </div>

      {/* ── Rule of Thirds Asymmetric 2/3 + 1/3 Layout ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* ══════════════════════════════════════════════════════════
            2/3 COLUMN: THE PLAYER CONTAINER (Video / Terminal)
           ══════════════════════════════════════════════════════════ */}
        <div className="lg:col-span-8 space-y-3">
          <div className="specular-border rounded-xl border border-zinc-800/80 bg-zinc-950/90 overflow-hidden shadow-2xl backdrop-blur-sm">
            {/* Window Titlebar */}
            <div className="flex items-center justify-between px-3 sm:px-4 py-2.5 border-b border-zinc-800/80 bg-zinc-950/95">
              <div className="flex items-center gap-2 min-w-0">
                <div className="flex items-center gap-1.5 shrink-0">
                  <span className="size-2 rounded-full bg-red-500/80 inline-block" />
                  <span className="size-2 rounded-full bg-yellow-500/80 inline-block" />
                  <span className="size-2 rounded-full bg-emerald-500/80 inline-block" />
                </div>
                <span className="ml-1 font-mono text-[11px] sm:text-xs text-zinc-400 truncate">
                  {mediaMode === "video"
                    ? "driftguard-explainer-master-1080p.mp4 — Consensus Sentinel Walkthrough"
                    : "driftguard-failover-drill.cast — sub-130ms UNIX socket verification"}
                </span>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                {mediaMode === "video" ? (
                  <>
                    <a
                      href="/driftguard-explainer.mp4"
                      download="driftguard-explainer-1080p.mp4"
                      className="text-zinc-400 hover:text-white transition-colors p-1 rounded hover:bg-zinc-800/60"
                      title="Download 1080p MP4 Video"
                    >
                      <Download className="size-3.5" />
                    </a>
                    <a
                      href="/driftguard-explainer.mp4"
                      target="_blank"
                      rel="noreferrer"
                      className="text-zinc-400 hover:text-white transition-colors p-1 rounded hover:bg-zinc-800/60"
                      title="Open video in new tab"
                    >
                      <ExternalLink className="size-3.5" />
                    </a>
                  </>
                ) : (
                  <span className="text-[11px] font-mono text-[#28A0F0] flex items-center gap-1">
                    <span className="size-1.5 rounded-full bg-[#28A0F0] animate-pulse" />
                    Sub-130ms Drill
                  </span>
                )}
              </div>
            </div>

            {/* Media Content Area */}
            <div className="relative bg-black aspect-video flex items-center justify-center overflow-hidden">
              {mediaMode === "video" ? (
                <video
                  ref={videoRef}
                  controls
                  preload="metadata"
                  poster="/driftguard-explainer-poster.png"
                  className="w-full h-full object-contain"
                >
                  <source src="/driftguard-explainer.mp4" type="video/mp4" />
                  Your browser does not support the video tag.
                </video>
              ) : (
                <img
                  src="/failover-demo.gif"
                  alt="DriftGuard Failover Drill"
                  className="w-full h-full object-contain"
                />
              )}
            </div>

            {/* Mobile-Optimized Horizontal Chapter Scroller */}
            <div className="p-3 bg-zinc-950/95 border-t border-zinc-800/80">
              <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar scroll-smooth py-0.5">
                <span className="text-zinc-500 font-mono text-[10px] uppercase tracking-wider shrink-0 mr-1 hidden sm:inline">
                  Chapters:
                </span>
                {chapters.map((ch, idx) => (
                  <button
                    key={idx}
                    onClick={() => seekToChapter(ch.time, idx)}
                    className={`px-2.5 py-1 rounded text-[11px] font-mono whitespace-nowrap transition-colors shrink-0 cursor-pointer ${
                      activeChapter === idx && mediaMode === "video"
                        ? "bg-sky-500/20 text-[#28A0F0] border border-sky-500/40 font-semibold"
                        : "bg-zinc-900 hover:bg-zinc-800 border border-zinc-800/80 text-zinc-400 hover:text-white"
                    }`}
                  >
                    {ch.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* ══════════════════════════════════════════════════════════
            1/3 COLUMN: ARCHITECTURAL BLUEPRINT (Dual-Plane Decoupling)
           ══════════════════════════════════════════════════════════ */}
        <div className="lg:col-span-4 space-y-3">
          <div className="specular-border rounded-xl border border-zinc-800/80 bg-zinc-950/80 p-4 sm:p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
              <div className="flex items-center gap-2">
                <Layers className="size-4 text-[#28A0F0]" />
                <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-white">
                  Dual-Plane Architecture
                </h3>
              </div>
              <Badge variant="outline" className="border-emerald-800/80 bg-emerald-950/40 text-emerald-400 text-[10px] font-mono">
                RFC-5841
              </Badge>
            </div>

            {/* Plane 1: Data Plane */}
            <div className="p-3 rounded-lg bg-zinc-900/60 border border-zinc-800/80 space-y-1">
              <div className="flex items-center justify-between text-xs font-mono font-semibold text-white">
                <span className="flex items-center gap-1.5">
                  <Server className="size-3.5 text-[#28A0F0]" />
                  01 / L7 Data Plane
                </span>
                <span className="text-[10px] text-zinc-400 font-mono">&lt; 3ms Latency</span>
              </div>
              <p className="text-[11px] text-zinc-400 leading-relaxed font-sans">
                Native HAProxy C-runtime forwarding JSON-RPC requests directly to active sequencers. Zero Python serialization overhead in client data path.
              </p>
            </div>

            {/* Plane 2: Control Plane */}
            <div className="p-3 rounded-lg bg-zinc-900/60 border border-zinc-800/80 space-y-1">
              <div className="flex items-center justify-between text-xs font-mono font-semibold text-white">
                <span className="flex items-center gap-1.5">
                  <Activity className="size-3.5 text-emerald-400" />
                  02 / Control Plane
                </span>
                <span className="text-[10px] text-zinc-400 font-mono">200ms Async Poller</span>
              </div>
              <p className="text-[11px] text-zinc-400 leading-relaxed font-sans">
                Out-of-band asynchronous Python daemon actively queries canonical anchors, detecting head divergence before client timeouts occur.
              </p>
            </div>

            {/* Plane 3: POSIX Socket IPC */}
            <div className="p-3 rounded-lg bg-zinc-900/60 border border-zinc-800/80 space-y-1">
              <div className="flex items-center justify-between text-xs font-mono font-semibold text-white">
                <span className="flex items-center gap-1.5">
                  <Terminal className="size-3.5 text-purple-400" />
                  03 / UNIX Socket IPC
                </span>
                <span className="text-[10px] text-[#28A0F0] font-mono">&lt; 130ms Drain</span>
              </div>
              <p className="text-[11px] text-zinc-400 leading-relaxed font-sans">
                Executes <code className="text-zinc-200">set server state maint</code> directly on HAProxy runtime socket. Existing in-flight connections finish gracefully with zero TCP RSTs.
              </p>
            </div>

            {/* Direct RFC & Spec Links */}
            <div className="pt-2 border-t border-zinc-800/80 flex flex-col gap-2">
              <a
                href="https://github.com/maskalfreeup-glitch/driftguard/blob/main/docs/guides/HIGH_THROUGHPUT_INGRESS_GUIDE.md"
                target="_blank"
                rel="noreferrer"
                className="text-xs text-[#28A0F0] hover:text-sky-300 transition-colors flex items-center justify-between font-mono font-medium p-2 rounded bg-sky-950/30 border border-sky-800/50"
              >
                <span className="flex items-center gap-1.5">
                  <BookOpen className="size-3" />
                  <span>High-Throughput Ingress RFC</span>
                </span>
                <ExternalLink className="size-3" />
              </a>

              <a
                href="https://github.com/maskalfreeup-glitch/driftguard/blob/main/docs/PILOT_PARTNER_LOI.md"
                target="_blank"
                rel="noreferrer"
                className="text-xs text-zinc-300 hover:text-white transition-colors flex items-center justify-between font-mono p-2 rounded bg-zinc-900/80 border border-zinc-800"
              >
                <span className="flex items-center gap-1.5">
                  <ShieldCheck className="size-3 text-emerald-400" />
                  <span>Pilot Partner Verification (LOI)</span>
                </span>
                <ExternalLink className="size-3" />
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
