import { useState } from "react"
import { DriftGuardLogo } from "@/components/DriftGuardLogo"
import {
  MessageSquare,
  Github,
  Menu,
  X,
  Terminal,
  BookOpen,
  Activity,
  Layers,
  ExternalLink,
  Check,
  Copy,
  Shield,
  FileCode
} from "lucide-react"

interface NavbarProps {
  activeTab: "overview" | "rpc" | "docs" | "audit"
  setActiveTab: (tab: "overview" | "rpc" | "docs" | "audit") => void
  incidentCount: number
}

export function Navbar({ activeTab, setActiveTab, incidentCount }: NavbarProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [copiedQuickstart, setCopiedQuickstart] = useState(false)

  const handleTabClick = (tab: "overview" | "rpc" | "docs" | "audit") => {
    setActiveTab(tab)
    setMobileMenuOpen(false)
  }

  const handleCopy = () => {
    navigator.clipboard.writeText("docker compose up -d")
    setCopiedQuickstart(true)
    setTimeout(() => setCopiedQuickstart(false), 2000)
  }

  return (
    <>
      <header className="relative z-30 sticky top-0 w-full border-b border-zinc-800/80 bg-[#09090b]/85 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between gap-2 sm:gap-4">
          {/* Left: Brand Logo & Status Indicator */}
          <div className="flex items-center gap-3 shrink-0">
            <div
              className="cursor-pointer flex items-center"
              onClick={() => handleTabClick("overview")}
            >
              <DriftGuardLogo iconSize={26} showBadge={false} />
            </div>

            {/* Live Operational Beacon Pill (Visible on all screens) */}
            <div className="hidden sm:inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-950/60 border border-emerald-800/80 text-[10px] font-mono text-emerald-400">
              <span className="size-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>LIVE SENTINEL</span>
            </div>
          </div>

          {/* Center: Segmented Navigation Pills (Hidden on mobile < md, shown on desktop) */}
          <nav className="hidden md:flex items-center bg-zinc-900/90 p-1 border border-zinc-800 rounded-full shadow-inner">
            <button
              onClick={() => handleTabClick("overview")}
              className={`text-xs px-3.5 py-1 rounded-full whitespace-nowrap transition-all font-medium ${
                activeTab === "overview"
                  ? "bg-zinc-800 text-white shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => handleTabClick("rpc")}
              className={`text-xs px-3.5 py-1 rounded-full whitespace-nowrap transition-all font-medium ${
                activeTab === "rpc"
                  ? "bg-zinc-800 text-white shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              Playground
            </button>
            <button
              onClick={() => handleTabClick("docs")}
              className={`text-xs px-3.5 py-1 rounded-full whitespace-nowrap transition-all font-medium ${
                activeTab === "docs"
                  ? "bg-zinc-800 text-white shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              Specifications
            </button>
            <button
              onClick={() => handleTabClick("audit")}
              className={`text-xs px-3.5 py-1 rounded-full whitespace-nowrap transition-all font-medium flex items-center gap-1.5 ${
                activeTab === "audit"
                  ? "bg-zinc-800 text-white shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              <span>Incident Ledger</span>
              <span className="px-1.5 py-0.2 rounded-full bg-zinc-800 text-zinc-300 border border-zinc-700 text-[10px] font-mono">
                {incidentCount}
              </span>
            </button>
          </nav>

          {/* Right Action Icons & Mobile Hamburger */}
          <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
            <a
              href="https://discord.gg/DZBDJSsSzN"
              target="_blank"
              rel="noreferrer"
              className="p-1.5 rounded-md text-zinc-400 hover:text-white hover:bg-zinc-900 transition-colors"
              title="Join DriftGuard Discord"
            >
              <MessageSquare className="size-4" />
            </a>
            <a
              href="https://github.com/maskalfreeup-glitch/driftguard"
              target="_blank"
              rel="noreferrer"
              className="p-1.5 rounded-md text-zinc-400 hover:text-white hover:bg-zinc-900 transition-colors"
              title="GitHub Repository"
            >
              <Github className="size-4" />
            </a>

            {/* Mobile Hamburger Button (Only on screens < md) */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-lg text-zinc-300 hover:text-white hover:bg-zinc-900 transition-colors border border-zinc-800 ml-1"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="size-4" /> : <Menu className="size-4" />}
            </button>
          </div>
        </div>
      </header>

      {/* ── Mobile Slide-Over Navigation Sheet ── */}
      {mobileMenuOpen && (
        <div className="md:hidden fixed inset-x-0 top-14 z-20 bg-[#09090b]/95 border-b border-zinc-800/90 backdrop-blur-xl shadow-2xl p-4 space-y-4 max-h-[calc(100vh-3.5rem)] overflow-y-auto">
          {/* Main Navigation Views */}
          <div className="space-y-1">
            <div className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 px-2 mb-1">
              Core Platform Views
            </div>
            <button
              onClick={() => handleTabClick("overview")}
              className={`w-full flex items-center justify-between p-2.5 rounded-lg text-xs font-mono transition-colors ${
                activeTab === "overview"
                  ? "bg-zinc-800 text-white font-semibold border border-zinc-700"
                  : "text-zinc-300 hover:bg-zinc-900"
              }`}
            >
              <span className="flex items-center gap-2">
                <Shield className="size-3.5 text-[#28A0F0]" />
                <span>Architecture Overview</span>
              </span>
              <span className="text-zinc-500">→</span>
            </button>

            <button
              onClick={() => handleTabClick("rpc")}
              className={`w-full flex items-center justify-between p-2.5 rounded-lg text-xs font-mono transition-colors ${
                activeTab === "rpc"
                  ? "bg-zinc-800 text-white font-semibold border border-zinc-700"
                  : "text-zinc-300 hover:bg-zinc-900"
              }`}
            >
              <span className="flex items-center gap-2">
                <Terminal className="size-3.5 text-emerald-400" />
                <span>JSON-RPC Gateway Tester</span>
              </span>
              <span className="text-zinc-500">→</span>
            </button>

            <button
              onClick={() => handleTabClick("docs")}
              className={`w-full flex items-center justify-between p-2.5 rounded-lg text-xs font-mono transition-colors ${
                activeTab === "docs"
                  ? "bg-zinc-800 text-white font-semibold border border-zinc-700"
                  : "text-zinc-300 hover:bg-zinc-900"
              }`}
            >
              <span className="flex items-center gap-2">
                <BookOpen className="size-3.5 text-purple-400" />
                <span>Sidecar Daemon Specifications</span>
              </span>
              <span className="text-zinc-500">→</span>
            </button>

            <button
              onClick={() => handleTabClick("audit")}
              className={`w-full flex items-center justify-between p-2.5 rounded-lg text-xs font-mono transition-colors ${
                activeTab === "audit"
                  ? "bg-zinc-800 text-white font-semibold border border-zinc-700"
                  : "text-zinc-300 hover:bg-zinc-900"
              }`}
            >
              <span className="flex items-center gap-2">
                <Activity className="size-3.5 text-[#28A0F0]" />
                <span>Incident Ledger &amp; Audits</span>
              </span>
              <span className="px-1.5 py-0.2 rounded bg-zinc-800 text-zinc-300 border border-zinc-700 text-[10px]">
                {incidentCount}
              </span>
            </button>
          </div>

          {/* Quick Technical Documents & RFCs */}
          <div className="space-y-1 pt-2 border-t border-zinc-800/80">
            <div className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 px-2 mb-1">
              Technical RFCs &amp; Evidence
            </div>
            <a
              href="https://github.com/maskalfreeup-glitch/driftguard/blob/main/docs/guides/HIGH_THROUGHPUT_INGRESS_GUIDE.md"
              target="_blank"
              rel="noreferrer"
              className="flex items-center justify-between p-2 rounded-lg text-xs font-mono text-zinc-400 hover:text-white hover:bg-zinc-900 transition-colors"
            >
              <span className="flex items-center gap-2">
                <FileCode className="size-3 text-zinc-500" />
                <span>High-Throughput Ingress Guide</span>
              </span>
              <ExternalLink className="size-3 text-zinc-600" />
            </a>
            <a
              href="https://github.com/maskalfreeup-glitch/driftguard/blob/main/docs/PILOT_PARTNER_LOI.md"
              target="_blank"
              rel="noreferrer"
              className="flex items-center justify-between p-2 rounded-lg text-xs font-mono text-zinc-400 hover:text-white hover:bg-zinc-900 transition-colors"
            >
              <span className="flex items-center gap-2">
                <Layers className="size-3 text-cyan-500" />
                <span>Pilot Partner LOI-2026-ORBIT-001</span>
              </span>
              <ExternalLink className="size-3 text-zinc-600" />
            </a>
            <a
              href="https://github.com/maskalfreeup-glitch/driftguard/blob/main/docs/reports/INCIDENT_2026-10-04_ARBITRUM_DESYNC.md"
              target="_blank"
              rel="noreferrer"
              className="flex items-center justify-between p-2 rounded-lg text-xs font-mono text-zinc-400 hover:text-white hover:bg-zinc-900 transition-colors"
            >
              <span className="flex items-center gap-2">
                <Activity className="size-3 text-amber-500" />
                <span>Arbitrum Desync Post-Mortem (2026-10-04)</span>
              </span>
              <ExternalLink className="size-3 text-zinc-600" />
            </a>
          </div>

          {/* Quickstart Command One-Liner */}
          <div className="pt-2 border-t border-zinc-800/80">
            <div className="flex items-center justify-between p-2 rounded bg-zinc-950 border border-zinc-800 text-[11px] font-mono text-zinc-300">
              <span className="truncate">docker compose up -d</span>
              <button
                onClick={handleCopy}
                className="ml-2 text-zinc-400 hover:text-white p-1"
                title="Copy Quickstart"
              >
                {copiedQuickstart ? <Check className="size-3 text-emerald-400" /> : <Copy className="size-3" />}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
