import { Cpu, ShieldCheck, Zap, Layers, Server, Activity } from "lucide-react"

export function TrustProofStrip() {
  const ecosystemPillars = [
    {
      title: "Arbitrum Nitro",
      subtitle: "250ms Micro-Block Cadence",
      icon: Zap,
      badge: "Core Architecture"
    },
    {
      title: "Orbit L3 Rollups",
      subtitle: "Dedicated Sequencer Shielding",
      icon: Layers,
      badge: "Appchains"
    },
    {
      title: "AnyTrust DAC",
      subtitle: "Quorum Parity Verification",
      icon: ShieldCheck,
      badge: "Arbitrum Nova"
    },
    {
      title: "ERC-4337 Bundlers",
      subtitle: "Zero Nonce Desync Guarantee",
      icon: Activity,
      badge: "Account Abstraction"
    },
    {
      title: "HAProxy L7 Engine",
      subtitle: "POSIX UNIX Socket IPC",
      icon: Server,
      badge: "Data Plane"
    },
    {
      title: "Wire Compatible",
      subtitle: "Viem · Alloy · Nethermind · Cast",
      icon: Cpu,
      badge: "JSON-RPC 2.0"
    }
  ]

  return (
    <div className="py-6 sm:py-8 border-y border-zinc-800/80 bg-zinc-950/40 backdrop-blur-sm">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-5">
          <p className="text-[10px] font-mono uppercase tracking-[0.2em] text-zinc-400">
            Engineered for High-Velocity EVM &amp; Arbitrum Infrastructure
          </p>
        </div>

        {/* 6-Item Responsive Grid (2 columns on mobile, 3 on tablet, 6 on desktop) */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2 sm:gap-3">
          {ecosystemPillars.map((p, idx) => {
            const Icon = p.icon
            return (
              <div
                key={idx}
                className="group relative p-3 rounded-lg border border-zinc-800/70 bg-zinc-900/40 hover:bg-zinc-900/80 hover:border-sky-500/30 transition-all duration-200 flex flex-col justify-between"
              >
                <div className="flex items-center justify-between gap-1 mb-2">
                  <div className="size-6 rounded-md bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-[#28A0F0] group-hover:scale-110 transition-transform">
                    <Icon className="size-3.5" />
                  </div>
                  <span className="text-[9px] font-mono text-zinc-400 border border-zinc-800 rounded px-1 py-0.2 bg-zinc-950">
                    {p.badge}
                  </span>
                </div>
                <div>
                  <div className="text-xs font-semibold text-white tracking-tight group-hover:text-sky-300 transition-colors">
                    {p.title}
                  </div>
                  <div className="text-[10px] text-zinc-400 leading-tight mt-0.5">
                    {p.subtitle}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
