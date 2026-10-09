import { Zap, Layers, ShieldCheck, Activity, Server, Cpu } from "lucide-react"

export function TrustProofStrip() {
  const ecosystemPillars = [
    { title: "Arbitrum Nitro", layer: "Execution", icon: Zap },
    { title: "Orbit L3", layer: "Rollups", icon: Layers },
    { title: "AnyTrust DAC", layer: "Quorum", icon: ShieldCheck },
    { title: "ERC-4337", layer: "Bundlers", icon: Activity },
    { title: "HAProxy L7", layer: "Data Plane", icon: Server },
    { title: "JSON-RPC 2.0", layer: "Wire", icon: Cpu }
  ]

  return (
    <div className="py-4 border-y border-zinc-800/80">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs font-mono">
        <span className="text-[10px] uppercase tracking-wider text-zinc-500 font-semibold shrink-0">
          Compatibility Matrix:
        </span>
        <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-zinc-300">
          {ecosystemPillars.map((p, idx) => {
            const Icon = p.icon
            return (
              <div key={idx} className="flex items-center gap-1.5 group">
                <Icon className="size-3.5 text-[#28A0F0] shrink-0" />
                <span className="text-zinc-200 font-medium group-hover:text-white transition-colors">
                  {p.title}
                </span>
                <span className="text-[10px] text-zinc-500 font-mono">
                  ({p.layer})
                </span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
