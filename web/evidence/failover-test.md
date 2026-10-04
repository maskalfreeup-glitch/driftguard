# DriftGuard Sepolia failover test

**Run:** 2026-09-30 07:02 UTC  
**Result:** Pass: public RPC served requests while the primary upstream was marked down.

## Procedure and observations

- Simulated a primary outage by changing `ethereum-sepolia-rpc.publicnode.com:443` to port `444` and restarting HAProxy.
- HAProxy stats showed:

  ```text
  evm_primary_pool/ethereum-sepolia-rpc.publicnode.com status=DOWN
  evm_primary_pool/rpc.sepolia.ethpandaops.io status=UP
  evm_primary_pool/BACKEND status=UP
  ```

- HAProxy logged the primary failure as `Layer4 timeout` and reported `0 active and 1 backup servers left. Running on backup.`
- RPC request through the public URL while the primary was down:

  ```text
  POST https://rpc.maskal.space
  {"jsonrpc":"2.0","id":1,"result":"0xb440c1"}
  HTTP 200
  ```

- RPC request through local port 8545 during the same outage returned the same block number and HTTP 200.
- Restored primary port 443 and restarted HAProxy. Both upstreams reported `UP`; the public URL returned block `0xb440c4` with HTTP 200.

## Test scope

The active-passive failover was exercised through the live public endpoint. HAProxy was restarted to inject and then clear the outage; this test confirms successful requests after promotion, not uninterrupted requests during the restart window.

The backup is `rpc.sepolia.ethpandaops.io`. The previous dRPC endpoint returned `chain is not available on free plan` during a separate check, so it was not used for this successful continuity test.

---

## Automated Terminal Session (AsciiCast)

![DriftGuard Failover Demo](failover-demo.gif)

A live demonstration recording is captured in [evidence/failover-demo.cast](failover-demo.cast), demonstrating:
1. Live Arbitrum One head query over `https://rpc.maskal.space/arb` (`x-upstream: primary`).
2. Sentinel consensus monitor probe (`https://rpc.maskal.space/healthz`).
3. Draining the primary node via the Sentinel socket / simulated consensus drift fault.
4. Immediate transparent cutover to fallback (`x-upstream: fallback`) with zero dropped requests (HTTP 200).
5. Primary node recovery back to active routing.

To replay the recorded terminal session:

```bash
asciinema play evidence/failover-demo.cast
```

