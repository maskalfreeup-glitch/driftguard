import { BookOpen, ExternalLink, Terminal, MessageSquare, Github, ShieldCheck, Activity, Download, FileCode, Layers, Radio, Award } from "lucide-react"

interface ResourcesSectionProps {
  onSelectTab: (tab: "overview" | "rpc" | "docs" | "audit") => void
}

export function ResourcesSection({ onSelectTab }: ResourcesSectionProps) {
  return (
    <div className="pt-8 pb-12 border-t border-zinc-800/80">
      <div className="space-y-6">
        {/* Section Header */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-2 border-b border-zinc-800/80 pb-4">
          <div>
            <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-[#28A0F0] mb-1">
              DOCUMENTATION &amp; FIELD VERIFICATION MATRIX
            </div>
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
              Ecosystem Architecture &amp; Engineering Proof
            </h2>
          </div>
          <p className="text-xs text-zinc-400 font-mono">
            Structured into 3 Core Technical Domains
          </p>
        </div>

        {/* ── Rule of Thirds 3-Column Resource Matrix ── */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* ══════════════════════════════════════════════════════════
              PILLAR 1: PRODUCTION GATEWAYS & INTERACTIVE VIEWS
             ══════════════════════════════════════════════════════════ */}
          <div className="p-5 rounded-xl border border-zinc-800/80 bg-zinc-950/60 specular-border flex flex-col justify-between space-y-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between border-b border-zinc-800/80 pb-2">
                <span className="text-xs font-mono font-bold uppercase tracking-wider text-white flex items-center gap-2">
                  <Terminal className="size-4 text-[#28A0F0]" />
                  01 / Live Ingress &amp; Views
                </span>
                <span className="text-[10px] font-mono text-zinc-500">GATEWAYS</span>
              </div>
              <p className="text-xs text-zinc-400 leading-relaxed font-sans">
                Interactive edge gateways, RPC methods, and empirical production failover records.
              </p>

              <div className="space-y-2 pt-1 font-mono text-xs">
                <button
                  onClick={() => onSelectTab("rpc")}
                  className="w-full text-left p-2.5 rounded-lg bg-zinc-900/60 hover:bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-zinc-200 transition-colors flex items-center justify-between group"
                >
                  <span className="flex items-center gap-2 truncate">
                    <span className="size-1.5 rounded-full bg-emerald-400" />
                    <span>JSON-RPC Gateway Tester</span>
                  </span>
                  <span className="text-zinc-500 group-hover:text-white transition-colors">→</span>
                </button>

                <button
                  onClick={() => onSelectTab("audit")}
                  className="w-full text-left p-2.5 rounded-lg bg-zinc-900/60 hover:bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-zinc-200 transition-colors flex items-center justify-between group"
                >
                  <span className="flex items-center gap-2 truncate">
                    <span className="size-1.5 rounded-full bg-[#28A0F0]" />
                    <span>Incident Audit Ledger (18 Events)</span>
                  </span>
                  <span className="text-zinc-500 group-hover:text-white transition-colors">→</span>
                </button>

                <button
                  onClick={() => onSelectTab("docs")}
                  className="w-full text-left p-2.5 rounded-lg bg-zinc-900/60 hover:bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-zinc-200 transition-colors flex items-center justify-between group"
                >
                  <span className="flex items-center gap-2 truncate">
                    <span className="size-1.5 rounded-full bg-purple-400" />
                    <span>Daemon Deployment Specs</span>
                  </span>
                  <span className="text-zinc-500 group-hover:text-white transition-colors">→</span>
                </button>
              </div>
            </div>

            <div className="pt-3 border-t border-zinc-800/80 text-[11px] font-mono text-zinc-500 flex items-center gap-1.5">
              <ShieldCheck className="size-3 text-emerald-400" />
              <span>Multi-Chain Ingress Core (42161 · 42170 · 421614)</span>
            </div>
          </div>

          {/* ══════════════════════════════════════════════════════════
              PILLAR 2: TECHNICAL RFCS & ENGINEERING PROOF
             ══════════════════════════════════════════════════════════ */}
          <div className="p-5 rounded-xl border border-zinc-800/80 bg-zinc-950/60 specular-border flex flex-col justify-between space-y-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between border-b border-zinc-800/80 pb-2">
                <span className="text-xs font-mono font-bold uppercase tracking-wider text-white flex items-center gap-2">
                  <BookOpen className="size-4 text-emerald-400" />
                  02 / Technical RFCs &amp; Proof
                </span>
                <span className="text-[10px] font-mono text-zinc-500">STANDARDS</span>
              </div>
              <p className="text-xs text-zinc-400 leading-relaxed font-sans">
                Peer-reviewed architectural RFCs, partner letter of intent, and live field post-mortems.
              </p>

              <div className="space-y-2 pt-1 font-mono text-xs">
                <a
                  href="https://github.com/maskalfreeup-glitch/driftguard/blob/main/docs/guides/HIGH_THROUGHPUT_INGRESS_GUIDE.md"
                  target="_blank"
                  rel="noreferrer"
                  className="p-2.5 rounded-lg bg-zinc-900/60 hover:bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-zinc-200 transition-colors flex items-center justify-between group block"
                >
                  <span className="flex items-center gap-2 truncate">
                    <FileCode className="size-3.5 text-zinc-400 group-hover:text-[#28A0F0]" />
                    <span>High-Throughput Ingress Guide</span>
                  </span>
                  <ExternalLink className="size-3 text-zinc-500 group-hover:text-white" />
                </a>

                <a
                  href="https://github.com/maskalfreeup-glitch/driftguard/blob/main/docs/PILOT_PARTNER_LOI.md"
                  target="_blank"
                  rel="noreferrer"
                  className="p-2.5 rounded-lg bg-zinc-900/60 hover:bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-zinc-200 transition-colors flex items-center justify-between group block"
                >
                  <span className="flex items-center gap-2 truncate">
                    <Award className="size-3.5 text-cyan-400" />
                    <span>Pilot Partner LOI-2026-ORBIT-001</span>
                  </span>
                  <ExternalLink className="size-3 text-zinc-500 group-hover:text-white" />
                </a>

                <a
                  href="https://github.com/maskalfreeup-glitch/driftguard/blob/main/docs/reports/INCIDENT_2026-10-04_ARBITRUM_DESYNC.md"
                  target="_blank"
                  rel="noreferrer"
                  className="p-2.5 rounded-lg bg-zinc-900/60 hover:bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-zinc-200 transition-colors flex items-center justify-between group block"
                >
                  <span className="flex items-center gap-2 truncate">
                    <Activity className="size-3.5 text-amber-400" />
                    <span>Arbitrum Desync Post-Mortem (2026-10-04)</span>
                  </span>
                  <ExternalLink className="size-3 text-zinc-500 group-hover:text-white" />
                </a>

                <a
                  href="https://github.com/maskalfreeup-glitch/driftguard/blob/main/docs/reports/INCIDENT_LEDGER.md"
                  target="_blank"
                  rel="noreferrer"
                  className="p-2.5 rounded-lg bg-zinc-900/60 hover:bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-zinc-200 transition-colors flex items-center justify-between group block"
                >
                  <span className="flex items-center gap-2 truncate">
                    <Layers className="size-3.5 text-purple-400" />
                    <span>Incident Ledger &amp; SRE Telemetry</span>
                  </span>
                  <ExternalLink className="size-3 text-zinc-500 group-hover:text-white" />
                </a>
              </div>
            </div>

            <div className="pt-3 border-t border-zinc-800/80 text-[11px] font-mono text-zinc-500 flex items-center gap-1.5">
              <ShieldCheck className="size-3 text-emerald-400" />
              <span>Full Open-Source Engineering Documentation</span>
            </div>
          </div>

          {/* ══════════════════════════════════════════════════════════
              PILLAR 3: COMMUNITY & TELEMETRY OPERATIONS
             ══════════════════════════════════════════════════════════ */}
          <div className="p-5 rounded-xl border border-zinc-800/80 bg-zinc-950/60 specular-border flex flex-col justify-between space-y-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between border-b border-zinc-800/80 pb-2">
                <span className="text-xs font-mono font-bold uppercase tracking-wider text-white flex items-center gap-2">
                  <Radio className="size-4 text-purple-400" />
                  03 / Community &amp; Telemetry
                </span>
                <span className="text-[10px] font-mono text-zinc-500">LIVE OPS</span>
              </div>
              <p className="text-xs text-zinc-400 leading-relaxed font-sans">
                Real-time operational streams, Discord alert bots, and open-source codebase.
              </p>

              <div className="space-y-2 pt-1 font-mono text-xs">
                <a
                  href="https://discord.gg/DZBDJSsSzN"
                  target="_blank"
                  rel="noreferrer"
                  className="p-2.5 rounded-lg bg-[#5865F2]/10 hover:bg-[#5865F2]/20 border border-[#5865F2]/30 text-white transition-colors flex items-center justify-between group block"
                >
                  <span className="flex items-center gap-2 truncate">
                    <MessageSquare className="size-3.5 text-[#5865F2]" />
                    <span>Discord #bot-stats Live Stream</span>
                  </span>
                  <ExternalLink className="size-3 text-zinc-400 group-hover:text-white" />
                </a>

                <a
                  href="https://github.com/maskalfreeup-glitch/driftguard"
                  target="_blank"
                  rel="noreferrer"
                  className="p-2.5 rounded-lg bg-zinc-900/60 hover:bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-zinc-200 transition-colors flex items-center justify-between group block"
                >
                  <span className="flex items-center gap-2 truncate">
                    <Github className="size-3.5 text-zinc-300" />
                    <span>GitHub: maskalfreeup-glitch/driftguard</span>
                  </span>
                  <ExternalLink className="size-3 text-zinc-500 group-hover:text-white" />
                </a>

                <a
                  href="/driftguard-explainer.mp4"
                  download="driftguard-explainer-1080p.mp4"
                  className="p-2.5 rounded-lg bg-zinc-900/60 hover:bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-zinc-200 transition-colors flex items-center justify-between group block"
                >
                  <span className="flex items-center gap-2 truncate">
                    <Download className="size-3.5 text-[#28A0F0]" />
                    <span>Download 1080p Master (5.8 MB)</span>
                  </span>
                  <span className="text-zinc-500 text-[10px]">MP4</span>
                </a>
              </div>
            </div>

            <div className="pt-3 border-t border-zinc-800/80 text-[11px] font-mono text-zinc-500 flex items-center gap-1.5">
              <span className="size-2 rounded-full bg-emerald-500" />
              <span>Real-Time ISO-8601 UTC Discord Webhook</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
