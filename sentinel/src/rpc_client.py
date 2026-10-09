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

    async def probe(self, endpoint_url: str, check_syncing: bool = True, timeout: float | None = None) -> NodeSample:
        """
        Queries eth_chainId, eth_blockNumber, and eth_syncing to evaluate node state.
        """
        start = time.perf_counter()
        now = time.time()
        eff_timeout = timeout if timeout is not None else self.timeout

        try:
            calls = [
                self._rpc_result(endpoint_url, "eth_blockNumber", 1, timeout=timeout),
                self._rpc_result(endpoint_url, "eth_chainId", 2, timeout=timeout),
            ]
            if check_syncing:
                calls.append(self._rpc_result(endpoint_url, "eth_syncing", 3, timeout=timeout))
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
                error=f"Request timed out (> {eff_timeout}s)",
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

    async def probe_reference(
        self,
        primary_url: str,
        fallback_urls: list[str] | None = None,
        timeout: float = 5.0,
    ) -> NodeSample:
        """
        Probes canonical reference endpoint with a 5s timeout.
        If primary reference fails, times out, or errors, attempts fallback reference URLs
        to prevent rate-limit stalls (e.g., on arbitrum-nova).
        """
        sample = await self.probe(primary_url, check_syncing=False, timeout=timeout)
        if sample.error is None and sample.block_number is not None:
            return sample

        # Primary reference failed or rate-limited; try fallback reference providers
        if fallback_urls:
            for fallback_url in fallback_urls:
                if not fallback_url or fallback_url == primary_url:
                    continue
                logger.warning(
                    "Primary reference %s failed (%s); trying fallback reference %s",
                    primary_url, sample.error, fallback_url
                )
                fb_sample = await self.probe(fallback_url, check_syncing=False, timeout=timeout)
                if fb_sample.error is None and fb_sample.block_number is not None:
                    return fb_sample

        return sample

    async def _rpc_result(self, endpoint_url: str, method: str, request_id: int, timeout: float | None = None):
        post_kwargs = {}
        if timeout is not None:
            post_kwargs["timeout"] = httpx.Timeout(timeout, connect=min(2.0, timeout))
        response = await self.client.post(
            endpoint_url,
            json={"jsonrpc": "2.0", "method": method, "params": [], "id": request_id},
            **post_kwargs,
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
