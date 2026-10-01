import asyncio
import logging
import re
import time
from dataclasses import dataclass

import httpx

from sentinel import __version__

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
    syncing_checked: bool = True


class RpcClient:
    def __init__(self, timeout: float = 3.5):
        self.timeout = timeout
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=50, keepalive_expiry=30.0)
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout, connect=2.0),
            limits=limits,
            headers={"Content-Type": "application/json", "User-Agent": f"DriftGuard-Sentinel/{__version__}"},
        )

    async def close(self):
        await self.client.aclose()

    async def probe(self, endpoint_url: str, check_syncing: bool = True) -> NodeSample:
        """
        Queries eth_chainId, eth_blockNumber, and eth_syncing to evaluate node state.
        """
        start = time.perf_counter()
        now = time.time()

        try:
            calls = [
                self._rpc_result(endpoint_url, "eth_blockNumber", 1),
                self._rpc_result(endpoint_url, "eth_chainId", 2),
            ]
            if check_syncing:
                calls.append(self._rpc_result(endpoint_url, "eth_syncing", 3))
            results = await asyncio.gather(*calls)
            block_result, chain_result = results[:2]
            sync_result = False
            if check_syncing:
                sync_result = results[2]

            if not isinstance(block_result, str) or not re.fullmatch(r"0x[0-9a-fA-F]+", block_result):
                raise ValueError("Malformed eth_blockNumber result")
            block_num = int(block_result, 16)
            if not isinstance(chain_result, str) or not re.fullmatch(r"0x[0-9a-fA-F]+", chain_result):
                raise ValueError("Malformed eth_chainId result")
            chain_id = int(chain_result, 16)
            if sync_result is not False and not isinstance(sync_result, dict):
                raise ValueError("Malformed eth_syncing result")
            is_syncing = isinstance(sync_result, dict)

            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

            return NodeSample(
                endpoint=endpoint_url,
                block_number=block_num,
                is_syncing=is_syncing,
                latency_ms=elapsed_ms,
                error=None,
                timestamp=now,
                chain_id=chain_id,
                syncing_checked=check_syncing,
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

    async def _rpc_result(self, endpoint_url: str, method: str, request_id: int):
        response = await self.client.post(
            endpoint_url,
            json={"jsonrpc": "2.0", "method": method, "params": [], "id": request_id},
        )
        if response.status_code != 200:
            raise ValueError(f"{method} returned HTTP {response.status_code}")
        body = response.json()
        if not isinstance(body, dict) or body.get("jsonrpc") != "2.0" or body.get("id") != request_id:
            raise ValueError(f"Malformed {method} JSON-RPC envelope")
        if body.get("error") is not None:
            err = body.get("error")
            if method == "eth_syncing" and isinstance(err, dict) and err.get("code") == -32601:
                return False
            raise ValueError(f"{method} returned a JSON-RPC error")
        if "result" not in body:
            raise ValueError(f"{method} response has no result")
        return body["result"]
