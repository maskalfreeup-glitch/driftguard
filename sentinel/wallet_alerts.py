#!/usr/bin/env python3
"""
DriftGuard Multi-Chain Wallet & Yield Alert Daemon
Zero-dependency background monitor for OFA payout address across ETH, ARB, BASE, and NOVA.
Dispatches rich embed alerts to Discord upon balance changes (MEV rebates or deposits).
"""

import argparse
import asyncio
import json
import logging
import os
import socket
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Dict, List, Optional


def load_env_file(filepath: str):
    """Fallback .env parser if python-dotenv is not installed."""
    if not os.path.exists(filepath):
        return
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key and key not in os.environ:
                        os.environ[key] = val
    except Exception:
        pass


# Try importing python-dotenv, fallback to local parsing
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Also look for .env in current and parent directory
load_env_file(".env")
load_env_file(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
load_env_file("/etc/default/haproxy")

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("driftguard.wallet_alerts")

DEFAULT_WALLET = "0x881C9c7D5bCAcb5fcEAfD12299756d4C38CCE20b"
DEFAULT_WEBHOOK = "https://discord.com/api/webhooks/1561717524138172486/4vQmKJwqohiRkzkjdj7Pf2beINtzSkxklei7_YPK92bclxsYOx0ObrGRoBbHhFKebEqa"

CORRIDORS = {
    "ETH": {
        "name": "Ethereum Mainnet",
        "path": "/eth",
        "explorer": "https://etherscan.io/address/",
        "upstreams": [
            "http://127.0.0.1:8545/eth",
            "https://rpc.driftguard.live/eth",
            "https://ethereum-rpc.publicnode.com",
        ],
        "symbol": "ETH",
    },
    "ARB": {
        "name": "Arbitrum One",
        "path": "/arb",
        "explorer": "https://arbiscan.io/address/",
        "upstreams": [
            "http://127.0.0.1:8545/arb",
            "https://rpc.driftguard.live/arb",
            "https://arb1.arbitrum.io/rpc",
        ],
        "symbol": "ETH",
    },
    "BASE": {
        "name": "Base",
        "path": "/base",
        "explorer": "https://basescan.org/address/",
        "upstreams": [
            "http://127.0.0.1:8545/base",
            "https://rpc.driftguard.live/base",
            "https://mainnet.base.org",
        ],
        "symbol": "ETH",
    },
    "NOVA": {
        "name": "Arbitrum Nova",
        "path": "/nova",
        "explorer": "https://nova.arbiscan.io/address/",
        "upstreams": [
            "http://127.0.0.1:8545/nova",
            "https://rpc.driftguard.live/nova",
            "https://nova.arbitrum.io/rpc",
        ],
        "symbol": "ETH",
    },
}


def get_node_name() -> str:
    """Return local host identifier."""
    env_node = os.environ.get("NODE_NAME")
    if env_node and env_node.strip():
        return env_node.strip()
    try:
        host = socket.gethostname()
        if host and host.strip():
            return host.strip()
    except Exception:
        pass
    return "dg-node"


def _sync_http_post(url: str, json_data: dict, headers: Optional[dict] = None, timeout: float = 6.0) -> tuple:
    """Synchronous HTTP POST with standard library urllib."""
    data = json.dumps(json_data).encode("utf-8")
    req_headers = {
        "Content-Type": "application/json",
        "User-Agent": "DriftGuard-WalletAlerts/1.0",
    }
    if headers:
        req_headers.update(headers)

    req = urllib.request.Request(url, data=data, headers=req_headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            body = resp.read().decode("utf-8")
            return status, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        return e.code, body
    except Exception as e:
        return 0, str(e)


class WalletAlertDaemon:
    def __init__(
        self,
        wallet_address: Optional[str] = None,
        webhook_url: Optional[str] = None,
        poll_interval: Optional[float] = None,
    ):
        self.wallet = (
            wallet_address
            or os.environ.get("OFA_PAYOUT_ADDRESS")
            or DEFAULT_WALLET
        ).strip()
        self.webhook_url = (
            webhook_url
            or os.environ.get("DISCORD_WEBHOOK_URL")
            or DEFAULT_WEBHOOK
        ).strip()
        self.poll_interval = float(
            poll_interval
            or os.environ.get("ALERT_POLL_INTERVAL")
            or 60
        )
        self.node_name = get_node_name()
        self.balances: Dict[str, int] = {}
        self._stop_event = asyncio.Event()

    async def send_discord_webhook(self, payload: dict) -> bool:
        """Send embed payload to configured Discord webhook asynchronously."""
        if not self.webhook_url:
            logger.warning("No DISCORD_WEBHOOK_URL set; skipping alert dispatch")
            return False

        status, body = await asyncio.to_thread(
            _sync_http_post,
            self.webhook_url,
            payload,
            timeout=8.0,
        )
        if status in (200, 204):
            logger.info("Discord alert delivered successfully")
            return True
        else:
            logger.error(f"Discord webhook failed with HTTP {status}: {body}")
            return False

    async def fetch_corridor_balance(self, chain_key: str) -> Optional[int]:
        """Query eth_getBalance for the payout wallet across candidate upstreams."""
        corridor = CORRIDORS[chain_key]
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getBalance",
            "params": [self.wallet, "latest"],
            "id": 1,
        }

        for upstream in corridor["upstreams"]:
            try:
                status, body = await asyncio.to_thread(
                    _sync_http_post,
                    upstream,
                    payload,
                    timeout=5.0,
                )
                if status == 200:
                    data = json.loads(body)
                    if "result" in data and isinstance(data["result"], str):
                        balance_wei = int(data["result"], 16)
                        return balance_wei
                    elif "error" in data:
                        logger.debug(f"{chain_key} [{upstream}] RPC error: {data['error']}")
                else:
                    logger.debug(f"{chain_key} [{upstream}] HTTP {status}")
            except Exception as e:
                logger.debug(f"{chain_key} [{upstream}] probe failed: {e}")

        logger.warning(f"Could not retrieve balance for {chain_key} from any upstream")
        return None

    async def check_balances(self, notify_rebates: bool = True) -> Dict[str, int]:
        """Poll all corridors and detect balance increments."""
        current_balances: Dict[str, int] = {}

        tasks = [self.fetch_corridor_balance(k) for k in CORRIDORS.keys()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for chain_key, result in zip(CORRIDORS.keys(), results):
            if isinstance(result, int):
                current_balances[chain_key] = result
                prev = self.balances.get(chain_key)

                if prev is not None and result != prev:
                    delta = result - prev
                    if delta > 0:
                        logger.info(f"Rebate/deposit detected on {chain_key}: +{delta} wei")
                        if notify_rebates:
                            await self.dispatch_rebate_alert(chain_key, delta, result)
                    else:
                        logger.info(f"Balance decreased on {chain_key}: {delta} wei")
                self.balances[chain_key] = result
            else:
                logger.warning(f"Failed balance probe for {chain_key}: {result}")

        return current_balances

    async def dispatch_rebate_alert(self, chain_key: str, delta_wei: int, total_wei: int):
        """Construct and send a rich Discord embed for an incoming rebate."""
        corridor = CORRIDORS[chain_key]
        delta_eth = delta_wei / 10**18
        total_eth = total_wei / 10**18
        explorer_url = f"{corridor['explorer']}{self.wallet}"

        payload = {
            "username": "DriftGuard Yield Sentinel",
            "avatar_url": "https://raw.githubusercontent.com/maskalfreeup-glitch/driftguard/main/docs/assets/shield.png",
            "embeds": [
                {
                    "title": "💰 MEV Rebate / Deposit Detected",
                    "description": (
                        f"An incoming transaction or OFA rebate was received on "
                        f"**{corridor['name']}**."
                    ),
                    "color": 0x10B981,  # Emerald Green
                    "fields": [
                        {
                            "name": "🌐 Network / Corridor",
                            "value": f"{corridor['name']} (`{chain_key}`)",
                            "inline": True,
                        },
                        {
                            "name": "💵 Rebate Amount",
                            "value": f"`+{delta_eth:.8f} {corridor['symbol']}`",
                            "inline": True,
                        },
                        {
                            "name": "📊 New Total Balance",
                            "value": f"`{total_eth:.8f} {corridor['symbol']}`",
                            "inline": True,
                        },
                        {
                            "name": "🎯 Payout Wallet",
                            "value": f"[`{self.wallet}`]({explorer_url})",
                            "inline": False,
                        },
                        {
                            "name": "🚀 Ingress Route",
                            "value": f"`https://rpc.driftguard.live{corridor['path']}`",
                            "inline": True,
                        },
                        {
                            "name": "🖥️ Node Source",
                            "value": f"`{self.node_name}`",
                            "inline": True,
                        },
                    ],
                    "footer": {
                        "text": "DriftGuard Sentinel • Multi-Chain OFA Monitor"
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ],
        }
        await self.send_discord_webhook(payload)

    async def dispatch_startup_alert(self):
        """Send initialization embed with baseline balances across all corridors."""
        balance_lines = []
        for chain_key, corridor in CORRIDORS.items():
            b = self.balances.get(chain_key)
            if b is not None:
                eth_val = b / 10**18
                balance_lines.append(f"• **{chain_key}** ({corridor['name']}): `{eth_val:.8f} ETH`")
            else:
                balance_lines.append(f"• **{chain_key}** ({corridor['name']}): *Pending...*")

        payload = {
            "username": "DriftGuard Yield Sentinel",
            "avatar_url": "https://raw.githubusercontent.com/maskalfreeup-glitch/driftguard/main/docs/assets/shield.png",
            "embeds": [
                {
                    "title": "🟢 DriftGuard Wallet & Yield Sentinel Online",
                    "description": (
                        f"Multi-chain yield and OFA rebate monitoring daemon started on **{self.node_name}**."
                    ),
                    "color": 0x3B82F6,  # Blue
                    "fields": [
                        {
                            "name": "🎯 Monitored Payout Wallet",
                            "value": f"`{self.wallet}`",
                            "inline": False,
                        },
                        {
                            "name": "📊 Initial Corridor Balances",
                            "value": "\n".join(balance_lines),
                            "inline": False,
                        },
                        {
                            "name": "⏱️ Polling Cadence",
                            "value": f"Every {int(self.poll_interval)} seconds",
                            "inline": True,
                        },
                    ],
                    "footer": {
                        "text": f"DriftGuard Sentinel • Multi-Chain OFA Monitor • Node: {self.node_name}"
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ],
        }
        await self.send_discord_webhook(payload)

    async def dispatch_test_alert(self):
        """Send a simulated rebate alert to verify webhook integration."""
        simulated_delta_wei = 15000000000000000  # 0.015 ETH
        simulated_total_wei = 35000000000000000  # 0.035 ETH
        logger.info("Dispatching simulated MEV rebate test alert...")
        await self.dispatch_rebate_alert("ARB", simulated_delta_wei, simulated_total_wei)

    async def run(self, send_startup: bool = True):
        """Run continuous monitoring loop."""
        logger.info(
            f"Starting WalletAlertDaemon for wallet {self.wallet} "
            f"on {self.node_name} (interval={self.poll_interval}s)"
        )
        # Initial baseline balance check (no alerts triggered)
        await self.check_balances(notify_rebates=False)

        if send_startup:
            await self.dispatch_startup_alert()

        try:
            while not self._stop_event.is_set():
                await asyncio.sleep(self.poll_interval)
                await self.check_balances(notify_rebates=True)
        except asyncio.CancelledError:
            logger.info("Monitoring loop cancelled, shutting down...")

    def stop(self):
        self._stop_event.set()


async def main():
    parser = argparse.ArgumentParser(description="DriftGuard Multi-Chain Wallet & Yield Alert Daemon")
    parser.add_argument("--wallet", help="Payout wallet address to monitor", default=None)
    parser.add_argument("--webhook", help="Discord webhook URL", default=None)
    parser.add_argument("--interval", type=float, help="Polling interval in seconds", default=None)
    parser.add_argument("--once", action="store_true", help="Perform a single balance check and exit")
    parser.add_argument("--test-alert", action="store_true", help="Send a simulated rebate alert and exit")
    parser.add_argument("--no-startup-alert", action="store_true", help="Suppress the initial startup embed")
    args = parser.parse_args()

    daemon = WalletAlertDaemon(
        wallet_address=args.wallet,
        webhook_url=args.webhook,
        poll_interval=args.interval,
    )

    if args.test_alert:
        await daemon.dispatch_test_alert()
        return

    if args.once:
        balances = await daemon.check_balances(notify_rebates=False)
        print(f"\nWallet: {daemon.wallet}")
        for chain, b in balances.items():
            print(f"  {chain}: {b / 10**18:.8f} ETH ({b} wei)")
        return

    await daemon.run(send_startup=not args.no_startup_alert)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(0)
