"""HAProxy High-Availability Guardrail & State Controller."""
from sentinel.src.haproxy_client import (
    can_safely_drain,
    get_backend_stats,
    send_haproxy_command,
    set_server_state,
)


def calculate_one_way_drift(canonical_head: int | None, node_head: int | None) -> int:
    """
    Compute one-way consensus drift delta (only penalize lagging nodes).

    A node is only in drift if it is BEHIND the canonical anchor:
        drift = canonical_head - node_head
    If node_head >= canonical_head (drift <= 0), the node is ahead/synced; return 0.
    """
    if canonical_head is None or node_head is None:
        return 0
    drift = canonical_head - node_head
    return 0 if drift <= 0 else drift


__all__ = [
    "calculate_one_way_drift",
    "can_safely_drain",
    "get_backend_stats",
    "send_haproxy_command",
    "set_server_state",
]
