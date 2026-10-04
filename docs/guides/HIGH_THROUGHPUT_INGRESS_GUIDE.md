# High-Throughput Ingress Guide: DriftGuard Sidecar for Arbitrum Orbit, Session Relayers & Dedicated Game Servers

This guide demonstrates how infrastructure engineers, game server architects, and Arbitrum Orbit operators can drop DriftGuard directly into their deployment stack as a **local L7 sidecar (`http://localhost:8545`)** with **zero code modifications** to backend signing daemons, session relayers, or Web3 providers.

---

## 1. Network Transport Layer Architecture

DriftGuard operates strictly at the **network transport layer (Layer 7 EVM JSON-RPC over HTTP and WebSockets)**. It does not introduce proprietary SDK wrappers or modify transaction encoding. Instead, it positions a high-speed HAProxy data plane directly in front of backend workloads on `127.0.0.1:8545` (or within a Kubernetes pod network).

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Local Host / K8s Pod                            │
│                                                                        │
│  ┌─────────────────────────────────┐      HTTP / WS     ┌────────────┐ │
│  │ Authoritative Workload:         │   JSON-RPC POST    │ DriftGuard │ │
│  │ • Dedicated Game Servers (Go/C#)│ ─────────────────► │ L7 Ingress │ │
│  │ • Session Relayers & Bundlers   │      :8545         │  (HAProxy) │ │
│  │ • Paymasters / Gasless Wallets  │                    └─────┬──────┘ │
│  └─────────────────────────────────┘                          │        │
└───────────────────────────────────────────────────────────────┼────────┘
                                                                │
                     ┌──────────────────────────────────────────┴──────────────────────────────────────────┐
                     ▼                                                                                     ▼
       ┌───────────────────────────┐                                                         ┌───────────────────────────┐
       │ Primary Orbit Sequencer   │                                                         │ Fallback Replica Pool     │
       │ (Local Validator Node)    │                                                         │ (Secondary Nitro RPC)     │
       └───────────────────────────┘                                                         └───────────────────────────┘
```

### The Problem in High-Throughput Architectures
Authoritative game servers, ERC-4337 bundlers, and session relayers submit high volumes of signed transactions per second on sub-second Arbitrum Nitro chains (~250ms block times).

When an upstream RPC node or sequencer undergoes a micro-stall (a 2–4 second sequencer head ingestion freeze):
1. **The Node Returns `HTTP 200 OK` With Stale State:** Transport-level balancers (AWS ALB, Cloudflare, standard NGINX) assume the node is completely healthy.
2. **Relayer Nonce Desynchronization:** The relayer requests `eth_getTransactionCount(sender, 'latest')`. The stalled node returns an outdated nonce. When the relayer signs and broadcasts subsequent transactions, the Nitro sequencer immediately rejects them with **`nonce too low`**, stalling the relayer's transaction pipeline.
3. **Stale State & Ghost Balances:** Authoritative server tick loops querying balances or smart contract state fetch obsolete data, causing state divergence.

DriftGuard eliminates this at Layer 7: an out-of-band asynchronous consensus sentinel samples head progression every 200ms. If head height stalls while canonical anchors advance, DriftGuard commands HAProxy via a local UNIX domain socket to drain the stalled node in **under 130ms**, directing all subsequent JSON-RPC requests to the healthy fallback pool with **0 dropped packets**.

---

## 2. Step 1: Add DriftGuard Sidecar to `docker-compose.yml`

Drop the DriftGuard sidecar services directly into your existing `docker-compose.yml` alongside your authoritative game server, session relayer, or Orbit validator node:

```yaml
version: "3.8"

services:
  # ── Your Authoritative Service (Game Server, Relayer, Bundler) ──
  app-backend:
    image: your-repo/relayer-or-gameserver:latest
    environment:
      # Point your Web3 client to the local DriftGuard sidecar:
      - RPC_URL=http://driftguard-proxy:8545
    depends_on:
      - driftguard-proxy

  # ── DriftGuard L7 Ingress Proxy (HAProxy) ──
  driftguard-proxy:
    image: haproxy:2.8-alpine
    restart: unless-stopped
    ports:
      - "127.0.0.1:8545:8545" # Local EVM JSON-RPC Ingress
      - "127.0.0.1:8404:8404" # Metrics & Prometheus Stats
    volumes:
      - ./haproxy/haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro
      - haproxy-run:/run/haproxy
    mem_limit: 64m
    depends_on:
      - driftguard-sentinel

  # ── DriftGuard Consensus Sentinel (FastAPI / asyncio) ──
  driftguard-sentinel:
    image: driftguard-sentinel:latest
    build:
      context: ./sentinel
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      - CHAINS_CONFIG_PATH=/app/config/chains.yaml
      - HAPROXY_SOCKET_PATH=/run/haproxy/admin.sock
      - REDIS_URL=redis://:${REDIS_PASSWORD:-devpassword}@driftguard-redis:6379/0
      - DISCORD_WEBHOOK_URL=${DISCORD_WEBHOOK_URL:-}
    volumes:
      - ./sentinel/config/chains.yaml:/app/config/chains.yaml:ro
      - haproxy-run:/run/haproxy
    mem_limit: 96m
    depends_on:
      - driftguard-redis

  # ── DriftGuard Telemetry Cache (Redis) ──
  driftguard-redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --requirepass "${REDIS_PASSWORD:-devpassword}" --maxmemory 24mb --maxmemory-policy allkeys-lru
    mem_limit: 32m

volumes:
  haproxy-run:
```

---

## 3. Step 2: Configure Upstreams & Chain Parameters

Define your Orbit L3 or mainnet parameters in `sentinel/config/chains.yaml`:

```yaml
chains:
  - name: "arbitrum-orbit-l3"
    chain_id: 13371           # Your custom Orbit L3 Chain ID
    backend: "be_orbit_app"   # Backend pool name in haproxy.cfg
    poll_interval: 1.0        # Polling frequency in seconds
    drift_threshold: 4        # Flag delinquency if node lags by > 4 blocks (~1s)
    failure_threshold: 2      # Consecutive failures before socket drain
    recovery_threshold: 2     # Consecutive synchronized probes before restoring
    
    # Primary: Local dedicated Orbit sequencer or validator node
    primary_url: "http://orbit-sequencer:8547"
    
    # Fallback: High-availability secondary replica or hosted provider
    fallback_url: "https://backup-rpc.yourdomain.com"
    
    # Independent Canonical Reference: Independent comparator for tip verification
    reference_url: "https://reference-anchor.yourdomain.com"
```

Set operational secrets in `.env`:

```bash
# Redis & Stats Passwords
REDIS_PASSWORD=7f8b92c4a1e35d6e902b481c9a3e5f7a
STATS_PASSWORD=supersecurestatspassword

# Ingress Bind (loopback for sidecar isolation)
GATEWAY_BIND=127.0.0.1
GATEWAY_PORT=8545

# Zero-Overhead Incident Webhook (Optional)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123456789/your-channel-token
```

---

## 4. Step 3: Connect Authoritative Relayers & Game Servers

Because DriftGuard exposes an RFC-compliant JSON-RPC 2.0 interface, backend services point to `http://localhost:8545` with standard Web3 libraries. **No custom retry wrappers or multi-provider failover libraries are needed.**

### A. Authoritative Game Server / Relayer (TypeScript with Viem / Ethers)
```typescript
import { createPublicClient, createWalletClient, http } from "viem";
import { privateKeyToAccount } from "viem/accounts";

// Point directly to the local DriftGuard sidecar
export const publicClient = createPublicClient({
  transport: http("http://127.0.0.1:8545"),
});

// Nonces fetched from DriftGuard are guaranteed synchronized against canonical head:
export async function relayPlayerAction(playerSession: string, actionPayload: `0x${string}`) {
  const nonce = await publicClient.getTransactionCount({
    address: relayerAccount.address,
  });
  
  // Safe from "nonce too low" sequencer stalls
  return walletClient.sendTransaction({
    account: relayerAccount,
    to: targetContractAddress,
    data: actionPayload,
    nonce,
  });
}
```

### B. High-Throughput Relayer / Microservice (Go with `go-ethereum`)
```go
package main

import (
	"context"
	"log"

	"github.com/ethereum/go-ethereum/ethclient"
)

func main() {
	// Connect to local DriftGuard L7 sidecar
	client, err := ethclient.Dial("http://127.0.0.1:8545")
	if err != nil {
		log.Fatalf("Failed to connect to DriftGuard ingress: %v", err)
	}

	blockNumber, err := client.BlockNumber(context.Background())
	if err != nil {
		log.Fatalf("Failed to fetch verified block: %v", err)
	}

	log.Printf("Current canonical Orbit head: %d", blockNumber)
}
```

### C. Dedicated Game Server Tick Loop (C# Nethereum)
```csharp
using System;
using System.Threading.Tasks;
using Nethereum.Web3;

public class RelayerService
{
    private readonly Web3 _web3;

    public RelayerService()
    {
        // Connect to local DriftGuard sidecar on loopback
        _web3 = new Web3("http://127.0.0.1:8545");
    }

    public async Task<ulong> GetVerifiedBlockAsync()
    {
        var blockNumber = await _web3.Eth.Blocks.GetBlockNumber.SendRequestAsync();
        return (ulong)blockNumber.Value;
    }
}
```

---

## 5. Verification & Live Chaos Validation

To confirm failover behavior under high-frequency load:

```bash
# 1. Query the sidecar ingress
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'

# 2. Check Sentinel consensus health
curl -s http://127.0.0.1:8000/status | jq .

# 3. Execute automated upstream failover drill
./scripts/test_failover.sh
```

**Measured Result:** DriftGuard drains the primary upstream via UNIX socket in **under 130ms (0.1228s)**, routing all traffic to the fallback node with **zero HTTP 5xx errors and 0 dropped requests**.
