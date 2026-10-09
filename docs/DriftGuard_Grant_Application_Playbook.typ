#set page(
  paper: "a4",
  margin: (top: 2.0cm, bottom: 2.0cm, left: 2.0cm, right: 2.0cm),
  header: context {
    if counter(page).get().first() > 1 {
      grid(
        columns: (1fr, auto),
        align(left + horizon)[
          #grid(
            columns: (auto, auto),
            gutter: 6pt,
            align(horizon)[#image("/public/favicon.svg", width: 11pt)],
            align(horizon)[#text(size: 8pt, fill: rgb("#475569"), weight: "bold", font: ("Roboto", "Liberation Sans"))[DRIFTGUARD | MAINTAINER GRANT APPLICATION PLAYBOOK]]
          )
        ],
        align(right + horizon)[
          #text(size: 7.5pt, fill: rgb("#0284C7"), weight: "bold", font: ("Roboto", "Liberation Sans"))[TACTICAL PLAYBOOK]
        ]
      )
      v(-4pt)
      line(length: 100%, stroke: 0.5pt + rgb("#CBD5E1"))
    }
  },
  footer: context {
    if counter(page).get().first() > 1 {
      line(length: 100%, stroke: 0.5pt + rgb("#E2E8F0"))
      v(2pt)
      grid(
        columns: (1fr, auto),
        align(left + horizon)[
          #text(size: 7.5pt, fill: rgb("#94A3B8"), font: ("Roboto", "Liberation Sans"))[CONFIDENTIAL -- DRIFTGUARD SYSTEMS INTERNAL MAINTAINER PLAYBOOK]
        ],
        align(right + horizon)[
          #text(size: 8pt, fill: rgb("#475569"), weight: "bold", font: ("Roboto", "Liberation Sans"))[Page #counter(page).display("1 of 1", both: true)]
        ]
      )
    }
  }
)

#set text(
  font: ("Roboto", "Liberation Sans", "Noto Sans"),
  size: 8.8pt,
  fill: rgb("#1E293B"),
  lang: "en"
)

#set par(justify: true, leading: 0.58em)

#show heading.where(level: 1): it => block(spacing: 10pt)[
  #v(3pt)
  #grid(
    columns: (4pt, 1fr),
    gutter: 7pt,
    rect(fill: rgb("#0284C7"), width: 4pt, height: 13pt, radius: 2pt),
    align(horizon)[#text(size: 12pt, weight: "bold", fill: rgb("#0F172A"))[#it.body]]
  )
  #v(1pt)
]

#show heading.where(level: 2): it => block(spacing: 7pt)[
  #v(2pt)
  #text(size: 9.5pt, weight: "bold", fill: rgb("#0369A1"))[#it.body]
  #v(1pt)
]

#show raw: set text(font: ("Liberation Mono", "DejaVu Sans Mono"), size: 7.2pt)
#show raw.where(block: true): it => block(
  fill: rgb("#090D16"),
  inset: 7pt,
  radius: 5pt,
  width: 100%,
  stroke: 0.5pt + rgb("#1E293B")
)[
  #text(fill: rgb("#E2E8F0"))[#it]
]

// ==========================================
// PAGE 1: COVER PAGE
// ==========================================

#align(center)[
  #v(0.2cm)
  #grid(
    columns: (auto, auto),
    gutter: 10pt,
    align(horizon)[#image("/public/favicon.svg", width: 26pt)],
    align(horizon)[
      #text(size: 17pt, weight: "black", fill: rgb("#090D16"), tracking: 0.5pt)[DRIFTGUARD]
      #h(4pt)
      #text(size: 10.5pt, weight: "medium", fill: rgb("#0284C7"))[PLAYBOOK]
    ]
  )

  #v(0.15cm)
  #rect(
    fill: rgb("#EFF6FF"),
    stroke: 1pt + rgb("#BFDBFE"),
    radius: 999pt,
    inset: (x: 12pt, y: 4pt)
  )[
    #text(size: 7.5pt, weight: "bold", fill: rgb("#1D4ED8"))[
      ● MAINTAINER TACTICAL GUIDE | ECOSYSTEM APPLICATION PLAYBOOK & DEFENSE
    ]
  ]

  #v(0.25cm)
  #block(radius: 8pt, clip: true)[#image("/public/banner.png", width: 100%)]

  #v(0.35cm)
  #text(size: 17pt, weight: "black", fill: rgb("#090D16"))[
    Grant Application Playbook & Submission Guide
  ]

  #v(0.15cm)
  #text(size: 10pt, weight: "medium", fill: rgb("#475569"))[
    Step-by-Step Portals, Form-Ready Snippets, Interview Defense Runbook & Calendar for Arbitrum, Base, Superchain, and Gitcoin
  ]

  #v(0.35cm)
]

#rect(
  fill: rgb("#F8FAFC"),
  stroke: 1pt + rgb("#CBD5E1"),
  radius: 7pt,
  inset: 9pt,
  width: 100%
)[
  #grid(
    columns: (1fr, 1fr),
    row-gutter: 6pt,
    column-gutter: 14pt,
    [
      #text(weight: "bold", size: 7.5pt, fill: rgb("#64748B"))[PRIMARY GOAL]\
      #text(weight: "bold", size: 8.5pt, fill: rgb("#0F172A"))[Secure \$25k--\$35k Tooling Grant Funding]
    ],
    [
      #text(weight: "bold", size: 7.5pt, fill: rgb("#64748B"))[TARGET ECOSYSTEMS]\
      #text(weight: "bold", size: 8.5pt, fill: rgb("#0284C7"))[Arbitrum (One/Orbit), Base, OP Superchain, Gitcoin]
    ],
    [
      #text(weight: "bold", size: 7.5pt, fill: rgb("#64748B"))[SUBMISSION SPRINT]\
      #text(size: 8pt, fill: rgb("#0F172A"))[Week 1 Prep \$\to\$ Week 2 Submissions \$\to\$ Week 4 Close]
    ],
    [
      #text(weight: "bold", size: 7.5pt, fill: rgb("#64748B"))[CRITICAL FRAMING RULE]\
      #text(weight: "bold", size: 8pt, fill: rgb("#16A34A"))[100% Tooling Grant (\$0 Requested for Hosting)]
    ],
    [
      #text(weight: "bold", size: 7.5pt, fill: rgb("#64748B"))[MAINTAINER REPO]\
      #text(size: 8pt, fill: rgb("#0F172A"))[#link("https://github.com/maskalfreeup-glitch/driftguard")[github.com/maskalfreeup-glitch/driftguard]]
    ],
    [
      #text(weight: "bold", size: 7.5pt, fill: rgb("#64748B"))[SUSTAINABILITY PROOF]\
      #text(size: 8pt, fill: rgb("#0F172A"))[B2B Retainer Service SOP (`docs/B2B_RETAINER_SERVICE_SOP.md`)]
    ],
    [
      #text(weight: "bold", size: 7.5pt, fill: rgb("#64748B"))[LIVE PROOF HARNESS]\
      #text(size: 8pt, fill: rgb("#0F172A"))[#link("https://rpc.driftguard.live")[rpc.driftguard.live] (Dual OCI Active-Active)]
    ],
    [
      #text(weight: "bold", size: 7.5pt, fill: rgb("#64748B"))[SECURITY CLASSIFICATION]\
      #text(weight: "bold", size: 8pt, fill: rgb("#DC2626"))[INTERNAL MAINTAINER USE ONLY]
    ]
  )
]

#v(0.35cm)

#rect(
  fill: rgb("#EFF6FF"),
  stroke: 1pt + rgb("#BFDBFE"),
  radius: 6pt,
  inset: 8pt,
  width: 100%
)[
  #text(size: 7.5pt, fill: rgb("#1E40AF"))[
    *Maintainer Mission Statement:* This playbook provides copy-paste ready application form snippets, submission portal links, evaluation criteria rubrics, and committee interview defense guidelines. Use this guide to execute a coordinated multi-ecosystem application campaign.
  ]
]

#pagebreak()

// ==========================================
// PAGE 2: PORTALS & FORM SNIPPETS
// ==========================================

= 1. Target Ecosystem Grant Portals

#table(
  columns: (1fr, 1.2fr, 1fr, 0.9fr, 0.9fr),
  fill: (col, row) => if row == 0 { rgb("#0F172A") } else if calc.even(row) { rgb("#F8FAFC") } else { white },
  stroke: 0.5pt + rgb("#CBD5E1"),
  inset: 5pt,
  align: (col, row) => if row == 0 { center + horizon } else { left + horizon },
  table.header(
    [*Grant Program*],
    [*Submission URL*],
    [*Track*],
    [*Funding Range*],
    [*Action*]
  ),
  [Arbitrum Questbook],
  [#link("https://arbitrum.questbook.app/")[arbitrum.questbook.app]],
  [Developer Tooling],
  [\$15k -- \$25k in ARB],
  [Submit Week 2],
  [Arbitrum Foundation],
  [#link("https://arbitrum.foundation/grants")[arbitrum.foundation/grants]],
  [Node Infrastructure],
  [\$25k -- \$50k in ARB],
  [Submit Week 2],
  [Base Builder Grants],
  [#link("https://base.org/grants")[base.org/grants]],
  [Developer Tooling],
  [\$10k -- \$25k in ETH],
  [Submit Week 2],
  [Optimism RetroPGF],
  [#link("https://app.optimism.io/retropgf")[app.optimism.io/retropgf]],
  [Superchain Tooling],
  [Retroactive Pool],
  [Open Rounds],
  [Gitcoin Grants OSS],
  [#link("https://grants.gitcoin.co/")[grants.gitcoin.co]],
  [Open Source Software],
  [Matching Pool],
  [Next Round]
)

#v(8pt)

= 2. Standard Application Form Fields (Copy & Paste Ready)

*Project Title:* `DriftGuard: Deterministic L7 Ingress Gateway & Out-of-Band Consensus Sentinel`\
*Tagline (Elevator Pitch):* `DriftGuard is an open-source, ultra-low-footprint (<45 MB RAM) systems daemon and sidecar controller providing sub-130ms deterministic failover for Arbitrum Orbit L3s, Base, and session relayers.`

== Project Description (Copy-Paste)
```markdown
DriftGuard is an open-source systems daemon and sidecar controller engineered for EVM rollups (Arbitrum One, Arbitrum Nova, Arbitrum Orbit L3s, Base) and session relayers requiring sub-130ms deterministic failover with zero client code modifications.

High-velocity rollups produce blocks at rapid cadence (~250ms on Arbitrum Nitro; sub-second flashblocks on Base). Standard cloud load balancers (AWS ALB, Cloudflare, vanilla NGINX) rely strictly on transport-layer health checks (TCP connect, HTTP 200). When an RPC node encounters an upstream ingestion freeze or background resynchronization (eth_syncing = true), it continues returning HTTP 200 OK while serving obsolete nonces and stale block heights.

This causes immediate ERC-4337 Account Abstraction paymaster failures ("nonce too low"), DeFi liquidation front-running losses, and game server state desynchronization.

DriftGuard implements a decoupled dual-plane architecture:
1. Data Plane: High-throughput C-native HAProxy 2.8+ L7 reverse proxy.
2. Control Plane: Asynchronous Python 3.12 consensus sentinel sampling canonical block heights every 200ms out-of-band.
3. Failover Engine: Atomic UNIX domain socket drain in < 1ms, terminating zero in-flight client TCP sessions.

DriftGuard is an open-source software primitive. The maintainers independently operate a zero-cost reference testbed at https://rpc.driftguard.live demonstrating empirical resilience with 122.8ms cutover in live SEV-2 triage.
```

== Post-Grant Sustainability & Business Model (Copy-Paste)
```markdown
DriftGuard operates a Dual-Track Sustainability Model:
1. Open-Source Public Good (100% Free): The core Docker sidecar, Kubernetes Helm chart, @driftguard/sdk, and Prometheus exporter are MIT-licensed and perpetually free.
2. Commercial B2B Retainer Service: Enterprise Orbit L3 chains, Web3 gaming studios, and ERC-4337 paymaster bundlers purchase managed ingress orchestration, custom consensus anchor calibration, and 24/7 incident response SLAs (\$2,500 - \$8,500/month).

This commercial retainer funds ongoing engineering and on-call maintenance without requiring perpetual DAO grant subsidies. Full SOP documented at docs/B2B_RETAINER_SERVICE_SOP.md.
```

#pagebreak()

// ==========================================
// PAGE 3: MILESTONE FORM DATA & DEFENSE CHEAT-SHEET
// ==========================================

= 3. Milestone Form Entries (Copy & Paste)

- *Milestone 1 (\$10,000 USD):* Production Core Engine, Dynamic UNIX Socket Drain, Multi-Chain Routing (/arb, /nova, /base), Standalone Docker Sidecar (\<45 MB RAM), Automated Chaos Test Suite. *KPI:* Sub-130ms cutover verified; 0 dropped requests under sustained load. *(100% Complete)*
- *Milestone 2 (\$10,000 USD):* WebSocket Sequencer Feed Listener (`wss://arb1.arbitrum.io/feed`), Arbitrum Nova AnyTrust DAC Monitor, Turnkey Orbit L3 / OP Stack Blueprints, TypeScript `@driftguard/sdk` with Viem transport. *KPI:* Cutover on feed disconnect in \< 50ms; 3 validated blueprints; >85% test coverage.
- *Milestone 3 (\$8,000 USD):* Prometheus Metrics Exporter, Official Grafana Dashboard Pack, Kubernetes Helm Chart Sidecar Operator, Automated Incident Alerting Webhooks (Discord, Telegram, PagerDuty). *KPI:* Helm chart lint/install passing; single-click Grafana import; \<200ms alert dispatch.
- *Milestone 4 (\$7,000 USD):* `driftguard-chaos` Developer CLI, 10,000 req/s Load Testing Benchmark Harness, Orbit Rollup Operator Integration Guides, 3 Onboarded Pilot Teams. *KPI:* Published benchmark at 10k req/s; chaos CLI published; 3 documented pilot partner retrospectives.

#v(8pt)

= 4. Grant Committee Interview Defense Cheat-Sheet

#table(
  columns: (1.4fr, 2.6fr),
  fill: (col, row) => if row == 0 { rgb("#0F172A") } else if calc.even(row) { rgb("#F8FAFC") } else { white },
  stroke: 0.5pt + rgb("#CBD5E1"),
  inset: 5pt,
  align: (col, row) => if row == 0 { center + horizon } else { left + horizon },
  table.header(
    [*Reviewer Question*],
    [*Maintainer Winning Answer*]
  ),
  [*"Why should the DAO fund this if you have a public endpoint? Is this a hosting grant?"*],
  [*"No, this is 100% a developer tooling grant. We are requesting \$0 for hosting.* The public endpoint is our own self-funded testbed proving the code works. The grant deliverable is the open-source software daemon, Helm chart, Viem SDK, and Orbit presets that any rollup operator runs on their own hardware."],
  [*"Why can't rollups just use AWS ALB or Cloudflare Load Balancing?"*],
  [*"Cloud load balancers only check HTTP 200 and TCP.* When an RPC node encounters an upstream sequencer ingestion stall, its web server keeps returning HTTP 200 OK while frozen 15 blocks behind. Wallets and paymasters get stale nonces and fail immediately. Cloud balancers are completely blind to block height and `eth_syncing`."],
  [*"Why not just use client-side Viem fallback()?"*],
  [*"Viem fallback incurs round-trip timeout penalties (5+ seconds per error).* It also cannot coordinate state across distributed relayer workers, causing nonce flapping and race conditions. DriftGuard moves failover to the local UNIX socket in \< 1ms with zero client code changes."],
  [*"How will you maintain this after the grant runs out?"*],
  [*"Through our Commercial B2B Retainer Service.* We provide managed sidecar orchestration and 24/7 on-call SLAs (\$2.5k--\$8.5k/mo) to enterprise Orbit L3 chains, games, and paymasters. This gives us long-term commercial sustainability without asking the DAO for ongoing subsidies."]
)

#v(8pt)

= 5. Reviewer 60-Second Live Verification Script
```bash
# 1. Test Ingress across Arbitrum One, Nova, and Base
curl -s -X POST https://rpc.driftguard.live/arb -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
curl -s -X POST https://rpc.driftguard.live/nova -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
curl -s -X POST https://rpc.driftguard.live/base -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'

# 2. Verify Live Out-of-Band Consensus Telemetry
curl -s https://rpc.driftguard.live/healthz | jq .
```

#v(16pt)
#align(center)[
  #text(size: 8pt, fill: rgb("#94A3B8"))[
    *DRIFTGUARD SYSTEMS* • MAINTAINER GRANT APPLICATION PLAYBOOK • VERSION 2.0\
    Operations Desk: `operations@driftguard.live` • Emergency On-Call: PagerDuty / Telegram Priority Desk\
    Repository: #link("https://github.com/maskalfreeup-glitch/driftguard")[github.com/maskalfreeup-glitch/driftguard] • Portal: #link("https://driftguard.live")[driftguard.live]
  ]
]
