import json

import httpx
import pytest

from sentinel.src.rpc_client import RpcClient


@pytest.mark.asyncio
async def test_probe_validates_json_rpc_envelopes_and_measures_full_probe():
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        results = {"eth_blockNumber": "0x10", "eth_chainId": "0xaa36a7", "eth_syncing": False}
        return httpx.Response(
            200,
            json={"jsonrpc": "2.0", "id": body["id"], "result": results[body["method"]]},
        )

    rpc = RpcClient()
    await rpc.close()
    rpc.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

    sample = await rpc.probe("https://rpc.example")
    await rpc.close()

    assert sample.block_number == 16
    assert sample.chain_id == 11155111
    assert sample.error is None
    assert sample.latency_ms >= 0


@pytest.mark.asyncio
async def test_probe_rejects_mismatched_json_rpc_id():
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": body["id"] + 1, "result": "0x10"})

    rpc = RpcClient()
    await rpc.close()
    rpc.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

    sample = await rpc.probe("https://rpc.example")
    await rpc.close()

    assert sample.block_number is None
    assert "Malformed eth_blockNumber JSON-RPC envelope" in sample.error
