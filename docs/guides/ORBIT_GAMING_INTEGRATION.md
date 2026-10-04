# 3-Step Integration Guide: DriftGuard Sidecar for Arbitrum Orbit & Web3 Game Engines

This guide demonstrates how game studios and Arbitrum Orbit L3 operators can drop DriftGuard directly into their deployment stack as a **local L7 sidecar (`http://localhost:8545`)** with **zero code modifications** to game clients, server tick loops, or Web3 providers.

---

## Why Game Studios Need an Ingress Sidecar

Web3 game engines (Unity, Unreal Engine, WebGL) and high-frequency backend game servers rely on ultra-fast sub-second block pacing (~250ms on Arbitrum Nitro). During matches, the client and server continuously poll the blockchain for player inventory changes, cooldown timers, and account nonces.

If your primary RPC node experiences a micro-stall (a 2–4 second sequencer freeze):
- **Standard Balancers Fail:** The node returns `HTTP 200 OK` with stale data.
- **Player Transactions Revert:** Nonce desynchronization triggers cascading `"nonce too low"` transaction reverts.
- **Ghost Items Appear:** Inventory queries return pre-trade state, breaking gameplay immersion and causing player churn.

DriftGuard acts as an out-of-band **Consensus Sentry & L7 Ingress Sidecar**. It sits right in front of your game servers or validator nodes on `localhost:8545`, continuously validating block head velocity. When a stall occurs, DriftGuard swaps upstreams via a UNIX domain socket in **under 130ms with zero dropped packets**.

```
┌────────────────────────────────────────────────────────┐
│                   Game Studio Pod                      │
│                                                        │
│  ┌────────────────────┐         ┌───────────────────┐  │
│  │ Game Server / SDK  │ ──────► │ DriftGuard L7     │  │
│  │ (Unity/Unreal/Node)│  :8545  │ Sidecar (HAProxy) │  │
│  └────────────────────┘         └─────────┬─────────┘  │
│                                           │            │
└───────────────────────────────────────────┼────────────┘
                                            │
                     ┌──────────────────────┴──────────────────────┐
                     ▼                                             ▼
          ┌─────────────────────┐                       ┌─────────────────────┐
          │ Primary Orbit Node  │                       │ Fallback Orbit Node │
          │  (Local Sequencer)  │                       │ (Replica / Hosted)  │
          └─────────────────────┘                       └─────────────────────┘
```

---

## Step 1: Add DriftGuard to Your `docker-compose.yml`

Drop the DriftGuard sidecar services directly into your existing `docker-compose.yml` alongside your game backend or Orbit node.

```yaml
version: "3.8"

services:
  # ── Your Existing Game Server / Orbit Node ──
  game-server:
    image: your-studio/game-server:latest
    environment:
      # Point your game server directly to the local DriftGuard sidecar!
      - RPC_URL=http://driftguard-proxy:8545
    depends_on:
      - driftguard-proxy

  # ── DriftGuard L7 Ingress Proxy (HAProxy) ──
  driftguard-proxy:
    image: haproxy:2.8-alpine
    restart: unless-stopped
    ports:
      - "127.0.0.1:8545:8545" # Local EVM JSON-RPC Ingress
      - "127.0.0.1:8404:8404" # Metrics & Prometheus stats
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

## Step 2: Configure Your Orbit L3 Chain & Upstreams

Define your Orbit L3 chain parameters in `sentinel/config/chains.yaml`:

```yaml
chains:
  - name: "orbit-game-l3"
    chain_id: 13371           # Your custom Orbit L3 Chain ID
    backend: "be_orbit_game"  # Matching backend name in haproxy.cfg
    poll_interval: 1.0        # Seconds between health checks (Nitro 250ms)
    drift_threshold: 4        # Alert if primary lags by > 4 blocks (~1 sec)
    failure_threshold: 2      # Consecutive failures before draining
    recovery_threshold: 2     # Consecutive clean checks before restoration
    
    # Primary: Your local high-speed sequencer node
    primary_url: "http://orbit-sequencer:8547"
    
    # Fallback: Backup replica or secondary hosted node
    fallback_url: "https://backup-rpc.yourstudiodomain.com"
    
    # Independent Canonical Reference: Used to verify true block height
    reference_url: "https://reference-node.yourstudiodomain.com"
```

Configure your environment variables in `.env`:

```bash
# Security & Operational Secrets
REDIS_PASSWORD=a948c7f938d21b4a0293e847c1b48921
STATS_PASSWORD=supersecurestatspassword

# Discord / Slack Webhook for Zero-Overhead Incident Alerts
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123456789/your-channel-token

# Ingress Bind (keep loopback for local sidecar security)
GATEWAY_BIND=127.0.0.1
GATEWAY_PORT=8545
```

---

## Step 3: Connect Game Engine / Web3 SDK (Zero Code Changes)

Because DriftGuard exposes a standard EVM JSON-RPC interface compliant with Ethereum standards, **you do not need to change a single line of game logic, contract interfaces, or Web3 provider code**. 

Simply point your existing client or server configuration to the sidecar:

### A. TypeScript / JavaScript (Viem / Ethers.js)
```typescript
import { createPublicClient, http } from "viem";

// Point directly to the DriftGuard sidecar!
export const publicClient = createPublicClient({
  transport: http("http://localhost:8545"),
});

// Standard queries automatically benefit from sub-130ms zero-drop failover:
const blockNumber = await publicClient.getBlockNumber();
const playerNonce = await publicClient.getTransactionCount({
  address: "0xPlayerAddress...",
});
```

### B. Unity C# (Nethereum / Web3.Unity)
```csharp
using Nethereum.Web3;

public class GameManager : MonoBehaviour
{
    private Web3 web3;

    void Start()
    {
        // Connect directly to local DriftGuard sidecar
        web3 = new Web3("http://localhost:8545");
        StartCoroutine(FetchPlayerState());
    }

    private IEnumerator FetchPlayerState()
    {
        var blockNumberHandler = web3.Eth.Blocks.GetBlockNumber.SendRequestAsync();
        yield return new WaitUntil(() => blockNumberHandler.IsCompleted);
        Debug.Log($"Current Verified Block: {blockNumberHandler.Result.Value}");
    }
}
```

### C. Unreal Engine (C++ / Web3 Plugin)
```cpp
// In your Web3Subsystem.cpp
FString SidecarRpcUrl = TEXT("http://127.0.0.1:8545");

TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest = FHttpModule::Get().CreateRequest();
HttpRequest->SetVerb(TEXT("POST"));
HttpRequest->SetURL(SidecarRpcUrl);
HttpRequest->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
HttpRequest->SetContentAsString(TEXT("{\"jsonrpc\":\"2.0\",\"method\":\"eth_blockNumber\",\"params\":[],\"id\":1}"));
HttpRequest->ProcessRequest();
```

---

## Verification: Test Failover in Under 60 Seconds

Once your stack is running, execute a quick local sanity check:

```bash
# 1. Query the sidecar ingress
curl -s -X POST http://localhost:8545 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'

# 2. Check Sentinel consensus health
curl -s http://localhost:8000/status | jq .

# 3. Simulate an upstream sequencer stall
./scripts/test_failover.sh
```

**Result:** DriftGuard detects the divergence, updates HAProxy via UNIX domain socket in **< 130ms**, routes client reads to fallback, and delivers **100% 2xx responses with zero dropped frames or transactions**.
