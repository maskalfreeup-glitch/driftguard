#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
if [ -f "${PROJECT_ROOT}/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "${PROJECT_ROOT}/.env"
    set +a
fi

GATEWAY_URL="${GATEWAY_URL:-http://127.0.0.1:${GATEWAY_PORT:-8545}}"
SEPOLIA_GATEWAY_URL="${GATEWAY_URL%/}/sepolia"
SENTINEL_URL="${SENTINEL_URL:-http://127.0.0.1:${SENTINEL_PORT:-8000}}"
STATS_URL="${STATS_URL:-http://127.0.0.1:${HAPROXY_STATS_PORT:-8404}}"
STATS_AUTH="${STATS_USER:-admin}:${STATS_PASSWORD:?Set STATS_PASSWORD in .env}"
EXPECTED_CHAIN_ID="${EXPECTED_CHAIN_ID:-11155111}"

GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
NC="\033[0m"

echo -e "${YELLOW}================================================================${NC}"
echo -e "${YELLOW}        DriftGuard Multi-Chain Gateway Verification Suite        ${NC}"
echo -e "${YELLOW}================================================================${NC}"

# Test 1: Sentinel Liveness
echo -n "[1/8] Testing Sentinel healthz... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${SENTINEL_URL}/healthz" || true)
if [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}PASS (HTTP 200)${NC}"
else
    echo -e "${RED}FAIL (HTTP ${STATUS})${NC}"
    exit 1
fi

# Test 2: Primary Node Health Probe
echo -n "[2/8] Testing Sentinel /healthz/primary probe... "
P_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${SENTINEL_URL}/healthz/primary" || true)
if [ "$P_STATUS" = "200" ]; then
    echo -e "${GREEN}PASS (HTTP 200 - Primary is in-sync)${NC}"
else
    echo -e "${YELLOW}WARN (HTTP ${P_STATUS} - Primary may be syncing or in failover)${NC}"
fi

# Test 3: EVM JSON-RPC eth_blockNumber through HAProxy Gateway
echo -n "[3/8] Testing eth_blockNumber through HAProxy (:8545)... "
BLOCK_RESP=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  "${SEPOLIA_GATEWAY_URL}")

if echo "$BLOCK_RESP" | grep -q '"result":"0x'; then
    HEX_BLOCK=$(echo "$BLOCK_RESP" | grep -o '"result":"[^"]*"' | cut -d'"' -f4)
    DEC_BLOCK=$((16#${HEX_BLOCK#0x}))
    echo -e "${GREEN}PASS (Block: ${DEC_BLOCK} [${HEX_BLOCK}])${NC}"
else
    echo -e "${RED}FAIL (Unexpected response: ${BLOCK_RESP})${NC}"
    exit 1
fi

# Test 4: Path-based routing and chain identity for all configured networks.
check_chain_id() {
    local path="$1" expected="$2" response
    local expected_hex
    expected_hex="$(printf '0x%x' "${expected}")"
    response=$(curl -sS -X POST -H "Content-Type: application/json" \
      -d '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":2}' \
      "${GATEWAY_URL%/}/${path}")
    if echo "${response}" | grep -qi "\"result\":\"${expected_hex}\""; then
        echo -e "${GREEN}PASS (${path}: chain ID ${expected} / ${expected_hex})${NC}"
    else
        echo -e "${RED}FAIL (${path}: expected ${expected_hex}, response: ${response})${NC}"
        exit 1
    fi
}

echo "[4/8] Checking chain identity by route..."
check_chain_id "base" 8453
check_chain_id "arb" 42161
check_chain_id "arbitrum" 42161
check_chain_id "sepolia" "${EXPECTED_CHAIN_ID}"

# Test 5: CORS Preflight Handling (OPTIONS -> 204)
echo -n "[5/8] Testing CORS Preflight (OPTIONS)... "
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

# Test 6: Method Whitelist Enforcement (DELETE rejected with 405, GET returns landing page)
echo -n "[6/8] Testing Method Whitelist (DELETE rejected with 405)... "
DEL_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "${GATEWAY_URL}")
GET_BODY=$(curl -s -X GET "${GATEWAY_URL}")

if [ "$DEL_STATUS" = "405" ] && echo "$GET_BODY" | grep -q "SYSTEM OPERATIONAL"; then
    echo -e "${GREEN}PASS (DELETE -> 405, GET -> Landing Page 200)${NC}"
else
    echo -e "${RED}FAIL (DELETE HTTP: ${DEL_STATUS})${NC}"
    exit 1
fi

# Test 7: Prometheus Metrics Exporters
echo -n "[7/8] Testing unknown chain route rejection (404)... "
UNKNOWN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":3}' \
  "${GATEWAY_URL%/}/unknown")
if [ "${UNKNOWN_STATUS}" = "404" ]; then
    echo -e "${GREEN}PASS (Unknown route -> 404)${NC}"
else
    echo -e "${RED}FAIL (Unknown route HTTP ${UNKNOWN_STATUS})${NC}"
    exit 1
fi

echo -n "[8/8] Testing Prometheus Exporter endpoints... "
SENTINEL_METRICS=$(curl -s "${SENTINEL_URL}/metrics" | grep -c "driftguard_" || true)
HAPROXY_METRICS=$(curl -s -u "${STATS_AUTH}" "${STATS_URL}/metrics" | grep -c "haproxy_" || true)

if [ "$SENTINEL_METRICS" -gt 0 ] && [ "$HAPROXY_METRICS" -gt 0 ]; then
    echo -e "${GREEN}PASS (Sentinel: ${SENTINEL_METRICS} metrics, HAProxy: ${HAPROXY_METRICS} metrics)${NC}"
else
    echo -e "${RED}FAIL (Sentinel: ${SENTINEL_METRICS}, HAProxy: ${HAPROXY_METRICS})${NC}"
    exit 1
fi

echo -e "\n${GREEN}✔ All DriftGuard gateway checks passed successfully!${NC}"
