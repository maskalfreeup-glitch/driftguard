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
            align(horizon)[#text(size: 8pt, fill: rgb("#475569"), weight: "bold", font: ("Roboto", "Liberation Sans"))[DRIFTGUARD | YOUTUBE CLIENT ACQUISITION BLUEPRINT & SCRIPT PACK]]
          )
        ],
        align(right + horizon)[
          #text(size: 7.5pt, fill: rgb("#DC2626"), weight: "bold", font: ("Roboto", "Liberation Sans"))[MEDIA & MARKETING RUNBOOK]
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
          #text(size: 7.5pt, fill: rgb("#94A3B8"), font: ("Roboto", "Liberation Sans"))[CONFIDENTIAL -- DRIFTGUARD SYSTEMS CLIENT ACQUISITION STRATEGY]
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
    rect(fill: rgb("#DC2626"), width: 4pt, height: 13pt, radius: 2pt),
    align(horizon)[#text(size: 12pt, weight: "bold", fill: rgb("#0F172A"))[#it.body]]
  )
  #v(1pt)
]

#show heading.where(level: 2): it => block(spacing: 7pt)[
  #v(2pt)
  #text(size: 9.5pt, weight: "bold", fill: rgb("#B91C1C"))[#it.body]
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
      #text(size: 10.5pt, weight: "medium", fill: rgb("#DC2626"))[MEDIA & MARKETING]
    ]
  )

  #v(0.15cm)
  #rect(
    fill: rgb("#FEF2F2"),
    stroke: 1pt + rgb("#FECACA"),
    radius: 999pt,
    inset: (x: 12pt, y: 4pt)
  )[
    #text(size: 7.5pt, weight: "bold", fill: rgb("#B91C1C"))[
      ● YOUTUBE POSITIONING BLUEPRINT | EDUCATIONAL TROJAN HORSE & B2B CONVERSION
    ]
  ]

  #v(0.25cm)
  #block(radius: 8pt, clip: true)[#image("/public/banner.png", width: 100%)]

  #v(0.35cm)
  #text(size: 17pt, weight: "black", fill: rgb("#090D16"))[
    YouTube Client Acquisition Series Blueprint
  ]

  #v(0.15cm)
  #text(size: 10pt, weight: "medium", fill: rgb("#475569"))[
    Full 4-Part Educational Script Pack, Technical Positioning Strategy & Inbound Retainer Conversion Funnel for Arbitrum Orbit L3s, Game Studios & Paymasters
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
      #text(weight: "bold", size: 7.5pt, fill: rgb("#64748B"))[CAMPAIGN IDENTIFIER]\
      #text(weight: "bold", size: 8.5pt, fill: rgb("#0F172A"))[DG-MKT-YT-001 (Version 2.0)]
    ],
    [
      #text(weight: "bold", size: 7.5pt, fill: rgb("#64748B"))[RETAINER CONVERSION TARGET]\
      #text(weight: "bold", size: 8.5pt, fill: rgb("#059669"))[\$2,500 -- \$8,500 / month Retainers]
    ],
    [
      #text(weight: "bold", size: 7.5pt, fill: rgb("#64748B"))[PRIMARY CLIENT TARGETS]\
      #text(size: 8pt, fill: rgb("#0F172A"))[Orbit L3 Founders | Game CTOs | Paymaster Bundlers]
    ],
    [
      #text(weight: "bold", size: 7.5pt, fill: rgb("#64748B"))[CORE CALL TO ACTION (CTA)]\
      #text(weight: "bold", size: 8pt, fill: rgb("#2563EB"))[Free 48-Hour RPC Resilience & Staleness Audit]
    ],
    [
      #text(weight: "bold", size: 7.5pt, fill: rgb("#64748B"))[STRATEGY FRAMEWORK]\
      #text(size: 8pt, fill: rgb("#0F172A"))[The "Educational Trojan Horse" Authority Funnel]
    ],
    [
      #text(weight: "bold", size: 7.5pt, fill: rgb("#64748B"))[VIDEO CONTENT VOLUME]\
      #text(size: 8pt, fill: rgb("#0F172A"))[4 Flagship Deep-Dive Educational Episodes]
    ],
    [
      #text(weight: "bold", size: 7.5pt, fill: rgb("#64748B"))[PROVEN REFERENCE TESTBED]\
      #text(size: 8pt, fill: rgb("#0F172A"))[#link("https://rpc.driftguard.live")[rpc.driftguard.live] (Active-Active OCI Cluster)]
    ],
    [
      #text(weight: "bold", size: 7.5pt, fill: rgb("#64748B"))[SECURITY CLASSIFICATION]\
      #text(weight: "bold", size: 8pt, fill: rgb("#DC2626"))[INTERNAL MAINTAINER STRATEGY RUNBOOK]
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
    *Core Strategic Directive:* Enterprise Web3 CTOs, rollup architects, and relayer leads do not respond to generic sales pitches. They respond to systems engineers who diagnose their production-halting bugs with surgical precision, teach the mechanics in code, and offer a managed enterprise service to eliminate the operational burden.
  ]
]

#pagebreak()

// ==========================================
// PAGE 2: FUNNEL STRATEGY & ROADMAP
// ==========================================

= 1. The "Educational Trojan Horse" Client Acquisition Funnel

```
+----------------------------------------------------------------------------------------------------+
|                             THE CLIENT ACQUISITION POSITIONING FUNNEL                              |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|   1. TOP OF FUNNEL: High-Signal Technical Authority on YouTube                                     |
|      • Teach the exact mechanics of obscure L2 failures ("The Silent 200 OK", Nonce Desync)        |
|      • Live terminal demonstrations, Wireshark/cURL inspections, and real mainnet crash data       |
|      • Zero fluff: 100% systems engineering (HAProxy C-sockets, Nitro 250ms drift, Async Python)   |
|                                                                                                    |
|   2. MIDDLE OF FUNNEL: Open-Source Generosity & Authority Proof                                    |
|      • Open-source all code under MIT license: "You can build and deploy this yourself"           |
|      • Showcase the live multi-node reference testbed (rpc.driftguard.live) and benchmarks         |
|                                                                                                    |
|   3. BOTTOM OF FUNNEL: High-Ticket B2B Conversion CTA                                              |
|      • Lead Magnet CTA: "Book a Free 48-Hour RPC Resilience & Staleness Audit"                     |
|      • Audit Delivery: We benchmark their upstream RPCs, map single-points-of-failure, and deliver |
|        a customized Resilience Scorecard (SOP-01 from our Enterprise Runbook).                     |
|      • The Retainer Offer: "If you want our systems team to manage this active-active gateway,     |
|        provide custom consensus anchors, and guarantee <15 min Sev-1 response on 24/7 on-call,    |
|        we offer monthly managed retainers ($2.5k - $8.5k/mo)."                                     |
+----------------------------------------------------------------------------------------------------+
```

#v(8pt)

= 2. 4-Part Video Series Content Roadmap

#table(
  columns: (0.8fr, 1.3fr, 1.5fr, 1fr),
  fill: (col, row) => if row == 0 { rgb("#0F172A") } else if calc.even(row) { rgb("#F8FAFC") } else { white },
  stroke: 0.5pt + rgb("#CBD5E1"),
  inset: 5pt,
  align: (col, row) => if row == 0 { center + horizon } else { left + horizon },
  table.header(
    [*Episode*],
    [*Title & Primary Hook*],
    [*Core Technical Teaching*],
    [*B2B Client Target*]
  ),
  [Episode 1],
  [*The "Silent 200 OK" Trap:*\ Why Fast Rollups Break When Nodes Say Healthy],
  [Transport-layer vs Consensus-layer health checking; ~250ms Nitro block velocity; why Cloudflare/AWS ALBs fail silently.],
  [Orbit L3 Rollup Founders & Infrastructure Leads],
  [Episode 2],
  [*The Paymaster Nightmare:*\ How Stale RPCs Paralyze Smart Wallets],
  [`eth_getTransactionCount` race conditions; why client-side `fallback()` causes 5s timeouts; monotonic nonce guarantees.],
  [ERC-4337 Account Abstraction Paymasters & Bundlers],
  [Episode 3],
  [*Sub-130ms Failover in Code:*\ Zero-Drop C-Sockets & Asyncio],
  [C-native HAProxy event loops; `/run/haproxy/admin.sock`; Python 3.12 asyncio sentinel; hysteresis flap prevention.],
  [DeFi Relayers, Keepers & MEV Operators],
  [Episode 4],
  [*Zero-Downtime Orbit L3 Nodes:*\ Active-Active HA for \< \$10/mo],
  [Active-active Cloudflare Anycast ingress; geo-redundant multi-node clustering; live SEV-2 incident triage breakdown.],
  [Dedicated Web3 Game Studios & Appchains]
)

#pagebreak()

// ==========================================
// PAGE 3: EPISODE 1 FULL SCRIPT
// ==========================================

= 3. Episode 1 Script: The "Silent 200 OK" Trap

*Title:* Why Your Rollup RPC Returns HTTP 200 While Silently Bleeding Transactions\
*Duration:* 10--12 Minutes | *Target:* Orbit Rollup Architects, DeFi Engineers

== Scene 1: The Hook (0:00 -- 1:30)
- *Visual:* Maintainer on camera in dark-mode engineering setup, cutting to Grafana dashboard showing 100% green HTTP 200 status while Discord support tickets flood in with failed transactions.
- *Script:*
  _"If you are running infrastructure on Arbitrum, Base, or an Orbit L3 rollup, I can almost guarantee you have a hidden timebomb in your stack right now.
  Your monitoring dashboard is completely green. AWS ALB or Cloudflare says 'All Targets Healthy - HTTP 200 OK'. But your users are in Discord screaming that their transactions are reverting, nonces are desynced, and smart wallet paymasters have completely frozen.
  In distributed systems, this is known as *The Silent 200 OK Problem*. In this video, I'm going to pull back the curtain on why standard cloud load balancers are architecturally blind to EVM rollup consensus, show you live on my terminal how a 3-second network blip on Arbitrum Nitro leaves an RPC node 12 blocks in the past, and teach you how to build an out-of-band consensus sentinel that drains delinquent nodes in under 130 milliseconds without dropping a single TCP connection. Let's dive in."_

== Scene 2: The Systems Deep Dive (1:30 -- 5:30)
- *Visual:* Animation comparing Layer 4/7 Transport Health checks vs Consensus-Layer Health checks.
- *Script:*
  _"Standard cloud load balancers—AWS ALB, Google Envoy, Cloudflare, vanilla NGINX—operate strictly at the transport layer. They establish a TCP handshake, send an HTTP GET/POST request, and if they get status code 200, they mark the node healthy.
  But on Arbitrum Nitro, blocks produce every *250 milliseconds*. When an RPC node encounters an upstream sequencer ingestion stall or enters background resynchronization (`eth_syncing = true`), its local web server doesn't crash. It happily accepts queries and returns `HTTP 200 OK`—serving data from block 511,619,835 while canonical head has surged to 511,619,849! To your AWS ALB, that node is 100% healthy. To your users, that node is living 14 blocks in the past."_

== Scene 3: Live Terminal Demonstration (5:30 -- 8:30)
- *Visual:* Terminal split-screen. Left: `autocannon` firing sustained requests. Right: injecting a simulated sequencer ingestion stall. Demonstrating standard load balancer leaking stale reads, while DriftGuard detects it in 180ms and cuts over in 122ms.
- *Script:*
  _"Watch the timestamp on DriftGuard: divergence detected in 180 milliseconds. The sentinel fires a direct socket command over `/run/haproxy/admin.sock`. The delinquent node is drained in exactly 122.8 milliseconds. Error rate: 0.00%. Zero dropped packets. Zero broken TCP connections."_

== Scene 4: The Teaching & Hysteresis Flap Prevention (8:30 -- 10:30)
- *Visual:* Code walkthrough of `haproxy.cfg` and `sentinel/src/monitor.py`. Explaining hysteresis flap prevention (`failure_threshold: 1`, `recovery_threshold: 2`).

== Scene 5: The B2B Client Acquisition CTA (10:30 -- 12:00)
- *Visual:* Maintainer on camera, pointing to description. Lower-third: *"Book a Free 48-Hour RPC Resilience Audit"*.
- *Script:*
  _"If you are an independent developer, take our open-source code and run it. That's why we built it as a public good.
  But if you are the Founder, CTO, or Lead Infrastructure Engineer of an *Arbitrum Orbit L3 chain, a Web3 gaming studio, or an ERC-4337 paymaster*, your uptime directly impacts your bottom line.
  Through our *DriftGuard Enterprise Retainer*, our systems team manages your active-active ingress gateway, provides custom consensus anchor calibration against your private validator nodes, and guarantees a sub-15-minute Sev-1 incident response SLA with 99.99% availability.
  In the description below, click the link to book a *Free 48-Hour RPC Resilience & Staleness Audit*. We will hook up our diagnostic harness to your existing RPC pool, benchmark your upstreams under load, identify your single points of failure, and deliver a comprehensive Resilience Scorecard at zero cost. Grab a time with our systems team, and let's ensure your rollup never serves a stale block again."_

#pagebreak()

// ==========================================
// PAGE 4: EPISODE 2 & 3 SCRIPTS
// ==========================================

= 4. Episode 2 Script: The Paymaster Nightmare

*Title:* Why Your ERC-4337 Smart Wallet Transactions Keep Reverting ("Nonce Too Low" Explained)\
*Duration:* 11--13 Minutes | *Target:* Account Abstraction Developers, Paymaster Providers

== Core Teaching & Spoken Script Highlights:
- *The Hook (0:00 -- 1:45):*
  _"You integrated ERC-4337 for gasless onboarding to give users a frictionless Web2 experience. But during peak mints or trading volume, 15% of your user operations fail with `nonce too low` or `AA25 invalid account nonce`. The issue isn't your smart contract or your paymaster code. It's the fact that your distributed bundler workers are querying a round-robin RPC pool where one node is lagging 3 blocks behind."_
- *The Systems Lesson (1:45 -- 7:00):*
  - Deep-dive into `eth_getTransactionCount(address, "latest")` race conditions across distributed bundlers.
  - Why client-side `fallback()` in Viem or Ethers creates catastrophic 5-second round-trip latency penalties and worker race conditions.
  - How an L7 proxy with stick-tables and consensus-anchored draining guarantees monotonically increasing nonce reads.
- *The Retainer CTA (9:30 -- 11:30):*
  _"If you are running an ERC-4337 paymaster or relayer queue handling more than 10,000 daily user operations, book a Free Paymaster Resilience Audit below. We will audit your relayer topology and show you how to eliminate nonce flapping permanently."_

#v(8pt)

= 5. Episode 3 Script: Sub-130ms Failover in Code

*Title:* Building a Sub-130ms EVM Failover Engine with HAProxy UNIX Sockets & Python Asyncio\
*Duration:* 12--15 Minutes | *Target:* DevOps Engineers, SREs, Systems Programmers

== Core Teaching & Spoken Script Highlights:
- *The Hook (0:00 -- 1:30):*
  _"Cloud load balancers take 10 to 30 seconds to fail over. In that window, an Arbitrum Nitro sequencer has processed 80 blocks. Here is how to achieve 122ms failover using raw UNIX domain sockets and asynchronous consensus polling."_
- *The Deep Technical Systems Breakdown (1:30 -- 10:00):*
  - Dissecting HAProxy's runtime administration socket (`stats socket /run/haproxy/admin.sock level admin`).
  - Executing `set server <backend>/<srv> state maint` directly into HAProxy's epoll loop without reloading the process or dropping in-flight TCP sessions.
  - Asynchronous HTTP/2 connection pooling with Python 3.12 and `httpx`.
  - Hysteresis algorithms in Python: calculating drift deltas against canonical block anchors every 200ms.
- *The Retainer CTA (12:00 -- 14:00):*
  _"Building this in-house requires continuous maintenance, custom Prometheus exporters, and on-call alerting. If you want a turn-key enterprise sidecar with 24/7 managed support for your infrastructure, check out our Retainer Service SOP and book an onboarding call below."_

#pagebreak()

// ==========================================
// PAGE 5: EPISODE 4 & YOUTUBE SEO METADATA
// ==========================================

= 6. Episode 4 Script: Zero-Downtime Orbit L3 Nodes

*Title:* How We Built a Geo-Redundant Active-Active RPC Cluster for Under \$10/mo (Architecture Teardown)\
*Duration:* 12--14 Minutes | *Target:* Web3 Gaming CTOs, Orbit Appchain Founders, Solo Node Validators

== Core Teaching & Spoken Script Highlights:
- *The Hook (0:00 -- 1:30):*
  _"Enterprise RPC vendors will charge an Orbit rollup team \$5,000 to \$10,000 a month for enterprise high availability. Today, I'm tearing down our production cluster: two Oracle Cloud Linux instances running active-active behind Cloudflare Anycast for practically zero cloud cost."_
- *The Production Architecture Breakdown (1:30 -- 9:30):*
  - Live inspection of Node 1 (`129.80.34.125`) and Node 2 (`193.122.236.215`).
  - Dual-connector Cloudflare tunnel routing with instant edge failover.
  - Review of the October 4, 2026 SEV-2 Arbitrum One sequencer incident triage log.
  - How Orbit gaming appchains eliminate "ghost inventory items" and session drops.
- *The Grand B2B Close (11:00 -- 13:00):*
  _"If you're launching an Orbit L3 chain or an on-chain game, infrastructure reliability is your brand reputation. You can use our open-source blueprints for free, OR you can hire DriftGuard Systems on a monthly retainer (\$5,000/mo for Orbit rollups) to orchestrate your multi-node cluster, calibrate your consensus sentinels, and provide guaranteed 99.99% SLA coverage with \<15 min Sev-1 response. Click the link below to schedule your Rollup Resilience Audit."_

#v(8pt)

= 7. Video Metadata & YouTube Optimization Pack

== Episode 1 Metadata & Description Template
```markdown
Your load balancer says "All Targets Healthy - HTTP 200 OK", but your users' transactions are 
reverting with "nonce too low" and your relayer queues are frozen. 

In this video, we break down "The Silent 200 OK Problem" on EVM rollups (Arbitrum Nitro, Base), 
demonstrate the root cause on a live terminal, and show how out-of-band consensus sentinels 
execute sub-130ms failover without dropping client connections.

📌 TIMESTAMPS:
0:00 - The Hidden RPC Timebomb on Fast Rollups
1:30 - Transport Layer (HTTP 200) vs Consensus Layer Health
3:45 - The 250ms Nitro Block Cadence & Why 3s Desyncs Are Fatal
5:30 - Live Terminal Demo: Simulating Sequencer Ingestion Stall
8:30 - The Fix: Decoupled Dual-Plane Architecture & UNIX Sockets
10:30 - Open Source Repo & Free RPC Architecture Audit

🔗 RESOURCES & LINKS:
• Book a Free 48-Hour RPC Resilience & Staleness Audit: https://driftguard.live/audit
• GitHub Repository (MIT Open Source): https://github.com/maskalfreeup-glitch/driftguard
• Live Reference Gateway: https://rpc.driftguard.live
• B2B Enterprise Retainer SOP: https://driftguard.live/enterprise

#Arbitrum #Web3Dev #SmartContracts #DevOps #EVM #AccountAbstraction
```

#pagebreak()

// ==========================================
// PAGE 6: INBOUND QUALIFICATION SOP
// ==========================================

= 8. Maintainer Inbound Lead Qualification Runbook

When a YouTube viewer clicks the link and books an audit, follow this exact SOP to convert them into a paid monthly retainer:

```
[Inbound Booking via YouTube Link]
          │
          ├── Client submits: Chain ID, Upstream RPCs, Monthly Tx Volume, Pain Points
          │
          v
[Step 1: Automated 48-Hour Pre-Flight Audit (SOP-01)]
          │
          ├── Maintainer points diagnostic probe at client's public/private endpoints
          ├── Measure 48-hour latency jitter, head propagation lag, and HTTP 429 errors
          │
          v
[Step 2: The 30-Minute Resilience Scorecard Call]
          │
          ├── Minutes 0-10: Walk client through their actual measured desync events & lag
          ├── Minutes 10-20: Show them why their current ALB/Viem fallback is causing reverts
          ├── Minutes 20-25: Present the DriftGuard Sidecar Architecture fix
          └── Minutes 25-30: Offer the B2B Retainer:
                • "You can self-host the open-source repo, OR..."
                • "Our team will deploy and manage the sidecar cluster, calibrate consensus
                   anchors, and provide 24/7 on-call Sev-1 response (<15 min SLA) for $5k/mo."
          │
          v
[Step 3: Retainer Agreement Execution]
          ├── Execute standard month-to-month service agreement
          └── Kick off SOP-02 (Sidecar Deployment & Canary Traffic Cutover)
```

#v(8pt)

= 9. Discovery Call Closing Scripts for $2,500 -- $8,500/mo Retainers

- *Handling the "We'll build it ourselves" Objection:*
  _"You absolutely can! Everything is in our GitHub under the MIT license. But building it in-house means your senior engineers are on-call 24/7 every time an Arbitrum sequencer feed drops or a public RPC flaps. For \$5,000/month, you get dedicated systems engineers managing the ingress gateway, guaranteed \<15 minute Sev-1 response, and a 99.99% availability SLA. It frees your team to build your core game or rollup."_
- *The "Free Audit to Retainer" Bridge:*
  _"Based on the 48-hour audit we just reviewed, your primary node lagged behind the canonical head 14 times, representing 42 missed Nitro blocks. Here are your options: Option 1, use our free Docker Compose template. Option 2, bring us on retainer under Tier 2, and we'll take over ingress reliability starting tomorrow."_

#v(16pt)
#align(center)[
  #text(size: 8pt, fill: rgb("#94A3B8"))[
    *DRIFTGUARD SYSTEMS* • YOUTUBE CLIENT ACQUISITION BLUEPRINT & SCRIPT PACK • VERSION 2.0\
    Lead Acquisition Desk: `growth@driftguard.live` • Operations Desk: `operations@driftguard.live`\
    Repository: #link("https://github.com/maskalfreeup-glitch/driftguard")[github.com/maskalfreeup-glitch/driftguard] • Portal: #link("https://driftguard.live")[driftguard.live]
  ]
]
