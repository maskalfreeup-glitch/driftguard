import { useState, useEffect, lazy, Suspense } from "react"
import { Navbar } from "@/components/Navbar"
import { MobileBottomNav } from "@/components/MobileBottomNav"
import { RuleOfThirdsHero } from "@/components/RuleOfThirdsHero"
import { MetricsTrio } from "@/components/MetricsTrio"
import { ExplainerShowcase } from "@/components/ExplainerShowcase"
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
    <div className="relative min-h-screen bg-[#090a0f] text-zinc-100 flex flex-col font-sans selection:bg-[#28A0F0]/25 selection:text-[#38bdf8] pb-12 md:pb-0">
      {/* ── Navigation Header ── */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={handleTabChange}
        incidentCount={LEDGER_INCIDENTS.length}
      />

      {/* ── Main View Container ── */}
      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 py-6 sm:py-10">
        {/* ══════════════════════════════════════════════════════════
            VIEW 1: OVERVIEW (HERO + ARCHITECTURE + WALKTHROUGH)
           ══════════════════════════════════════════════════════════ */}
        {activeTab === "overview" && (
          <div className="space-y-12 sm:space-y-16">
            <RuleOfThirdsHero
              onOpenPlayground={() => handleTabChange("rpc")}
            />

            <ExplainerShowcase />

            <MetricsTrio />
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
