import asyncio
import logging
import time
from typing import Any

from prometheus_client import Counter, Gauge

from .config import Settings
from .rpc_client import NodeSample, RpcClient
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
        self.last_sample: NodeSample | None = None
        self.last_drift = 0
        self.reason = "Initializing"


class DriftMonitor:
    def __init__(self, config: Settings, storage: StorageEngine):
        self.config = config
        self.storage = storage
        self.rpc_client = RpcClient(timeout=config.rpc_timeout)
        self.is_running = False
        self._task: asyncio.Task | None = None

        self.primary = NodeState("primary", config.primary_rpc_url)
        self.backup = NodeState("backup", config.backup_rpc_url)
        self.canonical = NodeState("canonical", config.canonical_rpc_url)

        # Chaos / Failover drill simulation states
        self.simulated_drift: dict[str, int | None] = {"primary": None, "backup": None}
        self.simulated_status: dict[str, str | None] = {"primary": None, "backup": None}

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

    def simulate_fault(self, node: str, drift: int | None = None, fault: str | None = None):
        if drift is not None:
            self.simulated_drift[node] = drift
        if fault is not None:
            self.simulated_status[node] = fault

        target = self.primary if node == "primary" else self.backup
        if (drift is not None and abs(drift) > self.config.drift_threshold) or fault is not None:
            target.consecutive_failures = self.config.failure_threshold
            target.consecutive_successes = 0
            target.status = "UNHEALTHY"
            target.last_drift = drift if drift is not None else 0
            target.reason = (
                f"Simulated drift anomaly: {drift} blocks" if drift is not None else f"Simulated fault: {fault}"
            )

    def reset_faults(self):
        self.simulated_drift = {"primary": None, "backup": None}
        self.simulated_status = {"primary": None, "backup": None}
        for target in (self.primary, self.backup):
            target.status = "INITIALIZING"
            target.consecutive_failures = 0
            target.consecutive_successes = 0
            target.reason = "Awaiting live health samples"

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
            return_exceptions=True,
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

        ref_sample = self.canonical.last_sample
        max_reference_age = max(2 * self.config.poll_interval + self.config.rpc_timeout, 5.0)
        reference_is_fresh = bool(
            self.canonical.status == "HEALTHY"
            and ref_sample
            and ref_sample.block_number is not None
            and now - ref_sample.timestamp <= max_reference_age
            and (ref_sample.chain_id is None or ref_sample.chain_id == self.config.expected_chain_id)
        )
        ref_block = ref_sample.block_number if reference_is_fresh and ref_sample else None

        # Evaluate Primary and Backup nodes
        await self._evaluate_node(self.primary, p_res, ref_block, now)
        await self._evaluate_node(self.backup, b_res, ref_block, now)

        # Log concise status summary
        if self.primary.last_sample and self.primary.last_sample.block_number:
            p_info = (
                f"b:{self.primary.last_sample.block_number} "
                f"d:{self.primary.last_drift} "
                f"{self.primary.last_sample.latency_ms}ms"
            )
        else:
            p_info = f"err:{self.primary.reason}"

        if self.backup.last_sample and self.backup.last_sample.block_number:
            b_info = (
                f"b:{self.backup.last_sample.block_number} "
                f"d:{self.backup.last_drift} "
                f"{self.backup.last_sample.latency_ms}ms"
            )
        else:
            b_info = f"err:{self.backup.reason}"

        c_info = f"b:{ref_block}" if ref_block else "unavailable"

        logger.info(
            f"[Cycle] Primary: [{self.primary.status}] ({p_info}) | "
            f"Backup: [{self.backup.status}] ({b_info}) | Ref: ({c_info})"
        )

    async def _evaluate_node(self, node: NodeState, sample_or_exc: Any, reference_block: int | None, timestamp: int):
        if not isinstance(sample_or_exc, NodeSample):
            sample = NodeSample(
                endpoint=node.url,
                block_number=None,
                is_syncing=False,
                latency_ms=0.0,
                error=f"Internal exception: {sample_or_exc}",
                timestamp=timestamp,
            )
        else:
            sample = sample_or_exc

        node.last_sample = sample
        is_faulty = False
        reason = "OK"
        drift = 0

        sim_drift = self.simulated_drift.get(node.name)
        sim_status = self.simulated_status.get(node.name)

        if sim_drift is not None:
            drift = sim_drift
            node.last_drift = drift
            if abs(drift) > self.config.drift_threshold:
                is_faulty = True
                reason = f"Simulated drift anomaly: {drift} blocks (threshold: {self.config.drift_threshold})"
        elif sim_status is not None:
            is_faulty = True
            reason = f"Simulated fault: {sim_status}"
        elif sample.error or sample.block_number is None:
            is_faulty = True
            reason = f"Unreachable: {sample.error}"
        elif sample.chain_id is not None and sample.chain_id != self.config.expected_chain_id:
            is_faulty = True
            reason = (f"Wrong chain ID: got {sample.chain_id}, "
                      f"expected {self.config.expected_chain_id}")
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
            is_faulty = True
            reason = "Canonical reference unavailable or stale"
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
            "consecutive_successes": node.consecutive_successes,
        }

        await self.storage.set_health(node.name, telemetry)
        await self.storage.push_history(node.name, telemetry)
