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
    assert field_map["Resolution Time (MTTR)"] == "2.1s (6 blocks caught up)"
    assert field_map["Protected Traffic"] == "1,420 queries routed (0% dropped)"

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
