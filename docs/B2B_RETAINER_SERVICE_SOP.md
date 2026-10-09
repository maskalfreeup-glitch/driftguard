# DriftGuard B2B Retainer Service: Standard Operating Procedure (SOP)

**Document ID:** DG-SOP-B2B-001  
**Classification:** Confidential &mdash; Enterprise Operations & Client Runbook  
**Target Clients:** Arbitrum Orbit L3 Appchains, Web3 Gaming Studios, ERC-4337 Account Abstraction Bundlers, and High-Volume Relayer Networks  
**Effective Date:** October 2026 | Version 2.0  
**Maintained By:** DriftGuard Systems Core Infrastructure Team  

---

## 1. Executive Overview & Service Scope

The **DriftGuard Enterprise Resilience Retainer** is a managed B2B infrastructure service providing turnkey L7 ingress management, out-of-band consensus verification, 24/7 incident response, and upstream provider resilience guarantees.

While the core DriftGuard software daemon remains 100% open-source and MIT-licensed, enterprise Web3 organizations require guaranteed uptime SLAs, dedicated on-call engineers, custom upstream pool calibration, and continuous chaos resilience auditing without hiring in-house distributed systems specialists.

```
+----------------------------------------------------------------------------------------------------+
|                               THE SUSTAINABILITY DUAL-TRACK MODEL                                  |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|   1. OPEN-SOURCE PUBLIC GOOD (100% Free - Grant Funded)                                            |
|      • Standalone Docker Sidecar (<45 MB RAM) & Kubernetes Helm Chart                              |
|      • TypeScript / Viem SDK (@driftguard/sdk)                                                     |
|      • Core Consensus Sentinel Engine (Arbitrum One, Nova, Orbit, Base)                            |
|                                                                                                    |
|   2. COMMERCIAL B2B RETAINER SERVICE (Enterprise Revenue - Self-Sustaining)                        |
|      • Managed Ingress Orchestration & Active-Active Multi-Region Sidecars                         |
|      • 24/7 Incident Escalation (15-Minute Sev-1 SLA) & Automated PagerDuty Triage                 |
|      • Custom Consensus Anchor Calibration (Private Validator Nodes + Tier-1 RPCs)                |
|      • Monthly Chaos Injection Drills & Upstream Provider Scorecards                               |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Target Client Profiles & Value Propositions

| Client Segment | Critical Pain Point | DriftGuard Retainer Solution | Value Delivered |
| :--- | :--- | :--- | :--- |
| **Arbitrum Orbit L3 Appchains** *(Gaming, Social, DeFi)* | Sequencer feed disconnects or AnyTrust DAC storage desyncs stall the entire chain. | Custom raw WebSocket sequencer listener + dedicated multi-node gateway cluster. | Guarantees continuous sequencer availability and sub-50ms disconnect mitigation. |
| **ERC-4337 Smart Account Bundlers** *(Biconomy, ZeroDev, Pimlico)* | Lagging RPC nodes return stale nonces, causing paymaster transactions to revert with `nonce too low`. | Monotonically guaranteed nonce routing and sub-130ms socket drain away from lagging nodes. | Eliminates failed user onboarding and relayer queue locks. |
| **DeFi Liquidators & Relayer Keepers** *(GMX, Camelot, Pendle)* | A 3-second RPC delay (12 missed Nitro blocks) results in missed liquidations and arbitrage losses. | Real-time consensus drift sentinel auditing blocks every 200ms out-of-band. | Protects MEV opportunities and prevents stale oracle contract queries. |
| **Dedicated Web3 Game Studios** *(Real-Time On-Chain Actions)* | Stale RPC reads cause "ghost items", inventory desync, and player session disconnects. | Sub-130ms transparent cutover without player TCP disconnection or game client code changes. | Preserves player experience and continuous server-authoritative synchronization. |

---

## 3. Retainer Tiers & Pricing Schedule

| Retainer Tier | Monthly Retainer | Target Customer | Core SLA & Service Inclusions |
| :--- | :--- | :--- | :--- |
| **Tier 1: Sentinel Standard** | **$2,500 / month** | dApps, Indexers & Independent Relayers | • Up to 3 chain backends monitored<br>• 24/7 automated Discord/Telegram webhook alerts<br>• Monthly upstream provider health audit<br>• 2-hour business-hours incident triage response |
| **Tier 2: Orbit Rollup Mission-Critical** | **$5,000 / month** | Orbit L3 Chains & Dedicated Game Studios | • Dedicated multi-node HA cluster sidecar architecture<br>• Custom consensus anchors (client validator + 2 private tier-1 RPCs)<br>• **< 15 min Sev-1 incident SLA** with 24/7 on-call paging<br>• Bi-weekly synthetic chaos injection drills<br>• Automated post-mortem reports within 24 hours |
| **Tier 3: Institutional Sovereign / Paymaster** | **$8,500 / month** | High-Volume Paymasters & Sovereign Rollups | • Active-active multi-region gateway orchestration<br>• Custom WebSocket raw sequencer feed listener<br>• AnyTrust Data Availability Committee (DAC) custom sentry<br>• Dedicated senior systems engineer on-call<br>• Custom Prometheus/Grafana enterprise dashboard<br>• **99.99% gateway availability guarantee** with contractual penalty credits |

---

## 4. SOP-01: Client Onboarding & Infrastructure Pre-Flight Audit

**Objective:** Audit the client's current RPC architecture, quantify peak throughput, identify single-points-of-failure (SPOFs), and establish baseline latency metrics within 5 business days.

### Step-by-Step Procedure:
1. **Intake Discovery Call (Day 1):**
   - Identify Chain ID(s), upstream RPC providers (Alchemy, Infura, QuickNode, local validator node), and peak queries-per-second (QPS).
   - Document client consumer types: ERC-4337 paymaster bundler, Go/Rust relayer daemon, game server backend, or public dApp frontend.
2. **Network Topology & Upstream Assessment (Day 2):**
   - Benchmark client's current upstream providers over 48 hours for:
     - p50 / p90 / p99 response latency.
     - Block propagation lag against the canonical sequencer.
     - Rate-limit thresholds and HTTP 429 response frequency.
3. **Consensus Anchor Selection (Day 3):**
   - Select 2 independent, non-correlated reference nodes (e.g., direct sequencer endpoint + private tier-1 fallback like dRPC/Tenderly) to ensure out-of-band monitoring integrity.
4. **Pre-Flight Audit Report Delivery (Day 4–5):**
   - Deliver an executive report detailing identified vulnerability vectors, recommended drift thresholds (typically 4 Nitro blocks ~ 1s), and recommended HAProxy stick-table rate limits.

---

## 5. SOP-02: Sidecar Deployment & HA Gateway Injection

**Objective:** Deploy DriftGuard sidecar instances in front of client workloads with zero client code changes.

```
  Client Environment:
  +---------------------------------------------------------------------------------+
  |  Host / Kubernetes Pod / VPS                                                    |
  |                                                                                 |
  |  +-----------------------+              HTTP POST (localhost:8545)              |
  |  | Client Relayer / App  | ------------------------------------+                |
  |  +-----------------------+                                     |                |
  |                                                                v                |
  |  +---------------------------------------------------------------------------+  |
  |  | DriftGuard Sidecar Container (HAProxy L7 + Async Sentinel + Redis)        |  |
  |  | • Memory RSS: < 45 MB RAM                                                 |  |
  |  | • Dynamic UNIX Socket: /run/haproxy/admin.sock                            |  |
  |  +-------------------------------------+-------------------------------------+  |
  |                                        |                                        |
  |                                        v (Upstream)                             |
  |                         +------------------------------+                        |
  |                         | Client Validator Node (Main) |                        |
  |                         +------------------------------+                        |
  +---------------------------------------------------------------------------------+
                                           | (Fallback Cutover)
                                           v
                            +------------------------------+
                            | Private Backup RPC (Alchemy) |
                            +------------------------------+
```

### Step-by-Step Procedure:
1. **Deployment Architecture Selection:**
   - **Option A (Kubernetes Sidecar):** Inject DriftGuard container into client's relayer or indexer pod spec using the official Helm chart.
   - **Option B (Docker Compose / Systemd):** Deploy DriftGuard directly on client's validator node VPS listening on `127.0.0.1:8545`.
2. **Configuration Calibration:**
   - Configure `sentinel/config/chains.yaml` with client's primary and fallback endpoints.
   - Set client environment variable: `RPC_URL=http://localhost:8545` (zero application code rewrites).
3. **UNIX Socket & Healthcheck Verification:**
   - Verify `/run/haproxy/admin.sock` connectivity:
     ```bash
     echo "show stat" | socat stdio unix-connect:/run/haproxy/admin.sock | grep -E 'be_arb|be_nova'
     ```
   - Confirm local `/healthz` returns `HTTP 200 OK` with active chain monitoring.
4. **Traffic Cutover:**
   - Direct 10% traffic canary -> verify zero errors -> 100% cutover.

---

## 6. SOP-03: Consensus Anchor Calibration & Drift Tuning

**Objective:** Calibrate drift thresholds to prevent false positives during transient public internet jitter while ensuring sub-second cutover during real stalls.

### Calibration Parameters Matrix:

| Parameter | Default (Standard) | High-Velocity Orbit L3 | High-Volume Relayer | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `poll_interval` | `0.2s` (200ms) | `0.1s` (100ms) | `0.15s` (150ms) | Out-of-band polling loop frequency |
| `drift_threshold` | `4 blocks` (~1.0s) | `3 blocks` (~750ms) | `2 blocks` (~500ms) | Maximum allowed block divergence |
| `failure_threshold` | `1 poll` | `1 poll` | `1 poll` | Consecutive failures before server drain |
| `recovery_threshold` | `2 polls` | `3 polls` | `3 polls` | Consecutive healthy polls before un-draining |
| `syncing_check` | `true` | `true` | `true` | Failover immediately if `eth_syncing = true` |

### Flap Prevention Runbook:
- If public network latency spikes cause flapping between primary and fallback, increase `recovery_threshold` to `3` or `4`.
- Never decrease `recovery_threshold` below `2` to ensure socket draining hysteresis remains stable.

---

## 7. SOP-04: 24/7 Incident Escalation & Response Runbook

**Objective:** Handle upstream provider desyncs, sequencer stalls, and network partitions within strict contractual SLAs.

### Incident Severity & SLA Matrix:

| Severity Level | Definition | Response SLA | Target Resolution | Primary Actions |
| :--- | :--- | :--- | :--- | :--- |
| **SEV-1 (Critical)** | Primary and fallback both desynced; client experiencing >0.1% transaction reverts; sequencer frozen. | **< 15 minutes** (Tier 2/3)<br>*(24/7 on-call paging)* | **< 30 minutes** | Automated failover verification; manual tertiary upstream injection via admin socket; client executive bridge opened. |
| **SEV-2 (Major)** | Primary upstream stalled; DriftGuard executed autonomous sub-130ms failover to fallback; client traffic unaffected. | **< 1 hour** | **< 2 hours** | Verify fallback capacity; triage delinquent primary; notify upstream provider NOC; monitor for canonical recovery. |
| **SEV-3 (Minor)** | Transient consensus jitter (<2 blocks); single poll timeout; telemetry warning. | **< 8 hours** | **Next business day** | Review Redis telemetry logs; calibrate timeout thresholds if jitter persists. |

### SEV-1 Escalation Workflow:
```
[Sentinel Trips Critical Alert] 
          │
          ├──> 1. PagerDuty on-call engineer paged (< 60 seconds)
          ├──> 2. Automated Discord / Telegram alert dispatched (< 200 ms)
          │
          v
[Systems Engineer Triage (< 15 min)]
          │
          ├── Inspect live sentinel state: curl -s http://localhost:8545/healthz
          ├── Inspect HAProxy socket state: echo "show servers state" | socat ...
          │
          ├── [Case A: Fallback healthy, Primary stalled]
          │     └── Confirm autonomous socket drain successful (HTTP 200 preserved).
          │
          └── [Case B: All upstreams desynced / Sequencer Stalled]
                ├── Inject emergency tertiary RPC into HAProxy runtime pool:
                │   echo "set server <backend>/<srv> addr <ip> port 8545" | socat ...
                └── Escalate to Rollup Sequencer Operator / Foundation Discord.
```

---

## 8. SOP-05: Chaos Drills, Upstream Benchmarking & Monthly Reporting

**Objective:** Proactively stress-test the client's architecture and provide empirical scorecards on their upstream RPC vendors.

### 1. Bi-Weekly Chaos Drills (Tier 2 & 3):
- Conduct synthetic fault injections during scheduled maintenance windows:
  - Inject 20-block head freeze into primary RPC via `driftguard-chaos`.
  - Verify HAProxy drains primary within **< 130ms**.
  - Measure packet drop rate (must remain **0.00%**).
  - Inject latency spike (>1000ms) to test hysteresis stability.

### 2. Monthly Upstream Vendor Scorecard:
- Every 30 days, deliver an executive resilience audit:
  - **Uptime & Staleness Hours:** Total minutes each upstream provider lagged behind canonical head.
  - **Average Drift-to-Drain Latency:** Measured failover speed across all recorded events.
  - **Provider Reliability Rating:** Empirical ranking of client's vendors (Alchemy vs QuickNode vs Private Node).
  - **Cost Optimization Advice:** Recommendations on reducing paid RPC tiers based on actual failover utilization.

---

## 9. Contractual Terms & Service Level Agreement (SLA)

1. **Gateway Availability SLA (Tier 2 & 3):**
   - DriftGuard guarantees **99.99% ingress gateway availability** for client workloads.
   - If availability falls below 99.99% in a billing cycle, client receives contractual service credits:
     - 99.90% – 99.98%: 15% monthly retainer credit.
     - 99.00% – 99.89%: 30% monthly retainer credit.
     - < 99.00%: 50% monthly retainer credit.
2. **Data Privacy & Key Custody:**
   - DriftGuard engineers **never** take custody of private keys, mnemonic phrases, or transaction signing credentials.
   - All RPC endpoints and consensus anchor credentials are encrypted via client-managed secret vaults or environment files.
3. **Termination & Knowledge Transfer:**
   - Retainer contracts operate on month-to-month or quarterly commitments.
   - Upon termination, DriftGuard delivers a complete infrastructure handoff pack, ensuring the client can continue running the open-source sidecar independently without vendor lock-in.
