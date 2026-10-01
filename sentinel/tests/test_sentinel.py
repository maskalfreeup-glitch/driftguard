import pytest

from sentinel.src.config import Settings
from sentinel.src.monitor import DriftMonitor
from sentinel.src.rpc_client import NodeSample
from sentinel.src.storage import StorageEngine


@pytest.mark.asyncio
async def test_storage_engine_in_memory_fallback():
    # Invalid redis URL to test resilient in-memory fallback
    storage = StorageEngine(redis_url="redis://invalid-host:6379/0", timeout=0.1)
    await storage.connect()

    data = {"status": "HEALTHY", "block": 100, "drift": 0}
    await storage.set_health("primary", data)

    cached = await storage.get_health("primary")
    assert cached is not None
    assert cached["status"] == "HEALTHY"
    assert cached["block"] == 100

    await storage.push_history("primary", data)
    history = await storage.get_history("primary")
    assert len(history) == 1
    assert history[0]["block"] == 100


@pytest.mark.asyncio
async def test_drift_monitor_healthy_evaluation():
    config = Settings(drift_threshold=2, failure_threshold=2, recovery_threshold=2)
    storage = StorageEngine(redis_url="redis://invalid-host:6379/0", timeout=0.1)
    monitor = DriftMonitor(config=config, storage=storage)

    # Initial state is INITIALIZING
    assert monitor.primary.status == "INITIALIZING"

    sample = NodeSample(
        endpoint="http://mock", block_number=1000, is_syncing=False, latency_ms=45.0, error=None, timestamp=1000.0
    )

    # 1st success
    await monitor._evaluate_node(monitor.primary, sample, reference_block=1001, timestamp=1000)
    assert monitor.primary.consecutive_successes == 1
    # Needs 2 successes to turn HEALTHY
    assert monitor.primary.status == "INITIALIZING"

    # 2nd success
    await monitor._evaluate_node(monitor.primary, sample, reference_block=1001, timestamp=1001)
    assert monitor.primary.consecutive_successes == 2
    assert monitor.primary.status == "HEALTHY"
    assert monitor.primary.last_drift == 1


@pytest.mark.asyncio
async def test_drift_monitor_drift_exceeded_trips_circuit():
    config = Settings(drift_threshold=2, failure_threshold=2, recovery_threshold=2)
    storage = StorageEngine(redis_url="redis://invalid-host:6379/0", timeout=0.1)
    monitor = DriftMonitor(config=config, storage=storage)
    monitor.primary.status = "HEALTHY"

    # Reference is 1010, target is 1000 -> drift is 10 (exceeds threshold 2)
    lagging_sample = NodeSample(
        endpoint="http://mock", block_number=1000, is_syncing=False, latency_ms=50.0, error=None, timestamp=1000.0
    )

    # 1st failure
    await monitor._evaluate_node(monitor.primary, lagging_sample, reference_block=1010, timestamp=1000)
    assert monitor.primary.consecutive_failures == 1
    assert monitor.primary.status == "HEALTHY"  # Hysteresis: not UNHEALTHY yet

    # 2nd failure
    await monitor._evaluate_node(monitor.primary, lagging_sample, reference_block=1010, timestamp=1001)
    assert monitor.primary.consecutive_failures == 2
    assert monitor.primary.status == "UNHEALTHY"
    assert "Drift threshold exceeded" in monitor.primary.reason


@pytest.mark.asyncio
async def test_drift_monitor_syncing_node_rejected():
    config = Settings(drift_threshold=2, failure_threshold=1)
    storage = StorageEngine(redis_url="redis://invalid-host:6379/0", timeout=0.1)
    monitor = DriftMonitor(config=config, storage=storage)

    syncing_sample = NodeSample(
        endpoint="http://mock", block_number=1000, is_syncing=True, latency_ms=25.0, error=None, timestamp=1000.0
    )

    await monitor._evaluate_node(monitor.primary, syncing_sample, reference_block=1000, timestamp=1000)
    assert monitor.primary.status == "UNHEALTHY"
    assert "actively syncing" in monitor.primary.reason
