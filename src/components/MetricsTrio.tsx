import { Zap, Activity, Cpu, ShieldCheck } from "lucide-react"

export function MetricsTrio() {
  const metrics = [
    {
      value: "< 130ms",
      unit: "POSIX IPC DRAIN",
      label: "Runtime Socket Drain",
      description: "Commands HAProxy via UNIX domain socket to drain delinquent upstreams in <130ms without TCP resets.",
      icon: Zap,
      badge: "SLA GUARANTEE",
      badgeColor: "border-sky-500/30 text-[#28A0F0] bg-sky-950/40"
    },
    {
      value: "250ms",
      unit: "ARBITRUM CADENCE",
      label: "Out-of-Band Probing",
      description: "Continuous asynchronous poll loop matches Arbitrum Nitro micro-block generation with zero client overhead.",
      icon: Activity,
      badge: "ZERO OVERHEAD",
      badgeColor: "border-emerald-500/30 text-emerald-400 bg-emerald-950/40"
    },
    {
      value: "< 45 MB",
      unit: "RESIDENT RAM (RSS)",
      label: "Resource Footprint",
      description: "Combined HAProxy L7 core + FastAPI asyncio daemon fits into low-cost validator nodes or minimal cloud VPS.",
      icon: Cpu,
      badge: "ROOTLESS SIDECAR",
      badgeColor: "border-purple-500/30 text-purple-400 bg-purple-950/40"
    }
  ]

  return (
    <div className="py-6 sm:py-8 my-4 sm:my-8 border-y border-zinc-800/80">
      {/* 3-Column Rule-of-Thirds Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6">
        {metrics.map((m, idx) => {
          const Icon = m.icon
          return (
            <div
              key={idx}
              className="relative p-5 sm:p-6 rounded-xl border border-zinc-800/80 bg-zinc-950/60 hover:bg-zinc-900/50 hover:border-zinc-700/80 transition-all duration-200 specular-border flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full border ${m.badgeColor}`}>
                    {m.badge}
                  </span>
                  <Icon className="size-4 text-zinc-500" />
                </div>

                <div className="space-y-1">
                  <div className="text-3xl sm:text-4xl font-extrabold font-mono tracking-tight text-white">
                    {m.value}
                  </div>
                  <div className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider">
                    {m.unit}
                  </div>
                </div>

                <div className="mt-3 text-sm font-semibold text-zinc-200">
                  {m.label}
                </div>

                <p className="mt-1.5 text-xs text-zinc-400 leading-relaxed font-sans">
                  {m.description}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-zinc-800/60 flex items-center gap-1.5 text-[11px] font-mono text-zinc-500">
                <ShieldCheck className="size-3 text-emerald-400 shrink-0" />
                <span>Deterministic Field Validated</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
