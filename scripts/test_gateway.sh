#!/usr/bin/env bash
set -euo pipefail

GATEWAY_URL="http://127.0.0.1:8545"
SENTINEL_URL="http://127.0.0.1:8000"
STATS_URL="http://127.0.0.1:8404"
STATS_AUTH="admin:driftguard_admin_secure_pass"

GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
NC="\033[0m"

echo -e "${YELLOW}================================================================${NC}"
echo -e "${YELLOW}           DriftGuard Automated Verification Suite              ${NC}"
echo -e "${YELLOW}================================================================${NC}"

# Test 1: Sentinel Liveness
echo -n "[1/7] Testing Sentinel healthz... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${SENTINEL_URL}/healthz" || true)
if [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}PASS (HTTP 200)${NC}"
else
    echo -e "${RED}FAIL (HTTP ${STATUS})${NC}"
    exit 1
fi

# Test 2: Primary Node Health Probe
echo -n "[2/7] Testing Sentinel /healthz/primary probe... "
P_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${SENTINEL_URL}/healthz/primary" || true)
if [ "$P_STATUS" = "200" ]; then
    echo -e "${GREEN}PASS (HTTP 200 - Primary is in-sync)${NC}"
else
    echo -e "${YELLOW}WARN (HTTP ${P_STATUS} - Primary may be syncing or in failover)${NC}"
fi

# Test 3: EVM JSON-RPC eth_blockNumber through HAProxy Gateway
echo -n "[3/7] Testing eth_blockNumber through HAProxy (:8545)... "
BLOCK_RESP=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  "${GATEWAY_URL}")

if echo "$BLOCK_RESP" | grep -q '"result":"0x'; then
    HEX_BLOCK=$(echo "$BLOCK_RESP" | grep -o '"result":"[^"]*"' | cut -d'"' -f4)
    DEC_BLOCK=$((16#${HEX_BLOCK#0x}))
    echo -e "${GREEN}PASS (Block: ${DEC_BLOCK} [${HEX_BLOCK}])${NC}"
else
    echo -e "${RED}FAIL (Unexpected response: ${BLOCK_RESP})${NC}"
    exit 1
fi

# Test 4: EVM JSON-RPC eth_chainId (Verify Sepolia 0xaa36a7)
echo -n "[4/7] Testing eth_chainId verification... "
CHAIN_RESP=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":2}' \
  "${GATEWAY_URL}")

if echo "$CHAIN_RESP" | grep -q '0xaa36a7'; then
    echo -e "${GREEN}PASS (Sepolia ChainID: 11155111 / 0xaa36a7)${NC}"
else
    echo -e "${RED}FAIL (Response: ${CHAIN_RESP})${NC}"
    exit 1
fi

# Test 5: CORS Preflight Handling (OPTIONS -> 204)
echo -n "[5/7] Testing CORS Preflight (OPTIONS)... "
CORS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS \
  -H "Origin: https://app.uniswap.org" \
  -H "Access-Control-Request-Method: POST" \
  "${GATEWAY_URL}")

if [ "$CORS_STATUS" = "204" ]; then
    echo -e "${GREEN}PASS (HTTP 204 No Content)${NC}"
else
    echo -e "${RED}FAIL (HTTP ${CORS_STATUS})${NC}"
    exit 1
fi

# Test 6: Method Whitelist Enforcement (GET -> 405 Method Not Allowed)
echo -n "[6/7] Testing Method Whitelist (GET rejected with 405)... "
GET_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET "${GATEWAY_URL}")
if [ "$GET_STATUS" = "405" ]; then
    echo -e "${GREEN}PASS (HTTP 405 Rejected)${NC}"
else
    echo -e "${RED}FAIL (HTTP ${GET_STATUS})${NC}"
    exit 1
fi

# Test 7: Prometheus Metrics Exporters
echo -n "[7/7] Testing Prometheus Exporter endpoints... "
SENTINEL_METRICS=$(curl -s "${SENTINEL_URL}/metrics" | grep -c "driftguard_" || true)
HAPROXY_METRICS=$(curl -s -u "${STATS_AUTH}" "${STATS_URL}/metrics" | grep -c "haproxy_" || true)

if [ "$SENTINEL_METRICS" -gt 0 ] && [ "$HAPROXY_METRICS" -gt 0 ]; then
    echo -e "${GREEN}PASS (Sentinel: ${SENTINEL_METRICS} metrics, HAProxy: ${HAPROXY_METRICS} metrics)${NC}"
else
    echo -e "${RED}FAIL (Sentinel: ${SENTINEL_METRICS}, HAProxy: ${HAPROXY_METRICS})${NC}"
    exit 1
fi

echo -e "\n${GREEN}✔ All DriftGuard gateway checks passed successfully!${NC}"
