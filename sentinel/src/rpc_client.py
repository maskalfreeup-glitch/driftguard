import time
import httpx
import logging
from dataclasses import dataclass
from typing import Optional, Tuple

logger = logging.getLogger("driftguard.rpc")

@dataclass
class NodeSample:
    endpoint: str
    block_number: Optional[int]
    is_syncing: bool
    latency_ms: float
    error: Optional[str]
    timestamp: float

class RpcClient:
    def __init__(self, timeout: float = 3.5):
        self.timeout = timeout
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=50, keepalive_expiry=30.0)
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout, connect=2.0),
            limits=limits,
            headers={"Content-Type": "application/json", "User-Agent": "DriftGuard-Sentinel/1.0"}
        )

    async def close(self):
        await self.client.aclose()

    async def probe(self, endpoint_url: str) -> NodeSample:
        """
        Queries eth_blockNumber and eth_syncing to evaluate node state.
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_blockNumber",
            "params": [],
            "id": 1
        }
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
                    timestamp=now
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
                    timestamp=now
                )

            hex_block = data.get("result")
            if not hex_block or not isinstance(hex_block, str):
                return NodeSample(
                    endpoint=endpoint_url,
                    block_number=None,
                    is_syncing=False,
                    latency_ms=elapsed_ms,
                    error=f"Invalid result: {hex_block}",
                    timestamp=now
                )

            block_num = int(hex_block, 16)

            # Check eth_syncing
            syncing_payload = {
                "jsonrpc": "2.0",
                "method": "eth_syncing",
                "params": [],
                "id": 2
            }
            is_syncing = False
            try:
                sync_resp = await self.client.post(endpoint_url, json=syncing_payload)
                if sync_resp.status_code == 200:
                    sync_data = sync_resp.json().get("result")
                    if sync_data is not False and sync_data is not None:
                        is_syncing = True
            except Exception:
                # If syncing check fails, don't discard block number, but log
                pass

            return NodeSample(
                endpoint=endpoint_url,
                block_number=block_num,
                is_syncing=is_syncing,
                latency_ms=elapsed_ms,
                error=None,
                timestamp=now
            )

        except httpx.TimeoutException:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            return NodeSample(
                endpoint=endpoint_url,
                block_number=None,
                is_syncing=False,
                latency_ms=elapsed_ms,
                error=f"Request timed out (> {self.timeout}s)",
                timestamp=now
            )
        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            return NodeSample(
                endpoint=endpoint_url,
                block_number=None,
                is_syncing=False,
                latency_ms=elapsed_ms,
                error=f"{type(e).__name__}: {str(e)}",
                timestamp=now
            )
