# 🛡️ DriftGuard

**High-Availability EVM RPC Gateway, Intelligent Drift Sentinel & Automated Failover**

DriftGuard is a production-grade infrastructure stack designed to protect Ethereum / EVM applications, indexers, and trading bots from silent node desynchronization, stale chain heads, latency spikes, and provider outages.

---

## 🏗️ Architecture

```mermaid
flowchart TD
    Client["dApp / Wallet / Indexer / Bot"] -->|JSON-RPC :8545| Gateway["HAProxy Edge Gateway"]
    
    subgraph Gateway ["HAProxy Edge Gateway (:8545 / :8404)"]
        direction TB
        CORS["CORS Preflight (204)"]
        RateLimit["Stick-Table Rate Limiter (Anti-DDoS)"]
        PayloadGuard["Payload Size Guard (< 2MB)"]
        PoolRouter{"Primary Pool Online?"}
        MetricsExporter["Prometheus Exporter (:8404/metrics)"]
        StatsUI["Protected Stats (:8404/stats)"]
    end

    PoolRouter -->|Yes (HTTP 200)| PrimaryPool["Primary Pool: PublicNode Sepolia"]
    PoolRouter -->|No (HTTP 503 Failover)| BackupPool["Backup Pool: dRPC Sepolia"]

    subgraph SentinelEngine ["Drift Sentinel Daemon (:8000)"]
        direction TB
        ProbeP["Probe Primary (eth_blockNumber & eth_syncing)"]
        ProbeB["Probe Backup (eth_blockNumber & eth_syncing)"]
        ProbeC["Probe Canonical (EthPandaOps Reference)"]
        DriftCalc["Drift & Latency Calculator"]
        CircuitBreaker["Circuit Breaker (Hysteresis Rise/Fall)"]
        SentinelProbes["Health Probes (/healthz/primary, /healthz/backup)"]
    end

    SentinelEngine -.->|HTTP Layer-7 Health Check| Gateway
    SentinelEngine -->|State, Telemetry & History| Redis[("Redis 7 (Encrypted & Memory Capped)")]
    PrimaryPool -->|TLS 1.3 Verified| ExtPrimary["https://ethereum-sepolia-rpc.publicnode.com"]
    BackupPool -->|TLS 1.3 Verified| ExtBackup["https://sepolia.drpc.org"]
```

---

## ❓ The Problem: Why Traditional Load Balancers Fail EVM Nodes

Standard load balancers (AWS ALB, NGINX, Cloudflare) rely on layer-4 TCP socket checks or shallow HTTP 200 responses. In Web3 infrastructure, **an RPC node can return HTTP 200 OK while being fatally broken**:
1. **Silent Head Lag (Block Drift):** The node is stuck 1,000 blocks behind the chain tip due to peering issues, yet responds to requests with stale data.
2. **Syncing State:** The node is catching up after a restart (`eth_syncing: true`). Serving queries causes silent state mismatches and failed transactions.
3. **Upstream Rate Limiting (429):** The node rejects JSON-RPC calls due to exhausted quotas while the HTTP server remains reachable.

**DriftGuard solves this by actively validating chain state** against an authoritative canonical reference, comparing block numbers in real time, and dynamically signaling HAProxy to drain lagging nodes before client applications are affected.

---

## ⚡ Core Features

- **Real-Time Block Drift Sentinel:** Concurrent asynchronous polling of Primary, Backup, and Canonical reference nodes measuring block heights, sync state, and round-trip latency.
- **Circuit Breaker with Hysteresis:** Configurable consecutive failure and recovery thresholds prevent flapping during brief network jitter.
- **Dynamic Failover & Host Preservation:** Cleanly switches between upstream RPC providers while rewriting SNI and `Host` headers per-provider without Cloudflare/reverse proxy SSL mismatches.
- **Hardened TLS Upstream Verification:** Full CA-bundle certificate validation (`verify required ca-file /etc/ssl/certs/ca-certificates.crt`), eliminating MITM vulnerabilities.
- **High-Throughput Connection Pooling:** Uses HAProxy `http-reuse aggressive` to maintain warm TLS 1.3 tunnels to upstream nodes, saving 50–150ms per JSON-RPC call.
- **Web3 & dApp Ready:**
  - Automatic browser CORS preflight handling (`OPTIONS` -> 204).
  - Strict HTTP method filtering (only `POST` and `OPTIONS` allowed).
  - Request body size guard (rejects malicious payloads > 2MB with JSON-RPC `-32600`).
- **In-Memory Resilient Telemetry:** Health states and historical telemetry are pushed to Redis 7, with automatic in-memory fallback if Redis is temporarily offline.
- **Dual Prometheus Observability:** Exposes native Prometheus metrics from both the HAProxy gateway (`:8404/metrics`) and the Sentinel engine (`:8000/metrics`).

---

## 🚀 Quick Start

### Prerequisites
- Docker Engine 24+ and Docker Compose v2.
- `curl` and `bash`.

### 1. Launch the Stack
```bash
git clone https://github.com/<your-account>/driftguard.git
cd driftguard
cp .env.example .env
make up
```

### 2. Verify JSON-RPC Routing
Send an Ethereum Sepolia JSON-RPC call to the gateway:
```bash
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  http://127.0.0.1:8545
```
Example Response:
```json
{"jsonrpc":"2.0","id":1,"result":"0x6739bc"}
```

### 3. Run Automated Gateway Test Suite
```bash
make test
```

---

## ⚙️ Configuration Reference (`.env`)

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `PRIMARY_RPC_URL` | `https://ethereum-sepolia-rpc.publicnode.com` | Primary preferred RPC provider |
| `PRIMARY_RPC_HOST` | `ethereum-sepolia-rpc.publicnode.com` | Primary hostname for SNI / Host headers |
| `PRIMARY_RPC_PORT` | `443` | Primary port |
| `BACKUP_RPC_URL` | `https://sepolia.drpc.org` | Automatic failover provider |
| `BACKUP_RPC_HOST` | `sepolia.drpc.org` | Backup hostname for SNI / Host headers |
| `BACKUP_RPC_PORT` | `443` | Backup port |
| `CANONICAL_RPC_URL` | `https://rpc.sepolia.ethpandaops.io` | Trusted reference to establish canonical chain tip |
| `DRIFT_THRESHOLD` | `2` | Maximum block lag before marking node UNHEALTHY |
| `POLL_INTERVAL` | `4.0` | Polling frequency (seconds) |
| `RPC_TIMEOUT` | `3.5` | Upstream query timeout (seconds) |
| `FAILURE_THRESHOLD`| `2` | Consecutive failures required to trigger circuit breaker |
| `RECOVERY_THRESHOLD`| `2` | Consecutive successes required to restore node |
| `RATE_LIMIT_PER_10S`| `200` | Max requests per 10s per IP (anti-abuse) |
| `STATS_USER` | `admin` | HAProxy stats dashboard username |
| `STATS_PASSWORD` | `driftguard_admin_secure_pass` | HAProxy stats dashboard password |
| `REDIS_PASSWORD` | `driftguard_redis_secure_pass` | Redis authentication token |

---

## 🧪 Automated Failover & Recovery Drill

DriftGuard includes an automated failover simulation script:
```bash
make test-failover
```

### What the Drill Does:
1. Verifies healthy baseline routing on Primary via HAProxy port `8545`.
2. Induces artificial drift by setting `DRIFT_THRESHOLD=-50`.
3. Observes Sentinel `/healthz/primary` trigger HTTP `503 Service Unavailable`.
4. Verifies HAProxy marks `primary_pool` DOWN and routes continuous client traffic through `backup_pool` with zero dropped requests.
5. Restores original configuration and watches Sentinel and HAProxy automatically recover `primary_pool` to UP.

---

## 📊 Observability & Telemetry

### 1. Diagnostic Status Dashboard
```bash
curl -s http://127.0.0.1:8000/status | jq .
```
Returns real-time block numbers, latencies, drift values, and circuit breaker metrics across all nodes.

### 2. Prometheus Metrics
- **Sentinel Metrics:** `http://127.0.0.1:8000/metrics`
  - `driftguard_block_height{node="primary|backup|canonical"}`
  - `driftguard_drift_blocks{node="primary|backup"}`
  - `driftguard_latency_seconds{node="primary|backup|canonical"}`
  - `driftguard_node_healthy{node="primary|backup"}`
  - `driftguard_circuit_trips_total{node="primary|backup"}`
- **HAProxy Metrics:** `http://127.0.0.1:8404/metrics` (Auth required)

### 3. HAProxy Stats Dashboard
Navigate to `http://127.0.0.1:8404/stats` in your browser.
- **Username:** `admin`
- **Password:** Configured in `STATS_PASSWORD`

---

## 🔒 Production Hardening Best Practices

- **Zero-Trust Network:** HAProxy and Redis communicate across an isolated internal Docker bridge network (`driftguard_net`).
- **Least Privilege:** Sentinel and HAProxy run as unprivileged, non-root users (`driftguard` uid 10001, `haproxy` uid 99).
- **Resource Constraints:** All containers specify strict memory and CPU limits to prevent noisy-neighbor host resource starvation.
- **Persistence & Eviction:** Redis runs with `--maxmemory 256mb --maxmemory-policy volatile-lru` and append-only disk logging.
- **CA Root Verification:** All upstream SSL/TLS handshakes strictly validate against the system CA certificates bundle.

---

## 📜 License
MIT License.
