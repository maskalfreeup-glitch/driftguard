import asyncio
import logging
import time
from typing import Any

from prometheus_client import Counter, Gauge

from sentinel.alerts import DiscordAlerter

from .config import ChainConfig, Settings, load_chains_config
from .haproxy_client import get_backend_stats, set_server_state
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
        self.current_haproxy_state: str | None = None


class ChainMonitor:
    """
    Dedicated, isolated monitor loop for a single EVM chain.
    Runs concurrently in its own asyncio Task so network latency on one chain
    never degrades monitoring on another.
    """

    def __init__(
        self,
        chain: ChainConfig,
        rpc_client: RpcClient,
        storage: StorageEngine,
        alerter: DiscordAlerter,
        socket_path: str,
        failure_threshold: int = 2,
        recovery_threshold: int = 2,
        max_reference_age: float = 10.0,
    ):
        self.chain = chain
        self.rpc_client = rpc_client
        self.storage = storage
        self.alerter = alerter
        self.socket_path = socket_path
        self.failure_threshold = failure_threshold
        self.recovery_threshold = recovery_threshold
        self.max_reference_age = max_reference_age

        self.primary = NodeState(f"{chain.backend}:primary", chain.primary_url)
        self.fallback = NodeState(f"{chain.backend}:fallback", chain.fallback_url)
        self.reference = NodeState(f"{chain.backend}:reference", chain.reference_url)
        self.reference.consecutive_failures = 0
        self.reference.consecutive_successes = 0
        self.reference_failure_threshold = 3
        self.reference_recovery_threshold = 3
        self.reference_degraded = False

        self.is_running = False
        self._task: asyncio.Task | None = None

        # Chaos / Failover drill simulation states
        self.simulated_drift: int | None = None
        self.simulated_fault: str | None = None
        self.simulated_node = "primary"
        self.incident_start: float | None = None
        self.trip_delta_blocks: int = 0

    @property
    def is_fail_open(self) -> bool:
        return (
            getattr(self.chain, "fail_open", False)
            or self.chain.name == "arbitrum-nova"
            or self.chain.backend == "be_nova"
        )

    async def start(self):
        self.is_running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(
            f"ChainMonitor[{self.chain.name}] initialized. Interval: {self.chain.poll_interval}s, "
            f"Drift threshold: {self.chain.drift_threshold} blocks, Backend: {self.chain.backend}"
        )

    async def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"ChainMonitor[{self.chain.name}] stopped.")

    async def _poll_loop(self):
        await asyncio.sleep(0.5)
        while self.is_running:
            try:
                await self._poll_cycle()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[{self.chain.name}] Error in chain monitor cycle: {e}", exc_info=True)

            await asyncio.sleep(self.chain.poll_interval)

    async def _poll_cycle(self):
        METRIC_POLL_COUNT.inc()
        now = int(time.time())

        # Concurrently probe primary, fallback, and reference (with fallbacks and 5s timeout)
        fallback_refs = getattr(self.chain, "reference_fallback_urls", [])
        p_res, f_res, r_res = await asyncio.gather(
            self.rpc_client.probe(self.chain.primary_url),
            self.rpc_client.probe(self.chain.fallback_url),
            self.rpc_client.probe_reference(
                self.chain.reference_url,
                fallback_urls=fallback_refs,
                timeout=5.0,
            ),
            return_exceptions=True,
        )

        reference_valid = (
            isinstance(r_res, NodeSample)
            and r_res.error is None
            and r_res.block_number is not None
            and r_res.chain_id == self.chain.chain_id
            and not r_res.is_syncing
            and 0 <= (time.time() - r_res.timestamp) <= self.max_reference_age
        )
        self.reference.last_sample = r_res if isinstance(r_res, NodeSample) else None

        if reference_valid:
            self.reference.consecutive_successes += 1
            self.reference.consecutive_failures = 0
            if self.reference.consecutive_successes >= self.reference_recovery_threshold:
                was_degraded = self.reference_degraded or self.reference.status == "DEGRADED"
                self.reference.status = "HEALTHY"
                self.reference.reason = "Healthy"
                if was_degraded:
                    self.reference_degraded = False
                    logger.info(
                        f"\033[92m[REFERENCE RECOVERED] [{self.chain.name}] Canonical reference restored to HEALTHY "
                        f"after {self.reference.consecutive_successes} consecutive successful probes.\033[0m"
                    )
                    await self.alerter.send_reference_recovered(
                        self.chain.name, self.chain.chain_id, self.chain.backend
                    )
        else:
            self.reference.consecutive_failures += 1
            self.reference.consecutive_successes = 0
            if isinstance(r_res, NodeSample) and r_res.error:
                err_msg = r_res.error
            elif not isinstance(r_res, NodeSample):
                err_msg = f"Exception: {r_res}"
            else:
                err_msg = "Invalid block height or chain ID"

            if self.reference.consecutive_failures >= self.reference_failure_threshold:
                should_alert = not self.reference_degraded
                self.reference.status = "DEGRADED"
                self.reference_degraded = True
                self.reference.reason = (
                    f"Canonical reference degraded ({self.reference.consecutive_failures} failures: {err_msg})"
                )
                if should_alert:
                    logger.warning(
                        f"\033[93m[FAIL-OPEN ACTIVE] [{self.chain.name}] Canonical reference degraded "
                        f"({self.reference.consecutive_failures} failures). "
                        f"Freezing routing state and preserving serving pools with 0 drains.\033[0m"
                    )
                    await self.alerter.send_reference_unavailable(
                        self.chain.name, self.chain.chain_id, self.chain.backend,
                        f"Canonical Reference Degraded (Fail-Open Active: Routing Frozen, 0 Drains) - {err_msg}",
                    )

        # FAIL-OPEN PRINCIPLE:
        # If canonical reference is not valid OR reference status is DEGRADED:
        # DO NOT drain serving nodes. FREEZE HAProxy routing state. Preserve backend traffic.
        if not reference_valid or self.reference.status != "HEALTHY":
            await self._evaluate_node_fail_open(self.primary, p_res, now)
            await self._evaluate_node_fail_open(self.fallback, f_res, now)
            return

        reference_head = r_res.block_number
        await self._evaluate_node(self.primary, p_res, reference_head, now)
        await self._evaluate_node(self.fallback, f_res, reference_head, now)

    async def _evaluate_node_fail_open(self, node: NodeState, sample_or_exc: Any, timestamp: int):
        """
        Fail-Open Evaluator:
        When reference is untrusted or degraded:
        - Freezes routing state (no HAProxy socket drain commands issued).
        - Records node reachability and block height telemetry.
        - Does NOT increment consecutive failures or trigger circuit trips.
        """
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
        if sample.block_number is not None:
            METRIC_BLOCK_HEIGHT.labels(node=node.name).set(sample.block_number)
            METRIC_LATENCY.labels(node=node.name).set(sample.latency_ms / 1000.0)
        METRIC_DRIFT.labels(node=node.name).set(0)
        METRIC_STATUS.labels(node=node.name).set(1 if node.status == "HEALTHY" else 0)

        telemetry = {
            "timestamp": timestamp,
            "chain": self.chain.name,
            "chain_id": self.chain.chain_id,
            "backend": self.chain.backend,
            "node": node.name,
            "status": node.status,
            "block_number": sample.block_number,
            "reference_block": None,
            "drift": 0,
            "latency_ms": sample.latency_ms,
            "is_syncing": sample.is_syncing,
            "syncing_checked": sample.syncing_checked,
            "reason": "Fail-Open Active (Routing Frozen)",
            "consecutive_failures": node.consecutive_failures,
            "consecutive_successes": node.consecutive_successes,
        }

        role = "primary" if node is self.primary else "fallback"
        await self.storage.set_health(f"{self.chain.backend}:{role}", telemetry)
        await self.storage.set_health(f"{self.chain.name}:{role}", telemetry)
        await self.storage.push_history(f"{self.chain.backend}:{role}", telemetry)

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

        simulated = node is (self.primary if self.simulated_node == "primary" else self.fallback)
        if simulated and self.simulated_drift is not None:
            drift = self.simulated_drift
            node.last_drift = drift
            if abs(drift) > self.chain.drift_threshold:
                is_faulty = True
                reason = f"Simulated drift anomaly: {drift} blocks (threshold: {self.chain.drift_threshold})"
        elif simulated and self.simulated_fault is not None:
            is_faulty = True
            reason = f"Simulated fault: {self.simulated_fault}"
        elif sample.error or sample.block_number is None:
            is_faulty = True
            reason = f"Unreachable: {sample.error}"
        elif sample.is_syncing:
            is_faulty = True
            reason = "Node is actively syncing"
        elif sample.chain_id != self.chain.chain_id:
            is_faulty = True
            reason = f"Wrong chain ID: got {sample.chain_id}, expected {self.chain.chain_id}"
        elif reference_block is not None:
            drift = reference_block - sample.block_number
            node.last_drift = drift
            if abs(drift) > self.chain.drift_threshold:
                is_faulty = True
                reason = f"Drift threshold exceeded: {drift} blocks (threshold: {self.chain.drift_threshold})"
        else:
            # Reference block unavailable: fail open, do not mark node faulty
            is_faulty = False
            drift = 0
            node.last_drift = 0

        # Update Metrics

        if sample.block_number is not None:
            METRIC_BLOCK_HEIGHT.labels(node=node.name).set(sample.block_number)
            METRIC_LATENCY.labels(node=node.name).set(sample.latency_ms / 1000.0)
            METRIC_DRIFT.labels(node=node.name).set(drift)

        # Circuit Breaker & Failover Logic
        if is_faulty:
            node.consecutive_failures += 1
            node.consecutive_successes = 0
            node.reason = reason
            if node.consecutive_failures >= self.failure_threshold:
                cutover_latency_ms = None
                if node.current_haproxy_state != "maint":
                    server = "primary" if node is self.primary else "fallback"
                    peer_node = self.fallback if node is self.primary else self.primary
                    # Minimum-Healthy Guardrail: refuse to drain if peer is already in maint
                    if peer_node.current_haproxy_state == "maint":
                        logger.error(
                            f"[FAIL-OPEN GUARDRAIL] Refusing to drain {self.chain.backend}/{server}: "
                            f"peer {peer_node.name} is already in maint. Preserving routing."
                        )
                    else:
                        t0 = time.perf_counter()
                        drained = await set_server_state(self.socket_path, self.chain.backend, server, "maint")
                        cutover_latency_ms = (time.perf_counter() - t0) * 1000.0
                        if drained:
                            node.current_haproxy_state = "maint"

                backend_stats = await get_backend_stats(self.chain.backend, socket_path=self.socket_path)

                if node.status != "UNHEALTHY":
                    METRIC_FAILOVERS.labels(node=node.name).inc()
                    logger.warning(
                        f"\033[91m[ALERT] [{self.chain.name}] Node '{node.name}' transitioned to UNHEALTHY! "
                        f"Failures: {node.consecutive_failures}, Reason: {reason}\033[0m"
                    )
                    self.incident_start = time.time()
                    self.trip_delta_blocks = drift
                    # Dispatch Discord incident embed with live HAProxy traffic stats & drain latency
                    await self.alerter.send_drift_tripped(
                        chain_name=self.chain.name,
                        chain_id=self.chain.chain_id,
                        backend=self.chain.backend,
                        canonical_head=reference_block,
                        primary_head=sample.block_number,
                        delta_blocks=drift,
                        node_role="primary" if node is self.primary else "fallback",
                        drain_latency_ms=cutover_latency_ms,
                        backend_stats=backend_stats,
                    )
                node.status = "UNHEALTHY"
        else:
            node.consecutive_successes += 1
            node.consecutive_failures = 0
            node.reason = "Healthy"
            if node.consecutive_successes >= self.recovery_threshold:
                if node.status != "HEALTHY":
                    logger.info(
                        f"\033[92m[RECOVERY] [{self.chain.name}] Node '{node.name}' restored to HEALTHY! "
                        f"Successes: {node.consecutive_successes}\033[0m"
                    )
                    # Dispatch Discord recovery embed
                    await self.alerter.send_consensus_recovered(
                        chain_name=self.chain.name,
                        backend=self.chain.backend,
                        drift_tripped_at=self.incident_start,
                        caught_up_blocks=self.trip_delta_blocks,
                    )
                    self.incident_start = None
                    self.trip_delta_blocks = 0
                node.status = "HEALTHY"
                if node.current_haproxy_state != "ready":
                    server = "primary" if node is self.primary else "fallback"
                    if await set_server_state(self.socket_path, self.chain.backend, server, "ready"):
                        node.current_haproxy_state = "ready"

        METRIC_STATUS.labels(node=node.name).set(1 if node.status == "HEALTHY" else 0)

        # Store Telemetry in Storage
        telemetry = {
            "timestamp": timestamp,
            "chain": self.chain.name,
            "chain_id": self.chain.chain_id,
            "backend": self.chain.backend,
            "node": node.name,
            "status": node.status,
            "block_number": sample.block_number,
            "reference_block": reference_block,
            "drift": drift,
            "latency_ms": sample.latency_ms,
            "is_syncing": sample.is_syncing,
            "syncing_checked": sample.syncing_checked,
            "reason": node.reason,
            "consecutive_failures": node.consecutive_failures,
            "consecutive_successes": node.consecutive_successes,
        }

        role = "primary" if node is self.primary else "fallback"
        await self.storage.set_health(f"{self.chain.backend}:{role}", telemetry)
        await self.storage.set_health(f"{self.chain.name}:{role}", telemetry)
        await self.storage.push_history(f"{self.chain.backend}:{role}", telemetry)

    async def simulate_fault(self, drift: int | None = None, fault: str | None = None,
                             node_name: str = "primary"):
        if node_name not in {"primary", "backup"}:
            raise ValueError("node must be primary or backup")
        target = self.primary if node_name == "primary" else self.fallback
        server = node_name if node_name == "primary" else "fallback"
        self.simulated_drift = drift
        self.simulated_fault = fault
        self.simulated_node = node_name
        if (drift is not None and abs(drift) > self.chain.drift_threshold) or fault is not None:
            target.consecutive_failures = self.failure_threshold
            target.consecutive_successes = 0
            target.status = "UNHEALTHY"
            target.last_drift = drift if drift is not None else 0
            target.reason = (
                f"Simulated drift anomaly: {drift} blocks" if drift is not None else f"Simulated fault: {fault}"
            )
            # Immediate HAProxy cutover for < 0.5s chaos drills
            if await set_server_state(self.socket_path, self.chain.backend, server, "maint"):
                target.current_haproxy_state = "maint"
            self.incident_start = time.time()
            self.trip_delta_blocks = drift or 0
            await self.alerter.send_drift_tripped(
                chain_name=self.chain.name,
                chain_id=self.chain.chain_id,
                backend=self.chain.backend,
                canonical_head=(target.last_sample.block_number + drift)
                if (target.last_sample and target.last_sample.block_number and drift is not None)
                else None,
                primary_head=target.last_sample.block_number if target.last_sample else None,
                delta_blocks=drift or 0,
                node_role=node_name,
            )

    async def reset_faults(self):
        self.simulated_drift = None
        self.simulated_fault = None
        self.simulated_node = "primary"
        for node, server in ((self.primary, "primary"), (self.fallback, "fallback")):
            node.status = "INITIALIZING"
            node.consecutive_failures = 0
            node.consecutive_successes = 0
            node.reason = "Awaiting live health probes"
            if await set_server_state(self.socket_path, self.chain.backend, server, "ready"):
                node.current_haproxy_state = "ready"
        await self.alerter.send_consensus_recovered(
            chain_name=self.chain.name,
            backend=self.chain.backend,
            drift_tripped_at=self.incident_start,
            caught_up_blocks=self.trip_delta_blocks,
        )
        self.incident_start = None
        self.trip_delta_blocks = 0


class DriftMonitor:
    """
    Fleet controller managing independent ChainMonitor tasks across all EVM networks.
    """

    def __init__(self, config: Settings, storage: StorageEngine, chains: list[ChainConfig] | None = None):
        self.config = config
        self.storage = storage
        self.rpc_client = RpcClient(timeout=config.rpc_timeout)
        self.alerter = DiscordAlerter(webhook_url=config.discord_webhook_url)
        self.is_running = False

        self.chain_configs = chains if chains is not None else load_chains_config(config.chains_config_path)
        self.chains: dict[str, ChainMonitor] = {}

        for cc in self.chain_configs:
            if cc.name in self.chains or cc.backend in self.chains:
                raise ValueError("chain names and backend names must not collide")
            chain_mon = ChainMonitor(
                chain=cc,
                rpc_client=self.rpc_client,
                storage=self.storage,
                alerter=self.alerter,
                socket_path=self.config.haproxy_socket_path,
                failure_threshold=self.config.failure_threshold,
                recovery_threshold=self.config.recovery_threshold,
                max_reference_age=self.config.max_reference_age,
            )
            self.chains[cc.name] = chain_mon
            self.chains[cc.backend] = chain_mon

        # Backwards-compatibility aliases for legacy tests and status endpoints
        default_chain = self.chains.get("base-mainnet") or next(iter(self.chains.values()))
        default_chain.failure_threshold = config.failure_threshold
        default_chain.recovery_threshold = config.recovery_threshold
        self._default_chain = default_chain
        self.primary = default_chain.primary
        self.backup = default_chain.fallback
        self.simulated_drift = {"primary": None, "backup": None}
        self.simulated_status = {"primary": None, "backup": None}

    @property
    def is_healthy(self) -> bool:
        return bool(self.unique_monitors()) and any(
            mon.reference.status in ("HEALTHY", "DEGRADED", "INITIALIZING")
            and (mon.primary.status == "HEALTHY" or mon.fallback.status == "HEALTHY")
            for mon in self.unique_monitors().values()
        )

    async def start(self):
        self.is_running = True
        for mon in self.unique_monitors().values():
            await mon.start()
        logger.info(f"DriftMonitor initialized with {len(self.unique_monitors())} active chain tasks.")

    async def stop(self):
        self.is_running = False
        for mon in self.unique_monitors().values():
            await mon.stop()
        await self.rpc_client.close()
        await self.alerter.close()
        logger.info("DriftMonitor stopped.")

    def unique_monitors(self) -> dict[str, ChainMonitor]:
        return {cc.name: self.chains[cc.name] for cc in self.chain_configs if cc.name in self.chains}

    async def _evaluate_node(self, node: NodeState, sample_or_exc: Any, reference_block: int | None, timestamp: int):
        """Backwards compatibility delegator for existing tests."""
        await self._default_chain._evaluate_node(node, sample_or_exc, reference_block, timestamp)

    async def simulate_fault(
        self,
        node: str = "primary",
        drift: int | None = None,
        fault: str | None = None,
        chain: str | None = None,
        backend: str | None = None,
    ):
        target_chain = self._resolve_chain(chain, backend)
        await target_chain.simulate_fault(
            drift=drift, fault=fault, node_name="primary" if node == "primary" else "backup"
        )

    async def reset_faults(self, chain: str | None = None, backend: str | None = None):

        if chain or backend:
            target = self._resolve_chain(chain, backend)
            await target.reset_faults()
        else:
            await asyncio.gather(*(mon.reset_faults() for mon in self.unique_monitors().values()))

    def _resolve_chain(self, chain: str | None = None, backend: str | None = None) -> ChainMonitor:
        by_backend = self.chains.get(backend) if backend else None
        by_name = self.chains.get(chain) if chain else None
        if by_backend and by_name and by_backend is not by_name:
            raise ValueError("chain and backend identify different networks")
        resolved = by_backend or by_name
        if resolved:
            return resolved
        if backend or chain:
            raise ValueError("Unknown chain or backend")
        return self.chains.get("be_base") or self._default_chain
