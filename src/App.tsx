import { useState, useEffect, lazy, Suspense } from "react"
import { AnnouncementBanner } from "@/components/AnnouncementBanner"
import { Navbar } from "@/components/Navbar"
import { MobileBottomNav } from "@/components/MobileBottomNav"
import { RuleOfThirdsHero } from "@/components/RuleOfThirdsHero"
import { TrustProofStrip } from "@/components/TrustProofStrip"
import { MetricsTrio } from "@/components/MetricsTrio"
import { ExplainerShowcase } from "@/components/ExplainerShowcase"
import { LiveTelemetryStreamCard } from "@/components/LiveTelemetryStreamCard"
import { ResourcesSection } from "@/components/ResourcesSection"
import { Footer } from "@/components/Footer"
import { LEDGER_INCIDENTS } from "@/constants/incidents"

const PlaygroundView = lazy(() => import("@/components/PlaygroundView").then((m) => ({ default: m.PlaygroundView })))
const DocsView = lazy(() => import("@/components/DocsView").then((m) => ({ default: m.DocsView })))
const LedgerView = lazy(() => import("@/components/LedgerView").then((m) => ({ default: m.LedgerView })))

type TabType = "overview" | "rpc" | "docs" | "audit"

function getTabFromUrl(): { tab: TabType; incidentId?: string } {
  if (typeof window === "undefined") return { tab: "overview" }

  const isDocsSubdomain =
    window.location.hostname.startsWith("docs.") || window.location.hostname === "docs.driftguard.live"
  if (isDocsSubdomain) return { tab: "docs" }

  const hash = window.location.hash.replace(/^#/, "").trim()
  if (!hash) return { tab: "overview" }

  const [path, queryString] = hash.split("?")
  const params = new URLSearchParams(queryString || "")
  const incidentId = params.get("id") || undefined

  if (path === "rpc" || path === "playground") return { tab: "rpc" }
  if (path === "docs" || path === "specs") return { tab: "docs" }
  if (path === "audit" || path === "ledger" || path === "incidents") return { tab: "audit", incidentId }
  if (path.startsWith("audit/") || path.startsWith("ledger/")) {
    return { tab: "audit", incidentId: path.split("/")[1] }
  }

  return { tab: "overview" }
}

function ViewSkeleton() {
  return (
    <div className="py-20 flex flex-col items-center justify-center space-y-3 font-mono text-xs text-zinc-500">
      <div className="size-5 rounded-full border-2 border-zinc-700 border-t-[#28A0F0] animate-spin" />
      <span>Loading view...</span>
    </div>
  )
}

export function App() {
  const initial = getTabFromUrl()
  const [activeTab, setActiveTab] = useState<TabType>(initial.tab)
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | undefined>(initial.incidentId)

  const handleTabChange = (tab: TabType, incidentId?: string) => {
    setActiveTab(tab)
    if (incidentId) {
      setSelectedIncidentId(incidentId)
      window.history.pushState(null, "", `#audit?id=${incidentId}`)
    } else {
      setSelectedIncidentId(undefined)
      const hash = tab === "overview" ? "" : `#${tab}`
      if (window.location.hash !== hash) {
        window.history.pushState(null, "", hash || window.location.pathname)
      }
    }
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  const handleWatchVideo = () => {
    const el = document.getElementById("explainer-video")
    if (el) {
      el.scrollIntoView({ behavior: "smooth" })
    }
  }

  // Sync state on browser back / forward navigation
  useEffect(() => {
    const onHashChange = () => {
      const parsed = getTabFromUrl()
      setActiveTab(parsed.tab)
      if (parsed.incidentId) {
        setSelectedIncidentId(parsed.incidentId)
      }
    }
    window.addEventListener("hashchange", onHashChange)
    window.addEventListener("popstate", onHashChange)
    return () => {
      window.removeEventListener("hashchange", onHashChange)
      window.removeEventListener("popstate", onHashChange)
    }
  }, [])

  // Human-friendly hotkeys for instant view switching (1 = Overview, 2 = Playground, 3 = Specs, 4 = Ledger)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (["INPUT", "TEXTAREA", "SELECT"].includes((e.target as HTMLElement)?.tagName)) {
        return
      }
      if (e.metaKey || e.ctrlKey || e.altKey) return
      if (e.key === "1") handleTabChange("overview")
      if (e.key === "2") handleTabChange("rpc")
      if (e.key === "3") handleTabChange("docs")
      if (e.key === "4") handleTabChange("audit")
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [])

  return (
    <div className="relative min-h-screen bg-[#08090d] text-zinc-100 flex flex-col selection:bg-[#28A0F0]/25 selection:text-[#38bdf8] font-sans overflow-x-hidden pb-12 md:pb-0">
      {/* ── Background Atmospheric Textures ── */}
      {/* 1. Subtle Radial Ambient Tint */}
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[600px] bg-[radial-gradient(ellipse_80%_40%_at_50%_-10%,rgba(40,160,240,0.06),transparent_75%)] z-0" />
      {/* 2. Micro Grid Pattern with Radial Mask */}
      <div className="pointer-events-none absolute inset-0 bg-grid-mesh [mask-image:radial-gradient(ellipse_75%_50%_at_50%_25%,#000_20%,transparent_100%)] opacity-40 z-0" />
      {/* 3. Subtle Dot Matrix Texture */}
      <div className="pointer-events-none absolute top-12 left-1/2 -translate-x-1/2 w-full max-w-5xl h-[450px] bg-dot-mesh [mask-image:radial-gradient(ellipse_50%_50%_at_50%_40%,#000_20%,transparent_100%)] opacity-25 z-0" />
      {/* 4. Film Grain / Cryptographic Noise Texture */}
      <div className="pointer-events-none fixed inset-0 bg-noise opacity-20 z-40" />

      {/* ── Top Announcement Ribbon ── */}
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

            {/* Ecosystem Proof Strip */}
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
        {activeTab === "rpc" && (
          <Suspense fallback={<ViewSkeleton />}>
            <PlaygroundView />
          </Suspense>
        )}

        {/* ══════════════════════════════════════════════════════════
            VIEW 3: SPECIFICATIONS & RUNTIME DEPLOYMENT
           ══════════════════════════════════════════════════════════ */}
        {activeTab === "docs" && (
          <Suspense fallback={<ViewSkeleton />}>
            <DocsView />
          </Suspense>
        )}

        {/* ══════════════════════════════════════════════════════════
            VIEW 4: PRODUCTION INCIDENT LEDGER & POST-MORTEMS
           ══════════════════════════════════════════════════════════ */}
        {activeTab === "audit" && (
          <Suspense fallback={<ViewSkeleton />}>
            <LedgerView initialIncidentId={selectedIncidentId} />
          </Suspense>
        )}
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
