#!/usr/bin/env python3
"""
DriftGuard Incident Alert Dry-Run & Webhook Verification Script
Tests and verifies the Discord embed schemas for both:
1. Consensus Drift Tripped (Color 0xE02424 / Red)
2. Consensus Recovered (Color 0x31C48D / Green)

Usage:
    python3 scripts/test_incident_alerts.py --dry-run
    python3 scripts/test_incident_alerts.py --dispatch
"""

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sentinel.alerts import COLOR_DRIFT_TRIPPED, COLOR_RECOVERED, DiscordAlerter  # noqa: E402


def validate_drift_tripped_schema(payload: dict) -> None:
    """Verifies that the Drift Tripped embed schema conforms to requirements."""
    assert "embeds" in payload and len(payload["embeds"]) == 1, "Must contain exactly 1 embed"
    embed = payload["embeds"][0]
    assert embed["color"] == COLOR_DRIFT_TRIPPED, f"Expected color {COLOR_DRIFT_TRIPPED}, got {embed.get('color')}"
    assert "Consensus Drift Tripped" in embed["title"], "Title must contain 'Consensus Drift Tripped'"

    # 1. Clean footer without duplicate UTC timestamp
    footer = embed.get("footer", {})
    assert footer.get("text") == "DriftGuard High-Availability EVM Gateway", (
        f"Footer text mismatch: {footer.get('text')}"
    )

    # 2. Top-level timestamp
    assert "timestamp" in embed, "Embed must have top-level timestamp"
    ts = datetime.fromisoformat(embed["timestamp"])
    assert ts.tzinfo is not None, "Timestamp must be timezone-aware (ISO-8601 UTC)"

    # 3. Enriched fields
    field_map = {f["name"]: f["value"] for f in embed.get("fields", [])}

    # Routing Transition
    assert "Routing Transition" in field_map, "Field 'Routing Transition' is required"
    assert "primary: DRAIN (0%) -> fallback: ACTIVE (100%)" in field_map["Routing Transition"], (
        f"Unexpected Routing Transition: {field_map['Routing Transition']}"
    )

    # Cutover latency label
    drain_val = field_map.get("Socket Drain Latency", "")
    assert "(POSIX Socket Drain)" in drain_val, f"Socket Drain Latency must include '(POSIX Socket Drain)': {drain_val}"
    assert "ms" in drain_val, f"Latency value must specify ms: {drain_val}"

    # HAProxy Ingress Stats
    assert "HAProxy Ingress Stats" in field_map, "Field 'HAProxy Ingress Stats' is required"
    assert "in-flight queries preserved (0 dropped)" in field_map["HAProxy Ingress Stats"], (
        f"HAProxy Ingress Stats must highlight zero packet loss: {field_map['HAProxy Ingress Stats']}"
    )


def validate_consensus_recovered_schema(payload: dict) -> None:
    """Verifies that the Consensus Recovered embed schema conforms to requirements."""
    assert "embeds" in payload and len(payload["embeds"]) == 1, "Must contain exactly 1 embed"
    embed = payload["embeds"][0]
    assert embed["color"] == COLOR_RECOVERED, f"Expected color {COLOR_RECOVERED}, got {embed.get('color')}"
    assert "Consensus Recovered" in embed["title"], "Title must contain 'Consensus Recovered'"

    # 1. Clean footer without duplicate UTC timestamp
    footer = embed.get("footer", {})
    assert footer.get("text") == "DriftGuard High-Availability EVM Gateway", (
        f"Footer text mismatch: {footer.get('text')}"
    )

    # 2. Top-level timestamp
    assert "timestamp" in embed, "Embed must have top-level timestamp"
    ts = datetime.fromisoformat(embed["timestamp"])
    assert ts.tzinfo is not None, "Timestamp must be timezone-aware (ISO-8601 UTC)"

    # 3. Enriched MTTR and Protected Traffic fields
    field_map = {f["name"]: f["value"] for f in embed.get("fields", [])}

    # Resolution Time (MTTR)
    assert "Resolution Time (MTTR)" in field_map, "Field 'Resolution Time (MTTR)' is required"
    mttr_val = field_map["Resolution Time (MTTR)"]
    assert "s (" in mttr_val and "blocks caught up)" in mttr_val, (
        f"Unexpected MTTR format: {mttr_val}"
    )

    # Protected Traffic
    assert "Protected Traffic" in field_map, "Field 'Protected Traffic' is required"
    assert "0% dropped" in field_map["Protected Traffic"], (
        f"Protected Traffic must summarize zero dropped: {field_map['Protected Traffic']}"
    )


async def run_simulation(dispatch: bool = False) -> int:
    alerter = DiscordAlerter()

    print("================================================================================")
    print(" 🛡️ DriftGuard Sentinel Incident Alert Dry-Run Schema Verification")
    print("================================================================================")

    # Step 1: Simulate Consensus Drift Tripped
    simulated_trip_time = time.time() - 2.1  # 2.1 seconds ago
    alerter._drift_tripped_at["be_arb"] = simulated_trip_time
    alerter._tripped_blocks["be_arb"] = 6

    tripped_payload = alerter.build_drift_tripped_payload(
        chain_name="Arbitrum One",
        chain_id=42161,
        backend="be_arb",
        canonical_head=511900000,
        primary_head=511899986,
        delta_blocks=14,
        node_role="primary",
        routing_transition="primary: DRAIN (0%) -> fallback: ACTIVE (100%)",
        drain_latency_ms=0.60,
        backend_stats={
            "total_requests": 14500,
            "current_in_flight": 18,
            "http_2xx": 14495,
            "http_5xx": 0,
        },
    )

    validate_drift_tripped_schema(tripped_payload)
    print("\n[OK] Alert 1 Schema Validated: 🚨 Consensus Drift Tripped")
    print(json.dumps(tripped_payload, indent=2))

    # Step 2: Simulate Consensus Recovered
    recovered_payload = alerter.build_consensus_recovered_payload(
        chain_name="Arbitrum One",
        backend="be_arb",
        primary_weight_restored="Ready (100%)",
        drift_tripped_at=simulated_trip_time,
        caught_up_blocks=6,
        protected_traffic="1,420 queries routed (0% dropped)",
    )

    validate_consensus_recovered_schema(recovered_payload)
    print("\n[OK] Alert 2 Schema Validated: ✅ Consensus Recovered")
    print(json.dumps(recovered_payload, indent=2))

    print("\n================================================================================")
    print(" ✅ All Embed Schemas Conformed to DriftGuard v1.1 Incident Alert Specifications!")
    print("================================================================================")

    if dispatch:
        if not alerter.webhook_url:
            print("\n[WARNING] DISCORD_WEBHOOK_URL is unset; skipping live webhook post.")
            return 0
        print("\n[INFO] Dispatching live test incident embeds to Discord webhook...")
        await alerter.send_drift_tripped(
            chain_name="Arbitrum One",
            chain_id=42161,
            backend="be_arb",
            canonical_head=511900000,
            primary_head=511899986,
            delta_blocks=14,
            drain_latency_ms=0.60,
            routing_transition="primary: DRAIN (0%) -> fallback: ACTIVE (100%)",
            backend_stats={"current_in_flight": 18},
            force=True,
        )
        time.sleep(1.0)
        await alerter.send_consensus_recovered(
            chain_name="Arbitrum One",
            backend="be_arb",
            primary_weight_restored="Ready (100%)",
            force=True,
            mttr_seconds=2.1,
            caught_up_blocks=6,
            protected_traffic="1,420 queries routed (0% dropped)",
        )
        print("[SUCCESS] Dispatched both embeds to Discord!")

    await alerter.close()
    return 0


def main():
    parser = argparse.ArgumentParser(description="Test and dry-run DriftGuard incident alert embeds")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Print embed schemas without posting")
    parser.add_argument("--dispatch", action="store_true", help="Post to live webhook if configured")
    args = parser.parse_args()

    sys.exit(asyncio.run(run_simulation(dispatch=args.dispatch)))


if __name__ == "__main__":
    main()
