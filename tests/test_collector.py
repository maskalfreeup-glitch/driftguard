"""
Comprehensive tests for DriftGuard EVM Consensus Telemetry Collector & 24h Aggregator.
Validates:
- RPC probe client parsing (eth_blockNumber, eth_syncing, net_peerCount)
- Mock fallback logic for unreachable local/remote nodes
- HAProxy UNIX domain socket communication & drain latency measurement
- DatabaseManager transactional persistence & incident/MTTR lifecycle
- ReportAggregator 24h metrics (peak delta, trip count, MTTR, socket drain)
- ASCII Summary Card rendering
"""

import os
import socket
import tempfile
import threading
import time

import pytest

from collector import (
    DatabaseManager,
    HAProxySocketClient,
    RpcProbeClient,
)
from report_24h import ReportAggregator, SummaryCardRenderer, format_duration


class MockHAProxySocketServer:
    """Spins up a lightweight temporary UNIX domain socket simulating HAProxy 'show stat'."""

    def __init__(self, stat_csv: str):
        self.temp_dir = tempfile.mkdtemp()
        self.socket_path = os.path.join(self.temp_dir, "haproxy_test.sock")
        self.stat_csv = stat_csv
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind(self.socket_path)
        self.sock.listen(5)
        self._running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        while self._running:
            try:
                conn, _ = self.sock.accept()
                req = conn.recv(1024)
                if b"show stat" in req:
                    conn.sendall(self.stat_csv.encode("utf-8"))
                conn.close()
            except Exception:
                break

    def stop(self):
        self._running = False
        try:
            self.sock.close()
        except Exception:
            pass
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)


@pytest.fixture
def mock_haproxy_server():
    sample_csv = (
        "# pxname,svname,qcur,qmax,scur,smax,slim,stot,bin,bout,dreq,dresp,ereq,econ,eresp,wretr,wredis,status\n"
        "fe_eth_rpc,FRONTEND,0,0,15,50,4096,250000,100,200,0,0,0,0,0,0,0,OPEN\n"
        "be_arb,primary,0,0,12,40,2000,200000,80,160,0,0,0,0,0,0,0,UP\n"
        "be_arb,fallback,0,0,3,10,2000,50000,20,40,0,0,0,0,0,0,0,UP\n"
        "be_arb,BACKEND,0,0,15,50,4000,250000,100,200,0,0,0,0,0,0,0,UP\n"
        "be_nova,drain_srv,0,0,0,5,1000,10000,10,20,0,0,0,0,0,0,0,DRAIN\n"
    )
    srv = MockHAProxySocketServer(sample_csv)
    yield srv
    srv.stop()


def test_haproxy_socket_query_and_drain_latency(mock_haproxy_server):
    client = HAProxySocketClient(socket_path=mock_haproxy_server.socket_path)
    res = client.query_stats(mock_fallback=False)

    assert res["connected"] is True
    assert res["drain_latency_ms"] >= 0.0
    assert res["total_requests"] == 500000  # FRONTEND (250000) + BACKEND (250000)
    assert res["active_conns"] == 30
    assert res["draining_count"] == 1  # drain_srv is in DRAIN state

    stats = {f"{s['pxname']}/{s['svname']}": s for s in res["stats"]}
    assert stats["be_arb/primary"]["status"] == "UP"
    assert stats["be_arb/primary"]["stot"] == 200000
    assert stats["be_nova/drain_srv"]["is_draining"] == 1


def test_haproxy_socket_missing_graceful():
    client = HAProxySocketClient(socket_path="/nonexistent/haproxy.sock")
    res = client.query_stats(mock_fallback=False)
    assert res["connected"] is False
    assert res["drain_latency_ms"] == 0.0
    assert res["stats"] == []


def test_mock_fallback_on_unreachable_node():
    rpc = RpcProbeClient(timeout=0.5)
    # Using a non-routable port to guarantee immediate connection failure
    unreachable_url = "http://127.0.0.1:59999"

    # 1. Without mock fallback -> UNREACHABLE
    sample_real = rpc.probe("node1", "Node 1", unreachable_url, mock_fallback=False)
    assert sample_real["status"] == "UNREACHABLE"
    assert sample_real["block_number"] is None
    assert "error" in sample_real

    # 2. With mock fallback -> simulated healthy node
    sample_mock = rpc.probe("node1", "Node 1", unreachable_url, mock_fallback=True, canonical_block=514000000)
    assert sample_mock["status"] == "HEALTHY"
    assert sample_mock["block_number"] is not None
    assert sample_mock["block_number"] >= 513999990
    assert sample_mock["peer_count"] > 0
    assert sample_mock["drift_delta"] in (0, 1)


def test_database_manager_and_incident_mttr_lifecycle(tmp_path):
    db_file = str(tmp_path / "metrics.db")
    db = DatabaseManager(db_file)

    t0 = time.time()
    canon_block = 514000100

    # Probe 1: Node 1 is healthy (drift = 0)
    canonical_sample = {
        "node_id": "canonical",
        "node_name": "Canonical",
        "endpoint_url": "https://arb1.arbitrum.io/rpc",
        "block_number": canon_block,
        "is_syncing": False,
        "peer_count": None,
        "latency_ms": 50.0,
        "drift_delta": 0,
        "status": "HEALTHY",
        "error": None,
    }
    node1_healthy = {
        "node_id": "node1",
        "node_name": "Node 1",
        "endpoint_url": "http://127.0.0.1:8547",
        "block_number": canon_block,
        "is_syncing": False,
        "peer_count": 32,
        "latency_ms": 4.0,
        "drift_delta": 0,
        "status": "HEALTHY",
        "error": None,
    }
    ha_dummy = {
        "connected": True,
        "drain_latency_ms": 1.2,
        "total_requests": 1000,
        "active_conns": 5,
        "draining_count": 0,
        "stats": [],
    }

    p1 = db.record_probe(t0, canonical_sample, [node1_healthy], ha_dummy)
    assert p1 == 1

    # Verify no open incidents
    with db.get_connection() as conn:
        active = conn.execute("SELECT * FROM incidents WHERE recovered = 0").fetchall()
        assert len(active) == 0

    # Probe 2: Node 1 experiences consensus drift (drift = 5 blocks > 2 threshold)
    t1 = t0 + 15.0
    node1_tripped = dict(node1_healthy)
    node1_tripped["block_number"] = canon_block - 5
    node1_tripped["drift_delta"] = 5
    node1_tripped["status"] = "DRIFTING"

    p2 = db.record_probe(t1, canonical_sample, [node1_tripped], ha_dummy)
    assert p2 == 2

    # Verify incident opened
    with db.get_connection() as conn:
        active = conn.execute("SELECT * FROM incidents WHERE recovered = 0").fetchall()
        assert len(active) == 1
        assert active[0]["node_id"] == "node1"
        assert active[0]["peak_drift"] == 5

    # Probe 3: Node 1 recovers back to delta = 0
    t2 = t1 + 30.0  # 30 seconds outage duration
    node1_recovered = dict(node1_healthy)
    p3 = db.record_probe(t2, canonical_sample, [node1_recovered], ha_dummy)
    assert p3 == 3

    # Verify incident closed and MTTR recorded
    with db.get_connection() as conn:
        active = conn.execute("SELECT * FROM incidents WHERE recovered = 0").fetchall()
        assert len(active) == 0
        closed = conn.execute("SELECT * FROM incidents WHERE recovered = 1").fetchall()
        assert len(closed) == 1
        assert closed[0]["duration_seconds"] == 30.0


def test_24h_aggregation_and_ascii_card_output(tmp_path):
    db_file = str(tmp_path / "metrics.db")
    db = DatabaseManager(db_file)

    now = time.time()
    # Populate test data spanning multiple probes
    for i in range(5):
        ts = now - (60 - i * 15)
        canon = {
            "node_id": "canonical", "node_name": "Canonical", "endpoint_url": "https://arb1.arbitrum.io/rpc",
            "block_number": 514000000 + i, "is_syncing": False, "peer_count": None,
            "latency_ms": 45.0, "drift_delta": 0, "status": "HEALTHY", "error": None
        }
        # Inject one drift trip on cycle 2
        drift = 4 if i == 2 else 1
        st = "DRIFTING" if drift > 2 else "HEALTHY"
        n1 = {
            "node_id": "node1", "node_name": "Node 1", "endpoint_url": "http://127.0.0.1:8547",
            "block_number": 514000000 + i - drift, "is_syncing": False, "peer_count": 30,
            "latency_ms": 5.0, "drift_delta": drift, "status": st, "error": None
        }
        n2 = {
            "node_id": "node2", "node_name": "Node 2", "endpoint_url": "http://100.64.0.2:8547",
            "block_number": 514000000 + i - 1, "is_syncing": False, "peer_count": 28,
            "latency_ms": 10.0, "drift_delta": 1, "status": "HEALTHY", "error": None
        }
        ha = {
            "connected": True,
            "drain_latency_ms": 0.95,
            "total_requests": 100000 + i * 100,
            "active_conns": 10,
            "draining_count": 0,
            "stats": [
                {
                    "pxname": "be_arb",
                    "svname": "primary",
                    "status": "UP",
                    "scur": 8,
                    "qcur": 0,
                    "stot": 90000 + i * 90,
                    "is_draining": 0,
                },
                {
                    "pxname": "be_arb",
                    "svname": "fallback",
                    "status": "UP",
                    "scur": 2,
                    "qcur": 0,
                    "stot": 10000 + i * 10,
                    "is_draining": 0,
                },
            ],
        }
        db.record_probe(ts, canon, [n1, n2], ha)

    aggregator = ReportAggregator(db_file, window_seconds=86400)
    data = aggregator.aggregate()

    assert data["total_probes"] == 5
    assert data["peak_drift_delta"] == 4
    assert data["trip_samples_delta_gt_2"] == 1
    assert data["avg_socket_drain_latency_ms"] == 0.95
    assert data["consensus_sla_pct"] == 90.0  # 9 healthy out of 10 node samples
    assert data["nodes"]["node1"]["trips_gt_2"] == 1
    assert data["nodes"]["node2"]["trips_gt_2"] == 0

    # Test ASCII rendering
    card = SummaryCardRenderer.render_ascii_card(data)
    assert "DRIFTGUARD 24-HOUR TELEMETRY REPORT" in card
    assert "Peak Consensus Drift Delta" in card
    assert "4 blocks" in card
    assert "HAProxy Socket Drain Latency (avg)" in card
    assert "0.95 ms" in card
    assert "Node 1" in card
    assert "Node 2" in card
    assert "Canonical" in card
    assert "```" in card


def test_format_duration_helper():
    assert format_duration(15.4) == "15.4s"
    assert format_duration(95.0) == "1m 35s"
    assert format_duration(3665.0) == "1h 1m"
    assert format_duration(None) == "N/A"
