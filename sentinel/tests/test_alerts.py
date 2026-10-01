import pytest

from sentinel.alerts import DiscordAlerter


@pytest.mark.asyncio
async def test_alert_dispatch_without_webhook_allocates_no_client():
    alerter = DiscordAlerter(webhook_url="")
    assert alerter._client is None
    assert await alerter.dispatch_embed("test", "test", 0, []) is False
    await alerter.close()
