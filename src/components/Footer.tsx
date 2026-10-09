import { DriftGuardLogo } from "@/components/DriftGuardLogo"
import { ExternalLink, ShieldCheck, Github, MessageSquare, Download, BookOpen, Terminal, Activity } from "lucide-react"

interface FooterProps {
  onSelectTab: (tab: "overview" | "rpc" | "docs" | "audit") => void
}

export function Footer({ onSelectTab }: FooterProps) {
  return (
    <footer className="border-t border-zinc-800/80 bg-[#07080b] text-zinc-400 text-xs pb-16 md:pb-8 pt-12 mt-12">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        {/* ── Rule of Thirds 3-Column Footer Grid ── */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 pb-10 border-b border-zinc-800/80">
          {/* ══════════════════════════════════════════════════════════
              COLUMN 1: BRAND, CORE MANDATE & OPEN SOURCE
             ══════════════════════════════════════════════════════════ */}
          <div className="space-y-4">
            <div className="cursor-pointer inline-block" onClick={() => onSelectTab("overview")}>
              <DriftGuardLogo iconSize={30} showBadge={true} />
            </div>

            <p className="text-zinc-400 text-xs leading-relaxed max-w-sm font-sans">
              Open-source consensus ingress gateway and out-of-band drift detection sentinel for Arbitrum Nitro, Orbit chains, and transaction relayers. Sub-130ms POSIX socket state transition with zero dropped requests.
            </p>

            <div className="space-y-1.5 font-mono text-[11px] text-zinc-500">
              <div className="flex items-center gap-2">
                <span className="size-2 rounded-full bg-emerald-500" />
                <span className="text-zinc-300">Open-Source Core (MIT License)</span>
              </div>
              <div className="flex items-center gap-2">
                <ShieldCheck className="size-3.5 text-[#28A0F0]" />
                <span>Zero Client SDK Modifications Required</span>
              </div>
            </div>
          </div>

          {/* ══════════════════════════════════════════════════════════
              COLUMN 2: TECHNICAL RFCS & FIELD EVIDENCE
             ══════════════════════════════════════════════════════════ */}
          <div className="space-y-3 font-mono">
            <div className="text-[11px] uppercase tracking-wider text-white font-semibold flex items-center gap-2">
              <BookOpen className="size-3.5 text-emerald-400" />
              <span>Technical Standards &amp; RFCs</span>
            </div>

            <ul className="space-y-2 text-xs">
              <li>
                <a
                  href="https://github.com/maskalfreeup-glitch/driftguard/blob/main/docs/guides/HIGH_THROUGHPUT_INGRESS_GUIDE.md"
                  target="_blank"
                  rel="noreferrer"
                  className="hover:text-white transition-colors flex items-center gap-1.5 text-zinc-300"
                >
                  <span>High-Throughput Ingress Guide</span>
                  <ExternalLink className="size-3 text-zinc-500" />
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/maskalfreeup-glitch/driftguard#architecture"
                  target="_blank"
                  rel="noreferrer"
                  className="hover:text-white transition-colors flex items-center gap-1.5 text-zinc-300"
                >
                  <span>Protocol Architecture Specification</span>
                  <ExternalLink className="size-3 text-zinc-500" />
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/maskalfreeup-glitch/driftguard/blob/main/docs/reports/INCIDENT_2026-10-04_ARBITRUM_DESYNC.md"
                  target="_blank"
                  rel="noreferrer"
                  className="hover:text-white transition-colors flex items-center gap-1.5 text-zinc-300"
                >
                  <span>Arbitrum Desync Post-Mortem (2026-10-04)</span>
                  <ExternalLink className="size-3 text-zinc-500" />
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/maskalfreeup-glitch/driftguard/blob/main/docs/reports/INCIDENT_LEDGER.md"
                  target="_blank"
                  rel="noreferrer"
                  className="hover:text-white transition-colors flex items-center gap-1.5 text-zinc-300"
                >
                  <span>Incident Ledger &amp; SRE Docs</span>
                  <ExternalLink className="size-3 text-zinc-500" />
                </a>
              </li>
            </ul>
          </div>

          {/* ══════════════════════════════════════════════════════════
              COLUMN 3: PLATFORM GATEWAYS & COMMUNITY OPERATIONS
             ══════════════════════════════════════════════════════════ */}
          <div className="space-y-3 font-mono">
            <div className="text-[11px] uppercase tracking-wider text-white font-semibold flex items-center gap-2">
              <Terminal className="size-3.5 text-[#28A0F0]" />
              <span>Gateways &amp; Live Telemetry</span>
            </div>

            <ul className="space-y-2 text-xs">
              <li>
                <button
                  onClick={() => onSelectTab("rpc")}
                  className="hover:text-white transition-colors flex items-center gap-1.5 text-zinc-300 text-left"
                >
                  <Terminal className="size-3 text-emerald-400" />
                  <span>JSON-RPC Gateway Tester</span>
                </button>
              </li>
              <li>
                <button
                  onClick={() => onSelectTab("audit")}
                  className="hover:text-white transition-colors flex items-center gap-1.5 text-zinc-300 text-left"
                >
                  <Activity className="size-3 text-[#28A0F0]" />
                  <span>Incident Audit Ledger (18 Events)</span>
                </button>
              </li>
              <li>
                <a
                  href="https://discord.gg/DZBDJSsSzN"
                  target="_blank"
                  rel="noreferrer"
                  className="hover:text-white transition-colors flex items-center gap-1.5 text-zinc-300"
                >
                  <MessageSquare className="size-3 text-[#5865F2]" />
                  <span>Discord #bot-stats Live Alerts</span>
                  <ExternalLink className="size-3 text-zinc-500" />
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/maskalfreeup-glitch/driftguard"
                  target="_blank"
                  rel="noreferrer"
                  className="hover:text-white transition-colors flex items-center gap-1.5 text-zinc-300"
                >
                  <Github className="size-3 text-zinc-400" />
                  <span>GitHub Repository &amp; Issues</span>
                  <ExternalLink className="size-3 text-zinc-500" />
                </a>
              </li>
              <li>
                <a
                  href="/driftguard-explainer.mp4"
                  download="driftguard-explainer.mp4"
                  className="hover:text-white transition-colors flex items-center gap-1.5 text-zinc-400"
                >
                  <Download className="size-3 text-[#28A0F0]" />
                  <span>Architecture Walkthrough Video (MP4)</span>
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* ── Bottom Disclaimer & Metadata Bar ── */}
        <div className="pt-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px] text-zinc-500 font-mono">
          <div>
            <span>DriftGuard Open-Source Project</span>
            <span className="mx-2">·</span>
            <span>MIT License • Arbitrum Nitro &amp; Orbit Ingress</span>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-zinc-400">Docker Sidecar RSS &lt; 45MB</span>
            <span>·</span>
            <span>Arbitrum Nitro EVM Compatible</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
