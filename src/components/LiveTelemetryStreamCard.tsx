import { Radio, MessageSquare, ArrowRight } from "lucide-react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface LiveTelemetryStreamCardProps {
  onOpenLedger: () => void
}

export function LiveTelemetryStreamCard({ onOpenLedger }: LiveTelemetryStreamCardProps) {
  return (
    <Card className="specular-border bg-zinc-900/40 border-zinc-800/80 shadow-xl overflow-hidden backdrop-blur-sm">
      <CardHeader className="pb-3 border-b border-zinc-800/60 bg-zinc-950/40">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Radio className="size-4 text-[#28A0F0] animate-pulse" />
            <CardTitle className="text-sm font-mono tracking-tight font-semibold text-white">
              LIVE PRODUCTION TELEMETRY STREAM
            </CardTitle>
          </div>
          <Badge variant="outline" className="border-sky-800/80 bg-sky-950/40 text-[#28A0F0] text-[10px] font-mono tracking-wider w-fit">
            DISCORD #BOT-STATS · 24/7 ACTIVE SENTINEL
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-4 space-y-4">
        <p className="text-xs sm:text-sm text-zinc-300 leading-relaxed font-sans">
          Every out-of-band consensus probe, block height delta, socket drain command, and recovery event is streamed directly to our public operations channel in real time.
        </p>
        <div className="rounded-lg bg-zinc-950 p-3 border border-zinc-800/80 font-mono text-xs space-y-1.5 text-zinc-400">
          <div className="flex items-center justify-between text-[11px] text-zinc-500 pb-1 border-b border-zinc-800/60">
            <span className="flex items-center gap-1.5">
              <span className="size-2 rounded-full bg-emerald-500" />
              socket://run/haproxy/admin.sock
            </span>
            <span>100% OPERATIONAL STREAM</span>
          </div>
          <div className="text-zinc-300 font-mono text-[11px] truncate">
            <span className="text-[#28A0F0]">[DISCORD EMBED]</span> sentinel.probe.arbitrum-one: delta=0 blocks | status=HEALTHY | p99=18ms
          </div>
        </div>
        <div className="pt-1 flex flex-wrap items-center justify-between gap-3">
          <a
            href="https://discord.gg/DZBDJSsSzN"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 bg-[#5865F2] hover:bg-[#4752C4] text-white text-xs font-semibold px-4 py-2.5 rounded-lg transition-colors shadow-sm"
          >
            <MessageSquare className="size-3.5 fill-current" />
            <span>View Live Alerts in Discord #bot-stats</span>
          </a>
          <button
            onClick={onOpenLedger}
            className="text-xs text-zinc-400 hover:text-white flex items-center gap-1 font-mono transition-colors p-1"
          >
            <span>View Incident Ledger</span>
            <ArrowRight className="size-3" />
          </button>
        </div>
      </CardContent>
    </Card>
  )
}
