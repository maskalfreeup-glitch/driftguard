# Arbitrum Foundation Grant Application: DriftGuard

**Project Name:** DriftGuard &mdash; Arbitrum L2/L3 Consensus & Nitro Sequence Guardian  
**Track:** Developer Tooling & Node Infrastructure  
**Target Ecosystems:** Arbitrum One (Chain ID `42161`), Arbitrum Nova (Chain ID `42170`), Arbitrum Sepolia (`421614`), and Arbitrum Orbit L3 Chains  
**Project Repository:** [github.com/maskalfreeup-glitch/driftguard](https://github.com/maskalfreeup-glitch/driftguard)  
**License:** [MIT License](https://opensource.org/licenses/MIT)  
**Total Funding Request:** $25,000 USD (equivalent in $ARB)  

---

## 1. Executive Summary

Arbitrum Nitro processes transactions at ~250ms sub-second block pacing, enabling ultra-fast execution for DeFi and high-throughput gaming. However, this high block velocity introduces a critical infrastructure failure mode: **silent RPC staleness and head-of-line blocking**. Standard web load balancers rely on shallow transport checks (HTTP 200, TCP connect). An RPC node can respond with HTTP 200 while lagging 20 blocks behind the canonical head, actively syncing (`eth_syncing = true`), or disconnected from the Nitro Sequencer feed.

In Arbitrum DeFi, a 5-second RPC desync represents ~20 missed blocks. Liquidation keepers miss profitable liquidations, oracle aggregators push stale prices, and automated traders suffer transaction reversions or extreme slippage.

**DriftGuard** is an open-source, turnkey high-availability JSON-RPC gateway purpose-built for EVM rollups, Orbit chains, DeFi indexers, and autonomous agents requiring sub-150ms transparent failover without custom client logic. It decouples a high-throughput C-native L7 data plane (HAProxy) from an out-of-band asynchronous consensus sentinel (FastAPI + Redis) that continuously samples primary, fallback, and independent reference RPCs against canonical chain identity, tip height, and syncing status. In live production drills on an Oracle Cloud micro instance, DriftGuard achieves **sub-130ms failover cutovers (0.1228s)** with **zero HTTP 5xx responses** and a total memory footprint under **120 MiB**.

---

## 2. Problem Statement: Silent Consensus Desync & Head-of-Line Blocking

### A. The 250ms Head Velocity Challenge
On Ethereum L1, a 1-block drift spans 12 seconds. On Arbitrum One and Nova, Nitro sequencers produce blocks at ~250ms intervals. Stale reads from desynchronized backup RPCs lead to reverted transactions, broken arbitrage bots, and faulty oracle updates. A brief RPC provider rate-limit or internal cache stall of 3 seconds leaves the node 12 blocks behind the tip. Wallets, DeFi indexers, and autonomous agents querying this node receive obsolete nonces and outdated contract states.

### B. Background Syncing Pitfalls
When an Arbitrum node restarts or recovers from a network interruption, it enters a catch-up phase (`eth_syncing = true`). During this window, nodes continue answering JSON-RPC queries with `HTTP 200 OK`, returning partial account balances, missing event logs, and incorrect receipt confirmations.

### C. Circuit Breaker Flapping
Transient latency spikes cause naive balancers to flap violently between endpoints, causing TCP resets, nonce collisions, and inconsistent read states. DriftGuard implements configurable hysteresis (`failure_threshold`, `recovery_threshold`) and socket-level server draining to ensure seamless, deterministic cutovers.

---

## 3. Architecture & Technical Design

### High-Level Flow

```
                      +---------------------------------------+
                      |  Arbitrum dApps / Indexers / Wallets  |
                      +-------------------+-------------------+
                                          |
                                          | HTTP POST (JSON-RPC)
                                          v
                      +---------------------------------------+
                      |         HAProxy L7 Ingress Gateway    |
                      |  Routes: /arb, /nova, /arb-sepolia    |
                      |  • Anti-abuse IP tracking & rate limit|
                      |  • Native JSON response gzip compress |
                      |  • Zero-downtime UNIX socket control  |
                      +-----------+---------------+-----------+
                                  |               |
               (Primary Healthy)  |               |  (Primary Stale / Drained)
                                  v               v
                      +---------------+       +---------------+
                      |  Primary RPC  |       | Fallback RPC  |
                      | (PublicNode)  |       | (Tenderly/dRPC|
                      +-------+-------+       +-------+-------+
                              ^                       ^
                              |                       |
                              |   Asynchronous Probes |
                              |   (ChainID, Head,     |
                              |    Syncing State)     |
                      +-------+-----------------------+-------+
                      |       Async Sentinel Health Daemon    |
                      |  • 2.0s poll loop per Arbitrum chain  |
                      |  • Drift Threshold (4 blocks ~ 1s)    |
                      |  • Admin Socket Server Drain (`maint`)|
                      |  • Discord Incident Alerting          |
                      +-----------+---------------+-----------+
                                  |               |
                                  v               v
                      +---------------+       +---------------+
                      | Canonical Ref |       | In-Memory     |
                      | Node (drpc/L1)|       | Redis / Cache |
                      +---------------+       +---------------+
```

### Key Technical Specifications
- **Architecture:** Decoupled high-throughput L7 data plane with an out-of-band asynchronous consensus sentinel. Low-overhead C-native routing (HAProxy) bound to an isolated asyncio consensus engine (FastAPI + Redis).
- **Ingress Layer:** HAProxy 2.8+ L7 reverse proxy with sticky tables, path stripping (`/arb` &rarr; `/`), response compression, and runtime UNIX socket configuration.
- **Sentinel Daemon:** Python 3.12 + FastAPI + asyncio + httpx HTTP/2 connection pooling.
- **State Store:** Redis 7 ephemeral telemetry cache with `allkeys-lru` eviction policy and automated 24h key TTL hygiene.
- **Memory Footprint:** 120 MiB aggregate container limit (Sentinel: 128M limit / 50M RSS, Proxy: 64M limit / 18M RSS, Redis: 32M limit / 7M RSS).
- **CPU Footprint:** ~3% idle utilization on 1-core micro VM.

---

## 4. Empirical Benchmarks (Verified Live on Cloud VPS)

The following benchmark was captured on a live production deployment (`instance-20260930-1859`, Oracle Cloud VM.Standard.E2.1.Micro) running automated verification:

| Metric | Target SLA | DriftGuard Live Result | Status |
| :--- | :--- | :--- | :--- |
| **Synthetic Drift Cutover Time** | < 1.500s | **0.1228 seconds** | **EXCEEDED (12x faster)** |
| **Sampled HTTP 5xx Responses** | 0 | **0 (Zero dropped requests)** | **PASSED** |
| **Idle Sentinel CPU** | < 10.0% | **3.17%** | **PASSED** |
| **Peak Memory Consumption** | < 256 MiB | **76.1 MiB total stack** | **PASSED** |
| **Multi-Chain Route Identification**| 100% | **100% (One, Nova, Sepolia)** | **PASSED** |

---

## 5. Scope of Work & Roadmap Milestones

### Milestone 1: Operational Edge & Core Gateways (Months 1–2)
*Status: Ready & Deployed as Functional PoC*
- Arbitrum One, Nova, and Sepolia live on `rpc.maskal.space` with sub-130ms failover across fallback pools.
- HAProxy path routing for Arbitrum One (`/arb`), Arbitrum Nova (`/nova`), and Arbitrum Sepolia (`/arb-sepolia`).
- Deduplicated UNIX domain socket state changes minimizing daemon overhead.
- Configurable Nitro drift thresholds calibrated for 250ms block times.
- Scripted reproducible chaos drill test suite (`test_failover.sh` and `test_gateway.sh`).
- **Deliverables:** Merged open-source codebase, verification scripts, live public edge gateway deployment.
- **Funding Allocation:** $8,000 USD (in $ARB)

### Milestone 2: Arbitrum Orbit / Stylus Native Support & Sequencer Feed (Months 3–4)
- **Arbitrum Orbit & Stylus Native Support:** Configuration blueprints and one-line Docker presets for emerging Arbitrum Orbit L3 chains and Stylus execution monitoring.
- **Arbitrum Sequencer Feed Listener:** Native WebSocket consumer for the raw Arbitrum sequencer feed (`wss://arb1.arbitrum.io/feed`), detecting sequencer stalls before block height discrepancies appear.
- **L1 Batch Poster & Inbox Probing:** Track delayed inbox status and L1 rollup batch posting lag to warn operators of delayed finality.
- **Deliverables:** WebSocket sentry module, Arbitrum Orbit/Stylus configuration presets, alerting integration.
- **Funding Allocation:** $10,000 USD (in $ARB)

### Milestone 3: Prometheus/Grafana Telemetry Pack, K8s Operator & Public Good RPC (Months 5–6)
- **Prometheus/Grafana Telemetry Pack:** Standardized dashboard templates exporting per-node drift offsets, switchover frequency, and latency delta distributions.
- **Helm Chart & K8s Sidecar:** Cloud-native packaging for DevOps teams running indexers (The Graph), relayer nodes, and Arbitrum validators.
- **Public Good Arbitrum Sepolia Gateway:** Community-facing, resilient public RPC gateway for Arbitrum Sepolia developers, backed by multi-provider failover.
- **Deliverables:** Published Helm repository, Grafana dashboard pack, live public testnet gateway, documentation portal.
- **Funding Allocation:** $7,000 USD (in $ARB)

---

## 6. Budget Breakdown

| Category | Description | Amount ($USD / ARB equivalent) |
| :--- | :--- | :--- |
| **Core Engineering** | Architecture, WebSocket Nitro feed integration, Orbit/Stylus presets, K8s packaging | $16,000 |
| **Infrastructure & Test Nodes** | Multi-provider RPC subscriptions (Alchemy, Infura, QuickNode, Tenderly) for testing | $4,500 |
| **Security & Resiliency Review**| Automated load testing, edge case audits, fuzzing RPC errors | $2,500 |
| **Documentation & Outreach** | Developer guides, video walkthroughs, Arbitrum forum updates | $2,000 |
| **Total** | | **$25,000 USD** |

---

## 7. Ecosystem Impact & Alignment

1. **Turnkey Orbit L3 & dApp Resiliency:** Turnkey high-availability gateway for Orbit chains, DeFi protocols (GMX, Camelot, Uniswap, Pendle), DeFi indexers, and autonomous agents requiring sub-150ms transparent failover without custom client logic.
2. **Gaming & High-Velocity L2 Support:** Provides Arbitrum Nova games with zero-downtime, sub-second failover without requiring expensive enterprise infrastructure.
3. **Decentralized Node Public Goods:** Lowers the barrier for solo node runners and independent teams to operate enterprise-grade high-availability infrastructure on free/cheap cloud instances.

---

## 8. Live Demonstration & Reviewer Verification Suite

![DriftGuard Failover Demo](evidence/failover-demo.gif)

Reviewers can verify the live DriftGuard production gateway running on OCI and routed through Cloudflare Edge without installing dependencies:

### 1. Multi-Chain Ingress Smoke Test

```bash
# Query Arbitrum One
curl -s -X POST https://rpc.maskal.space/arb \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'

# Query Arbitrum Nova
curl -s -X POST https://rpc.maskal.space/nova \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'

# Query Arbitrum Sepolia Testnet
curl -s -X POST https://rpc.maskal.space/arb-sepolia \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
```

### 2. Inspect L7 Gateway Headers & Routing Metadata

```bash
curl -i -s -X POST https://rpc.maskal.space/arb \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' | grep -E 'HTTP/|x-driftguard|x-upstream|result'
```

*Expected Output:*

```http
HTTP/2 200
x-driftguard-gateway: HAProxy-L7
x-upstream: primary
{"jsonrpc":"2.0","id":1,"result":"0x..."}
```

### 3. Sentinel Live Consensus State Verification

Verifies background node polling and chain drift states via the Sentinel API:

```bash
# Query live consensus monitor state
curl -s https://rpc.maskal.space/healthz | jq .
```

### 4. Failover & Consensus Architecture

* **Ingress Data Plane:** HAProxy 2.8 L7 reverse proxy with health-check state machine and dynamic socket-driven weight adjustment.
* **Control Plane:** Out-of-band Python/asyncio Sentinel evaluating upstream drift against canonical reference nodes at 2s polling intervals.
* **Storage/State:** Redis caching layer maintaining node health history, flap-damping cooldowns, and drift metrics.

### 5. Automated Chaos & Failover Benchmark (Deep Review)

To prove zero dropped requests during an active upstream provider blackout:

```bash
# On the VPS: Run automated failover benchmark
cd ~/driftguard
./scripts/test_failover.sh
```


