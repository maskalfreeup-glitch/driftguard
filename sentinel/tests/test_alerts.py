import json
from datetime import datetime
from unittest.mock import patch

import httpx
import pytest

from sentinel.alerts import DiscordAlerter
from sentinel.src.haproxy_client import get_backend_stats


@pytest.mark.asyncio
async def test_alert_dispatch_without_webhook_allocates_no_client():
    alerter = DiscordAlerter(webhook_url="")
    assert alerter._client is None
    assert await alerter.dispatch_embed("test", "test", 0, []) is False
    await alerter.close()


@pytest.mark.asyncio
async def test_dispatch_drift_alert_with_haproxy_stats_and_drain_latency():
    dispatched = []

    def mock_handler(request: httpx.Request):
        dispatched.append(json.loads(request.content))
        return httpx.Response(204)

    client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    alerter = DiscordAlerter(webhook_url="https://discord.com/api/webhooks/mock/drift", client=client)

    stats = {
        "total_requests": 14500,
        "current_in_flight": 12,
        "http_2xx": 14495,
        "http_5xx": 5,
    }

    res = await alerter.dispatch_drift_alert(
        chain_name="Arbitrum One",
        chain_id=42161,
        backend="be_arb",
        canonical_head=511900000,
        primary_head=511899986,
        delta_blocks=14,
        drain_latency_ms=123.85,
        backend_stats=stats,
        failover_action="Drained primary -> Fallback active",
    )

    assert res is True
    assert len(dispatched) == 1
    embed = dispatched[0]["embeds"][0]

    # Verify clean footer and ISO-8601 UTC timestamp format
    assert embed["footer"]["text"] == "DriftGuard High-Availability EVM Gateway"
    assert "timestamp" in embed
    ts = datetime.fromisoformat(embed["timestamp"])
    assert ts.tzinfo is not None

    field_map = {f["name"]: f["value"] for f in embed["fields"]}
    assert field_map["Chain Name"] == "Arbitrum One"
    assert field_map["Chain ID"] == "42161"
    assert field_map["Backend"] == "be_arb"
    assert field_map["Canonical Head"] == "#511900000"
    assert field_map["Primary Head"] == "#511899986"
    assert "14 blocks" in field_map["Delta Blocks"]
    assert "123.85 ms (POSIX Socket Drain)" in field_map["Socket Drain Latency"]
    assert "12 in-flight queries preserved (0 dropped)" in field_map["HAProxy Ingress Stats"]
    assert "0.00% dropped" in field_map["Error Rate & Packet Drops"]
    assert "primary: DRAIN (0%) -> fallback: ACTIVE (100%)" in field_map["Routing Transition"]

    await alerter.close()


@pytest.mark.asyncio
async def test_dispatch_consensus_recovered_with_mttr_and_catchup():
    dispatched = []

    def mock_handler(request: httpx.Request):
        dispatched.append(json.loads(request.content))
        return httpx.Response(204)

    client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    alerter = DiscordAlerter(webhook_url="https://discord.com/api/webhooks/mock/recovery", client=client)

    # Trip alert
    alerter._drift_tripped_at["be_arb"] = 1000.0
    alerter._tripped_blocks["be_arb"] = 6

    res = await alerter.send_consensus_recovered(
        chain_name="Arbitrum One",
        backend="be_arb",
        primary_weight_restored="Ready (100%)",
        force=True,
        drift_tripped_at=1000.0,
        now=1002.1,
        caught_up_blocks=6,
        protected_traffic="1,420 queries routed (0% dropped)",
    )

    assert res is True
    assert len(dispatched) == 1
    embed = dispatched[0]["embeds"][0]

    assert embed["footer"]["text"] == "DriftGuard High-Availability EVM Gateway"
    assert "timestamp" in embed
    ts = datetime.fromisoformat(embed["timestamp"])
    assert ts.tzinfo is not None

    field_map = {f["name"]: f["value"] for f in embed["fields"]}
    assert field_map["Chain Name"] == "Arbitrum One"
    assert field_map["Status"] == "Synced to Tip"
    assert field_map["Primary Weight Restored"] == "Ready (100%)"
    mttr_val = field_map.get("Time to Recovery (MTTR)") or field_map.get("Resolution Time (MTTR)")
    assert mttr_val == "2.1s (6 blocks caught up)"
    traffic_val = field_map.get("Traffic Summary") or field_map.get("Protected Traffic")
    assert "0%" in traffic_val

    await alerter.close()


@pytest.mark.asyncio
async def test_get_backend_stats_parser():
    mock_csv = (
        "# pxname,svname,qcur,qmax,scur,smax,slim,stot,bin,bout,dreq,dresp,ereq,econ,eresp,wretr,wredis,"
        "status,weight,act,bck,chkfail,chkdown,lastchg,downtime,qlimit,pid,iid,sid,throttle,lbtot,tracked,"
        "type,rate,rate_lim,rate_max,check_status,check_code,check_duration,hrsp_1xx,hrsp_2xx,hrsp_3xx,"
        "hrsp_4xx,hrsp_5xx,hrsp_other\n"
        "be_arb,primary,0,0,2,10,,500,100,200,,0,,0,0,0,0,UP,1,1,0,0,0,100,0,,1,5,1,,500,,2,0,,10,L7OK,200,30,0,"
        "498,0,2,0,0\n"
        "be_arb,fallback,0,0,1,5,,250,50,100,,0,,0,0,0,0,UP,1,1,0,0,0,100,0,,1,5,2,,250,,2,0,,5,L7OK,200,30,0,"
        "249,0,1,0,0\n"
        "be_arb,BACKEND,0,0,3,15,410,750,150,300,0,0,,0,0,0,0,UP,1,1,1,,0,100,0,,1,5,0,,750,,1,0,,15,,,,0,"
        "747,0,3,0,0\n"
    )

    with patch("os.path.exists", return_value=True):
        with patch("sentinel.src.haproxy_client.send_haproxy_command", return_value=mock_csv):
            stats = await get_backend_stats("be_arb", socket_path="/mock/admin.sock")

    assert stats["total_requests"] == 750
    assert stats["current_in_flight"] == 3
    assert stats["http_2xx"] == 747
    assert stats["http_5xx"] == 0


@pytest.mark.asyncio
async def test_trip_and_recovery_mttr_calculation():
    dispatched = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        dispatched.append(json.loads(request.content))
        return httpx.Response(204)

    client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    alerter = DiscordAlerter(webhook_url="https://discord.com/api/webhooks/mock/incident", client=client)

    # 1. Trip alert at t=1000.0 with 8 blocks drift
    await alerter.send_drift_tripped(
        chain_name="Arbitrum One",
        chain_id=42161,
        backend="be_arb",
        canonical_head=100,
        primary_head=92,
        delta_blocks=8,
        now=1000.0,
        force=True,
    )
    assert alerter.incident_start == 1000.0
    assert alerter.trip_delta_blocks == 8

    # 2. Recover at t=1003.4
    await alerter.send_consensus_recovered(
        chain_name="Arbitrum One",
        backend="be_arb",
        now=1003.4,
        force=True,
    )
    assert len(dispatched) == 2

    # Verify tripped embed footer
    trip_embed = dispatched[0]["embeds"][0]
    assert trip_embed["footer"] == {"text": "DriftGuard High-Availability EVM Gateway"}
    assert "timestamp" in trip_embed

    # Verify recovery embed fields and footer
    rec_embed = dispatched[1]["embeds"][0]
    assert rec_embed["footer"] == {"text": "DriftGuard High-Availability EVM Gateway"}
    assert "timestamp" in rec_embed

    fields = {f["name"]: f for f in rec_embed["fields"]}
    assert "Time to Recovery (MTTR)" in fields
    assert fields["Time to Recovery (MTTR)"]["value"] == "3.4s (8 blocks caught up)"
    assert fields["Time to Recovery (MTTR)"]["inline"] is True

    assert "Traffic Summary" in fields
    assert fields["Traffic Summary"]["value"] == "Preserved with 0% 5xx errors"
    assert fields["Traffic Summary"]["inline"] is True

    # Assert incident_start is reset
    assert alerter.incident_start is None

    await alerter.close()


@pytest.mark.asyncio
async def test_alert_titles_include_node_identifier():
    dispatched = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        dispatched.append(json.loads(request.content))
        return httpx.Response(204)

    client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))

    # Test with NODE_NAME set in env
    with patch.dict("os.environ", {"NODE_NAME": "dg-node1"}):
        alerter = DiscordAlerter(webhook_url="https://discord.com/api/webhooks/mock/node1", client=client)
        assert alerter.node_name == "dg-node1"

        await alerter.send_drift_tripped(
            chain_name="Arbitrum One",
            chain_id=42161,
            backend="be_arb",
            canonical_head=100,
            primary_head=90,
            delta_blocks=10,
            force=True,
        )
        assert dispatched[-1]["embeds"][0]["title"] == "🚨 Consensus Drift Tripped - Arbitrum One (dg-node1)"

        await alerter.send_consensus_recovered(
            chain_name="Arbitrum One",
            backend="be_arb",
            force=True,
        )
        assert dispatched[-1]["embeds"][0]["title"] == "✅ Consensus Recovered - Arbitrum One (dg-node1)"

    # Test payload builders with custom node_name override
    alerter_custom = DiscordAlerter(webhook_url="", node_name="custom-node")
    p_trip = alerter_custom.build_drift_tripped_payload(chain_name="Arbitrum Nova", node_name="dg-node2")
    assert p_trip["embeds"][0]["title"] == "🚨 Consensus Drift Tripped - Arbitrum Nova (dg-node2)"

    p_rec = alerter_custom.build_consensus_recovered_payload(chain_name="Arbitrum Nova", node_name="dg-node2")
    assert p_rec["embeds"][0]["title"] == "✅ Consensus Recovered - Arbitrum Nova (dg-node2)"

    # Test payload builder defaulting to self.node_name
    p_trip_def = alerter_custom.build_drift_tripped_payload(chain_name="Arbitrum Nova")
    assert p_trip_def["embeds"][0]["title"] == "🚨 Consensus Drift Tripped - Arbitrum Nova (custom-node)"

    p_rec_def = alerter_custom.build_consensus_recovered_payload(chain_name="Arbitrum Nova")
    assert p_rec_def["embeds"][0]["title"] == "✅ Consensus Recovered - Arbitrum Nova (custom-node)"

    # Test fallback to dg-node when env is empty and hostname fails
    with patch.dict("os.environ", {}, clear=True):
        with patch("socket.gethostname", side_effect=Exception("no hostname")):
            fallback_alerter = DiscordAlerter(webhook_url="")
            p_fb = fallback_alerter.build_drift_tripped_payload(chain_name="Arbitrum Sepolia")
            assert p_fb["embeds"][0]["title"] == "🚨 Consensus Drift Tripped - Arbitrum Sepolia (dg-node)"

    await client.aclose()


@pytest.mark.asyncio
async def test_routing_transition_reflects_node_role():
    alerter = DiscordAlerter(webhook_url="")

    # Primary node tripped -> drain primary, fallback active
    p_prim = alerter.build_drift_tripped_payload(node_role="primary")
    fields_prim = {f["name"]: f["value"] for f in p_prim["embeds"][0]["fields"]}
    assert fields_prim["Routing Transition"] == "primary: DRAIN (0%) -> fallback: ACTIVE (100%)"

    # Fallback node tripped -> drain fallback, primary active
    p_fall = alerter.build_drift_tripped_payload(node_role="fallback")
    fields_fall = {f["name"]: f["value"] for f in p_fall["embeds"][0]["fields"]}
    assert fields_fall["Routing Transition"] == "fallback: DRAIN (0%) -> primary: ACTIVE (100%)"

    # Backup alias tripped -> drain fallback, primary active
    p_back = alerter.build_drift_tripped_payload(node_role="backup")
    fields_back = {f["name"]: f["value"] for f in p_back["embeds"][0]["fields"]}
    assert fields_back["Routing Transition"] == "fallback: DRAIN (0%) -> primary: ACTIVE (100%)"
