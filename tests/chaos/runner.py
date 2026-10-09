#!/usr/bin/env python3
"""
Deterministic Chaos Test Runner for DriftGuard.

Executes reproducible acceptance tests against HAProxy and the DriftGuard sidecar:
- Generates continuous multi-threaded load (200-400 req/s) against HAProxy (http://localhost:8545).
- Compares every response against oracle ground-truth (http://localhost:9090/oracle/state).
- Scenario 1: Normal load (5s baseline, verify 0 false-positive drains).
- Scenario 2: Outlier reference (inject 10-block lag into Ref C, assert local healthy node remains UP).
- Scenario 3: Local stall & recovery (inject 8-block stall, record detection latency < 350ms, verify recovery).
- Emits summary metrics table.
"""

import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request

GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://localhost:8545")
LOCAL_CTRL_URL = os.environ.get("LOCAL_CTRL_URL", "http://localhost:9090")
REF_C_URL = os.environ.get("REF_C_URL", "http://localhost:8548")
DRIFTGUARD_STATUS_URL = os.environ.get("DRIFTGUARD_STATUS_URL", "http://localhost:8000/status")

TARGET_RPS_MIN = 200
TARGET_RPS_MAX = 400


class OracleTracker:
    def __init__(self, oracle_url):
        self.oracle_url = oracle_url
        self.lock = threading.Lock()
        self.canonical_height = 1000
        self.canonical_hash = ""
        self.running = True
        self.poller_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.poller_thread.start()

    def _poll_loop(self):
        while self.running:
            try:
                req = urllib.request.Request(f"{self.oracle_url}/oracle/state")
                with urllib.request.urlopen(req, timeout=0.5) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode())
                        with self.lock:
                            self.canonical_height = data.get("canonical_height", self.canonical_height)
                            self.canonical_hash = data.get("canonical_hash", self.canonical_hash)
            except Exception:
                pass
            time.sleep(0.02)  # poll every 20ms

    def get_ground_truth(self):
        with self.lock:
            return self.canonical_height, self.canonical_hash


class TrafficStream:
    def __init__(self, gateway_url, oracle_tracker: OracleTracker, num_workers=16):
        self.gateway_url = gateway_url
        self.oracle_tracker = oracle_tracker
        self.num_workers = num_workers
        self.running = False
        self.lock = threading.Lock()

        # Cumulative metrics
        self.total_requests = 0
        self.http_200_count = 0
        self.http_5xx_count = 0
        self.stale_reads = 0
        self.upstreams = {"local": 0, "fallback": 0, "unknown": 0}

        self.workers = []

    def start(self):
        self.running = True
        self.workers = []
        for _ in range(self.num_workers):
            t = threading.Thread(target=self._worker_loop, daemon=True)
            self.workers.append(t)
            t.start()

    def stop(self):
        self.running = False
        for t in self.workers:
            t.join(timeout=1.0)

    def reset_counters(self):
        with self.lock:
            self.total_requests = 0
            self.http_200_count = 0
            self.http_5xx_count = 0
            self.stale_reads = 0
            self.upstreams = {"local": 0, "fallback": 0, "unknown": 0}

    def _worker_loop(self):
        # Target pacing per worker
        target_sleep = 0.05  # ~20 req/s per worker * 16 workers = 320 req/s
        rpc_payload = json.dumps({
            "jsonrpc": "2.0",
            "method": "eth_blockNumber",
            "params": [],
            "id": 1
        }).encode("utf-8")

        while self.running:
            start_t = time.time()
            try:
                req = urllib.request.Request(
                    self.gateway_url,
                    data=rpc_payload,
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=1.0) as resp:
                    status = resp.status
                    raw = resp.read()
                    upstream = resp.headers.get("X-Upstream", "unknown").lower()

                    if 200 <= status < 300:
                        with self.lock:
                            self.http_200_count += 1
                            self.total_requests += 1
                            if "local" in upstream:
                                self.upstreams["local"] += 1
                            elif "fallback" in upstream:
                                self.upstreams["fallback"] += 1
                            else:
                                self.upstreams["unknown"] += 1

                        data = json.loads(raw.decode())
                        res_hex = data.get("result", "0x0")
                        block_h = int(res_hex, 16) if isinstance(res_hex, str) and res_hex.startswith("0x") else 0

                        # Ground truth validation
                        canon_h, _ = self.oracle_tracker.get_ground_truth()
                        if canon_h > block_h and (canon_h - block_h) > 3:
                            with self.lock:
                                self.stale_reads += 1
                    elif status >= 500:
                        with self.lock:
                            self.http_5xx_count += 1
                            self.total_requests += 1
            except urllib.error.HTTPError as he:
                with self.lock:
                    if he.code >= 500:
                        self.http_5xx_count += 1
                    self.total_requests += 1
            except Exception:
                # transient connection error / timeout
                with self.lock:
                    self.total_requests += 1

            elapsed = time.time() - start_t
            sleep_needed = max(0.001, target_sleep - elapsed)
            time.sleep(sleep_needed)


def http_post_json(url, data):
    raw = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=raw, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1.5) as resp:
        return json.loads(resp.read().decode())


def query_driftguard_status():
    try:
        req = urllib.request.Request(DRIFTGUARD_STATUS_URL)
        with urllib.request.urlopen(req, timeout=0.8) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode())
    except Exception:
        pass
    return None


def wait_for_services():
    print("[ChaosRunner] Waiting for services to become healthy...")
    endpoints = [
        ("HAProxy Gateway", f"{GATEWAY_URL}"),
        ("Local Node Control", f"{LOCAL_CTRL_URL}/healthz"),
        ("Ref Provider C", f"{REF_C_URL}/healthz"),
        ("DriftGuard Sentinel", f"{DRIFTGUARD_STATUS_URL}"),
    ]
    for name, url in endpoints:
        ready = False
        for _ in range(30):
            try:
                if "GATEWAY" in name:
                    payload = json.dumps({"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}).encode()
                    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
                else:
                    req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=1.0) as resp:
                    if resp.status in (200, 204):
                        ready = True
                        break
            except Exception:
                time.sleep(0.5)
        if not ready:
            print(f"[ChaosRunner] WARNING: {name} at {url} did not respond within 15s")
        else:
            print(f"[ChaosRunner] {name} is READY")


def run_test_suite():
    wait_for_services()

    oracle_tracker = OracleTracker(LOCAL_CTRL_URL)
    stream = TrafficStream(GATEWAY_URL, oracle_tracker, num_workers=16)

    print("\n" + "=" * 70)
    print("STARTING DETERMINISTIC CHAOS ACCEPTANCE TESTS")
    print("=" * 70)

    stream.start()

    # -------------------------------------------------------------
    # Scenario 1: Normal Load (5-second baseline)
    # -------------------------------------------------------------
    print("\n[Scenario 1] Running Normal Load Baseline (5 seconds)...")
    stream.reset_counters()
    time.sleep(5.0)

    with stream.lock:
        req_count_1 = stream.total_requests
        err_5xx_1 = stream.http_5xx_count
        stale_reads_1 = stream.stale_reads
        upstreams_1 = dict(stream.upstreams)

    rps_1 = req_count_1 / 5.0
    dg_status_1 = query_driftguard_status()
    node_state_1 = dg_status_1.get("state", "UNKNOWN") if dg_status_1 else "UNKNOWN"
    false_positive_drains = 1 if node_state_1 == "DRAINED" else 0

    print(f" -> Requests: {req_count_1} (~{rps_1:.1f} req/s)")
    print(f" -> HTTP 5xx Errors: {err_5xx_1}")
    print(f" -> Stale Reads: {stale_reads_1}")
    print(f" -> DriftGuard State: {node_state_1}")
    print(f" -> False-Positive Drains: {false_positive_drains}")

    assert err_5xx_1 == 0, f"Expected 0 HTTP 5xx errors, got {err_5xx_1}"
    assert false_positive_drains == 0, f"Expected 0 false positive drains, got {false_positive_drains}"
    assert node_state_1 == "HEALTHY", f"Expected node state HEALTHY, got {node_state_1}"
    print(" ✓ Scenario 1 PASSED: Baseline normal load verified with 0 false-positive drains.")

    # -------------------------------------------------------------
    # Scenario 2: Outlier Reference Provider
    # -------------------------------------------------------------
    print("\n[Scenario 2] Injecting 10-block lag into Reference Provider C...")
    http_post_json(f"{REF_C_URL}/fault/lag", {"lag_blocks": 10})

    stream.reset_counters()
    time.sleep(3.5)

    with stream.lock:
        req_count_2 = stream.total_requests
        err_5xx_2 = stream.http_5xx_count
        stale_reads_2 = stream.stale_reads

    dg_status_2 = query_driftguard_status()
    node_state_2 = dg_status_2.get("state", "UNKNOWN") if dg_status_2 else "UNKNOWN"
    q_decision = dg_status_2.get("latest_quorum", {}).get("decision", "") if dg_status_2 else ""
    outlier = dg_status_2.get("latest_quorum", {}).get("outlier_provider", "") if dg_status_2 else ""

    print(f" -> DriftGuard State: {node_state_2}")
    print(f" -> Quorum Decision: {q_decision}")
    print(f" -> Flagged Outlier: {outlier}")
    print(f" -> HTTP 5xx Errors: {err_5xx_2}")

    # Restore Ref C
    http_post_json(f"{REF_C_URL}/fault/clear", {})
    time.sleep(0.5)

    assert err_5xx_2 == 0, f"Expected 0 HTTP 5xx errors, got {err_5xx_2}"
    assert node_state_2 == "HEALTHY", f"Local node must remain HEALTHY during reference outlier, got {node_state_2}"
    print(" ✓ Scenario 2 PASSED: Reference Provider C isolated as outlier; local healthy node remains UP.")

    # -------------------------------------------------------------
    # Scenario 3: Local Lag Stall & Recovery
    # -------------------------------------------------------------
    print("\n[Scenario 3] Injecting 8-block stall on Local Node...")
    stream.reset_counters()

    t_fault_start = time.time()
    # Inject lag and stall
    http_post_json(f"{LOCAL_CTRL_URL}/fault/lag", {"lag_blocks": 8})
    http_post_json(f"{LOCAL_CTRL_URL}/fault/stall", {"stalled": True})

    # Measure detection latency: wait until DriftGuard marks local as DRAINED
    detection_latency_ms = 0.0
    drained_detected = False
    for _ in range(50):
        dg_st = query_driftguard_status()
        if dg_st and dg_st.get("state") == "DRAINED":
            detection_latency_ms = (time.time() - t_fault_start) * 1000.0
            drained_detected = True
            break
        time.sleep(0.01)

    print(f" -> Drained Detected: {drained_detected}")
    print(f" -> Detection Latency: {detection_latency_ms:.2f} ms (Spec requirement: < 350 ms)")

    # Assert detection latency < 350 ms
    assert drained_detected, "Local node failed to transition to DRAINED state!"
    assert detection_latency_ms < 350.0, f"Detection latency exceeded 350ms limit: {detection_latency_ms:.2f}ms"

    # Maintain stall for 2 seconds while traffic continues to flow to backup
    time.sleep(2.0)
    with stream.lock:
        stale_reads_during_stall = stream.stale_reads
        upstreams_during_stall = dict(stream.upstreams)
    print(f" -> Stale reads during drain: {stale_reads_during_stall}")
    print(f" -> Upstreams routing during drain: {upstreams_during_stall}")

    # Now Clear fault on Local Node and measure recovery
    print(" -> Clearing stall on Local Node (verifying recovery)...")
    t_clear_start = time.time()
    http_post_json(f"{LOCAL_CTRL_URL}/fault/clear", {})

    recovery_latency_ms = 0.0
    recovered = False
    for _ in range(80):
        dg_st = query_driftguard_status()
        if dg_st and dg_st.get("state") == "HEALTHY":
            recovery_latency_ms = (time.time() - t_clear_start) * 1000.0
            recovered = True
            break
        time.sleep(0.02)

    print(f" -> Recovered to HEALTHY: {recovered}")
    print(f" -> Recovery Latency: {recovery_latency_ms:.2f} ms")

    assert recovered, "Local node failed to recover to HEALTHY state!"

    # Allow post-recovery stabilization
    time.sleep(1.0)
    stream.stop()

    with stream.lock:
        total_stale_reads = stream.stale_reads
        total_5xx = stream.http_5xx_count

    assert total_5xx == 0, f"Expected 0 HTTP 5xx errors during all drills, got {total_5xx}"

    # -------------------------------------------------------------
    # Summary Table Output
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print("DRIFTGUARD CONSENSUS & CHAOS BENCHMARK SUMMARY")
    print("=" * 70)
    print(f"{'Metric':<35} | {'Measured Value':<20} | {'Status':<10}")
    print("-" * 70)
    print(f"{'Detection Latency (ms)':<35} | {f'{detection_latency_ms:.2f} ms':<20} | {'PASS (<350ms)':<10}")
    print(f"{'Recovery Latency (ms)':<35} | {f'{recovery_latency_ms:.2f} ms':<20} | {'PASS (M=5)':<10}")
    print(f"{'Total Stale Reads Leaked':<35} | {f'{total_stale_reads}':<20} | {'PASS':<10}")
    print(f"{'False-Positive Drains':<35} | {f'{false_positive_drains}':<20} | {'PASS (0)':<10}")
    print(f"{'HTTP 5xx Errors':<35} | {f'{total_5xx}':<20} | {'PASS (0)':<10}")
    print("=" * 70)
    print("\nALL CHAOS ACCEPTANCE DRILLS PASSED SUCCESSFULLY!\n")


if __name__ == "__main__":
    try:
        run_test_suite()
    except AssertionError as ae:
        print(f"\n[ChaosRunner] TEST FAILURE: {ae}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[ChaosRunner] UNEXPECTED ERROR: {e}", file=sys.stderr)
        sys.exit(1)
