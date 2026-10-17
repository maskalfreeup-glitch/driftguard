#!/usr/bin/env python3
"""
DriftGuard - 24-Hour EVM Consensus Telemetry Aggregator
======================================================
Pulls rolling 24-hour metrics (last 86,400 seconds) from SQLite metrics.db:
- Total requests (HAProxy L7 ingress + telemetry probe volume)
- Trip count & frequency where delta > 2 blocks
- Peak consensus drift delta
- Average HAProxy runtime socket drain latency
- Node MTTR (Mean Time To Recovery)
- Formats output into a clean ASCII/Discord-ready summary card.
"""

import argparse
import json
import logging
import os
import sqlite3
import sys
import time
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("driftguard.report")

DEFAULT_DB_PATH = os.environ.get("DRIFTGUARD_DB_PATH", "/var/lib/driftguard/metrics.db")


def find_db_path(candidate_path: str = DEFAULT_DB_PATH) -> str:
    """Finds existing metrics database in /var/lib/driftguard, ~/.driftguard, or current directory."""
    paths_to_check = [
        candidate_path,
        os.path.expanduser("~/.driftguard/metrics.db"),
        os.path.abspath("metrics.db"),
        "/var/lib/driftguard/metrics.db",
    ]
    for p in paths_to_check:
        if os.path.isfile(p):
            return p
    return candidate_path


def format_duration(seconds: Optional[float]) -> str:
    if seconds is None:
        return "N/A"
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"


class ReportAggregator:
    def __init__(self, db_path: str, window_seconds: float = 86400.0):
        self.db_path = find_db_path(db_path)
        self.window_seconds = window_seconds

    def _get_connection(self) -> sqlite3.Connection:
        if not os.path.isfile(self.db_path):
            raise FileNotFoundError(f"Metrics database not found at '{self.db_path}'")
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        return conn

    def aggregate(self) -> Dict[str, Any]:
        """Calculates rolling 24-hour consensus metrics."""
        now = time.time()
        cutoff_ts = now - self.window_seconds
        window_hours = self.window_seconds / 3600.0

        with self._get_connection() as conn:
            cur = conn.cursor()

            # 1. Probe Counts & Time Range
            cur.execute(
                """
                SELECT COUNT(*) as total_probes,
                       MIN(timestamp) as min_ts,
                       MAX(timestamp) as max_ts,
                       AVG(haproxy_drain_latency_ms) as avg_drain_lat,
                       MIN(haproxy_drain_latency_ms) as min_drain_lat,
                       MAX(haproxy_drain_latency_ms) as max_drain_lat
                FROM probes
                WHERE timestamp >= ?
                """,
                (cutoff_ts,),
            )
            p_row = cur.fetchone()
            total_probes = p_row["total_probes"] or 0
            earliest_ts = p_row["min_ts"] or cutoff_ts
            latest_ts = p_row["max_ts"] or now
            actual_span_hours = max(0.01, (latest_ts - earliest_ts) / 3600.0)

            # Average socket drain latency
            cur.execute(
                """
                SELECT AVG(haproxy_drain_latency_ms) as avg_lat
                FROM probes
                WHERE timestamp >= ? AND haproxy_connected = 1 AND haproxy_drain_latency_ms > 0
                """,
                (cutoff_ts,),
            )
            drain_lat_row = cur.fetchone()
            avg_socket_drain_latency = round(drain_lat_row["avg_lat"] or 0.0, 2)

            # 2. HAProxy Ingress Request Volume
            cur.execute(
                """
                SELECT MAX(stot) as max_stot, MIN(stot) as min_stot, MAX(scur) as max_scur
                FROM haproxy_metrics
                WHERE timestamp >= ? AND svname in ('BACKEND', 'FRONTEND')
                """,
                (cutoff_ts,),
            )
            h_row = cur.fetchone()
            haproxy_max_stot = h_row["max_stot"] or 0
            haproxy_min_stot = h_row["min_stot"] or 0
            haproxy_req_delta = max(0, haproxy_max_stot - haproxy_min_stot)
            if haproxy_req_delta == 0 and haproxy_max_stot > 0:
                haproxy_req_delta = haproxy_max_stot

            # 3. Peak Drift Delta across Node 1 & Node 2
            cur.execute(
                """
                SELECT MAX(drift_delta) as peak_delta
                FROM node_metrics
                WHERE timestamp >= ? AND node_id != 'canonical' AND drift_delta IS NOT NULL
                """,
                (cutoff_ts,),
            )
            peak_row = cur.fetchone()
            peak_drift_delta = peak_row["peak_delta"] if peak_row["peak_delta"] is not None else 0

            # 4. Trip Counts where delta > 2 blocks
            cur.execute(
                """
                SELECT COUNT(*) as trip_samples
                FROM node_metrics
                WHERE timestamp >= ? AND node_id != 'canonical' AND drift_delta > 2
                """,
                (cutoff_ts,),
            )
            trip_samples_count = cur.fetchone()["trip_samples"] or 0

            cur.execute(
                """
                SELECT COUNT(*) as trip_events
                FROM incidents
                WHERE start_time >= ? AND trip_reason LIKE '%delta=%'
                """,
                (cutoff_ts,),
            )
            trip_events_count = cur.fetchone()["trip_events"] or 0

            # Total incident trips (including down/error)
            cur.execute(
                """
                SELECT COUNT(*) as total_incidents
                FROM incidents
                WHERE start_time >= ?
                """,
                (cutoff_ts,),
            )
            total_incidents_count = cur.fetchone()["total_incidents"] or 0

            # 5. Cluster & Node MTTR (Mean Time To Recovery)
            cur.execute(
                """
                SELECT AVG(duration_seconds) as avg_mttr,
                       COUNT(*) as recovered_count,
                       MIN(duration_seconds) as min_mttr,
                       MAX(duration_seconds) as max_mttr
                FROM incidents
                WHERE start_time >= ? AND recovered = 1
                """,
                (cutoff_ts,),
            )
            mttr_row = cur.fetchone()
            cluster_mttr_sec = mttr_row["avg_mttr"]
            recovered_count = mttr_row["recovered_count"] or 0

            # Active open incidents
            cur.execute(
                """
                SELECT node_id, start_time, trip_reason
                FROM incidents
                WHERE recovered = 0
                """,
            )
            active_incidents = [dict(r) for r in cur.fetchall()]

            # 6. Node-by-Node Detailed Breakdown
            node_ids = ["canonical", "node1", "node2"]
            nodes_data = {}
            for nid in node_ids:
                cur.execute(
                    """
                    SELECT node_name, endpoint_url,
                           COUNT(*) as total_samples,
                           AVG(latency_ms) as avg_lat,
                           MIN(latency_ms) as min_lat,
                           MAX(latency_ms) as max_lat,
                           MAX(drift_delta) as node_peak_drift,
                           SUM(CASE WHEN drift_delta > 2 THEN 1 ELSE 0 END) as node_trips_gt_2,
                           SUM(CASE WHEN status = 'HEALTHY' THEN 1 ELSE 0 END) as healthy_count
                    FROM node_metrics
                    WHERE timestamp >= ? AND node_id = ?
                    GROUP BY node_id
                    """,
                    (cutoff_ts, nid),
                )
                nr = cur.fetchone()

                # Get latest sample
                cur.execute(
                    """
                    SELECT block_number, drift_delta, peer_count, latency_ms, status, error, timestamp
                    FROM node_metrics
                    WHERE node_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                    """,
                    (nid,),
                )
                latest = cur.fetchone()

                # Node MTTR
                cur.execute(
                    """
                    SELECT AVG(duration_seconds) as node_mttr, COUNT(*) as node_recovered
                    FROM incidents
                    WHERE node_id = ? AND start_time >= ? AND recovered = 1
                    """,
                    (nid, cutoff_ts),
                )
                node_mttr_row = cur.fetchone()

                total_s = nr["total_samples"] if nr else 0
                healthy_s = nr["healthy_count"] if nr else 0
                health_pct = round((healthy_s / total_s * 100.0), 2) if total_s > 0 else 100.0

                nodes_data[nid] = {
                    "node_id": nid,
                    "node_name": nr["node_name"] if nr else nid,
                    "endpoint_url": nr["endpoint_url"] if nr else "",
                    "total_samples": total_s,
                    "latest_block": latest["block_number"] if latest else None,
                    "latest_delta": latest["drift_delta"] if latest else None,
                    "latest_peers": latest["peer_count"] if latest else None,
                    "latest_status": latest["status"] if latest else "UNKNOWN",
                    "latest_latency": round(latest["latency_ms"], 2) if latest and latest["latency_ms"] else None,
                    "avg_latency": round(nr["avg_lat"], 2) if nr and nr["avg_lat"] else 0.0,
                    "peak_drift": nr["node_peak_drift"] if nr and nr["node_peak_drift"] is not None else 0,
                    "trips_gt_2": nr["node_trips_gt_2"] if nr else 0,
                    "health_pct": health_pct,
                    "mttr_sec": node_mttr_row["node_mttr"] if node_mttr_row else None,
                }

            # 7. HAProxy Latest Backends Overview
            cur.execute(
                """
                SELECT pxname, svname, status, scur, qcur, stot, is_draining
                FROM haproxy_metrics
                WHERE probe_id = (SELECT MAX(id) FROM probes)
                ORDER BY pxname, svname
                """
            )
            haproxy_rows = [dict(r) for r in cur.fetchall()]

            # Overall Consensus SLA %
            total_evals = sum(nodes_data[k]["total_samples"] for k in ("node1", "node2"))
            total_healthy = sum(
                (nodes_data[k]["total_samples"] - nodes_data[k]["trips_gt_2"])
                for k in ("node1", "node2")
            )
            consensus_sla = round((total_healthy / total_evals * 100.0), 2) if total_evals > 0 else 100.0

            return {
                "window_hours": round(window_hours, 1),
                "actual_span_hours": round(actual_span_hours, 2),
                "start_time": datetime.fromtimestamp(earliest_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                "end_time": datetime.fromtimestamp(latest_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                "total_probes": total_probes,
                "total_requests": haproxy_req_delta + total_probes,
                "haproxy_ingress_requests": haproxy_req_delta,
                "peak_drift_delta": peak_drift_delta,
                "trip_samples_delta_gt_2": trip_samples_count,
                "trip_events_delta_gt_2": trip_events_count,
                "total_incident_trips": total_incidents_count,
                "trip_frequency_per_hour": round(trip_events_count / max(0.1, actual_span_hours), 2),
                "avg_socket_drain_latency_ms": avg_socket_drain_latency,
                "cluster_mttr_seconds": cluster_mttr_sec,
                "recovered_incidents": recovered_count,
                "active_incidents": active_incidents,
                "consensus_sla_pct": consensus_sla,
                "nodes": nodes_data,
                "haproxy_backends": haproxy_rows,
                "db_path": self.db_path,
            }


class SummaryCardRenderer:
    """Renders high-fidelity ASCII summary tables formatted for CLI and Discord embeds."""

    @staticmethod
    def render_ascii_card(data: Dict[str, Any]) -> str:
        w_hours = data["window_hours"]
        start_t = data["start_time"]
        end_t = data["end_time"]
        ha_req = f"{data['haproxy_ingress_requests']:,}"
        probes = f"{data['total_probes']:,}"
        peak_delta = f"{data['peak_drift_delta']} blocks" if data["peak_drift_delta"] is not None else "0 blocks"
        trips_gt_2 = data["trip_samples_delta_gt_2"]
        trip_events = data["trip_events_delta_gt_2"]
        drain_lat = f"{data['avg_socket_drain_latency_ms']:.2f} ms"

        mttr_sec = data["cluster_mttr_seconds"]
        if mttr_sec is not None and mttr_sec > 0:
            mttr_str = format_duration(mttr_sec)
        elif data["total_incident_trips"] == 0:
            mttr_str = "0.0s (100% SLA, Zero Outages)"
        else:
            mttr_str = "N/A (Active Incident)"

        sla = f"{data['consensus_sla_pct']:.2f}%"

        card = []
        card.append("```")
        card.append("+" + "=" * 78 + "+")
        card.append("|" + " " * 19 + "DRIFTGUARD 24-HOUR TELEMETRY REPORT" + " " * 24 + "|")
        card.append("|" + f" Window: {start_t} -> {end_t} (Rolling {w_hours}h)".center(78) + "|")
        card.append("+" + "=" * 78 + "+")
        card.append("| [ 24-HOUR CONSENSUS KPIS & DRIFT METRICS ]" + " " * 35 + "|")
        card.append("+---------------------------------------+--------------------------------------+")
        card.append(f"| Total Ingress Requests (HAProxy L7)   | {ha_req:<36} |")
        card.append(f"| Telemetry Probe Cycles (15s polling)  | {probes:<36} |")
        card.append(f"| Consensus Trips (Drift Delta > 2 blk) | {f'{trip_events} events ({trips_gt_2} samples)':<36} |")
        card.append(f"| Peak Consensus Drift Delta            | {peak_delta:<36} |")
        card.append(f"| HAProxy Socket Drain Latency (avg)    | {drain_lat:<36} |")
        card.append(f"| Node MTTR (Mean Time To Recovery)     | {mttr_str:<36} |")
        card.append(f"| Cluster Consensus Adherence SLA       | {sla:<36} |")
        card.append("+---------------------------------------+--------------------------------------+")
        card.append("")
        card.append("[ ARBITRUM NODE TELEMETRY & DRIFT DELTAS ]")
        card.append("+-----------+-----------------------+-------------+-------+----------+--------+-------+---------+")
        card.append("| Node      | Endpoint              | Head Block  | Peers | Latency  | Drift  | Trips | Status  |")
        card.append("+-----------+-----------------------+-------------+-------+----------+--------+-------+---------+")

        nodes = data.get("nodes", {})
        for nid in ("canonical", "node1", "node2"):
            n = nodes.get(nid, {})
            name = "Canonical" if nid == "canonical" else ("Node 1" if nid == "node1" else "Node 2")
            url = n.get("endpoint_url", "")
            # Shorten URL for clean table display
            url_clean = url.replace("https://", "").replace("http://", "")
            if len(url_clean) > 21:
                url_clean = url_clean[:18] + "..."

            block_str = f"{n.get('latest_block'):,}" if n.get("latest_block") else "N/A"
            peers_str = str(n.get("latest_peers")) if n.get("latest_peers") is not None else "--"
            lat_str = f"{n.get('avg_latency'):.1f}ms" if n.get("avg_latency") else "--"
            drift_str = f"{n.get('latest_delta')} blk" if n.get("latest_delta") is not None else "--"
            trips_str = str(n.get("trips_gt_2", 0))
            status_str = n.get("latest_status", "UNKNOWN")

            node_row = (
                f"| {name:<9} | {url_clean:<21} | {block_str:>11} | {peers_str:>5} | "
                f"{lat_str:>8} | {drift_str:>6} | {trips_str:>5} | {status_str:<7} |"
            )
            card.append(node_row)
        card.append("+-----------+-----------------------+-------------+-------+----------+--------+-------+---------+")

        # HAProxy backends table
        ha_backends = data.get("haproxy_backends", [])
        if ha_backends:
            card.append("")
            card.append("[ HAPROXY RUNTIME SOCKET & DRAIN STATUS ]")
            card.append("+------------------+----------+----------+------------+------------+---------------+")
            card.append("| Backend / Server | Status   | Active   | Queued     | Total Reqs | Drain State   |")
            card.append("+------------------+----------+----------+------------+------------+---------------+")
            for b in ha_backends:
                b_name = f"{b.get('pxname')}/{b.get('svname')}"
                if len(b_name) > 16:
                    b_name = b_name[:14] + ".."
                st = b.get("status", "UP")
                scur = f"{b.get('scur', 0)} c"
                qcur = f"{b.get('qcur', 0)} q"
                stot = f"{b.get('stot', 0):,}"
                drain_s = "DRAINING" if b.get("is_draining") else ("BACKUP" if "fallback" in b_name else "NORMAL")
                card.append(
                    f"| {b_name:<16} | {st:<8} | {scur:>8} | {qcur:>10} | {stot:>10} | {drain_s:<13} |"
                )
            card.append("+------------------+----------+----------+------------+------------+---------------+")

        # Active incidents if any
        active = data.get("active_incidents", [])
        if active:
            card.append("")
            card.append(f"⚠️  ACTIVE UNRESOLVED INCIDENTS ({len(active)}):")
            for inc in active:
                st_time_str = datetime.fromtimestamp(inc["start_time"], tz=timezone.utc).strftime("%H:%M:%S UTC")
                card.append(f"  - [{inc['node_id'].upper()}] {inc['trip_reason']} (Started: {st_time_str})")

        card.append("```")
        return "\n".join(card)


def dispatch_to_discord(
    webhook_url: str,
    content: str,
    title: str = "DriftGuard 24-Hour Telemetry Report",
) -> bool:
    """Dispatches formatted report card to Discord webhook."""
    if not webhook_url:
        logger.warning("No Discord webhook URL provided.")
        return False
    payload = {
        "username": "DriftGuard Consensus Sentinel",
        "avatar_url": (
            "https://raw.githubusercontent.com/ethereum/ethereum-org-website/master/"
            "src/assets/assets-page/eth-diamond-purple.png"
        ),
        "content": content,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "DriftGuard-Alerter/2.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8.0) as resp:
            logger.info(f"Report successfully posted to Discord (HTTP {resp.status})")
            return True
    except Exception as e:
        logger.error(f"Failed posting report to Discord: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="DriftGuard 24-Hour EVM Consensus Telemetry Reporter")
    parser.add_argument("--db-path", type=str, default=DEFAULT_DB_PATH, help="Path to SQLite metrics DB")
    parser.add_argument("--hours", type=float, default=24.0, help="Rolling window in hours (default: 24.0)")
    parser.add_argument(
        "--window-seconds",
        type=float,
        default=86400.0,
        help="Window size in seconds (default: 86400.0)",
    )
    parser.add_argument("--json", action="store_true", help="Output raw aggregated JSON metrics")
    parser.add_argument("--discord", action="store_true", help="Post summary table directly to Discord webhook")
    parser.add_argument("--webhook-url", type=str, default="", help="Discord webhook URL override")

    args = parser.parse_args()

    win_seconds = args.hours * 3600.0 if args.hours != 24.0 else args.window_seconds
    aggregator = ReportAggregator(db_path=args.db_path, window_seconds=win_seconds)

    try:
        data = aggregator.aggregate()
    except Exception as e:
        logger.error(f"Failed to generate 24h telemetry report: {e}", exc_info=True)
        sys.exit(1)

    if args.json:
        print(json.dumps(data, indent=2))
        return

    card = SummaryCardRenderer.render_ascii_card(data)
    print(card)

    if args.discord:
        webhook = (
            args.webhook_url
            or os.environ.get("DISCORD_VPS_WEBHOOK_URL")
            or os.environ.get("DISCORD_WEBHOOK_URL")
            or ""
        )
        dispatch_to_discord(webhook, card)


if __name__ == "__main__":
    main()
