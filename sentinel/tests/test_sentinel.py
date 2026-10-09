import time
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from sentinel.src.config import ChainConfig, Settings
from sentinel.src.main import _require_admin, settings
from sentinel.src.monitor import DriftMonitor
from sentinel.src.rpc_client import NodeSample
from sentinel.src.storage import StorageEngine

TEST_CHAIN = ChainConfig(
    name="test-chain", chain_id=11155111, backend="be_test",
    primary_url="https://primary.example", fallback_url="https://fallback.example",
    reference_url="https://reference.example",
)


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
    config = Settings(failure_threshold=2, recovery_threshold=2)
    storage = StorageEngine(redis_url="redis://invalid-host:6379/0", timeout=0.1)
    monitor = DriftMonitor(config=config, storage=storage, chains=[TEST_CHAIN])

    # Initial state is INITIALIZING
    assert monitor.primary.status == "INITIALIZING"

    sample = NodeSample(
        endpoint="http://mock", block_number=1000, is_syncing=False, latency_ms=45.0, error=None,
        timestamp=1000.0, chain_id=11155111
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
    config = Settings(failure_threshold=2, recovery_threshold=2)
    storage = StorageEngine(redis_url="redis://invalid-host:6379/0", timeout=0.1)
    monitor = DriftMonitor(config=config, storage=storage, chains=[TEST_CHAIN])
    monitor.primary.status = "HEALTHY"

    # Reference is 1010, target is 1000 -> drift is 10 (exceeds threshold 2)
    lagging_sample = NodeSample(
        endpoint="http://mock", block_number=1000, is_syncing=False, latency_ms=50.0, error=None,
        timestamp=1000.0, chain_id=11155111
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
async def test_drift_monitor_node_ahead_of_reference_is_not_penalized():
    config = Settings(failure_threshold=2, recovery_threshold=1)
    storage = StorageEngine(redis_url="redis://invalid-host:6379/0", timeout=0.1)
    monitor = DriftMonitor(config=config, storage=storage, chains=[TEST_CHAIN])
    monitor.primary.status = "HEALTHY"

    # Reference is 85283569, but node is at 85283581 (12 blocks ahead, negative delta)
    ahead_sample = NodeSample(
        endpoint="http://mock", block_number=85283581, is_syncing=False, latency_ms=40.0, error=None,
        timestamp=1000.0, chain_id=11155111
    )

    await monitor._evaluate_node(monitor.primary, ahead_sample, reference_block=85283569, timestamp=1000)
    assert monitor.primary.consecutive_failures == 0
    assert monitor.primary.consecutive_successes >= 1
    assert monitor.primary.status == "HEALTHY"
    assert monitor.primary.last_drift == 0
    assert monitor.primary.reason == "Healthy"


def test_calculate_one_way_drift():
    from sentinel.ha_guard import calculate_one_way_drift

    # Node is behind canonical reference -> positive drift
    assert calculate_one_way_drift(canonical_head=100, node_head=90) == 10
    assert calculate_one_way_drift(canonical_head=100, node_head=99) == 1

    # Node is ahead of canonical reference -> clamped to 0
    assert calculate_one_way_drift(canonical_head=100, node_head=110) == 0
    assert calculate_one_way_drift(canonical_head=85283569, node_head=85283581) == 0

    # Node is at same block -> 0
    assert calculate_one_way_drift(canonical_head=100, node_head=100) == 0

    # None values -> 0
    assert calculate_one_way_drift(canonical_head=None, node_head=100) == 0
    assert calculate_one_way_drift(canonical_head=100, node_head=None) == 0


@pytest.mark.asyncio
async def test_drift_monitor_syncing_node_rejected():
    config = Settings(failure_threshold=1)
    storage = StorageEngine(redis_url="redis://invalid-host:6379/0", timeout=0.1)
    monitor = DriftMonitor(config=config, storage=storage, chains=[TEST_CHAIN])

    syncing_sample = NodeSample(
        endpoint="http://mock", block_number=1000, is_syncing=True, latency_ms=25.0, error=None,
        timestamp=1000.0, chain_id=11155111
    )

    await monitor._evaluate_node(monitor.primary, syncing_sample, reference_block=1000, timestamp=1000)
    assert monitor.primary.status == "UNHEALTHY"
    assert "actively syncing" in monitor.primary.reason


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_reference_loss_fails_open_preserving_routing():
    config = Settings(failure_threshold=3, recovery_threshold=2)
    storage = StorageEngine(redis_url="redis://invalid-host:6379/0", timeout=0.1)
    monitor = DriftMonitor(config=config, storage=storage, chains=[TEST_CHAIN])
    monitor.primary.status = "HEALTHY"
    sample = NodeSample(
        endpoint="https://mock", block_number=1000, is_syncing=False, latency_ms=10.0,
        error=None, timestamp=1000.0, chain_id=TEST_CHAIN.chain_id,
    )

    await monitor._evaluate_node(monitor.primary, sample, reference_block=None, timestamp=1001)

    # Fail-Open principle: healthy node is preserved when reference is unavailable
    assert monitor.primary.status == "HEALTHY"
    assert monitor.primary.consecutive_failures == 0
    assert monitor.primary.last_drift == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("reference_chain_id,reference_time", [(1, None), (11155111, 1.0)])
async def test_poll_cycle_fails_open_and_freezes_routing_when_reference_untrusted(
    monkeypatch, reference_chain_id, reference_time
):
    config = Settings(failure_threshold=3, max_reference_age=2)
    storage = StorageEngine(redis_url="redis://invalid-host:6379/0", timeout=0.1)
    monitor = DriftMonitor(config=config, storage=storage, chains=[TEST_CHAIN])
    chain_monitor = monitor._default_chain
    chain_monitor.primary.status = "HEALTHY"
    chain_monitor.fallback.status = "HEALTHY"
    now = time.time()

    async def fake_probe(endpoint, check_syncing=True, timeout=None):
        is_reference = endpoint == TEST_CHAIN.reference_url
        return NodeSample(
            endpoint=endpoint,
            block_number=100,
            is_syncing=False,
            latency_ms=1.0,
            error=None,
            timestamp=(reference_time if reference_time is not None else now) if is_reference else now,
            chain_id=(reference_chain_id if is_reference else TEST_CHAIN.chain_id),
            syncing_checked=check_syncing,
        )

    monkeypatch.setattr(monitor.rpc_client, "probe", fake_probe)
    set_state = AsyncMock(return_value=True)
    monkeypatch.setattr("sentinel.src.monitor.set_server_state", set_state)
    mock_unavailable = AsyncMock(return_value=True)
    monkeypatch.setattr(monitor.alerter, "send_reference_unavailable", mock_unavailable)

    # Probe 1: single dropped sample does not immediately flap reference status
    await chain_monitor._poll_cycle()
    assert chain_monitor.reference.consecutive_failures == 1
    assert chain_monitor.reference.status != "DEGRADED"
    assert set_state.await_count == 0  # 0 drains

    # Probe 2: still debouncing
    await chain_monitor._poll_cycle()
    assert chain_monitor.reference.consecutive_failures == 2
    assert chain_monitor.reference.status != "DEGRADED"
    assert set_state.await_count == 0  # 0 drains

    # Probe 3: threshold reached (3 consecutive failed probes) -> DEGRADED
    await chain_monitor._poll_cycle()
    assert chain_monitor.reference.consecutive_failures == 3
    assert chain_monitor.reference.status == "DEGRADED"

    # Fail-Open Verification:
    # 1. Zero drain commands issued via HAProxy socket
    assert set_state.await_count == 0
    # 2. Serving pools are preserved
    assert chain_monitor.primary.status == "HEALTHY"
    assert chain_monitor.fallback.status == "HEALTHY"
    # 3. Warning alert emitted
    assert mock_unavailable.await_count == 1


@pytest.mark.asyncio
async def test_reference_hysteresis_recovery(monkeypatch):
    config = Settings(failure_threshold=3, max_reference_age=2)
    storage = StorageEngine(redis_url="redis://invalid-host:6379/0", timeout=0.1)
    monitor = DriftMonitor(config=config, storage=storage, chains=[TEST_CHAIN])
    chain_monitor = monitor._default_chain
    chain_monitor.reference.status = "DEGRADED"
    chain_monitor.reference_degraded = True
    chain_monitor.reference.consecutive_failures = 3
    now = time.time()

    async def healthy_probe(endpoint, check_syncing=True, timeout=None):
        return NodeSample(
            endpoint=endpoint,
            block_number=100,
            is_syncing=False,
            latency_ms=1.0,
            error=None,
            timestamp=now,
            chain_id=TEST_CHAIN.chain_id,
            syncing_checked=check_syncing,
        )

    monkeypatch.setattr(monitor.rpc_client, "probe", healthy_probe)
    mock_recovered = AsyncMock(return_value=True)
    monkeypatch.setattr(monitor.alerter, "send_reference_recovered", mock_recovered)

    # 1st healthy sample
    await chain_monitor._poll_cycle()
    assert chain_monitor.reference.consecutive_successes == 1
    assert chain_monitor.reference.status == "DEGRADED"

    # 2nd healthy sample
    await chain_monitor._poll_cycle()
    assert chain_monitor.reference.consecutive_successes == 2
    assert chain_monitor.reference.status == "DEGRADED"

    # 3rd healthy sample: recovers to HEALTHY
    await chain_monitor._poll_cycle()
    assert chain_monitor.reference.consecutive_successes == 3
    assert chain_monitor.reference.status == "HEALTHY"
    assert mock_recovered.await_count == 1


@pytest.mark.asyncio
async def test_wrong_chain_id_is_rejected():
    config = Settings(failure_threshold=1)
    storage = StorageEngine(redis_url="redis://invalid-host:6379/0", timeout=0.1)
    monitor = DriftMonitor(config=config, storage=storage, chains=[TEST_CHAIN])
    wrong_chain = NodeSample(
        endpoint="https://mock", block_number=1000, is_syncing=False, latency_ms=10.0,
        error=None, timestamp=1000.0, chain_id=1,
    )

    await monitor._evaluate_node(monitor.primary, wrong_chain, reference_block=1000, timestamp=1001)

    assert monitor.primary.status == "UNHEALTHY"
    assert "Wrong chain ID" in monitor.primary.reason


@pytest.mark.asyncio
async def test_missing_chain_id_is_rejected():
    config = Settings(failure_threshold=1)
    storage = StorageEngine(redis_url="redis://invalid-host:6379/0", timeout=0.1)
    monitor = DriftMonitor(config=config, storage=storage, chains=[TEST_CHAIN])
    missing_chain = NodeSample(
        endpoint="https://mock", block_number=1000, is_syncing=False, latency_ms=10.0,
        error=None, timestamp=1000.0, chain_id=None,
    )

    await monitor._evaluate_node(monitor.primary, missing_chain, reference_block=1000, timestamp=1001)

    assert monitor.primary.status == "UNHEALTHY"
    assert "Wrong chain ID" in monitor.primary.reason


def test_admin_routes_require_configured_bearer_token(monkeypatch):
    monkeypatch.setattr(settings, "admin_token", "test-only-token")

    with pytest.raises(HTTPException) as missing:
        _require_admin(None)
    assert missing.value.status_code == 404

    with pytest.raises(HTTPException) as wrong:
        _require_admin("Bearer incorrect")
    assert wrong.value.status_code == 404

    assert _require_admin("Bearer test-only-token") is None


def test_chain_configuration_requires_three_distinct_https_endpoints():
    with pytest.raises(ValueError):
        ChainConfig(name="bad", chain_id=1, backend="be_bad", primary_url="http://a",
                    fallback_url="https://b", reference_url="https://c")


@pytest.mark.asyncio
async def test_discord_alerter_empty_webhook_noop():
    from sentinel.alerts import DiscordAlerter
    alerter = DiscordAlerter(webhook_url="")
    # Should cleanly no-op and return False without making network calls
    assert await alerter.send_drift_tripped("Base", 8453, "be_base", 100, 90, 10) is False
    assert await alerter.send_consensus_recovered("Base", "be_base") is False
    await alerter.close()


@pytest.mark.asyncio
async def test_discord_alerter_embed_payload():
    import httpx

    from sentinel.alerts import COLOR_DRIFT_TRIPPED, COLOR_RECOVERED, DiscordAlerter

    dispatched = []

    def mock_handler(request: httpx.Request):

        import json
        dispatched.append(json.loads(request.content))
        return httpx.Response(204)

    transport = httpx.MockTransport(mock_handler)
    client = httpx.AsyncClient(transport=transport)
    alerter = DiscordAlerter(webhook_url="https://discord.com/api/webhooks/mock/test", client=client)

    # 1. Test Drift Tripped Embed
    res = await alerter.send_drift_tripped(
        chain_name="Base Mainnet",
        chain_id=8453,
        backend="be_base",
        canonical_head=2000,
        primary_head=1950,
        delta_blocks=50,
        failover_action="Drained primary -> Fallback active",
    )
    assert res is True
    assert len(dispatched) == 1
    embed = dispatched[0]["embeds"][0]
    assert embed["color"] == COLOR_DRIFT_TRIPPED  # 0xE02424
    assert "timestamp" in embed
    ts = datetime.fromisoformat(embed["timestamp"])
    assert ts.tzinfo is not None
    assert embed["footer"]["text"] == "DriftGuard High-Availability EVM Gateway"
    field_names = [f["name"] for f in embed["fields"]]
    assert "Chain Name" in field_names
    assert "Chain ID" in field_names
    assert "Backend" in field_names
    assert "Canonical Head" in field_names
    assert "Primary Head" in field_names
    assert "Delta Blocks" in field_names
    assert "Socket Drain Latency" in field_names
    assert "HAProxy Ingress Stats" in field_names
    assert "Error Rate & Packet Drops" in field_names
    assert "Routing Transition" in field_names

    # 2. Test Cooldown / Debounce suppression
    res_dup = await alerter.send_drift_tripped(
        chain_name="Base Mainnet",
        chain_id=8453,
        backend="be_base",
        canonical_head=2000,
        primary_head=1950,
        delta_blocks=50,
    )
    assert res_dup is False  # Suppressed due to debounce
    assert len(dispatched) == 1

    # 3. Test Recovery Embed
    res_rec = await alerter.send_consensus_recovered(
        chain_name="Base Mainnet",
        backend="be_base",
        primary_weight_restored="Ready (100%)",
        force=True,
    )
    assert res_rec is True
    assert len(dispatched) == 2
    rec_embed = dispatched[1]["embeds"][0]
    assert rec_embed["color"] == COLOR_RECOVERED  # 0x31C48D
    assert "timestamp" in rec_embed
    rec_ts = datetime.fromisoformat(rec_embed["timestamp"])
    assert rec_ts.tzinfo is not None
    assert rec_embed["footer"]["text"] == "DriftGuard High-Availability EVM Gateway"
    rec_fields = {f["name"]: f["value"] for f in rec_embed["fields"]}
    assert rec_fields["Chain Name"] == "Base Mainnet"
    assert rec_fields["Status"] == "Synced to Tip"
    assert rec_fields["Primary Weight Restored"] == "Ready (100%)"
    assert "Time to Recovery (MTTR)" in rec_fields or "Resolution Time (MTTR)" in rec_fields
    assert "Traffic Summary" in rec_fields or "Protected Traffic" in rec_fields

    await alerter.close()


@pytest.mark.asyncio
async def test_multi_chain_monitor_loads_all_chains():
    from sentinel.src.config import load_chains_config
    chains = load_chains_config("sentinel/config/chains.yaml")
    assert len(chains) >= 3
    backends = {c.backend for c in chains}
    assert "be_arb" in backends

    config = Settings(drift_threshold=2)
    storage = StorageEngine(redis_url="redis://invalid-host:6379/0", timeout=0.1)
    monitor = DriftMonitor(config=config, storage=storage, chains=chains)
    unique = monitor.unique_monitors()
    assert len(unique) == len(chains)
    assert "arbitrum-one" in unique


def test_chains_config_poll_interval_sub_250ms():
    from sentinel.src.config import load_chains_config
    chains = load_chains_config("sentinel/config/chains.yaml")
    for chain in chains:
        assert chain.poll_interval == 0.2, (
            f"{chain.name} poll_interval should be 0.2s (200ms), got {chain.poll_interval}"
        )


def test_anchor_environment_variable_overrides(monkeypatch):
    from sentinel.src.config import load_chains_config

    monkeypatch.setenv("ANCHOR_ARB_ONE", "https://custom-alchemy-one.example/v2/secret-key")
    monkeypatch.setenv("ANCHOR_ARB_NOVA", "https://custom-drpc-nova.example/secret-key")
    monkeypatch.setenv("ANCHOR_ARB_SEPOLIA", "https://custom-alchemy-sepolia.example/v2/secret-key")

    chains = load_chains_config("sentinel/config/chains.yaml")
    chain_map = {c.name: c for c in chains}

    assert chain_map["arbitrum-one"].reference_url == "https://custom-alchemy-one.example/v2/secret-key"
    assert chain_map["arbitrum-nova"].reference_url == "https://custom-drpc-nova.example/secret-key"
    assert chain_map["arbitrum-sepolia"].reference_url == "https://custom-alchemy-sepolia.example/v2/secret-key"


def test_anchor_environment_variable_fallback_when_unset(monkeypatch):
    from sentinel.src.config import load_chains_config

    monkeypatch.delenv("ANCHOR_ARB_ONE", raising=False)
    monkeypatch.delenv("ANCHOR_ARB_NOVA", raising=False)
    monkeypatch.delenv("ANCHOR_ARB_SEPOLIA", raising=False)

    chains = load_chains_config("sentinel/config/chains.yaml")
    chain_map = {c.name: c for c in chains}

    assert chain_map["arbitrum-one"].reference_url == "https://arbitrum.gateway.tenderly.co"
    assert chain_map["arbitrum-nova"].reference_url == "https://arbitrum-nova.drpc.org"
    assert chain_map["arbitrum-sepolia"].reference_url == "https://arbitrum-sepolia.drpc.org"


@pytest.mark.asyncio
async def test_arbitrum_nova_enforces_fail_open_on_reference_failure(monkeypatch):
    from sentinel.src.config import load_chains_config
    chains = load_chains_config("sentinel/config/chains.yaml")
    nova_config = next(c for c in chains if c.name == "arbitrum-nova")
    assert nova_config.fail_open is True

    config = Settings(failure_threshold=2, recovery_threshold=2)
    storage = StorageEngine(redis_url="redis://invalid-host:6379/0", timeout=0.1)
    monitor = DriftMonitor(config=config, storage=storage, chains=[nova_config])
    nova_monitor = monitor.unique_monitors()["arbitrum-nova"]
    nova_monitor.primary.status = "HEALTHY"
    nova_monitor.fallback.status = "HEALTHY"

    # Simulate reference provider failing / rate limiting (returns HTTP 429 / error)
    async def mock_probe_reference(url, fallback_urls=None, timeout=5.0):
        return NodeSample(
            endpoint=url,
            block_number=None,
            is_syncing=False,
            latency_ms=500.0,
            error="HTTP 429 Too Many Requests (Rate limit exceeded)",
            timestamp=time.time(),
        )

    async def mock_probe(endpoint, check_syncing=True, timeout=None):
        return NodeSample(
            endpoint=endpoint,
            block_number=85282920,
            is_syncing=False,
            latency_ms=10.0,
            error=None,
            timestamp=time.time(),
            chain_id=42170,
        )

    monkeypatch.setattr(nova_monitor.rpc_client, "probe_reference", mock_probe_reference)
    monkeypatch.setattr(nova_monitor.rpc_client, "probe", mock_probe)
    set_state = AsyncMock(return_value=True)
    monkeypatch.setattr("sentinel.src.monitor.set_server_state", set_state)
    mock_unavailable = AsyncMock(return_value=True)
    monkeypatch.setattr(nova_monitor.alerter, "send_reference_unavailable", mock_unavailable)

    # Execute multiple poll cycles while reference is rate-limited
    for _ in range(5):
        await nova_monitor._poll_cycle()

    # Fail-Open Assertions:
    # 1. HAProxy drain command was NEVER called (0 drains)
    assert set_state.await_count == 0
    # 2. Serving nodes remained HEALTHY and routing intact
    assert nova_monitor.primary.status == "HEALTHY"
    assert nova_monitor.fallback.status == "HEALTHY"
    # 3. Serving nodes were not penalized with consecutive failures
    assert nova_monitor.primary.consecutive_failures == 0
    assert nova_monitor.fallback.consecutive_failures == 0
