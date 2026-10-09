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
            align(horizon)[#text(size: 8pt, fill: rgb("#475569"), weight: "bold", font: ("Roboto", "Liberation Sans"))[DRIFTGUARD | B2B RETAINER SERVICE STANDARD OPERATING PROCEDURE]]
          )
        ],
        align(right + horizon)[
          #text(size: 7.5pt, fill: rgb("#059669"), weight: "bold", font: ("Roboto", "Liberation Sans"))[ENTERPRISE RUNBOOK]
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
          #text(size: 7.5pt, fill: rgb("#94A3B8"), font: ("Roboto", "Liberation Sans"))[CONFIDENTIAL -- DRIFTGUARD SYSTEMS ENTERPRISE OPERATIONS & CLIENT RUNBOOK]
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
    rect(fill: rgb("#059669"), width: 4pt, height: 13pt, radius: 2pt),
    align(horizon)[#text(size: 12pt, weight: "bold", fill: rgb("#0F172A"))[#it.body]]
  )
  #v(1pt)
]

#show heading.where(level: 2): it => block(spacing: 7pt)[
  #v(2pt)
  #text(size: 9.5pt, weight: "bold", fill: rgb("#047857"))[#it.body]
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
      #text(size: 10.5pt, weight: "medium", fill: rgb("#059669"))[ENTERPRISE]
    ]
  )

  #v(0.15cm)
  #rect(
    fill: rgb("#F0FDF4"),
    stroke: 1pt + rgb("#BBF7D0"),
    radius: 999pt,
    inset: (x: 12pt, y: 4pt)
  )[
    #text(size: 7.5pt, weight: "bold", fill: rgb("#16A34A"))[
      ● STANDARD OPERATING PROCEDURE (SOP) | B2B CLIENT RETAINER SERVICE RUNBOOK
    ]
  ]

  #v(0.25cm)
  #block(radius: 8pt, clip: true)[#image("/public/banner.png", width: 100%)]

  #v(0.35cm)
  #text(size: 17pt, weight: "black", fill: rgb("#090D16"))[
    B2B Retainer Service Operations Runbook
  ]

  #v(0.15cm)
  #text(size: 10pt, weight: "medium", fill: rgb("#475569"))[
    Turnkey Ingress Orchestration, Out-of-Band Consensus Sentinel Monitoring & 24/7 Incident Escalation for Arbitrum Orbit L3s, Game Studios & Account Abstraction Bundlers
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
      #text(weight: "bold", size: 7.5pt, fill: rgb("#64748B"))[DOCUMENT IDENTIFIER]\
      #text(weight: "bold", size: 8.5pt, fill: rgb("#0F172A"))[DG-SOP-B2B-001 (Version 2.0)]
    ],
    [
      #text(weight: "bold", size: 7.5pt, fill: rgb("#64748B"))[COMMERCIAL PRICING TIERS]\
      #text(weight: "bold", size: 8.5pt, fill: rgb("#059669"))[\$2,500 / \$5,000 / \$8,500 per Month]
    ],
    [
      #text(weight: "bold", size: 7.5pt, fill: rgb("#64748B"))[TARGET CLIENT BASE]\
      #text(size: 8pt, fill: rgb("#0F172A"))[Orbit L3 Rollups | Game Studios | ERC-4337 Bundlers]
    ],
    [
      #text(weight: "bold", size: 7.5pt, fill: rgb("#64748B"))[INCIDENT RESPONSE SLA]\
      #text(size: 8pt, fill: rgb("#0F172A"))[\< 15 min Sev-1 Escalation (24/7 Paging)]
    ],
    [
      #text(weight: "bold", size: 7.5pt, fill: rgb("#64748B"))[GATEWAY AVAILABILITY SLA]\
      #text(size: 8pt, fill: rgb("#0F172A"))[99.99% Availability Guarantee (Contractual Credits)]
    ],
    [
      #text(weight: "bold", size: 7.5pt, fill: rgb("#64748B"))[MAINTAINER CORE TEAM]\
      #text(size: 8pt, fill: rgb("#0F172A"))[DriftGuard Systems Infrastructure Group]
    ],
    [
      #text(weight: "bold", size: 7.5pt, fill: rgb("#64748B"))[KEY CUSTODY POLICY]\
      #text(size: 8pt, fill: rgb("#0F172A"))[Zero Custody (No Private Keys or Signers Handled)]
    ],
    [
      #text(weight: "bold", size: 7.5pt, fill: rgb("#64748B"))[SECURITY CLASSIFICATION]\
      #text(weight: "bold", size: 8pt, fill: rgb("#DC2626"))[INTERNAL MAINTAINER & CLIENT OPERATIONS]
    ]
  )
]

#v(0.35cm)

#rect(
  fill: rgb("#ECFDF5"),
  stroke: 1pt + rgb("#A7F3D0"),
  radius: 6pt,
  inset: 8pt,
  width: 100%
)[
  #text(size: 7.5pt, fill: rgb("#065F46"))[
    *Commercial Framework Intent:* This Standard Operating Procedure governs the commercial retainer operations of DriftGuard Systems. It establishes the client onboarding protocol, sidecar injection patterns, drift calibration tables, 24/7 severity response SLAs, and monthly upstream vendor reporting delivered under paid B2B enterprise service agreements.
  ]
]

#pagebreak()

// ==========================================
// PAGE 2: SERVICE CATALOG & VALUE PROPOSITION
// ==========================================

= 1. Executive Overview & Service Catalog

The *DriftGuard Enterprise Resilience Retainer* is a managed B2B infrastructure service providing turnkey L7 ingress management, out-of-band consensus verification, 24/7 incident response, and upstream provider resilience guarantees.

While the core DriftGuard software daemon remains 100% open-source and MIT-licensed, enterprise Web3 organizations require guaranteed uptime SLAs, dedicated on-call engineers, custom upstream pool calibration, and continuous chaos resilience auditing without hiring in-house distributed systems specialists.

== Target Client Profiles & Acute Pain Points

#table(
  columns: (1fr, 1.2fr, 1.2fr, 1fr),
  fill: (col, row) => if row == 0 { rgb("#0F172A") } else if calc.even(row) { rgb("#F8FAFC") } else { white },
  stroke: 0.5pt + rgb("#CBD5E1"),
  inset: 5pt,
  align: (col, row) => if row == 0 { center + horizon } else { left + horizon },
  table.header(
    [*Client Segment*],
    [*Critical Pain Point*],
    [*DriftGuard Retainer Solution*],
    [*Value Delivered*]
  ),
  [
    *Arbitrum Orbit L3 Appchains*\
    (Gaming, Social, DeFi)
  ],
  [Sequencer feed disconnects or AnyTrust DAC storage desyncs stall the entire chain.],
  [Custom raw WebSocket sequencer listener + dedicated multi-node gateway cluster.],
  [Guarantees continuous sequencer availability and sub-50ms disconnect mitigation.],
  [
    *ERC-4337 Paymaster Bundlers*\
    (Biconomy, ZeroDev, Pimlico)
  ],
  [Lagging RPC nodes return stale nonces, causing paymaster transactions to revert with `nonce too low`.],
  [Monotonically guaranteed nonce routing and sub-130ms socket drain away from lagging nodes.],
  [Eliminates failed user onboarding and relayer queue locks.],
  [
    *DeFi Liquidators & Relayers*\
    (GMX, Camelot, Pendle Keepers)
  ],
  [A 3-second RPC delay (12 missed Nitro blocks) results in missed liquidations and arbitrage losses.],
  [Real-time consensus drift sentinel auditing blocks every 200ms out-of-band.],
  [Protects MEV opportunities and prevents stale oracle contract queries.],
  [
    *Dedicated Web3 Game Studios*\
    (Real-Time Action Games)
  ],
  [Stale RPC reads cause "ghost items", inventory desync, and player session disconnects.],
  [Sub-130ms transparent cutover without player TCP disconnection or game client code changes.],
  [Preserves player experience and continuous server-authoritative synchronization.]
)

#v(8pt)

= 2. Retainer Tiers & Pricing Schedule

#table(
  columns: (1fr, 0.9fr, 1.1fr, 1.8fr),
  fill: (col, row) => if row == 0 { rgb("#0F172A") } else if calc.even(row) { rgb("#F8FAFC") } else { white },
  stroke: 0.5pt + rgb("#CBD5E1"),
  inset: 5pt,
  align: (col, row) => if row == 0 { center + horizon } else { left + horizon },
  table.header(
    [*Retainer Tier*],
    [*Monthly Price*],
    [*Target Organization*],
    [*Service Level Agreement & Deliverables*]
  ),
  [Tier 1: Sentinel Standard],
  [\$2,500 / month],
  [dApps, Indexers & Relayers],
  [Up to 3 chain backends; 24/7 automated Discord/Telegram webhook alerts; monthly upstream provider health audit; 2-hour business-hours incident triage response.],
  [Tier 2: Orbit Rollup Mission-Critical],
  [\$5,000 / month],
  [Orbit L3 Chains & Game Studios],
  [Dedicated multi-node HA cluster sidecar architecture; custom consensus anchors (client validator + 2 private tier-1 RPCs); *\< 15 min Sev-1 incident SLA* with 24/7 on-call paging; bi-weekly synthetic chaos injection drills; post-mortems within 24 hours.],
  [Tier 3: Institutional Sovereign / Paymaster],
  [\$8,500 / month],
  [High-Volume Paymasters & Sovereign Chains],
  [Active-active multi-region gateway orchestration; custom WebSocket raw sequencer feed listener; AnyTrust Data Availability Committee (DAC) custom sentry; dedicated senior systems engineer on-call; custom Grafana enterprise dashboard; *99.99% availability guarantee*.]
)

#pagebreak()

// ==========================================
// PAGE 3: ONBOARDING & SIDECAR INJECTION SOP
// ==========================================

= 3. SOP-01: Client Onboarding & Pre-Flight Audit

*Objective:* Audit the client's current RPC architecture, quantify peak throughput, identify single-points-of-failure (SPOFs), and establish baseline latency metrics within 5 business days.

== 5-Day Pre-Flight Audit Workflow
1. *Day 1 (Discovery & Inventory Intake):*
   - Document Chain ID(s), upstream RPC providers (Alchemy, Infura, QuickNode, local validator), and peak queries-per-second (QPS).
   - Classify client consumer types: ERC-4337 paymaster bundler, Go/Rust relayer daemon, game server backend, or public dApp frontend.
2. *Day 2 (Upstream Provider Resilience Profiling):*
   - Benchmark client's current upstream providers over 48 hours for p50/p90/p99 response latency, block propagation lag against the canonical sequencer, and HTTP 429 rate-limiting frequency.
3. *Day 3 (Consensus Anchor Selection):*
   - Select 2 independent, non-correlated reference nodes (e.g., direct sequencer endpoint + private tier-1 fallback like dRPC/Tenderly) to ensure out-of-band monitoring integrity.
4. *Day 4--5 (Pre-Flight Audit Report Delivery):*
   - Deliver an executive report detailing identified vulnerability vectors, recommended drift thresholds (typically 4 Nitro blocks ~ 1s), and recommended HAProxy stick-table rate limits.

#v(8pt)

= 4. SOP-02: Sidecar Deployment & HA Gateway Injection

*Objective:* Deploy DriftGuard sidecar instances in front of client workloads with zero client code changes.

```
  Client Environment:
  [ Client Relayer / App ] ===== HTTP POST (localhost:8545) =====> [ DriftGuard Sidecar Container ]
                                                                      • HAProxy L7 Gateway
                                                                      • Python 3.12 Sentinel Daemon
                                                                      • Dynamic UNIX Socket Drain
                                                                             |                 |
                                                            (Primary Healthy)|                 |(Primary Drained)
                                                                             v                 v
                                                            [ Client Validator Node ]   [ Private Fallback RPC ]
```

== Deployment Procedures:
- *Option A (Kubernetes Sidecar Pattern):* Inject DriftGuard sidecar container into client's relayer or indexer pod spec using the official Helm chart. Set `RPC_URL=http://localhost:8545`.
- *Option B (Docker Compose / Systemd on Validator VPS):* Deploy DriftGuard directly on client's validator node VPS listening on `127.0.0.1:8545`.
- *UNIX Socket Verification Runbook:*
  ```bash
  # Verify local HAProxy administration socket connectivity
  echo "show stat" | socat stdio unix-connect:/run/haproxy/admin.sock | grep -E 'be_arb|be_nova'
  
  # Verify local consensus sentinel healthz
  curl -s http://localhost:8545/healthz | jq .
  ```
- *Zero-Downtime Traffic Canary Cutover:* Direct 10% traffic canary $\to$ verify zero errors over 1 hour $\to$ execute 100% cutover.

#pagebreak()

// ==========================================
// PAGE 4: CONSENSUS TUNING & INCIDENT RESPONSE SOP
// ==========================================

= 5. SOP-03: Consensus Anchor Calibration & Drift Tuning

*Objective:* Calibrate drift thresholds to prevent false positives during transient public internet jitter while ensuring sub-second cutover during real stalls.

#table(
  columns: (1fr, 0.9fr, 1.1fr, 1.1fr, 1.4fr),
  fill: (col, row) => if row == 0 { rgb("#0F172A") } else if calc.even(row) { rgb("#F8FAFC") } else { white },
  stroke: 0.5pt + rgb("#CBD5E1"),
  inset: 5pt,
  align: (col, row) => if row == 0 { center + horizon } else { left + horizon },
  table.header(
    [*Parameter*],
    [*Default (Standard)*],
    [*High-Velocity Orbit L3*],
    [*High-Volume Relayer*],
    [*Operational Purpose*]
  ),
  [`poll_interval`],
  [`0.2s` (200ms)],
  [`0.1s` (100ms)],
  [`0.15s` (150ms)],
  [Out-of-band polling loop frequency.],
  [`drift_threshold`],
  [`4 blocks` (~1.0s)],
  [`3 blocks` (~750ms)],
  [`2 blocks` (~500ms)],
  [Maximum allowed block divergence.],
  [`failure_threshold`],
  [`1 poll`],
  [`1 poll`],
  [`1 poll`],
  [Consecutive failures before server drain.],
  [`recovery_threshold`],
  [`2 polls`],
  [`3 polls`],
  [`3 polls`],
  [Consecutive healthy polls before un-draining.],
  [`syncing_check`],
  [`true`],
  [`true`],
  [`true`],
  [Failover immediately if `eth_syncing = true`.]
)

*Flap Prevention Runbook:* If public network jitter causes rapid flapping between primary and fallback, increase `recovery_threshold` to `3` or `4`. Never decrease `recovery_threshold` below `2` to maintain hysteresis stability.

#v(8pt)

= 6. SOP-04: 24/7 Incident Escalation & Response Runbook

*Objective:* Handle upstream provider desyncs, sequencer stalls, and network partitions within strict contractual SLAs.

#table(
  columns: (0.9fr, 1.3fr, 0.9fr, 0.9fr, 1.5fr),
  fill: (col, row) => if row == 0 { rgb("#0F172A") } else if calc.even(row) { rgb("#F8FAFC") } else { white },
  stroke: 0.5pt + rgb("#CBD5E1"),
  inset: 5pt,
  align: (col, row) => if row == 0 { center + horizon } else { left + horizon },
  table.header(
    [*Severity Level*],
    [*Definition*],
    [*Response SLA*],
    [*Target Resolution*],
    [*Primary Actions*]
  ),
  [SEV-1 (Critical)],
  [Primary & fallback both desynced; client experiencing \>0.1% transaction reverts; sequencer frozen.],
  [*\< 15 minutes*\ (Tier 2/3 on-call)],
  [\< 30 minutes],
  [Automated failover verification; manual tertiary upstream injection via admin socket; client executive bridge opened.],
  [SEV-2 (Major)],
  [Primary upstream stalled; DriftGuard executed autonomous sub-130ms failover to fallback; client unaffected.],
  [\< 1 hour],
  [\< 2 hours],
  [Verify fallback capacity; triage delinquent primary; notify upstream provider NOC; monitor for canonical recovery.],
  [SEV-3 (Minor)],
  [Transient consensus jitter (\<2 blocks); single poll timeout; telemetry warning.],
  [\< 8 hours],
  [Next business day],
  [Review Redis telemetry logs; calibrate timeout thresholds if jitter persists.]
)

== SEV-1 Incident Escalation Workflow
1. *Trigger:* Sentinel trips critical alert $\to$ PagerDuty on-call paged (\<60s) $\to$ Automated Discord/Telegram alert dispatched (\<200ms).
2. *Diagnostics (\<15 min):* Systems engineer inspects `curl -s http://localhost:8545/healthz` and verifies HAProxy state via admin socket.
3. *Fallback Verification:* Confirm autonomous socket drain successful and client HTTP 200 responses preserved.
4. *Emergency Tertiary Injection:* If all upstreams desync, inject emergency tertiary RPC into HAProxy pool at runtime via UNIX socket:
   ```bash
   echo "set server be_arb/srv_fallback addr <new_ip> port 8545" | socat stdio unix-connect:/run/haproxy/admin.sock
   ```
5. *Post-Mortem:* Deliver formal post-mortem report to client within 24 hours.

#pagebreak()

// ==========================================
// PAGE 5: CHAOS DRILLS, REPORTING & SLA TERMS
// ==========================================

= 7. SOP-05: Chaos Drills, Upstream Benchmarking & Monthly Reporting

*Objective:* Proactively stress-test the client's architecture and provide empirical scorecards on their upstream RPC vendors.

== Bi-Weekly Chaos Drills (Tier 2 & 3)
- Conduct synthetic fault injections during scheduled maintenance windows:
  - Inject 20-block head freeze into primary RPC via `driftguard-chaos`.
  - Verify HAProxy drains primary within *\< 130ms*.
  - Measure packet drop rate (must remain *0.00%*).
  - Inject latency spike (\>1000ms) to test hysteresis stability.

== Monthly Upstream Vendor Scorecard
Every 30 days, DriftGuard delivers an executive resilience audit covering:
- *Uptime & Staleness Hours:* Total minutes each upstream provider lagged behind canonical head.
- *Average Drift-to-Drain Latency:* Measured failover speed across all recorded events.
- *Provider Reliability Rating:* Empirical ranking of client's vendors (Alchemy vs QuickNode vs Private Node).
- *Cost Optimization Advice:* Recommendations on reducing paid RPC tiers based on actual failover utilization.

#v(8pt)

= 8. SOP-06: Client Service Level Agreement (SLA) & Contractual Terms

== 1. Gateway Availability Guarantee (99.99%)
- DriftGuard guarantees *99.99% ingress gateway availability* for client workloads on Tier 2 and Tier 3 retainers.
- If availability falls below 99.99% in a monthly billing cycle, the client receives contractual service credits:
  - *99.90% -- 99.98%:* 15% monthly retainer credit.
  - *99.00% -- 99.89%:* 30% monthly retainer credit.
  - *\< 99.00%:* 50% monthly retainer credit.

== 2. Data Privacy & Zero Key Custody
- DriftGuard engineers *never* take custody of private keys, mnemonic phrases, or transaction signing credentials.
- All RPC endpoints and consensus anchor credentials are encrypted via client-managed secret vaults or environment files.

== 3. Contractual Termination & Knowledge Transfer
- Retainer contracts operate on flexible month-to-month or quarterly commitments.
- Upon termination, DriftGuard delivers a complete infrastructure handoff pack, ensuring the client can continue running the open-source sidecar independently without vendor lock-in.

#v(16pt)
#align(center)[
  #text(size: 8pt, fill: rgb("#94A3B8"))[
    *DRIFTGUARD SYSTEMS* • ENTERPRISE OPERATIONS & B2B CLIENT RETAINER SOP • VERSION 2.0\
    Operations Desk: `operations@driftguard.live` • Emergency On-Call: PagerDuty / Telegram Priority Desk\
    Repository: #link("https://github.com/maskalfreeup-glitch/driftguard")[github.com/maskalfreeup-glitch/driftguard] • Portal: #link("https://driftguard.live")[driftguard.live]
  ]
]
