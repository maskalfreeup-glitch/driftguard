import logging
import time
from dataclasses import dataclass

import httpx

logger = logging.getLogger("driftguard.rpc")


@dataclass
class NodeSample:
    endpoint: str
    block_number: int | None
    is_syncing: bool
    latency_ms: float
    error: str | None
    timestamp: float
    chain_id: int | None = None


class RpcClient:
    def __init__(self, timeout: float = 3.5):
        self.timeout = timeout
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=50, keepalive_expiry=30.0)
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout, connect=2.0),
            limits=limits,
            headers={"Content-Type": "application/json", "User-Agent": "DriftGuard-Sentinel/1.0"},
        )

    async def close(self):
        await self.client.aclose()

    async def probe(self, endpoint_url: str) -> NodeSample:
        """
        Queries eth_chainId, eth_blockNumber, and eth_syncing to evaluate node state.
        """
        payload = {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}
        start = time.perf_counter()
        now = time.time()

        try:
            resp = await self.client.post(endpoint_url, json=payload)
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

            if resp.status_code != 200:
                return NodeSample(
                    endpoint=endpoint_url,
                    block_number=None,
                    is_syncing=False,
                    latency_ms=elapsed_ms,
                    error=f"HTTP {resp.status_code}: {resp.text[:100]}",
                    timestamp=now,
                )

            data = resp.json()
            if "error" in data:
                err_msg = data["error"].get("message", "Unknown RPC error")
                return NodeSample(
                    endpoint=endpoint_url,
                    block_number=None,
                    is_syncing=False,
                    latency_ms=elapsed_ms,
                    error=f"RPC Error: {err_msg}",
                    timestamp=now,
                )

            hex_block = data.get("result")
            if not hex_block or not isinstance(hex_block, str):
                return NodeSample(
                    endpoint=endpoint_url,
                    block_number=None,
                    is_syncing=False,
                    latency_ms=elapsed_ms,
                    error=f"Invalid result: {hex_block}",
                    timestamp=now,
                )

            try:
                block_num = int(hex_block, 16)
                if block_num < 0:
                    raise ValueError("negative block number")
            except ValueError as exc:
                return NodeSample(endpoint_url, None, False, elapsed_ms, f"Invalid block number: {exc}", now)

            chain_resp = await self.client.post(
                endpoint_url,
                json={"jsonrpc": "2.0", "method": "eth_chainId", "params": [], "id": 3},
            )
            if chain_resp.status_code != 200:
                return NodeSample(endpoint_url, None, False, elapsed_ms,
                                  f"eth_chainId HTTP {chain_resp.status_code}", now)
            chain_data = chain_resp.json()
            chain_value = chain_data.get("result")
            if chain_data.get("error") or not isinstance(chain_value, str):
                return NodeSample(endpoint_url, None, False, elapsed_ms,
                                  "Invalid eth_chainId response", now)
            try:
                chain_id = int(chain_value, 16)
            except ValueError:
                return NodeSample(endpoint_url, None, False, elapsed_ms,
                                  "Malformed eth_chainId result", now)

            # Check eth_syncing
            syncing_payload = {"jsonrpc": "2.0", "method": "eth_syncing", "params": [], "id": 2}
            is_syncing = False
            try:
                sync_resp = await self.client.post(endpoint_url, json=syncing_payload)
                if sync_resp.status_code != 200:
                    raise ValueError(f"eth_syncing HTTP {sync_resp.status_code}")
                sync_body = sync_resp.json()
                if sync_body.get("error") or "result" not in sync_body:
                    raise ValueError("invalid eth_syncing response")
                sync_result = sync_body["result"]
                if sync_result is not False and not isinstance(sync_result, dict):
                    raise ValueError("invalid eth_syncing result")
                is_syncing = isinstance(sync_result, dict)
            except Exception as exc:
                return NodeSample(endpoint_url, None, False, elapsed_ms, f"eth_syncing failed: {exc}", now)

            return NodeSample(
                endpoint=endpoint_url,
                block_number=block_num,
                is_syncing=is_syncing,
                latency_ms=elapsed_ms,
                error=None,
                timestamp=now,
                chain_id=chain_id,
            )

        except httpx.TimeoutException:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            return NodeSample(
                endpoint=endpoint_url,
                block_number=None,
                is_syncing=False,
                latency_ms=elapsed_ms,
                error=f"Request timed out (> {self.timeout}s)",
                timestamp=now,
            )
        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            return NodeSample(
                endpoint=endpoint_url,
                block_number=None,
                is_syncing=False,
                latency_ms=elapsed_ms,
                error=f"{type(e).__name__}: {e!s}",
                timestamp=now,
            )
