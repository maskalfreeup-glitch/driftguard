# Multi-Ecosystem Milestone-Based Grant Proposal: DriftGuard

**Project Name:** DriftGuard &mdash; Deterministic L7 Ingress Gateway & Out-of-Band Consensus Sentinel for EVM Rollups, Orbit L3 Chains, and Session Relayers  
**Primary Track:** Developer Tooling & Node Infrastructure (100% Open-Source Tooling Grant)  
**Target Ecosystems:**  
- **Arbitrum One, Arbitrum Nova, Arbitrum Sepolia & Arbitrum Orbit L3s** (Nitro / Stylus)
- **Base & Optimism Superchain** (OP Stack Rollups, Chain ID `8453`)
- **Web3 Public Goods** (Gitcoin Grants OSS & Octant)  
**Project Repository:** [github.com/maskalfreeup-glitch/driftguard](https://github.com/maskalfreeup-glitch/driftguard)  
**Zero-Cost Empirical Reference Testbed:** [rpc.driftguard.live](https://rpc.driftguard.live)  
**Interactive Dashboard & Documentation:** [driftguard.live](https://driftguard.live)  
**License:** [MIT Open Source License](https://opensource.org/licenses/MIT)  
**Total Funding Request:** $35,000 USD (in $ARB, $OP, or USDC equivalent, distributed across 4 verifiable engineering milestones)  
**Contact:** Maskal (`hello@maskal.space` | GitHub: [@maskalfreeup-glitch](https://github.com/maskalfreeup-glitch) | Community Discord: [discord.gg/DZBDJSsSzN](https://discord.gg/DZBDJSsSzN))  

---

> ### ⚠️ Critical Scope & Deliverable Clarification: Tooling vs. Hosting
> **This application is strictly for Developer Tooling & Software Engineering, NOT hosting subsidies.**  
> Grant programs rightly reject proposals seeking cloud hosting subsidies. DriftGuard does **not** request funds for public server bills or cloud infrastructure operations.  
> 
> The publicly accessible endpoint at `rpc.driftguard.live` is operated independently by the maintainers at **zero cost to the grant program** strictly as an empirical reference testbed and reproducible proof harness.  
> 
> **What this grant funds:** 100% reusable, open-source software primitives:
> 1. The standalone, ultra-low-footprint (<45 MB RAM) Docker & Kubernetes sidecar controller that rollup operators and relayers run on their own infrastructure.
> 2. The client-side TypeScript/Viem transport SDK (`@driftguard/sdk`).
> 3. Orbit L3 / OP Stack 1-click blueprints, WebSocket sequencer feed listeners, and Prometheus/Grafana observability packs.
> 4. Automated CLI chaos testing and fuzzing harnesses for node teams.

---

## 1. Executive Summary

EVM Layer 2 and Layer 3 rollups operate at unprecedented block velocities: **Arbitrum Nitro processes micro-blocks at ~250ms cadence**, while **Base and the OP Superchain generate blocks every 2 seconds with sub-second flashblocks**. This throughput enables real-time DeFi execution, consumer smart-wallet experiences, and on-chain gaming.

However, high block velocity exposes a critical, widespread vulnerability in decentralized infrastructure: **"The Silent 200 OK" Consensus Drift Problem**.

Standard cloud load balancers (AWS ALB, Cloudflare, vanilla NGINX) and client-side RPC fallbacks (Viem `fallback`, Ethers `FallbackProvider`) evaluate node health exclusively at the **transport layer (TCP connect, HTTP 200)**. When an RPC node encounters an upstream sequencer ingestion stall, thread starvation, or background resynchronization (`eth_syncing = true`), it continues returning `HTTP 200 OK` while serving stale block states.

In high-velocity rollups, a 3-second RPC desync represents **12 missed blocks on Arbitrum** or **several state transitions on Base**:
1. **ERC-4337 Account Abstraction & Session Relayers:** Querying `eth_getTransactionCount` against a lagging node returns obsolete nonces. Signed user transactions immediately revert with `nonce too low`, stalling user onboarding and relayer queues.
2. **DeFi Liquidators & Oracle Aggregators:** Automated arbitrage and liquidation bots make decisions on stale orderbook states, suffering slippage or front-running failures.
3. **Orbit L3 Rollups & Dedicated Game Servers:** Real-time state queries read pre-transaction states, causing "ghost items", inventory desyncs, and dropped user sessions.

**DriftGuard** is an open-source, ultra-low-footprint (<45 MB RAM) systems daemon and sidecar controller engineered to deliver **sub-130ms deterministic failover with zero client code modifications**. 

By decoupling the high-throughput JSON-RPC data plane (C-native HAProxy 2.8+ runtime) from an asynchronous out-of-band consensus sentinel (Python 3.12 + FastAPI + asyncio), DriftGuard audits canonical block heights every 200ms. If primary upstream drift exceeds threshold, it executes an atomic UNIX domain socket drain in **< 1ms**, terminating zero in-flight client TCP sessions.

---

## 2. Ecosystem Alignment & Grant Program Mapping

DriftGuard directly solves the consensus staleness and relayer fragility problems across four premier ecosystems:

| Ecosystem | Grant Program / Track | Strategic Alignment & Value Proposition | Target Grant Size |
| :--- | :--- | :--- | :--- |
| **Arbitrum Foundation & Arbitrum DAO** | **Developer Tooling & Node Infrastructure** (Questbook CGP / Direct Foundation Grants) | Arbitrum Nitro (~250ms blocks) and Arbitrum Nova AnyTrust (Data Availability Committee certificates) suffer acute desyncs. DriftGuard provides Orbit L3 chains and Stylus dApps with turnkey sub-130ms failover without enterprise cloud costs. | **$25,000 – $35,000 USD** (in $ARB) |
| **Base / Coinbase Ventures** | **Base Builder Grants / Ecosystem Fund** (Dev Tooling & Account Abstraction) | High density of Coinbase Smart Wallets and ERC-4337 paymasters. DriftGuard eliminates `nonce too low` transaction failures for Biconomy, ZeroDev, and Pimlico bundlers on Base Mainnet (`/base`). | **$15,000 – $25,000 USD** (in USDC/ETH) |
| **Optimism / Superchain** | **Retro Funding / Superchain Dev Tooling** | Out-of-band consensus verification across the OP Stack rollup cluster (OP Mainnet, Base, Zora, Mode). Prevents Superchain indexer stalling and protects cross-chain bridge relayers. | **$15,000 – $20,000 USD** (in $OP) |
| **Public Goods (Gitcoin / Octant)** | **Gitcoin Grants OSS / Octant Community Epochs** | 100% open-source MIT software; zero proprietary cloud vendor lock-in; empowers solo validators to run enterprise-grade HA RPC nodes on free-tier VPS hardware (<$5/mo). | Matching Pools / Retroactive |

---

## 3. The Core Problem: "The Silent 200 OK" Trap

```
  Traditional Balancers (Cloudflare / AWS ALB / Vanilla Nginx):
  +----------------------+      HTTP POST /eth_blockNumber
  | Client / Relayer     | --------------------------------------> [ Upstream RPC Node ]
  +----------------------+                                         • Frozen 14 blocks behind head
                                <---------------------------------- • eth_syncing = true
                                     HTTP 200 OK (STALE DATA!)     • Serves outdated nonces
  Result: Transaction reverts on-chain ("nonce too low"), relayer stalls, DeFi bot loses MEV opportunity.

  DriftGuard Decoupled Dual-Plane Architecture:
  +----------------------+      HTTP POST (Standard EVM JSON-RPC)
  | Client / Relayer     | --------------------------------------> [ HAProxy L7 Data Plane ]
  +----------------------+                                                |
                                                                          | Dynamic UNIX Socket Drain
                                                                          | (< 1ms socket execution)
  +----------------------+      Async Out-of-Band Probes (200ms)          v
  | Consensus Sentinel   | --------------------------------------> [ Primary Node Drained -> `maint` ]
  | (Control Plane)      |                                         [ Fallback Node Promoted -> `up`  ]
  +----------------------+
  Result: Zero dropped packets, sub-130ms deterministic failover, guaranteed canonical head reads.
```

### Why Existing Solutions Fail on Fast L2s

| Metric / Feature | Cloud Load Balancers (AWS ALB, Cloudflare) | Client-Side Fallback (Viem / Ethers) | Vanilla Active-Passive HAProxy | **DriftGuard Tooling Sidecar** |
| :--- | :--- | :--- | :--- | :--- |
| **Consensus Awareness** | None (Transport Layer HTTP 200 only) | None (Tries next RPC after error) | None (Periodic TCP/HTTP check) | **Full (Evaluates block drift, syncing state, chain ID)** |
| **Failover Trigger Cadence** | 10s – 30s timeout interval | Round-trip request timeout (5s+) | 2s – 5s health intervals | **200ms out-of-band poll loop** |
| **Failover Latency** | 10,000ms+ (10+ seconds) | 2,000ms – 5,000ms per client | 2,000ms – 5,000ms | **< 130ms (Empirically 122.8ms)** |
| **Client Code Changes** | None | Requires rewriting SDK in all apps | None | **Zero (`http://localhost:8545`)** |
| **Multi-Language Support**| All | TypeScript / JS only | All | **Universal (Go, Rust, Python, C#, JS)** |
| **Memory Footprint** | N/A (Cloud Managed) | In-process client overhead | ~20 MB | **< 45 MB aggregate RSS** |

---

## 4. Empirical Field Proof: Live Active-Active Reference Cluster

DriftGuard is not an unverified concept. It is fully engineered and running live in a **geo-redundant active-active reference cluster** operated at zero cost to the grant program:

### A. Reference Cluster Topology
- **Node 1 (`129.80.34.125`):** Oracle Cloud Infrastructure (Oracle Linux 9), Docker CE 29.8.2, full DriftGuard stack (`driftguard-proxy`, `driftguard-sentinel`, `driftguard-redis`), multi-connector Cloudflare tunnel.
- **Node 2 (`193.122.236.215`):** Oracle Cloud Infrastructure (Oracle Linux 9), Docker CE 29.8.2, full DriftGuard stack, multi-connector Cloudflare tunnel.
- **Anycast Ingress:** Both nodes concurrently serve live test queries under `https://rpc.driftguard.live` with instant edge failover if either node halts.

### B. SEV-2 Incident Validation (October 4, 2026)
During an Arbitrum One upstream sequencer ingestion stall ([INC-20261004-ARB1](docs/reports/INCIDENT_2026-10-04_ARBITRUM_DESYNC.md)), the primary provider froze at block `#511619835` while continuing to return `HTTP 200 OK`. 
- **Time to Detection:** 180ms
- **Failover Transition:** 122.8ms
- **Packet Drop Rate:** **0.00% across 800+ concurrent JSON-RPC queries**
- **Incident Ledger:** 18 consecutive real-world divergence events handled with average cutover latency of **121.1ms** ([docs/reports/INCIDENT_LEDGER.md](docs/reports/INCIDENT_LEDGER.md)).

---

## 5. Milestone-Based Work Plan (100% Software Engineering)

We propose a **4-stage milestone schedule** spanning 16 weeks, focused strictly on **open-source tooling, libraries, blueprints, and testing harnesses**:

```
  +----------------------------------------------------------------------------------------------------+
  |                                   MILESTONE EXECUTION ROADMAP                                      |
  +----------------------------------------------------------------------------------------------------+
  |                                                                                                    |
  |  [Milestone 1: Weeks 1–4]  =====>  [Milestone 2: Weeks 5–8]  =====>  [Milestone 3: Weeks 9–12]   |
  |  • Multi-Chain Core Engine         • WebSocket Feed Sentinel          • Prometheus Exporter Pack   |
  |  • Dynamic Socket Controller       • Orbit L3 & Base Presets          • K8s Helm Sidecar Chart     |
  |  • Local Sidecar Architecture      • TypeScript / Viem SDK            • Multi-Channel Alerting     |
  |  ($10,000 USD / ARB)               ($10,000 USD / ARB)                ($8,000 USD / ARB)           |
  |                                                                                                    |
  |                                                ||                                                  |
  |                                                \/                                                  |
  |                                    [Milestone 4: Weeks 13–16]                                      |
  |                                    • Developer Chaos Testing CLI                                   |
  |                                    • 10k req/s Benchmarking Harness                                |
  |                                    • Orbit Appchain Onboarding Tooling                             |
  |                                    ($7,000 USD / ARB)                                              |
  |                                                                                                    |
  +----------------------------------------------------------------------------------------------------+
```

### Milestone 1: Core Systems Engine, Multi-Chain Routing & Consensus Sentinel (Weeks 1–4)
*Status: 100% Completed, Deployed & Verifiable*  
**Funding Allocation:** $10,000 USD (equivalent in $ARB or USDC)

**Tooling Deliverables:**
1. **Decoupled Dual-Plane Ingress Engine:** Production HAProxy 2.8+ L7 configuration integrated with out-of-band asynchronous consensus sentinel daemon (Python 3.12 + FastAPI + asyncio + Redis 7).
2. **Sub-130ms UNIX Socket Controller:** Atomic C-runtime socket controller issuing `set server <backend>/<server> state maint` within HAProxy's event loop in <1ms without dropping TCP connections.
3. **Multi-Chain Route Configurations:** Standardized routing and stick-table anti-abuse configurations for Arbitrum One (`/arb`), Arbitrum Nova (`/nova`), Arbitrum Sepolia (`/arb-sepolia`), and Base (`/base`).
4. **Reproducible Chaos & Failover Test Suite:** Standalone command-line testing scripts ([`scripts/test_failover.sh`](scripts/test_failover.sh) and [`scripts/test_gateway.sh`](scripts/test_gateway.sh)) validating zero dropped packets.
5. **Reference Testbed Deployment:** Live multi-node verification cluster on Oracle Cloud Infrastructure demonstrating production stability.

**Acceptance Criteria & Verifiable KPIs:**
- [x] Failover cutover latency verified **< 130ms** (measured 122.8ms).
- [x] Zero dropped requests (`0.00% error rate`) during active upstream server drain.
- [x] Live public health telemetry returning canonical block heights at `https://rpc.driftguard.live/healthz`.
- [x] Standalone container stack memory consumption verified **< 45 MB RAM RSS** under idle load.

---

### Milestone 2: High-Velocity Sequencer Feeds, Orbit Presets & Viem SDK (Weeks 5–8)
*Status: Ready for Execution upon Grant Approval*  
**Funding Allocation:** $10,000 USD (equivalent in $ARB or USDC)

**Tooling Deliverables:**
1. **Arbitrum Raw WebSocket Sequencer Feed Listener:** Integration of a native WebSocket client subscribing directly to raw Nitro sequencer feeds (`wss://arb1.arbitrum.io/feed`), detecting sequencer stalls and TCP disconnections before block height drift emerges.
2. **Arbitrum Nova AnyTrust Data Availability Committee (DAC) Monitor:** Synthetic probe validating DAC certificate availability and DA storage health to prevent Nova state stalling.
3. **Orbit L3 & OP Stack 1-Click Blueprints:** Turnkey Docker Compose and environment presets tailored for custom Arbitrum Orbit rollup chains (Xai, Sanko, ApeChain) and Base/OP Stack appchains.
4. **Client-Side SDK Package (`@driftguard/sdk`):** Lightweight TypeScript/Viem library providing plug-and-play transport wrappers, health check hooks, and automatic local sidecar discovery.

**Acceptance Criteria & Verifiable KPIs:**
- [ ] Sequencer feed disconnect detected and cutover triggered in **< 50ms**.
- [ ] 3 production-tested blueprints published (Arbitrum Orbit Nitro, Arbitrum Nova AnyTrust, Base OP Stack).
- [ ] `@driftguard/sdk` published to npm with 100% TypeScript type definitions and integration tests.
- [ ] Test suite coverage exceeding **> 85%**.

---

### Milestone 3: Cloud-Native Operator Tooling, Prometheus/Grafana & Alerting (Weeks 9–12)
*Status: Scheduled*  
**Funding Allocation:** $8,000 USD (equivalent in $ARB or USDC)

**Tooling Deliverables:**
1. **Prometheus Metrics Exporter:** Production metric exporter publishing real-time telemetry: `driftguard_block_lag`, `driftguard_failover_events_total`, `driftguard_upstream_latency_ms`, and backend server health states.
2. **Official Grafana Dashboard Pack:** Ready-to-import Grafana dashboard JSON models with visual block drift heatmaps, failover counters, and p99 latency distributions.
3. **Kubernetes Helm Chart & Sidecar Manifests:** Production-grade Helm chart supporting Kubernetes sidecar injection alongside validator nodes, session relayers, and The Graph indexers.
4. **Multi-Channel Automated Incident Alerting:** Webhook notification engine supporting Discord embeds, Telegram alerts, and PagerDuty webhooks for validator DevOps teams.

**Acceptance Criteria & Verifiable KPIs:**
- [ ] Helm chart published to public GitHub Pages Helm repository and successfully passing `helm lint` and `helm test`.
- [ ] Grafana dashboard packaged and importable into standard Grafana 10+ without external plugins.
- [ ] Alert dispatch latency **< 200ms** from incident trip to Discord/Telegram delivery.

---

### Milestone 4: Developer Chaos Testing CLI & Rollup Adoption Tooling (Weeks 13–16)
*Status: Scheduled*  
**Funding Allocation:** $7,000 USD (equivalent in $ARB or USDC)

**Tooling Deliverables:**
1. **DriftGuard Chaos CLI (`driftguard-chaos`):** Open-source developer CLI allowing node teams to inject synthetic block stalling, network partition, and JSON-RPC latency to test their failover readiness.
2. **10,000 req/s Benchmarking Harness:** Automated load testing harness evaluating node throughput under Byzantine upstream failures with public report generator.
3. **Rollup & Relayer Integration Guides:** Step-by-step developer documentation and integration tutorials for ERC-4337 bundlers, DeFi liquidators, and Orbit node runners.
4. **Ecosystem Retrospective & Governance Forum Report:** Final post-grant retrospective published on the Arbitrum Governance Forum and Base developer channels.

**Acceptance Criteria & Verifiable KPIs:**
- [ ] Chaos CLI published and installable via `npm` / `pip` with comprehensive documentation.
- [ ] Published benchmark demonstrating <150ms failover under sustained **10,000 requests/sec**.
- [ ] Onboarding of at least 3 ecosystem pilot teams / relayers with documented feedback.

---

## 6. Budget Allocation (Strictly Software Engineering & Tooling)

| Budget Category | Description | Amount ($USD) | Percentage |
| :--- | :--- | :--- | :--- |
| **Core Systems & Sentinel Engineering** | HAProxy L7 data plane optimization, Python async sentinel daemon, WebSocket sequencer feed client, Viem SDK | $18,000 | 51.4% |
| **Cloud-Native Packaging & Helm Tooling** | Kubernetes Helm charts, sidecar manifests, Prometheus exporter, Grafana dashboard suite | $6,500 | 18.6% |
| **Testing Harnesses & Chaos CLI** | Development of `driftguard-chaos` CLI, automated load-testing suite, Byzantine payload fuzzing | $5,000 | 14.3% |
| **Security Auditing & Socket Hardening** | Automated race-condition audits on UNIX socket drains, JSON-RPC malformed payload fuzzing, memory leak profiling | $3,000 | 8.6% |
| **Documentation & Developer Tooling Guides** | Developer integration documentation, video guides, governance forum updates, ecosystem pilot onboarding | $2,500 | 7.1% |
| **Hosting & Server Operating Costs** | **$0 requested (Self-funded by maintainers)** | **$0** | **0.0%** |
| **Total** | | **$35,000 USD** | **100%** |

---

## 7. Financial Sustainability & B2B Commercial Retainer Model

Grant committees evaluate whether a project will survive after the grant concludes. DriftGuard solves long-term economic sustainability without ongoing DAO subsidies through a **Commercial B2B Retainer Service**:

### The Sustainability Dual-Track
1. **Open-Source Public Good (100% Free):** The core Docker sidecar, Kubernetes Helm chart, `@driftguard/sdk`, and Prometheus exporters remain perpetually free, MIT-licensed, and self-hostable by any developer.
2. **Commercial B2B Retainer Service:** Institutional rollup teams, high-volume ERC-4337 paymasters, and gaming studios purchase enterprise support, managed sidecar orchestration, and 24/7 incident response SLAs.

### B2B Client Segments & Retainer Tiers
- **Tier 1: Sentinel Standard ($2,500 / month):** Up to 3 chain backends, 24/7 automated Discord webhook alerting, monthly upstream provider resilience audit, business-hours incident triage.
- **Tier 2: Orbit Rollup Mission-Critical ($5,000 / month):** Dedicated multi-node sidecar architecture, custom consensus anchors (private validator + multiple tier-1 RPCs), <15 min Sev-1 incident SLA, automated PagerDuty/Telegram alerts, bi-weekly chaos injection drills.
- **Tier 3: Institutional Relayer / Sovereign Chain ($8,500 / month):** Active-active multi-region gateway orchestration, custom AnyTrust DAC / Sequencer feed integration, dedicated systems engineer on-call, tailored zero-downtime cutover rule engines, custom Grafana enterprise dashboard.

*(Refer to [`docs/B2B_RETAINER_SERVICE_SOP.md`](docs/B2B_RETAINER_SERVICE_SOP.md) for complete Standard Operating Procedures).*

---

## 8. Application Timeline & Go-To-Market Submission Calendar

| Timeline Stage | Target Period | Specific Actions & Milestones | Expected Outcome |
| :--- | :--- | :--- | :--- |
| **Phase 1: Verification Sandbox** | **Week 1** | - Freeze reproducible chaos testing scripts in public repository<br>- Record 5-minute technical walkthrough video of live reference cluster<br>- Finalize B2B Retainer SOP documentation | Grant application packages 100% ready with live empirical proof |
| **Phase 2: Formal Submissions** | **Week 2** | - Submit formal proposal to **Arbitrum Questbook (Developer Tooling Domain)**<br>- Submit direct grant application on **Arbitrum Foundation Portal**<br>- Submit grant application on **Base Builder Grants / Coinbase Ventures Portal**<br>- Submit project profile to **Gitcoin Grants** | Applications entered into official review pipelines |
| **Phase 3: Governance & Community Advocacy** | **Week 3** | - Publish RFC / discussion thread on [Arbitrum Governance Forum](https://forum.arbitrum.foundation) under *Developer Tooling*<br>- Post explainer and live testbed links on Base Farcaster (`/base`, `/base-devs`) and Discord<br>- Host open AMA / technical demo in Arbitrum Discord | Community awareness, delegate feedback, and domain reviewer engagement |
| **Phase 4: Reviewer Interviews & Milestone 1 Signoff** | **Week 4** | - Technical interview with grant committee reviewers<br>- Live interactive failover demonstration against reference testbed<br>- Execute grant agreement / escrow setup<br>- **Milestone 1 Verification & Tranche 1 Release ($10,000 USD)** | Tranche 1 funded; formal kickoff of Milestone 2 |
| **Phase 5: Orbit & Feed Sentry Execution** | **Weeks 5–8** | - Implement WebSocket raw sequencer feed listener<br>- Publish `@driftguard/sdk` to npm with Viem integration<br>- Release Arbitrum Orbit & Base Docker presets<br>- **Milestone 2 Acceptance & Tranche 2 Release ($10,000 USD)** | Tranche 2 approved and disbursed |
| **Phase 6: Helm, Grafana & Telemetry Pack** | **Weeks 9–12** | - Publish official Prometheus exporter & Grafana dashboard JSON<br>- Release Kubernetes Helm chart sidecar operator<br>- Integrate Discord/Telegram/PagerDuty alerting engine<br>- **Milestone 3 Acceptance & Tranche 3 Release ($8,000 USD)** | Tranche 3 approved and disbursed |
| **Phase 7: Chaos CLI, Adoption & Final Report** | **Weeks 13–16** | - Release `driftguard-chaos` CLI and benchmarking harness<br>- Onboard 3 pilot teams and conduct 10,000 req/s stress testing<br>- Publish final grant retrospective and governance report<br>- **Milestone 4 Acceptance & Tranche 4 Release ($7,000 USD)** | Tooling suite complete; long-term commercial sustainability active |

---

## 9. Reviewer Live Verification Guide (Zero-Install)

Any grant reviewer or DAO delegate can independently verify DriftGuard in **less than 60 seconds** using standard shell commands:

### 1. Test Ingress Across Supported Ecosystems

```bash
# Query Arbitrum One Mainnet (Chain ID 42161)
curl -s -w "\nHTTP Status: %{http_code} | Total Latency: %{time_total}s\n" \
  -X POST https://rpc.driftguard.live/arb \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'

# Query Arbitrum Nova AnyTrust (Chain ID 42170)
curl -s -w "\nHTTP Status: %{http_code} | Total Latency: %{time_total}s\n" \
  -X POST https://rpc.driftguard.live/nova \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'

# Query Base Mainnet (Chain ID 8453)
curl -s -w "\nHTTP Status: %{http_code} | Total Latency: %{time_total}s\n" \
  -X POST https://rpc.driftguard.live/base \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
```

### 2. Inspect Ingress Gateway Routing Headers

```bash
curl -i -s -X POST https://rpc.driftguard.live/arb \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' | grep -E 'HTTP/|x-driftguard|x-upstream|result'
```

### 3. Verify Live Consensus Sentinel Telemetry

```bash
curl -s https://rpc.driftguard.live/healthz | jq .
```

### 4. Run Automated Chaos & Failover Test Suite Locally

```bash
git clone https://github.com/maskalfreeup-glitch/driftguard.git
cd driftguard
./scripts/test_failover.sh
```

---

## 10. Team & Maintenance Commitment

- **Lead Systems Engineer:** Maskal (@maskalfreeup-glitch) &mdash; Systems architecture, high-concurrency network programming, and EVM node operations.
- **Commitment:** DriftGuard is an open-source public good licensed under the permissive MIT license. The project has zero token-gating, zero SaaS licensing fees, and no proprietary vendor lock-in.
- **Sustainability:** The core daemon is engineered to run on free or low-cost cloud compute (<$5/mo VPS or Oracle Cloud free-tier ARM instances), and commercial ongoing maintenance is backed by the B2B Retainer Service model.
