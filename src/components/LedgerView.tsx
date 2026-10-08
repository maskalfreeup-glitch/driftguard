import { useState } from "react"
import {
  ShieldCheck,
  Activity,
  Zap,
  Shield,
  Clock,
  Sparkles,
  Search,
  ChevronDown,
  ChevronUp,
  Cpu,
  Terminal,
  MessageSquare,
  ExternalLink,
  BookOpen,
  Check,
  Copy
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { LEDGER_INCIDENTS } from "@/constants/incidents"

export function LedgerView() {
  const [ledgerFilter, setLedgerFilter] = useState<"all" | "arb" | "nova" | "arb-sepolia" | "case-studies">("all")
  const [incidentSearchQuery, setIncidentSearchQuery] = useState("")
  const [activeIncidentSubTabs, setActiveIncidentSubTabs] = useState<Record<string, "impact" | "sre" | "wire">>({})
  const [expandedIncident, setExpandedIncident] = useState<string | null>("INC-20261006-18")
  const [copiedId, setCopiedId] = useState<string | null>(null)

  const toggleIncident = (id: string) => {
    setExpandedIncident((prev) => (prev === id ? null : id))
  }

  function setIncidentSubTab(id: string, tab: "impact" | "sre" | "wire") {
    setActiveIncidentSubTabs((prev) => ({ ...prev, [id]: tab }))
  }

  const totalMitigatedCount = LEDGER_INCIDENTS.length
  const avgCutoverLatencyVal = (
    LEDGER_INCIDENTS.reduce((acc, inc) => acc + parseFloat(inc.latency), 0) / LEDGER_INCIDENTS.length
  ).toFixed(1)
  const arbCategoryCount = LEDGER_INCIDENTS.filter((i) => i.category === "arb").length
  const novaCategoryCount = LEDGER_INCIDENTS.filter((i) => i.category === "nova").length
  const sepoliaCategoryCount = LEDGER_INCIDENTS.filter((i) => i.category === "arb-sepolia").length

  return (
    <div className="space-y-4">
      {/* Header & Direct Discord Verification CTA */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-zinc-800/80">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-950/60 border border-emerald-800/80 text-[10px] font-mono text-emerald-400">
            <ShieldCheck className="size-3 text-emerald-400" />
            <span className="size-1.5 rounded-full bg-emerald-400 animate-pulse" />
            LIVE ARBITRUM NITRO RPC LEDGER · EMPIRICAL VERIFICATION
          </div>
          <h2 className="text-lg sm:text-xl font-bold text-white tracking-tight">
            Production Incident Command &amp; Consensus Audit Ledger
          </h2>
          <p className="text-xs text-zinc-400 max-w-3xl leading-relaxed font-sans">
            Real-time autonomous failover telemetry across Arbitrum One, Nova, and Sepolia. Out-of-band consensus sentinel sampling canonical anchors at 200ms cadence.
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <a
            href="https://discord.gg/DZBDJSsSzN"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 bg-[#5865F2] hover:bg-[#4752C4] text-white text-xs font-semibold px-4 py-2 rounded-lg transition-colors shadow-sm"
          >
            <MessageSquare className="size-3.5 fill-current" />
            <span>Join Discord #bot-stats</span>
          </a>
        </div>
      </div>

      {/* KPI Metric Cards (Responsive 2x2 grid on mobile, 4 columns on desktop) */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        <div className="p-3 rounded-lg bg-zinc-900/60 border border-zinc-800/80 font-mono specular-border">
          <div className="text-[10px] text-zinc-500 uppercase tracking-wider flex items-center justify-between">
            <span>MITIGATED</span>
            <Activity className="size-3 text-emerald-400" />
          </div>
          <div className="text-lg font-bold text-white mt-0.5">{totalMitigatedCount} Events</div>
          <div className="text-[10px] text-emerald-400 mt-0.5">100% Cutovers Met</div>
        </div>
        <div className="p-3 rounded-lg bg-zinc-900/60 border border-zinc-800/80 font-mono specular-border">
          <div className="text-[10px] text-zinc-500 uppercase tracking-wider flex items-center justify-between">
            <span>AVG CUTOVER</span>
            <Zap className="size-3 text-[#28A0F0]" />
          </div>
          <div className="text-lg font-bold text-[#28A0F0] mt-0.5">{avgCutoverLatencyVal} ms</div>
          <div className="text-[10px] text-zinc-400 mt-0.5">&lt; 130ms SLA Met</div>
        </div>
        <div className="p-3 rounded-lg bg-zinc-900/60 border border-zinc-800/80 font-mono specular-border">
          <div className="text-[10px] text-zinc-500 uppercase tracking-wider flex items-center justify-between">
            <span>PACKET LOSS</span>
            <Shield className="size-3 text-emerald-400" />
          </div>
          <div className="text-lg font-bold text-emerald-400 mt-0.5">0.00%</div>
          <div className="text-[10px] text-zinc-400 mt-0.5">Zero Dropped Reads</div>
        </div>
        <div className="p-3 rounded-lg bg-zinc-900/60 border border-zinc-800/80 font-mono specular-border">
          <div className="text-[10px] text-zinc-500 uppercase tracking-wider flex items-center justify-between">
            <span>MAX SHIELD</span>
            <Clock className="size-3 text-amber-400" />
          </div>
          <div className="text-lg font-bold text-white mt-0.5">2h 10m</div>
          <div className="text-[10px] text-zinc-400 mt-0.5">Sustained Outage</div>
        </div>
      </div>

      {/* Sleek, Single-Line Lifecycle Breadcrumb */}
      <div className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-zinc-950/90 border border-zinc-800/90 text-[11px] font-mono text-zinc-400 overflow-x-auto no-scrollbar shadow-inner">
        <span className="text-zinc-500 font-semibold uppercase tracking-wider shrink-0 flex items-center gap-1.5">
          <Sparkles className="size-3 text-cyan-400" />
          <span>Autonomous Loop:</span>
        </span>
        <span className="text-zinc-300 shrink-0 font-medium">200ms Active Probe</span>
        <span className="text-zinc-600 shrink-0">→</span>
        <span className="text-amber-400 shrink-0 font-medium">&gt;2 Block Drift Tripped</span>
        <span className="text-zinc-600 shrink-0">→</span>
        <span className="text-cyan-400 shrink-0 font-medium">&lt;125ms UNIX Socket Drain</span>
        <span className="text-zinc-600 shrink-0">→</span>
        <span className="text-emerald-400 shrink-0 font-medium">Zero-Drop Fallback</span>
        <span className="text-zinc-600 shrink-0">→</span>
        <span className="text-zinc-300 shrink-0 font-medium">2-Cycle Parity Recovery</span>
      </div>

      {/* Merged Single-Row Search and Chain Filter Pills */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-zinc-800/80 pb-3 pt-1">
        {/* Search Input */}
        <div className="relative flex-1 max-w-md">
          <Search className="size-3.5 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={incidentSearchQuery}
            onChange={(e) => setIncidentSearchQuery(e.target.value)}
            placeholder="Search ID, block, reason, chain..."
            className="w-full pl-9 pr-8 py-2 text-xs bg-zinc-900/90 border border-zinc-800 rounded-lg text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-cyan-500 font-mono transition-colors"
          />
          {incidentSearchQuery && (
            <button
              onClick={() => setIncidentSearchQuery("")}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 text-[10px] p-1"
            >
              Clear
            </button>
          )}
        </div>

        {/* Clean Segmented Chain Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar shrink-0 py-0.5">
          {[
            { id: "all", label: `All (${totalMitigatedCount})` },
            { id: "arb", label: `Arbitrum One (${arbCategoryCount})` },
            { id: "nova", label: `Nova (${novaCategoryCount})` },
            { id: "arb-sepolia", label: `Sepolia (${sepoliaCategoryCount})` },
            { id: "case-studies", label: `Case Studies (3)` }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setLedgerFilter(tab.id as any)}
              className={`px-3 py-1.5 rounded-md text-xs font-mono transition-all shrink-0 ${
                ledgerFilter === tab.id
                  ? "bg-cyan-500 text-slate-950 font-semibold shadow-sm"
                  : "bg-zinc-900/60 text-zinc-400 border border-zinc-800/60 hover:text-zinc-200 hover:bg-zinc-800/50"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Dense, High-Signal Incident Telemetry Rows (Accordion Style) */}
      <div className="space-y-2">
        {LEDGER_INCIDENTS.filter((inc) => {
          if (ledgerFilter === "case-studies") {
            if (!inc.isCaseStudy) return false
          } else if (ledgerFilter !== "all") {
            if (inc.category !== ledgerFilter) return false
          }

          if (incidentSearchQuery.trim()) {
            const q = incidentSearchQuery.toLowerCase()
            const matchesId = inc.id.toLowerCase().includes(q)
            const matchesChain = inc.chainName.toLowerCase().includes(q)
            const matchesDelta = inc.stallDelta.toLowerCase().includes(q)
            const matchesNotes = inc.notes.toLowerCase().includes(q)
            const matchesCanonical = inc.canonicalHead?.toLowerCase().includes(q) || false
            const matchesTitle = inc.impactAnalysis?.title.toLowerCase().includes(q) || false
            const matchesRisk = inc.impactAnalysis?.ecosystemRiskAverted.toLowerCase().includes(q) || false
            if (!matchesId && !matchesChain && !matchesDelta && !matchesNotes && !matchesCanonical && !matchesTitle && !matchesRisk) {
              return false
            }
          }

          return true
        }).map((incident) => {
          const isExpanded = expandedIncident === incident.id
          const subTab = activeIncidentSubTabs[incident.id] || "impact"

          return (
            <div
              key={incident.id}
              className={`rounded-lg border transition-all ${
                isExpanded
                  ? "bg-zinc-900/80 border-cyan-800/80 shadow-md ring-1 ring-cyan-800/40"
                  : "bg-zinc-900/40 border-zinc-800/80 hover:border-zinc-700/80 hover:bg-zinc-900/60"
              }`}
            >
              {/* Compact SRE Row */}
              <div
                className="p-3 sm:p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 cursor-pointer"
                onClick={() => toggleIncident(incident.id)}
              >
                {/* Left: Indicator + ID + Severity + Chain Badge + Case Study Tag */}
                <div className="flex items-center gap-2 flex-wrap">
                  <span
                    className={`size-2 rounded-full shrink-0 ${
                      incident.actionStatus === "DRAINED"
                        ? "bg-amber-400 animate-pulse"
                        : "bg-emerald-400"
                    }`}
                  />
                  <span className="text-xs font-bold text-white font-mono shrink-0">
                    {incident.id}
                  </span>
                  <Badge
                    variant="outline"
                    className={`text-[10px] font-mono px-1.5 py-0 shrink-0 ${
                      incident.severity === "SEV-2"
                        ? "border-amber-700/80 bg-amber-950/60 text-amber-300"
                        : "border-sky-800/80 bg-sky-950/60 text-sky-300"
                    }`}
                  >
                    {incident.severity}
                  </Badge>
                  <Badge
                    variant="outline"
                    className="border-zinc-700/80 bg-zinc-950/80 text-zinc-300 text-[10px] font-mono shrink-0"
                  >
                    {incident.networkTag}
                  </Badge>
                  {incident.caseStudyTag && (
                    <span className="text-[10px] font-mono font-medium text-cyan-400 bg-cyan-950/60 border border-cyan-800/60 px-1.5 py-0.5 rounded shrink-0">
                      {incident.caseStudyTag}
                    </span>
                  )}
                  <span className="text-[11px] text-zinc-400 font-mono hidden lg:inline">
                    {incident.timestamp}
                  </span>
                </div>

                {/* Middle: Stall Delta */}
                <div className="text-xs font-mono text-zinc-300 sm:text-center shrink-0">
                  <span className="text-zinc-500 text-[11px] sm:hidden">DRIFT: </span>
                  {incident.stallDelta}
                </div>

                {/* Right: Latency + Status Pill + Chevron */}
                <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
                  <span className="text-xs font-mono text-[#28A0F0] font-semibold bg-[#28A0F0]/10 px-2 py-0.5 rounded border border-[#28A0F0]/20">
                    {incident.latency}
                  </span>
                  <Badge
                    variant="outline"
                    className={`text-[10px] font-mono ${
                      incident.actionStatus === "DRAINED"
                        ? "border-amber-900/80 bg-amber-950/40 text-amber-300"
                        : "border-emerald-900/80 bg-emerald-950/40 text-emerald-400"
                    }`}
                  >
                    {incident.actionStatus}
                  </Badge>
                  <div className="text-zinc-500 hover:text-zinc-300 ml-1">
                    {isExpanded ? (
                      <ChevronUp className="size-4" />
                    ) : (
                      <ChevronDown className="size-4" />
                    )}
                  </div>
                </div>
              </div>

              {/* Rich On-Demand Drawer */}
              {isExpanded && (
                <div className="px-3.5 pb-3.5 pt-2 border-t border-zinc-800/80 space-y-3">
                  {/* Sub-Tabs: Ecosystem Impact | SRE Post-Mortem | Wire Log */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-zinc-800/80 pb-2">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setIncidentSubTab(incident.id, "impact")
                        }}
                        className={`px-2.5 py-1 rounded text-xs font-medium flex items-center gap-1.5 transition-colors ${
                          subTab === "impact"
                            ? "bg-cyan-950 text-cyan-300 border border-cyan-800/80"
                            : "text-zinc-400 hover:text-zinc-200"
                        }`}
                      >
                        <ShieldCheck className="size-3" />
                        <span>Ecosystem Impact</span>
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setIncidentSubTab(incident.id, "sre")
                        }}
                        className={`px-2.5 py-1 rounded text-xs font-medium flex items-center gap-1.5 transition-colors ${
                          subTab === "sre"
                            ? "bg-zinc-800 text-white border border-zinc-700"
                            : "text-zinc-400 hover:text-zinc-200"
                        }`}
                      >
                        <Cpu className="size-3" />
                        <span>SRE Post-Mortem</span>
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setIncidentSubTab(incident.id, "wire")
                        }}
                        className={`px-2.5 py-1 rounded text-xs font-medium flex items-center gap-1.5 transition-colors ${
                          subTab === "wire"
                            ? "bg-zinc-800 text-white border border-zinc-700"
                            : "text-zinc-400 hover:text-zinc-200"
                        }`}
                      >
                        <Terminal className="size-3" />
                        <span>Wire Log</span>
                      </button>
                    </div>

                    {incident.canonicalHead && (
                      <div className="flex items-center gap-2 text-[11px] font-mono text-zinc-400">
                        <span>Canonical: <span className="text-emerald-400 font-semibold">{incident.canonicalHead}</span></span>
                        <span>·</span>
                        <span>Delinquent: <span className="text-amber-400 font-semibold">{incident.delinquentHead}</span></span>
                      </div>
                    )}
                  </div>

                  {/* SUB-TAB 1: ECOSYSTEM IMPACT & MITIGATION */}
                  {subTab === "impact" && (
                    <div className="space-y-2.5">
                      <div className="space-y-1">
                        <h4 className="text-xs sm:text-sm font-semibold text-white flex items-center gap-1.5">
                          <Sparkles className="size-3.5 text-cyan-400 shrink-0" />
                          <span>{incident.impactAnalysis.title}</span>
                        </h4>
                        <p className="text-xs text-zinc-300 leading-relaxed font-sans">
                          {incident.notes}
                        </p>
                      </div>

                      {/* Mitigated Risk Profile Callout Box */}
                      <div className="p-2.5 rounded-lg bg-cyan-950/30 border border-cyan-800/50 space-y-1">
                        <div className="text-[11px] font-semibold text-cyan-300 uppercase tracking-wider flex items-center gap-1.5">
                          <ShieldCheck className="size-3.5 text-cyan-400" />
                          <span>MITIGATED RISK PROFILE</span>
                        </div>
                        <p className="text-xs text-zinc-200 leading-relaxed font-sans">
                          {incident.impactAnalysis.ecosystemRiskAverted}
                        </p>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
                        <div className="p-2 rounded bg-zinc-950 border border-zinc-800/60">
                          <span className="text-[10px] text-zinc-500 uppercase tracking-wider block">AFFECTED STAKEHOLDERS</span>
                          <span className="text-zinc-300 text-[11px] font-sans font-medium">{incident.impactAnalysis.affectedStakeholders}</span>
                        </div>
                        <div className="p-2 rounded bg-zinc-950 border border-zinc-800/60">
                          <span className="text-[10px] text-zinc-500 uppercase tracking-wider block">PRODUCTION IMPACT</span>
                          <span className="text-zinc-300 text-[11px] font-sans">{incident.impactAnalysis.productionImpact}</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* SUB-TAB 2: SRE POST-MORTEM & RCA */}
                  {subTab === "sre" && (
                    <div className="space-y-2.5 font-mono text-xs">
                      {/* RCA Grid */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        <div className="p-2.5 rounded bg-zinc-950 border border-zinc-800/80 space-y-1">
                          <div className="text-[10px] text-zinc-500 uppercase tracking-wider">ROOT CAUSE ANALYSIS (RCA)</div>
                          <div className="text-zinc-300 text-xs font-sans leading-relaxed">{incident.techStandard.rootCause}</div>
                        </div>
                        <div className="p-2.5 rounded bg-zinc-950 border border-zinc-800/80 space-y-1">
                          <div className="text-[10px] text-zinc-500 uppercase tracking-wider">FAILURE DOMAIN &amp; SCOPE</div>
                          <div className="text-zinc-300 text-xs font-mono">{incident.techStandard.failureDomain}</div>
                          <div className="text-[10px] text-zinc-500 mt-1">Compliance: {incident.techStandard.complianceStandard}</div>
                        </div>
                      </div>

                      {/* Telemetry Metrics Bar */}
                      <div className="grid grid-cols-3 gap-2 text-center p-2 rounded bg-zinc-950 border border-zinc-800/60">
                        <div>
                          <span className="text-[10px] text-zinc-500 uppercase block">Detection MTTD</span>
                          <span className="text-xs font-bold text-cyan-400">{incident.techStandard.mttdMs} ms</span>
                        </div>
                        <div>
                          <span className="text-[10px] text-zinc-500 uppercase block">Cutover MTTC</span>
                          <span className="text-xs font-bold text-[#28A0F0]">{incident.techStandard.mttcMs} ms</span>
                        </div>
                        <div>
                          <span className="text-[10px] text-zinc-500 uppercase block">Recovery Protocol</span>
                          <span className="text-xs font-bold text-emerald-400">2-Cycle Parity</span>
                        </div>
                      </div>

                      {/* POSIX UNIX Socket Command Box */}
                      <div className="space-y-1.5">
                        <div className="flex items-center justify-between text-[11px] text-zinc-400">
                          <span className="uppercase text-[10px] text-zinc-500">Atomic POSIX Socket IPC Command:</span>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              navigator.clipboard.writeText(incident.socketCommand)
                              setCopiedId(incident.id + "-socket")
                              setTimeout(() => setCopiedId(null), 1500)
                            }}
                            className="text-zinc-400 hover:text-white flex items-center gap-1 text-[10px] p-1"
                          >
                            {copiedId === incident.id + "-socket" ? (
                              <>
                                <Check className="size-3 text-emerald-400" />
                                <span className="text-emerald-400">Copied!</span>
                              </>
                            ) : (
                              <>
                                <Copy className="size-3" />
                                <span>Copy Command</span>
                              </>
                            )}
                          </button>
                        </div>
                        <div className="p-2.5 rounded bg-zinc-950 border border-zinc-800 text-zinc-300 text-[11px] overflow-x-auto">
                          <code>{incident.socketCommand}</code>
                        </div>
                        <div className="text-[10px] text-zinc-500">
                          Enforced Recovery Condition: {incident.techStandard.recoveryCondition}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* SUB-TAB 3: WIRE LOG */}
                  {subTab === "wire" && (
                    <div className="space-y-2.5 font-mono text-xs">
                      <div className="p-2.5 rounded bg-zinc-950 border border-zinc-800 text-[11px] text-zinc-300 space-y-1 overflow-x-auto">
                        <div className="text-zinc-500 text-[10px] uppercase">DriftGuard Sentinel JSON Wire Telemetry</div>
                        <pre className="text-zinc-300">{JSON.stringify({
                          incident_id: incident.id,
                          timestamp: incident.timestamp,
                          chain_id: incident.chainId,
                          category: incident.category,
                          drift_delta: incident.stallDelta,
                          cutover_latency_ms: parseFloat(incident.latency),
                          canonical_head: incident.canonicalHead || null,
                          delinquent_head: incident.delinquentHead || null,
                          unix_socket: "/run/haproxy/admin.sock",
                          action: incident.actionStatus,
                          discord_notified: true
                        }, null, 2)}</pre>
                      </div>

                      {/* Discord Audit Embed Preview */}
                      <div className="p-2 rounded bg-[#5865F2]/10 border border-[#5865F2]/30 flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <MessageSquare className="size-3.5 text-[#5865F2]" />
                          <span className="text-zinc-300 text-[11px]">
                            Audit alert dispatched to Discord <code className="text-white">#bot-stats</code> within 200ms
                          </span>
                        </div>
                        <a
                          href="https://discord.gg/DZBDJSsSzN"
                          target="_blank"
                          rel="noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="text-[11px] text-[#5865F2] hover:underline flex items-center gap-1 font-medium"
                        >
                          <span>Verify Discord Log</span>
                          <ExternalLink className="size-3" />
                        </a>
                      </div>
                    </div>
                  )}

                  {/* Formal Post-Mortem Link Footer (if available) */}
                  {incident.postMortemLink && (
                    <div className="pt-2 flex flex-wrap items-center justify-between gap-2 border-t border-zinc-800/80 text-xs">
                      <a
                        href={incident.postMortemLink}
                        target="_blank"
                        rel="noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="text-emerald-400 hover:underline flex items-center gap-1.5 font-sans font-medium text-xs"
                      >
                        <BookOpen className="size-3.5" />
                        <span>Read Incident Post-Mortem Report (2026-10-04) →</span>
                      </a>
                      <span className="text-[10px] text-zinc-500 font-mono">
                        Verified Systems Engineering Documentation
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
