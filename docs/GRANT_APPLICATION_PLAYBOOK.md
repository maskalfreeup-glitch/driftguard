# DriftGuard: Grant Application Action Playbook & Submission Guide

This playbook provides step-by-step submission instructions, form-ready copy/paste snippets, and a scheduled execution timeline for applying to ecosystem grants.

---

> ### ⚠️ Critical Framing Rule: Developer Tooling Grant (Not Hosting)
> Most Web3 grant committees (Arbitrum Questbook, Base, Optimism) **explicitly reject** applications seeking cloud hosting subsidies. 
> - **We request $0 for server hosting.**
> - The live cluster at `rpc.driftguard.live` is operated independently by the maintainers at zero grant cost as an empirical reference testbed and proof harness.
> - The grant funds **100% open-source software primitives, client SDKs, Docker/K8s sidecar controllers, and automated chaos testing CLI tools**.
> - Financial sustainability after the grant is driven by the **Commercial B2B Retainer Service** ([`docs/B2B_RETAINER_SERVICE_SOP.md`](B2B_RETAINER_SERVICE_SOP.md)).

---

## 1. Target Ecosystems & Portals Overview

| Ecosystem / Grant Program | Portal / Submission URL | Domain / Track | Funding Range | Status |
| :--- | :--- | :--- | :--- | :--- |
| **1. Arbitrum Questbook (CGP)** | [arbitrum.questbook.app](https://arbitrum.questbook.app/) | Developer Tooling & Node Infra | $15,000 – $25,000 in $ARB | Ready to Submit |
| **2. Arbitrum Foundation Grants** | [arbitrum.foundation/grants](https://arbitrum.foundation/grants) | Infrastructure & Tooling | $25,000 – $50,000 in $ARB | Ready to Submit |
| **3. Base Builder Grants / Ecosystem Fund** | [base.org/grants](https://base.org/grants) or [paragraph.xyz/@grants.base.eth](https://paragraph.xyz/@grants.base.eth) | Developer Tooling & Smart Accounts | $10,000 – $25,000 in ETH/USDC | Ready to Submit |
| **4. Optimism Retro Funding / Superchain** | [optimism.io/retropgf](https://app.optimism.io/retropgf) | Developer Tooling | Retroactive / Matching Pool | Open Rounds |
| **5. Gitcoin Grants (GG Round)** | [grants.gitcoin.co](https://grants.gitcoin.co/) | Open Source Software (OSS) | Community Quadratic Pool | Round Schedule |

---

## 2. Standard Application Form Fields (Copy & Paste Ready)

### Project Title
`DriftGuard: Deterministic L7 Ingress Gateway & Out-of-Band Consensus Sentinel for Rollups & Session Relayers`

### One-Line Tagline (Elevator Pitch)
`DriftGuard is an open-source, ultra-low-footprint (<45 MB RAM) systems daemon and sidecar controller providing sub-130ms deterministic failover for Arbitrum Orbit L3s, Base, and session relayers.`

### Track / Category
`Developer Tooling & Node Infrastructure`

### Project Description
```markdown
DriftGuard is an open-source systems daemon and sidecar controller engineered for EVM rollups (Arbitrum One, Arbitrum Nova, Arbitrum Orbit L3s, Base) and session relayers requiring sub-130ms deterministic failover with zero client code modifications.

High-velocity rollups produce blocks at rapid cadence (~250ms on Arbitrum Nitro; sub-second flashblocks on Base). Standard cloud load balancers (AWS ALB, Cloudflare, standard NGINX) rely strictly on transport-layer health checks (TCP connect, HTTP 200). When an RPC node encounters an upstream ingestion freeze or background resynchronization (eth_syncing = true), it continues returning HTTP 200 OK while serving obsolete nonces and stale block heights.

This causes immediate ERC-4337 Account Abstraction paymaster failures ("nonce too low"), DeFi liquidation front-running losses, and game server state desynchronization.

DriftGuard implements a decoupled dual-plane architecture:
1. Data Plane: High-throughput C-native HAProxy 2.8+ L7 reverse proxy.
2. Control Plane: Asynchronous Python 3.12 consensus sentinel sampling canonical block heights every 200ms out-of-band.
3. Failover Engine: Atomic UNIX domain socket drain in < 1ms, terminating zero in-flight client TCP sessions.

DriftGuard is an open-source software primitive. The maintainers independently operate a zero-cost reference testbed at https://rpc.driftguard.live demonstrating empirical resilience with 122.8ms cutover in live SEV-2 triage.
```

### Problem Statement
```markdown
On Arbitrum Nitro (~250ms blocks) and Base, a 3-second RPC desync represents 12 missed blocks. Standard load balancers and client-side fallbacks (Viem fallback) fail because:
1. Transport Layer Blindness: Standard proxies only evaluate HTTP status (200 OK). They cannot detect consensus divergence or eth_syncing = true.
2. Latency Penalty & Nonce Flapping: Client-side fallbacks incur full round-trip timeouts (5s+) on every failover, breaking session key relayers and causing nonce collisions across distributed workers.
3. High Resource Footprint: Existing blockchain load balancers consume hundreds of megabytes of RAM, pricing out solo validators and independent node operators.
```

### Proposed Milestones & Funding Request ($25,000 – $35,000 USD)

#### Milestone 1: Multi-Chain Core Engine & Consensus Sentinel (Weeks 1–4) — $10,000 USD
- **Status:** 100% Completed, Deployed in Live Production.
- **Deliverables:** Merged open-source repository; standalone Docker sidecar controller (<45 MB RAM RSS); multi-chain routing for Arbitrum One (/arb), Arbitrum Nova (/nova), Arbitrum Sepolia (/arb-sepolia), and Base (/base); automated chaos test suite; live telemetry at `rpc.driftguard.live/healthz`.
- **KPIs:** Measured failover cutover < 130ms (achieved 122.8ms in SEV-2 triage); 0 dropped requests under sustained load; < 45 MB RAM aggregate container footprint.

#### Milestone 2: WebSocket Feed Sentinel, Orbit Presets & Viem SDK (Weeks 5–8) — $10,000 USD
- **Deliverables:** Native WebSocket client subscribing directly to raw Nitro sequencer feeds (`wss://arb1.arbitrum.io/feed`) to catch stalls in < 50ms; Arbitrum Nova AnyTrust Data Availability Committee (DAC) certificate monitor; 1-click Docker sidecar presets for custom Orbit L3s and Base/OP Stack appchains; TypeScript `@driftguard/sdk` npm package with custom Viem transport.
- **KPIs:** Sequencer feed disconnection cutover < 50ms; 3 validated rollup blueprints; npm package published with >85% test coverage.

#### Milestone 3: Cloud-Native Operator Tooling, Prometheus/Grafana & Multi-Channel Alerting (Weeks 9–12) — $8,000 USD
- **Deliverables:** Official Prometheus metrics exporter (`driftguard_block_lag`, `driftguard_failover_latency_ms`); pre-configured Grafana dashboard JSON pack; production Kubernetes Helm chart sidecar operator; automated incident webhooks for Discord, Telegram, and PagerDuty.
- **KPIs:** Helm chart passing lint/test in standard k8s cluster; Grafana dashboard single-click import; alert delivery latency < 200ms.

#### Milestone 4: Developer Chaos Testing CLI & Rollup Adoption Tooling (Weeks 13–16) — $7,000 USD
- **Deliverables:** `driftguard-chaos` CLI allowing node teams to inject synthetic block stalling, network partitions, and latency; 10,000 req/s load-testing benchmark harness; step-by-step developer tutorials and onboarding for 3+ ecosystem pilot teams.
- **KPIs:** Chaos CLI published on npm/pip; 10,000 req/s benchmark report published; 3+ pilot partner teams onboarded with documented feedback.

---

### Financial Sustainability & Business Model (Post-Grant Plan)
```markdown
DriftGuard operates a Dual-Track Sustainability Model:
1. Open-Source Public Good (100% Free): The core Docker sidecar, Kubernetes Helm chart, @driftguard/sdk, and Prometheus exporter are MIT-licensed and perpetually free.
2. Commercial B2B Retainer Service: Enterprise Orbit L3 chains, Web3 gaming studios, and ERC-4337 paymaster bundlers purchase managed ingress orchestration, custom consensus anchor calibration, and 24/7 incident response SLAs ($2,500 - $8,500/month).

This commercial retainer funds ongoing engineering and on-call maintenance without requiring perpetual DAO grant subsidies. Full SOP documented at docs/B2B_RETAINER_SERVICE_SOP.md.
```

---

## 3. Reviewer Verification Links & Quick Proofs

Reviewers can verify the project in under 60 seconds:
- **Live Endpoint Test:** `curl -s -X POST https://rpc.driftguard.live/arb -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'`
- **Consensus Sentinel State:** `curl -s https://rpc.driftguard.live/healthz | jq .`
- **Failover Visual Demo:** [evidence/failover-demo.gif](https://github.com/maskalfreeup-glitch/driftguard/blob/main/evidence/failover-demo.gif)
- **Live Explainer & Architecture:** [driftguard.live](https://driftguard.live)
- **Real-World SEV-2 Incident Post-Mortem:** [INCIDENT_2026-10-04_ARBITRUM_DESYNC.md](https://github.com/maskalfreeup-glitch/driftguard/blob/main/docs/reports/INCIDENT_2026-10-04_ARBITRUM_DESYNC.md)

---

## 4. Week-by-Week Action Plan

```
[Week 1: Polish & Sandbox]
  ├── Verify live healthz on Node 1 & Node 2
  ├── Confirm Git repository is clean (MIT License, README, docs)
  └── Test public gateway responses (/arb, /nova, /base)

[Week 2: Application Submissions]
  ├── Submit to Arbitrum Questbook (Developer Tooling Domain)
  ├── Submit to Arbitrum Foundation Direct Grant Form
  ├── Submit to Base Builder Grants
  └── Create Gitcoin Grants OSS profile

[Week 3: Governance & Community Awareness]
  ├── Publish discussion post on Arbitrum Governance Forum (forum.arbitrum.foundation)
  ├── Share live testbed & benchmarks on Farcaster (/base, /base-devs)
  └── Share incident post-mortem in Arbitrum Discord (#dev-chat)

[Week 4: Reviewer Calls & Milestone 1 Verification]
  ├── Conduct 15-min live demo with Questbook / Foundation reviewers
  ├── Execute grant agreement / escrow setup
  └── Reviewers verify Milestone 1 (already live!) -> Tranche 1 release ($10,000)

[Weeks 5–16: Milestone Execution & Updates]
  ├── Bi-weekly progress updates posted to governance forums
  ├── Milestone 2 completion & review -> Tranche 2 release ($10,000)
  ├── Milestone 3 completion & review -> Tranche 3 release ($8,000)
  └── Milestone 4 completion & review -> Tranche 4 release ($7,000)
```
