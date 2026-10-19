"""
DriftGuard Sentinel - Adaptive Cadence Monitoring Loop
Throttles JSON-RPC consensus polling dynamically:
- delta == 0: sleep 0.40s (in-sync, matching ~250-400ms Arbitrum block time)
- delta >= 1: sleep 0.10s (drift detected, rapid hysteresis recovery & socket draining)
- exception / timeout: backoff with 1.0s sleep
"""

import asyncio
import logging

from sentinel.src.monitor import (
    ChainMonitor,
    DriftMonitor,
    NodeSample,
    NodeState,
    calculate_one_way_drift,
)
from sentinel.src.rpc_client import RpcClient

logger = logging.getLogger("driftguard.sentinel")


def get_sleep_interval(delta: int) -> float:
    """
    Return adaptive cadence sleep duration based on drift delta:
    - delta == 0: 0.40s (in-sync)
    - delta >= 1: 0.10s (drift detected)
    """
    if delta == 0:
        return 0.40
    elif delta >= 1:
        return 0.10
    return 0.40


async def poll_node_block(rpc_client: RpcClient, url: str) -> int | None:
    """Query eth_blockNumber from an RPC endpoint."""
    sample = await rpc_client.probe(url, check_syncing=False, timeout=3.0)
    return sample.block_number


async def monitor_drift_cadence_loop(
    primary_url: str,
    reference_url: str,
    rpc_client: RpcClient | None = None,
    stop_event: asyncio.Event | None = None,
    callback=None,
):
    """
    Core monitoring loop querying eth_blockNumber with adaptive throttling:
    - delta == 0 (in-sync): sleep 0.40s
    - delta >= 1 (drift detected): sleep 0.10s
    - exception / timeout: sleep 1.0s
    """
    client = rpc_client or RpcClient(timeout=3.0)
    should_close = rpc_client is None

    try:
        while stop_event is None or not stop_event.is_set():
            sleep_time = 0.40
            try:
                p_head, r_head = await asyncio.gather(
                    poll_node_block(client, primary_url),
                    poll_node_block(client, reference_url),
                )
                if p_head is not None and r_head is not None:
                    delta = calculate_one_way_drift(r_head, p_head)
                    if delta == 0:
                        sleep_time = 0.40
                    elif delta >= 1:
                        sleep_time = 0.10
                    if callback:
                        res = callback(delta, p_head, r_head)
                        if asyncio.iscoroutine(res):
                            await res
                else:
                    sleep_time = 1.0
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Error querying eth_blockNumber: {e}")
                sleep_time = 1.0

            await asyncio.sleep(sleep_time)
    finally:
        if should_close:
            await client.close()


__all__ = [
    "ChainMonitor",
    "DriftMonitor",
    "NodeSample",
    "NodeState",
    "calculate_one_way_drift",
    "get_sleep_interval",
    "monitor_drift_cadence_loop",
    "poll_node_block",
]
