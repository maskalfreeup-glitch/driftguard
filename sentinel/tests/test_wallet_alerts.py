import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from sentinel.wallet_alerts import WalletAlertDaemon, CORRIDORS


@pytest.mark.asyncio
async def test_wallet_alert_daemon_init():
    daemon = WalletAlertDaemon(
        wallet_address="0x881C9c7D5bCAcb5fcEAfD12299756d4C38CCE20b",
        webhook_url="https://discord.com/api/webhooks/test/test",
        poll_interval=30.0,
    )
    assert daemon.wallet == "0x881C9c7D5bCAcb5fcEAfD12299756d4C38CCE20b"
    assert daemon.webhook_url == "https://discord.com/api/webhooks/test/test"
    assert daemon.poll_interval == 30.0
    assert daemon.balances == {}


@pytest.mark.asyncio
async def test_check_balances_rebate_detection():
    daemon = WalletAlertDaemon(
        wallet_address="0x881C9c7D5bCAcb5fcEAfD12299756d4C38CCE20b",
        webhook_url="https://discord.com/api/webhooks/test/test",
        poll_interval=10.0,
    )

    # Initial state
    daemon.balances = {
        "ETH": 1000000000000000000,
        "ARB": 500000000000000000,
        "BASE": 0,
        "NOVA": 0,
    }

    # Simulate balance increase on ARB (+0.05 ETH)
    mock_balances = {
        "ETH": 1000000000000000000,
        "ARB": 550000000000000000,
        "BASE": 0,
        "NOVA": 0,
    }

    async def mock_fetch(chain_key):
        return mock_balances[chain_key]

    daemon.fetch_corridor_balance = mock_fetch
    daemon.dispatch_rebate_alert = AsyncMock()

    updated = await daemon.check_balances(notify_rebates=True)
    assert updated["ARB"] == 550000000000000000
    daemon.dispatch_rebate_alert.assert_awaited_once_with(
        "ARB", 50000000000000000, 550000000000000000
    )


@pytest.mark.asyncio
async def test_dispatch_rebate_alert_payload():
    daemon = WalletAlertDaemon(
        wallet_address="0x881C9c7D5bCAcb5fcEAfD12299756d4C38CCE20b",
        webhook_url="https://discord.com/api/webhooks/test/test",
    )
    sent_payloads = []

    async def mock_send(payload):
        sent_payloads.append(payload)
        return True

    daemon.send_discord_webhook = mock_send
    await daemon.dispatch_rebate_alert("ETH", 10000000000000000, 1010000000000000000)

    assert len(sent_payloads) == 1
    embed = sent_payloads[0]["embeds"][0]
    assert "💰 MEV Rebate / Deposit Detected" in embed["title"]
    assert any("Ethereum Mainnet" in f["value"] for f in embed["fields"])
    assert any("0.01000000 ETH" in f["value"] for f in embed["fields"])
