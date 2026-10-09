import { Zap, Activity, Cpu } from "lucide-react"

export function MetricsTrio() {
  const metrics = [
    {
      value: "< 130ms",
      label: "Socket Drain Cutover",
      description: "HAProxy POSIX socket maint toggle with zero TCP connection resets",
      icon: Zap,
    },
    {
      value: "200ms",
      label: "Asynchronous Probe Cadence",
      description: "Out-of-band tip verification polling independent canonical references",
      icon: Activity,
    },
    {
      value: "< 45 MB",
      label: "Resident Memory Footprint",
      description: "Combined C-runtime reverse proxy and asynchronous Python sentinel RSS",
      icon: Cpu,
    }
  ]

  return (
    <div className="max-w-5xl mx-auto py-16 px-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {metrics.map((m, idx) => {
          const Icon = m.icon
          return (
            <div
              key={idx}
              className="p-6 rounded-xl border border-zinc-800/80 bg-zinc-900/40 space-y-3 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="text-3xl font-extrabold font-mono tracking-tight text-white">
                  {m.value}
                </div>
                <Icon className="size-4 text-zinc-500" />
              </div>
              <div className="text-sm font-semibold font-mono text-zinc-200">
                {m.label}
              </div>
              <p className="text-xs text-zinc-400 leading-relaxed font-sans">
                {m.description}
              </p>
            </div>
          )
        })}
      </div>
    </div>
  )
}
