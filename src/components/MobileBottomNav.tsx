import { Shield, Terminal, BookOpen, Activity } from "lucide-react"

interface MobileBottomNavProps {
  activeTab: "overview" | "rpc" | "docs" | "audit"
  setActiveTab: (tab: "overview" | "rpc" | "docs" | "audit") => void
  incidentCount: number
}

export function MobileBottomNav({ activeTab, setActiveTab, incidentCount }: MobileBottomNavProps) {
  const tabs = [
    {
      id: "overview" as const,
      label: "Overview",
      icon: Shield,
    },
    {
      id: "rpc" as const,
      label: "Playground",
      icon: Terminal,
    },
    {
      id: "docs" as const,
      label: "Specs",
      icon: BookOpen,
    },
    {
      id: "audit" as const,
      label: "Incidents",
      icon: Activity,
      badge: incidentCount,
    },
  ]

  return (
    <div className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-[#09090b]/90 backdrop-blur-xl border-t border-zinc-800/90 py-1.5 px-3 flex items-center justify-around shadow-[0_-8px_24px_rgba(0,0,0,0.6)]">
      {tabs.map((tab) => {
        const Icon = tab.icon
        const isActive = activeTab === tab.id

        return (
          <button
            key={tab.id}
            onClick={() => {
              setActiveTab(tab.id)
              window.scrollTo({ top: 0, behavior: "smooth" })
            }}
            className={`relative flex flex-col items-center justify-center py-1 px-3 rounded-lg transition-all ${
              isActive
                ? "text-white"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            {/* Top active indicator line */}
            {isActive && (
              <span className="absolute -top-1.5 w-6 h-0.5 bg-[#28A0F0] rounded-full shadow-[0_0_8px_#28A0F0]" />
            )}

            <div className="relative">
              <Icon className={`size-4.5 ${isActive ? "text-[#28A0F0]" : "text-zinc-400"}`} />
              {tab.badge && (
                <span className="absolute -top-1.5 -right-3 text-[9px] font-mono font-bold px-1 rounded-full bg-cyan-950 text-[#28A0F0] border border-cyan-800">
                  {tab.badge}
                </span>
              )}
            </div>

            <span className={`text-[10px] font-mono mt-1 ${isActive ? "font-semibold text-white" : "text-zinc-400"}`}>
              {tab.label}
            </span>
          </button>
        )
      })}
    </div>
  )
}
