import logging
import os
import time
from typing import Any

import httpx

logger = logging.getLogger("driftguard.alerts")

COLOR_DRIFT_TRIPPED = 0xE02424  # Red
COLOR_RECOVERED = 0x31C48D      # Green


class DiscordAlerter:
    """
    Zero-overhead asynchronous Discord webhook incident alert dispatcher.
    Uses httpx.AsyncClient directly without heavy bot frameworks.
    Guarantees zero runtime overhead when DISCORD_WEBHOOK_URL is unset.
    """

    def __init__(self, webhook_url: str | None = None, cooldown_seconds: float = 10.0,
                 client: httpx.AsyncClient | None = None):
        self.webhook_url = (webhook_url if webhook_url is not None
                            else os.environ.get("DISCORD_WEBHOOK_URL", "")).strip()
        self.cooldown_seconds = cooldown_seconds
        self._external_client = client is not None
        self._client = client or (httpx.AsyncClient(timeout=5.0) if self.webhook_url else None)
        # Tracks {backend: (state, timestamp)} to prevent rate-limit flooding (HTTP 429) during flapping
        self._backend_state: dict[str, tuple[str, float]] = {}

    async def close(self):
        if not self._external_client and self._client:
            await self._client.aclose()

    def should_suppress_alert(self, backend: str, state: str, now: float) -> bool:
        if backend in self._backend_state:
            last_state, last_time = self._backend_state[backend]
            if state == last_state:
                logger.debug(f"Suppressed redundant alert for {backend} with state {state}")
                return True
            if (now - last_time) < self.cooldown_seconds:
                logger.warning(f"Suppressed flapping alert for {backend} ({state}); cooldown active")
                return True
        return False

    async def dispatch_embed(self, title: str, description: str, color: int,
                             fields: list[dict[str, Any]]) -> bool:
        if not self.webhook_url:
            return False
        if self._client is None:
            logger.error("Alert webhook is configured but no HTTP client is available")
            return False

        avatar_url = (
            "https://raw.githubusercontent.com/ethereum/ethereum-org-website/master/"
            "src/assets/assets-page/eth-diamond-purple.png"
        )
        payload = {
            "username": "DriftGuard Sentinel",
            "avatar_url": avatar_url,
            "embeds": [

                {
                    "title": title,
                    "description": description,
                    "color": color,
                    "fields": fields,
                    "footer": {"text": "DriftGuard High-Availability EVM Gateway"},
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
            ],
        }

        try:
            resp = await self._client.post(self.webhook_url, json=payload)
            if resp.status_code in (200, 204):
                logger.info(f"Successfully dispatched Discord incident alert: '{title}'")
                return True
            elif resp.status_code == 429:
                logger.warning(f"Discord rate limited webhook dispatch (HTTP 429): {resp.text}")
                return False
            else:
                logger.warning(f"Discord webhook responded with HTTP {resp.status_code}: {resp.text}")
                return False
        except Exception as e:
            logger.warning(f"Failed to dispatch Discord webhook: {e}")
            return False

    async def send_drift_tripped(
        self,
        chain_name: str,
        chain_id: int,
        backend: str,
        canonical_head: int | None,
        primary_head: int | None,
        delta_blocks: int,
        node_role: str = "primary",
        failover_action: str = "Drained primary -> Fallback active",
        force: bool = False,
    ) -> bool:
        if not self.webhook_url:
            return False

        now = time.time()
        if not force and self.should_suppress_alert(backend, "TRIPPED", now):
            return False

        self._backend_state[backend] = ("TRIPPED", now)

        canon_head_str = f"#{canonical_head}" if canonical_head is not None else "N/A"
        prim_head_str = f"#{primary_head}" if primary_head is not None else "N/A"
        fields = [
            {"name": "Chain Name", "value": chain_name, "inline": True},
            {"name": "Chain ID", "value": str(chain_id), "inline": True},
            {"name": "Backend", "value": backend, "inline": True},
            {"name": "Canonical Head", "value": canon_head_str, "inline": True},
            {"name": f"{node_role.title()} Head", "value": prim_head_str, "inline": True},
            {"name": "Delta Blocks", "value": str(delta_blocks), "inline": True},
            {"name": "Failover Action", "value": failover_action, "inline": False},
        ]

        return await self.dispatch_embed(
            title=f"🚨 Consensus Drift Tripped - {chain_name}",
            description=(
                f"{node_role.title()} node failed health checks with "
                f"**{delta_blocks}** blocks of drift or a probe fault."
            ),
            color=COLOR_DRIFT_TRIPPED,
            fields=fields,
        )

    async def send_reference_unavailable(
        self, chain_name: str, chain_id: int, backend: str, reason: str
    ) -> bool:

        if not self.webhook_url:
            return False
        now = time.time()
        if self.should_suppress_alert(backend, "REFERENCE_UNAVAILABLE", now):
            return False
        self._backend_state[backend] = ("REFERENCE_UNAVAILABLE", now)
        return await self.dispatch_embed(
            title=f"Canonical Reference Unavailable - {chain_name}",
            description="Serving pools were drained because the independent chain reference could not be trusted.",
            color=COLOR_DRIFT_TRIPPED,
            fields=[
                {"name": "Chain ID", "value": str(chain_id), "inline": True},
                {"name": "Backend", "value": backend, "inline": True},
                {"name": "Reason", "value": reason[:1000], "inline": False},
            ],
        )

    async def send_consensus_recovered(
        self,
        chain_name: str,
        backend: str,
        primary_weight_restored: str = "Ready (100%)",
        force: bool = False,
    ) -> bool:
        if not self.webhook_url:
            return False

        now = time.time()
        if not force and self.should_suppress_alert(backend, "RECOVERED", now):
            return False

        self._backend_state[backend] = ("RECOVERED", now)

        fields = [
            {"name": "Chain Name", "value": chain_name, "inline": True},
            {"name": "Status", "value": "Synced to Tip", "inline": True},
            {"name": "Primary Weight Restored", "value": primary_weight_restored, "inline": True},
        ]

        return await self.dispatch_embed(
            title=f"✅ Consensus Recovered - {chain_name}",
            description="Primary node re-synchronized with canonical head. Primary restored.",
            color=COLOR_RECOVERED,
            fields=fields,
        )
