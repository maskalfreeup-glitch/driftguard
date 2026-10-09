#!/usr/bin/env python3
"""
Deterministic Mock EVM Node for DriftGuard Acceptance & Chaos Testing.

Features:
- Deterministic block progression on background ticker (default: 250ms for Arbitrum Nitro).
- Cryptographic hash chaining: hash = sha256(height:parentHash:forkId).
- Standard JSON-RPC 2.0 endpoints: eth_blockNumber, eth_getBlockByNumber, eth_chainId, eth_syncing.
- REST fault injection API:
  - POST /fault/lag   {"lag_blocks": N}
  - POST /fault/stall {"stalled": true}
  - POST /fault/diverge {"fork_id": "..."}
  - POST /fault/clear
- Ground truth oracle endpoint: GET /oracle/state
"""

import argparse
import hashlib
import json
import socket
import sys
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn


class MockNodeLedger:
    def __init__(self, initial_height=1000, block_time_ms=250, chain_id="0xa4b1"):
        self.lock = threading.Lock()
        self.block_time_ms = block_time_ms
        self.chain_id = chain_id

        # Canonical ledger state
        self.canonical_height = initial_height
        self.block_cache = {}  # (height, fork_id) -> (hash, parent_hash)

        # Precompute initial history up to initial_height
        self._precompute_genesis(initial_height)

        # Fault state
        self.lag_blocks = 0
        self.stalled = False
        self.stall_height = initial_height
        self.fork_id = "canonical"

        # Background ticker
        self.running = True
        self.ticker_thread = threading.Thread(target=self._ticker_loop, daemon=True)
        self.ticker_thread.start()

    def _hash_for_block(self, height, parent_hash, fork_id):
        raw = f"{height}:{parent_hash}:{fork_id}".encode("utf-8")
        return "0x" + hashlib.sha256(raw).hexdigest()

    def _precompute_genesis(self, height):
        zero_parent = "0x" + "0" * 64
        curr_parent = zero_parent
        for h in range(1, height + 1):
            b_hash = self._hash_for_block(h, curr_parent, "canonical")
            self.block_cache[(h, "canonical")] = (b_hash, curr_parent)
            curr_parent = b_hash

    def get_block(self, height, fork_id="canonical"):
        with self.lock:
            return self._get_or_compute_block(height, fork_id)

    def _get_or_compute_block(self, height, fork_id):
        if height <= 0:
            zero_parent = "0x" + "0" * 64
            zero_hash = "0x" + "0" * 64
            return zero_hash, zero_parent

        key = (height, fork_id)
        if key in self.block_cache:
            return self.block_cache[key]

        # Compute parent hash recursively
        parent_hash, _ = self._get_or_compute_block(height - 1, fork_id)
        b_hash = self._hash_for_block(height, parent_hash, fork_id)
        self.block_cache[key] = (b_hash, parent_hash)
        return b_hash, parent_hash

    def _ticker_loop(self):
        interval = self.block_time_ms / 1000.0
        while self.running:
            time.sleep(interval)
            with self.lock:
                self.canonical_height += 1
                # Ensure canonical block computed
                self._get_or_compute_block(self.canonical_height, "canonical")
                # Also compute divergent block if currently diverging
                if self.fork_id != "canonical":
                    self._get_or_compute_block(self.canonical_height, self.fork_id)

    def get_visible_height(self):
        with self.lock:
            if self.stalled:
                return self.stall_height
            vis = max(1, self.canonical_height - self.lag_blocks)
            return vis

    def get_visible_tip(self):
        with self.lock:
            vis_h = self.stall_height if self.stalled else max(1, self.canonical_height - self.lag_blocks)
            f_id = self.fork_id
            b_hash, p_hash = self._get_or_compute_block(vis_h, f_id)
            return vis_h, b_hash, p_hash, f_id

    def get_canonical_tip(self):
        with self.lock:
            c_h = self.canonical_height
            b_hash, p_hash = self._get_or_compute_block(c_h, "canonical")
            return c_h, b_hash, p_hash

    # Fault control API implementations
    def set_lag(self, lag_blocks):
        with self.lock:
            self.lag_blocks = int(lag_blocks)

    def set_stall(self, stalled):
        with self.lock:
            if stalled and not self.stalled:
                self.stalled = True
                self.stall_height = max(1, self.canonical_height - self.lag_blocks)
            elif not stalled:
                self.stalled = False

    def set_diverge(self, fork_id):
        with self.lock:
            self.fork_id = str(fork_id)

    def clear_faults(self):
        with self.lock:
            self.lag_blocks = 0
            self.stalled = False
            self.fork_id = "canonical"


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def make_request_handler(ledger: MockNodeLedger):
    class MockRPCHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            # Suppress default stdout log noise for high req/s
            pass

        def _send_json(self, status_code, payload):
            data = json.dumps(payload).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            self.wfile.write(data)

        def do_OPTIONS(self):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

        def do_GET(self):
            path = self.path.split("?")[0].rstrip("/")
            if path in ("", "/healthz"):
                self._send_json(200, {"status": "ok"})
                return

            if path == "/oracle/state":
                c_h, c_hash, c_parent = ledger.get_canonical_tip()
                v_h, v_hash, v_parent, f_id = ledger.get_visible_tip()
                with ledger.lock:
                    stalled = ledger.stalled
                    lag = ledger.lag_blocks
                self._send_json(200, {
                    "canonical_height": c_h,
                    "canonical_hash": c_hash,
                    "canonical_parent": c_parent,
                    "visible_height": v_h,
                    "visible_hash": v_hash,
                    "visible_parent": v_parent,
                    "stalled": stalled,
                    "lag_blocks": lag,
                    "fork_id": f_id,
                })
                return

            self._send_json(404, {"error": "not found"})

        def do_POST(self):
            path = self.path.split("?")[0].rstrip("/")
            content_len = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_len) if content_len > 0 else b"{}"

            try:
                body = json.loads(raw_body.decode("utf-8")) if raw_body else {}
            except Exception:
                body = {}

            # Fault Control Endpoints
            if path == "/fault/lag":
                lag = body.get("lag_blocks", 0)
                ledger.set_lag(lag)
                self._send_json(200, {"status": "ok", "lag_blocks": lag})
                return

            if path == "/fault/stall":
                stalled = body.get("stalled", True)
                ledger.set_stall(stalled)
                self._send_json(200, {"status": "ok", "stalled": stalled, "visible_height": ledger.get_visible_height()})
                return

            if path == "/fault/diverge":
                fork_id = body.get("fork_id", "divergent_branch")
                ledger.set_diverge(fork_id)
                self._send_json(200, {"status": "ok", "fork_id": fork_id})
                return

            if path == "/fault/clear":
                ledger.clear_faults()
                self._send_json(200, {"status": "ok", "message": "all faults cleared"})
                return

            # EVM JSON-RPC 2.0 Handler
            if isinstance(body, list):
                # Batch JSON-RPC
                responses = [self._handle_single_rpc(req) for req in body]
                self._send_json(200, responses)
                return

            resp = self._handle_single_rpc(body)
            self._send_json(200, resp)

        def _handle_single_rpc(self, req):
            req_id = req.get("id", 1)
            method = req.get("method", "")
            params = req.get("params", [])

            if method == "eth_blockNumber":
                vis_h = ledger.get_visible_height()
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": hex(vis_h),
                }

            if method == "eth_chainId":
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": ledger.chain_id,
                }

            if method == "eth_syncing":
                with ledger.lock:
                    stalled = ledger.stalled
                    lag = ledger.lag_blocks
                    c_h = ledger.canonical_height
                vis_h = ledger.get_visible_height()
                if lag > 0 or stalled:
                    return {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "startingBlock": "0x0",
                            "currentBlock": hex(vis_h),
                            "highestBlock": hex(c_h),
                        },
                    }
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": False,
                }

            if method == "eth_getBlockByNumber":
                block_param = params[0] if len(params) > 0 else "latest"
                vis_h, vis_hash, vis_parent, fork_id = ledger.get_visible_tip()

                if block_param == "latest":
                    target_h = vis_h
                elif block_param == "earliest":
                    target_h = 1
                elif str(block_param).startswith("0x"):
                    target_h = int(block_param, 16)
                else:
                    try:
                        target_h = int(block_param)
                    except Exception:
                        target_h = vis_h

                b_hash, p_hash = ledger.get_block(target_h, fork_id)
                block_obj = {
                    "number": hex(target_h),
                    "hash": b_hash,
                    "parentHash": p_hash,
                    "nonce": "0x0000000000000000",
                    "sha3Uncles": "0x1dcc4de8dec75d7aab85b567b6cc0ef9cac469363db7b736ac37244d909ee333",
                    "logsBloom": "0x" + "0" * 512,
                    "transactionsRoot": "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421",
                    "stateRoot": "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421",
                    "receiptsRoot": "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421",
                    "miner": "0x0000000000000000000000000000000000000000",
                    "difficulty": "0x0",
                    "totalDifficulty": "0x0",
                    "extraData": "0x",
                    "size": "0x200",
                    "gasLimit": "0x1c9c380",
                    "gasUsed": "0x0",
                    "timestamp": hex(int(time.time())),
                    "transactions": [],
                }
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": block_obj,
                }

            # Default fallback for unhandled calls
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": "0x0",
            }

    return MockRPCHandler


def start_server(host, port, ledger):
    handler = make_request_handler(ledger)
    server = ThreadedHTTPServer((host, port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def main():
    parser = argparse.ArgumentParser(description="Deterministic Mock EVM Node for DriftGuard")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    parser.add_argument("--port", type=int, default=8545, help="RPC port")
    parser.add_argument("--control-port", type=int, default=None, help="Optional separate control/fault port")
    parser.add_argument("--block-time-ms", type=int, default=250, help="Block time ticker in ms")
    parser.add_argument("--initial-height", type=int, default=1000, help="Initial block number")
    parser.add_argument("--chain-id", default="0xa4b1", help="Chain ID (hex, 0xa4b1=42161)")
    args = parser.parse_args()

    ledger = MockNodeLedger(
        initial_height=args.initial_height,
        block_time_ms=args.block_time_ms,
        chain_id=args.chain_id,
    )

    print(f"[MockRPC] Starting RPC server on {args.host}:{args.port} (block_time={args.block_time_ms}ms, chain_id={args.chain_id})...")
    srv_rpc, _ = start_server(args.host, args.port, ledger)

    if args.control_port and args.control_port != args.port:
        print(f"[MockRPC] Starting Control server on {args.host}:{args.control_port}...")
        srv_ctl, _ = start_server(args.host, args.control_port, ledger)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[MockRPC] Shutting down...")
        ledger.running = False


if __name__ == "__main__":
    main()
