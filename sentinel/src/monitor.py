import asyncio
import logging
import time
from typing import Dict, Any, Optional
from prometheus_client import Gauge, Counter

from .config import Settings
from .rpc_client import RpcClient, NodeSample
from .storage import StorageEngine

logger = logging.getLogger("driftguard.monitor")

# Prometheus Metrics Definitions
METRIC_BLOCK_HEIGHT = Gauge("driftguard_block_height", "Current block height observed", ["node"])
METRIC_DRIFT = Gauge("driftguard_drift_blocks", "Drift in blocks relative to canonical reference", ["node"])
METRIC_LATENCY = Gauge("driftguard_latency_seconds", "RPC response latency in seconds", ["node"])
METRIC_STATUS = Gauge("driftguard_node_healthy", "Node health status (1 for healthy, 0 for unhealthy)", ["node"])
METRIC_POLL_COUNT = Counter("driftguard_polls_total", "Total poll cycles executed")
METRIC_FAILOVERS = Counter("driftguard_circuit_trips_total", "Total circuit breaker trips to unhealthy", ["node"])

class NodeState:
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url
        self.status = "INITIALIZING"
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.last_sample: Optional[NodeSample] = None
        self.last_drift = 0
        self.reason = "Initializing"

class DriftMonitor:
    def __init__(self, config: Settings, storage: StorageEngine):
        self.config = config
        self.storage = storage
        self.rpc_client = RpcClient(timeout=config.rpc_timeout)
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

        self.primary = NodeState("primary", config.primary_rpc_url)
        self.backup = NodeState("backup", config.backup_rpc_url)
        self.canonical = NodeState("canonical", config.canonical_rpc_url)

    async def start(self):
        self.is_running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(
            f"DriftMonitor initialized. Polling interval: {self.config.poll_interval}s, "
            f"Drift threshold: {self.config.drift_threshold} blocks"
        )

    async def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self.rpc_client.close()
        logger.info("DriftMonitor stopped.")

    async def _poll_loop(self):
        # Initial slight delay to allow services to stabilize
        await asyncio.sleep(0.5)

        while self.is_running:
            try:
                await self._poll_cycle()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Unexpected error in monitor cycle: {e}", exc_info=True)

            await asyncio.sleep(self.config.poll_interval)

    async def _poll_cycle(self):
        METRIC_POLL_COUNT.inc()

        # Concurrent probe to all 3 endpoints
        p_res, b_res, c_res = await asyncio.gather(
            self.rpc_client.probe(self.primary.url),
            self.rpc_client.probe(self.backup.url),
            self.rpc_client.probe(self.canonical.url),
            return_exceptions=True
        )

        now = int(time.time())

        # Process Canonical Sample
        if isinstance(c_res, NodeSample):
            self.canonical.last_sample = c_res
            if c_res.block_number is not None:
                self.canonical.status = "HEALTHY"
                METRIC_BLOCK_HEIGHT.labels(node="canonical").set(c_res.block_number)
                METRIC_LATENCY.labels(node="canonical").set(c_res.latency_ms / 1000.0)
            else:
                self.canonical.status = "DEGRADED"
                logger.warning(f"Canonical RPC warning: {c_res.error}")
        else:
            self.canonical.status = "DEGRADED"
            logger.warning(f"Canonical RPC exception: {c_res}")

        ref_block = self.canonical.last_sample.block_number if self.canonical.last_sample else None

        # Evaluate Primary and Backup nodes
        await self._evaluate_node(self.primary, p_res, ref_block, now)
        await self._evaluate_node(self.backup, b_res, ref_block, now)

        # Log concise status summary
        p_info = f"b:{self.primary.last_sample.block_number} d:{self.primary.last_drift} {self.primary.last_sample.latency_ms}ms" if self.primary.last_sample and self.primary.last_sample.block_number else f"err:{self.primary.reason}"
        b_info = f"b:{self.backup.last_sample.block_number} d:{self.backup.last_drift} {self.backup.last_sample.latency_ms}ms" if self.backup.last_sample and self.backup.last_sample.block_number else f"err:{self.backup.reason}"
        c_info = f"b:{ref_block}" if ref_block else "unavailable"

        logger.info(
            f"[Cycle] Primary: [{self.primary.status}] ({p_info}) | "
            f"Backup: [{self.backup.status}] ({b_info}) | Ref: ({c_info})"
        )

    async def _evaluate_node(
        self,
        node: NodeState,
        sample_or_exc: Any,
        reference_block: Optional[int],
        timestamp: int
    ):
        if not isinstance(sample_or_exc, NodeSample):
            sample = NodeSample(
                endpoint=node.url,
                block_number=None,
                is_syncing=False,
                latency_ms=0.0,
                error=f"Internal exception: {sample_or_exc}",
                timestamp=timestamp
            )
        else:
            sample = sample_or_exc

        node.last_sample = sample
        is_faulty = False
        reason = "OK"
        drift = 0

        if sample.error or sample.block_number is None:
            is_faulty = True
            reason = f"Unreachable: {sample.error}"
        elif sample.is_syncing:
            is_faulty = True
            reason = "Node is actively syncing"
        elif reference_block is not None:
            # Positive drift: reference is ahead of target (target lagging)
            drift = reference_block - sample.block_number
            node.last_drift = drift
            if abs(drift) > self.config.drift_threshold:
                is_faulty = True
                reason = f"Drift threshold exceeded: {drift} blocks (threshold: {self.config.drift_threshold})"
        else:
            # If reference is unavailable, check if block exists
            node.last_drift = 0

        # Update Metrics
        if sample.block_number is not None:
            METRIC_BLOCK_HEIGHT.labels(node=node.name).set(sample.block_number)
            METRIC_LATENCY.labels(node=node.name).set(sample.latency_ms / 1000.0)
            METRIC_DRIFT.labels(node=node.name).set(drift)

        # Circuit Breaker / Hysteresis Logic
        if is_faulty:
            node.consecutive_failures += 1
            node.consecutive_successes = 0
            node.reason = reason
            if node.consecutive_failures >= self.config.failure_threshold:
                if node.status != "UNHEALTHY":
                    METRIC_FAILOVERS.labels(node=node.name).inc()
                    logger.warning(
                        f"\033[91m[ALERT] Node '{node.name}' transitioned to UNHEALTHY! "
                        f"Failures: {node.consecutive_failures}, Reason: {reason}\033[0m"
                    )
                node.status = "UNHEALTHY"
        else:
            node.consecutive_successes += 1
            node.consecutive_failures = 0
            node.reason = "Healthy"
            if node.consecutive_successes >= self.config.recovery_threshold:
                if node.status != "HEALTHY":
                    logger.info(
                        f"\033[92m[RECOVERY] Node '{node.name}' restored to HEALTHY! "
                        f"Successes: {node.consecutive_successes}\033[0m"
                    )
                node.status = "HEALTHY"

        METRIC_STATUS.labels(node=node.name).set(1 if node.status == "HEALTHY" else 0)

        # Store Telemetry in Redis & In-Memory cache
        telemetry = {
            "timestamp": timestamp,
            "node": node.name,
            "status": node.status,
            "block_number": sample.block_number,
            "reference_block": reference_block,
            "drift": drift,
            "latency_ms": sample.latency_ms,
            "is_syncing": sample.is_syncing,
            "reason": node.reason,
            "consecutive_failures": node.consecutive_failures,
            "consecutive_successes": node.consecutive_successes
        }

        await self.storage.set_health(node.name, telemetry)
        await self.storage.push_history(node.name, telemetry)
