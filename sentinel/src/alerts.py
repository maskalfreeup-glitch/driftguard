"""Sentinel alert dispatcher module."""
from sentinel.alerts import (
    COLOR_DRIFT_TRIPPED,
    COLOR_RECOVERED,
    DiscordAlerter,
)

__all__ = [
    "COLOR_DRIFT_TRIPPED",
    "COLOR_RECOVERED",
    "DiscordAlerter",
    "dispatch_drift_alert",
]


async def dispatch_drift_alert(alerter: DiscordAlerter, *args, **kwargs) -> bool:
    """Module-level helper to dispatch a drift alert via the provided alerter instance."""
    return await alerter.dispatch_drift_alert(*args, **kwargs)
