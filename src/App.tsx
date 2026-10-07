import { useState, useEffect } from "react"
import { AnnouncementBanner } from "@/components/AnnouncementBanner"
import { Navbar } from "@/components/Navbar"
import { MobileBottomNav } from "@/components/MobileBottomNav"
import { RuleOfThirdsHero } from "@/components/RuleOfThirdsHero"
import { TrustProofStrip } from "@/components/TrustProofStrip"
import { MetricsTrio } from "@/components/MetricsTrio"
import { ExplainerShowcase } from "@/components/ExplainerShowcase"
import { LiveTelemetryStreamCard } from "@/components/LiveTelemetryStreamCard"
import { ResourcesSection } from "@/components/ResourcesSection"
import { PlaygroundView } from "@/components/PlaygroundView"
import { DocsView } from "@/components/DocsView"
import { LedgerView } from "@/components/LedgerView"
import { Footer } from "@/components/Footer"
import { LEDGER_INCIDENTS } from "@/constants/incidents"

export function App() {
  const isDocs =
    typeof window !== "undefined" &&
    (window.location.hostname.startsWith("docs.") || window.location.hostname === "docs.driftguard.live")

  const [activeTab, setActiveTab] = useState<"overview" | "rpc" | "docs" | "audit">(
    isDocs ? "docs" : "overview"
  )

  const handleTabChange = (tab: "overview" | "rpc" | "docs" | "audit") => {
    setActiveTab(tab)
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  const handleWatchVideo = () => {
    const el = document.getElementById("explainer-video")
    if (el) {
      el.scrollIntoView({ behavior: "smooth" })
    }
  }

  // Ensure scroll is top on view switch
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" as ScrollBehavior })
  }, [activeTab])

  return (
    <div className="relative min-h-screen bg-[#08090d] text-zinc-100 flex flex-col selection:bg-[#28A0F0]/25 selection:text-[#38bdf8] font-sans overflow-x-hidden pb-12 md:pb-0">
      {/* ── Background EVM / Arbitrum Atmospheric Textures ── */}
      {/* 1. Top Ethereal Cyan Radial Aurora */}
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[700px] bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(40,160,240,0.18),transparent_75%)] z-0" />
      {/* 2. Micro Grid Pattern with Radial Mask */}
      <div className="pointer-events-none absolute inset-0 bg-grid-mesh [mask-image:radial-gradient(ellipse_75%_50%_at_50%_25%,#000_20%,transparent_100%)] opacity-70 z-0" />
      {/* 3. Cyber Dot Matrix Glow behind Hero */}
      <div className="pointer-events-none absolute top-12 left-1/2 -translate-x-1/2 w-full max-w-5xl h-[500px] bg-dot-mesh [mask-image:radial-gradient(ellipse_50%_50%_at_50%_40%,#000_20%,transparent_100%)] opacity-50 z-0" />
      {/* 4. Film Grain / Cryptographic Noise Texture */}
      <div className="pointer-events-none fixed inset-0 bg-noise opacity-30 z-40" />

      {/* ── Top VC & Grant Announcement Ribbon ── */}
      <AnnouncementBanner />

      {/* ── Responsive Sticky Navigation Header with Mobile Drawer ── */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={handleTabChange}
        incidentCount={LEDGER_INCIDENTS.length}
      />

      {/* ── Main View Container with Precision Rails ── */}
      <main className="relative z-10 flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-10">
        {/* ══════════════════════════════════════════════════════════
            VIEW 1: OVERVIEW (RULE OF THIRDS + ARCHITECTURE)
           ══════════════════════════════════════════════════════════ */}
        {activeTab === "overview" && (
          <div className="space-y-10 sm:space-y-14">
            {/* Rule of Thirds Asymmetric Hero */}
            <RuleOfThirdsHero
              onWatchVideo={handleWatchVideo}
              onOpenPlayground={() => handleTabChange("rpc")}
              onOpenSpecs={() => handleTabChange("docs")}
              onOpenLedger={() => handleTabChange("audit")}
            />

            {/* Institutional Ecosystem Proof Strip */}
            <TrustProofStrip />

            {/* Rule of Thirds 3-Column Metrics Pillars */}
            <MetricsTrio />

            {/* Explainer Video & Asciinema Terminal Drill Showcase */}
            <ExplainerShowcase />

            {/* Discord Live Operations Telemetry Stream Card */}
            <LiveTelemetryStreamCard
              onOpenLedger={() => handleTabChange("audit")}
            />

            {/* Re-organized Rule of Thirds Links & Resources Matrix */}
            <ResourcesSection
              onSelectTab={handleTabChange}
            />
          </div>
        )}

        {/* ══════════════════════════════════════════════════════════
            VIEW 2: RPC PLAYGROUND & ENDPOINTS
           ══════════════════════════════════════════════════════════ */}
        {activeTab === "rpc" && <PlaygroundView />}

        {/* ══════════════════════════════════════════════════════════
            VIEW 3: SPECIFICATIONS & RUNTIME DEPLOYMENT
           ══════════════════════════════════════════════════════════ */}
        {activeTab === "docs" && <DocsView />}

        {/* ══════════════════════════════════════════════════════════
            VIEW 4: PRODUCTION INCIDENT LEDGER & POST-MORTEMS
           ══════════════════════════════════════════════════════════ */}
        {activeTab === "audit" && <LedgerView />}
      </main>

      {/* ── Rule of Thirds Footer ── */}
      <Footer onSelectTab={handleTabChange} />

      {/* ── Sticky Mobile Bottom Quick Dock ── */}
      <MobileBottomNav
        activeTab={activeTab}
        setActiveTab={handleTabChange}
        incidentCount={LEDGER_INCIDENTS.length}
      />
    </div>
  )
}

export default App
