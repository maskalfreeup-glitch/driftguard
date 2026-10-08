import { useState } from "react"
import { Terminal, Copy, Check, BookOpen, ExternalLink, FileCode2, AlertTriangle, Radio, MessageSquare } from "lucide-react"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export function DocsView() {
  const [copiedId, setCopiedId] = useState<string | null>(null)

  function copyToClipboard(text: string, id: string) {
    navigator.clipboard.writeText(text)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  return (
    <div className="space-y-8 pb-24 md:pb-8">
      {/* Header */}
      <div className="border-b border-zinc-800/80 pb-4">
        <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight mb-1">
          Runtime Deployment &amp; Client Integration Specification
        </h2>
        <p className="text-xs sm:text-sm text-zinc-400 max-w-3xl leading-relaxed">
          Reference deployment topologies, local sidecar daemon orchestration, and deterministic upstream failover configuration for Arbitrum Nitro and Orbit execution clients.
        </p>
      </div>

      {/* 01 / Sidecar Daemon Orchestration */}
      <Card className="specular-border bg-zinc-900/40 border-zinc-800/80 shadow-xl">
        <CardHeader className="pb-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <CardTitle className="text-sm font-semibold text-white flex items-center gap-2 font-mono">
              <Terminal className="size-4 text-zinc-300" />
              01 / Sidecar Daemon Orchestration
            </CardTitle>
            <Badge variant="outline" className="border-zinc-800 bg-zinc-950/60 text-[#28A0F0] text-[10px] font-mono tracking-wider w-fit">
              CONTAINERIZED SIDECAR · IPC UNIX SOCKET · ROOTLESS
            </Badge>
          </div>
          <CardDescription className="text-xs text-zinc-400 leading-relaxed pt-1">
            Deploy the combined HAProxy L7 data plane and asynchronous Python consensus sentinel adjacent to your validator, relayer, or RPC gateway stack.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3.5">
          <div className="relative rounded-md bg-zinc-950 p-3.5 border border-zinc-800/80 font-mono text-xs text-zinc-200 flex items-center justify-between gap-4">
            <code className="text-zinc-300 overflow-x-auto">
              git clone https://github.com/maskalfreeup-glitch/driftguard &amp;&amp; cd driftguard &amp;&amp; docker compose up -d
            </code>
            <button
              onClick={() =>
                copyToClipboard(
                  "git clone https://github.com/maskalfreeup-glitch/driftguard && cd driftguard && docker compose up -d",
                  "quickstart-sidecar"
                )
              }
              className="p-1.5 rounded text-zinc-400 hover:text-white bg-zinc-800/60 shrink-0"
              title="Copy Command"
            >
              {copiedId === "quickstart-sidecar" ? <Check className="size-3.5 text-emerald-400" /> : <Copy className="size-3.5" />}
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-1">
            <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800/60 space-y-1">
              <div className="text-[11px] font-semibold text-white font-mono">Loopback Interface (127.0.0.1:8545)</div>
              <div className="text-[11px] text-zinc-400 leading-relaxed font-sans">
                High-concurrency HAProxy L7 runtime routing with &lt; 3ms C-runtime latency overhead.
              </div>
            </div>
            <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800/60 space-y-1">
              <div className="text-[11px] font-semibold text-white font-mono">Consensus Drift Eviction</div>
              <div className="text-[11px] text-zinc-400 leading-relaxed font-sans">
                Automated UNIX socket drain upon &gt;= 4 blocks (~1.0s) head divergence relative to canonical anchor.
              </div>
            </div>
            <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800/60 space-y-1">
              <div className="text-[11px] font-semibold text-white font-mono">Wire-Compatible Transport</div>
              <div className="text-[11px] text-zinc-400 leading-relaxed font-sans">
                Strict JSON-RPC 2.0 conformance; drop-in reverse proxy for Viem, Go-Ethereum, Nethermind, and Alloy.
              </div>
            </div>
          </div>

          <p className="text-xs text-zinc-400 leading-relaxed pt-1 font-sans">
            The ingress gateway binds to <code className="text-zinc-300 bg-zinc-950 px-1 py-0.5 rounded border border-zinc-800 font-mono">http://127.0.0.1:8545/arb</code>. Upstream Nitro execution endpoints, chain IDs, verification intervals, and alerting webhooks are configured via <code className="text-zinc-300 bg-zinc-950 px-1 py-0.5 rounded border border-zinc-800 font-mono">.env</code>.
          </p>

          <div className="pt-2 flex flex-wrap items-center justify-between gap-2 border-t border-zinc-800/60">
            <a
              href="https://github.com/maskalfreeup-glitch/driftguard/blob/main/docs/guides/HIGH_THROUGHPUT_INGRESS_GUIDE.md"
              target="_blank"
              rel="noreferrer"
              className="text-xs text-[#28A0F0] hover:underline flex items-center gap-1 font-medium font-mono"
            >
              <BookOpen className="size-3" />
              <span>[ Technical Architecture RFC ]</span>
            </a>
            <a
              href="https://github.com/maskalfreeup-glitch/driftguard/blob/main/docs/PILOT_PARTNER_LOI.md"
              target="_blank"
              rel="noreferrer"
              className="text-xs text-zinc-400 hover:text-zinc-200 flex items-center gap-1 font-mono"
            >
              <ExternalLink className="size-3" />
              <span>[ Partner Verification: LOI-2026-ORBIT-001 ]</span>
            </a>
          </div>
        </CardContent>
      </Card>

      {/* 02 / Execution Client Runtime Bindings */}
      <div className="space-y-3">
        <div className="space-y-0.5">
          <h3 className="text-xs font-mono uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
            <FileCode2 className="size-3.5" />
            02 / Execution Client Runtime Bindings
          </h3>
          <p className="text-xs text-zinc-500 font-sans">
            Production connection snippets for standard EVM frameworks and developer toolchains.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {/* Foundry Card */}
          <Card className="bg-zinc-900/40 border-zinc-800/80 specular-border">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-semibold text-white font-mono">Foundry / Cast</CardTitle>
              <CardDescription className="text-[11px] text-zinc-500 font-mono">CLI command query</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="relative rounded bg-zinc-950 p-2.5 border border-zinc-800/80 font-mono text-[11px] text-zinc-300">
                <code>cast block-number \<br />  --rpc-url https://rpc.driftguard.live/arb</code>
                <button
                  onClick={() =>
                    copyToClipboard(
                      "cast block-number --rpc-url https://rpc.driftguard.live/arb",
                      "cast-cmd"
                    )
                  }
                  className="absolute top-2 right-2 p-1 text-zinc-400 hover:text-white"
                  title="Copy Cast Command"
                >
                  {copiedId === "cast-cmd" ? <Check className="size-3 text-emerald-400" /> : <Copy className="size-3" />}
                </button>
              </div>
            </CardContent>
          </Card>

          {/* Hardhat Card */}
          <Card className="bg-zinc-900/40 border-zinc-800/80 specular-border">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-semibold text-white font-mono">Hardhat Config</CardTitle>
              <CardDescription className="text-[11px] text-zinc-500 font-mono">hardhat.config.ts</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="relative rounded bg-zinc-950 p-2.5 border border-zinc-800/80 font-mono text-[11px] text-zinc-300">
                <pre className="overflow-x-auto leading-tight">{`networks: {
  arbitrum: {
    url: "https://rpc.driftguard.live/arb",
    chainId: 42161,
  },
}`}</pre>
                <button
                  onClick={() =>
                    copyToClipboard(
                      `networks: {\n  arbitrum: {\n    url: "https://rpc.driftguard.live/arb",\n    chainId: 42161,\n  },\n}`,
                      "hardhat-cfg"
                    )
                  }
                  className="absolute top-2 right-2 p-1 text-zinc-400 hover:text-white"
                  title="Copy Hardhat Config"
                >
                  {copiedId === "hardhat-cfg" ? <Check className="size-3 text-emerald-400" /> : <Copy className="size-3" />}
                </button>
              </div>
            </CardContent>
          </Card>

          {/* Viem / Alloy Card */}
          <Card className="bg-zinc-900/40 border-zinc-800/80 specular-border">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-semibold text-white font-mono">Viem / Ethers / Alloy</CardTitle>
              <CardDescription className="text-[11px] text-zinc-500 font-mono">RPC Transport Binding</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="relative rounded bg-zinc-950 p-2.5 border border-zinc-800/80 font-mono text-[11px] text-zinc-300">
                <pre className="overflow-x-auto leading-tight">{`import { createPublicClient, http } from 'viem';
import { arbitrum } from 'viem/chains';

export const client = createPublicClient({
  chain: arbitrum,
  transport: http('https://rpc.driftguard.live/arb'),
});`}</pre>
                <button
                  onClick={() =>
                    copyToClipboard(
                      `import { createPublicClient, http } from 'viem';\nimport { arbitrum } from 'viem/chains';\n\nexport const client = createPublicClient({\n  chain: arbitrum,\n  transport: http('https://rpc.driftguard.live/arb'),\n});`,
                      "viem-cfg"
                    )
                  }
                  className="absolute top-2 right-2 p-1 text-zinc-400 hover:text-white"
                  title="Copy Viem Snippet"
                >
                  {copiedId === "viem-cfg" ? <Check className="size-3 text-emerald-400" /> : <Copy className="size-3" />}
                </button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* 03 / Deterministic Out-of-Band Health Model */}
      <Card className="bg-zinc-900/40 border-zinc-800/80 specular-border">
        <CardHeader className="pb-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <CardTitle className="text-sm font-semibold text-white flex items-center gap-2 font-mono">
              <AlertTriangle className="size-4 text-zinc-300" />
              03 / Deterministic Out-of-Band Health Model
            </CardTitle>
            <Badge variant="outline" className="border-zinc-800 bg-zinc-950/60 text-zinc-400 text-[10px] font-mono tracking-wider w-fit">
              DECOUPLED CONTROL PLANE
            </Badge>
          </div>
          <CardDescription className="text-xs text-zinc-400 leading-relaxed pt-1 font-sans">
            Formal decoupling of L7 JSON-RPC data forwarding from asynchronous consensus verification.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="p-3.5 rounded-lg bg-zinc-950 border border-zinc-800/80 space-y-1.5">
              <span className="text-zinc-500 font-mono text-xs">01</span>
              <h4 className="text-xs font-semibold text-white font-mono">Sequencer Ingestion Stalls</h4>
              <p className="text-xs text-zinc-400 leading-relaxed font-sans">
                Upstream process serves HTTP 200 with stale state root during sequencer queue contention.
              </p>
            </div>

            <div className="p-3.5 rounded-lg bg-zinc-950 border border-zinc-800/80 space-y-1.5">
              <span className="text-zinc-500 font-mono text-xs">02</span>
              <h4 className="text-xs font-semibold text-white font-mono">Asynchronous Consensus Probe</h4>
              <p className="text-xs text-zinc-400 leading-relaxed font-sans">
                Sentinel polls independent out-of-band canonical anchor every 200ms without client latency overhead.
              </p>
            </div>

            <div className="p-3.5 rounded-lg bg-zinc-950 border border-zinc-800/80 space-y-1.5">
              <span className="text-zinc-500 font-mono text-xs">03</span>
              <h4 className="text-xs font-semibold text-white font-mono">Dynamic UNIX Socket Drain</h4>
              <p className="text-xs text-zinc-400 leading-relaxed font-sans">
                Executes 'set server state maint' via /run/haproxy/admin.sock within 130ms. Zero TCP connection resets.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 04 / Telemetry Event Dispatch & Webhooks */}
      <Card className="bg-zinc-900/40 border-zinc-800/80 specular-border">
        <CardHeader className="pb-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <CardTitle className="text-sm font-semibold text-white flex items-center gap-2 font-mono">
              <Radio className="size-4 text-zinc-300" />
              04 / Telemetry Event Dispatch &amp; Webhooks
            </CardTitle>
            <Badge variant="outline" className="border-zinc-800 bg-zinc-950/60 text-zinc-400 text-[10px] font-mono tracking-wider w-fit">
              OPERATIONAL TELEMETRY
            </Badge>
          </div>
          <CardDescription className="text-xs text-zinc-400 leading-relaxed pt-1 font-sans">
            Real-time webhook notification configuration for threshold breaches, socket drains, and consensus re-synchronizations.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3.5">
          <div className="relative rounded-md bg-zinc-950 p-3.5 border border-zinc-800/80 font-mono text-xs text-zinc-300">
            <pre className="overflow-x-auto leading-relaxed">{`# Discord Telemetry Webhook Configuration
DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/your-channel-webhook"

# Out-of-Band Alerting Thresholds & Debounce
FAILOVER_ALERT_COOLDOWN=10.0
DRIFT_THRESHOLD=4
FAILURE_THRESHOLD=2
RECOVERY_THRESHOLD=2`}</pre>
            <button
              onClick={() =>
                copyToClipboard(
                  `# Discord Telemetry Webhook Configuration\nDISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/your-channel-webhook"\n\n# Out-of-Band Alerting Thresholds & Debounce\nFAILOVER_ALERT_COOLDOWN=10.0\nDRIFT_THRESHOLD=4\nFAILURE_THRESHOLD=2\nRECOVERY_THRESHOLD=2`,
                  "env-webhooks"
                )
              }
              className="absolute top-3 right-3 p-1.5 rounded text-zinc-400 hover:text-white bg-zinc-800/60"
              title="Copy Webhook Configuration"
            >
              {copiedId === "env-webhooks" ? <Check className="size-3 text-emerald-400" /> : <Copy className="size-3" />}
            </button>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-zinc-800/60 text-xs font-mono">
            <span className="text-zinc-400">
              Live Operations Channel: Automated alerts streaming continuously to Discord #bot-stats (ISO-8601 UTC).
            </span>
            <a
              href="https://discord.gg/DZBDJSsSzN"
              target="_blank"
              rel="noreferrer"
              className="text-[#28A0F0] hover:underline flex items-center gap-1 font-medium font-sans"
            >
              <MessageSquare className="size-3" />
              <span>Join Discord #bot-stats →</span>
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
