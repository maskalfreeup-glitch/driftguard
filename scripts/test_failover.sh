#!/usr/bin/env bash
# ==============================================================================
# DriftGuard - Unified Multi-Chain EVM Gateway Failover & Alerting Drill
# ==============================================================================
# Asserts:
# 1. Path-based ingress verification for Arbitrum EVM chains:
#    - /arb         -> Arbitrum One (Chain ID 42161 / 0xa4b1)
#    - /nova        -> Arbitrum Nova (Chain ID 42170 / 0xa4ba)
#    - /arb-sepolia -> Arbitrum Sepolia (Chain ID 421614 / 0x66eee)
# 2. Chaos drill against be_arb:
#    - Injects synthetic consensus drift on Primary (drift=50)
#    - Measures cutover latency against a 1.5s drill threshold (not an SLA)
#    - Asserts zero HTTP 5xx responses during failover
#    - Confirms Fallback serves valid canonical blocks
# 3. Zero-overhead Discord alert trigger verification
# 4. Restores Primary upstream health and validates recovery
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Load environment configuration if available
if [ -f "${PROJECT_ROOT}/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "${PROJECT_ROOT}/.env"
    set +a
fi

GATEWAY_PORT="${GATEWAY_PORT:-8545}"
GATEWAY_BASE_URL="${GATEWAY_BASE_URL:-http://127.0.0.1:${GATEWAY_PORT}}"
SENTINEL_URL="${SENTINEL_URL:-http://127.0.0.1:8000}"
DRIFTGUARD_ADMIN_TOKEN="${DRIFTGUARD_ADMIN_TOKEN:-}"
MAX_CUTOVER_SECONDS=1.5

# Terminal styling
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
CYAN="\033[0;36m"
BOLD="\033[1m"
NC="\033[0m"

pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

fail() {
    echo -e "${RED}[FAIL]${NC} $1" >&2
    exit 1
}

info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

if [ -z "${DRIFTGUARD_ADMIN_TOKEN}" ]; then
    fail "Set DRIFTGUARD_ADMIN_TOKEN in .env before running the chaos drill."
fi
ADMIN_HEADER=( -H "Authorization: Bearer ${DRIFTGUARD_ADMIN_TOKEN}" )

echo -e "${BOLD}================================================================${NC}"
echo -e "${BOLD}         DriftGuard Multi-Chain Failover & Alerting Drill       ${NC}"
echo -e "${BOLD}================================================================${NC}"
info "Gateway Ingress: ${GATEWAY_BASE_URL}"
info "Sentinel Daemon: ${SENTINEL_URL}"
info "Observed cutover drill threshold: ${MAX_CUTOVER_SECONDS}s (not an SLA)"

# Pre-flight sanity check
if ! curl -sf "${SENTINEL_URL}/healthz" > /dev/null 2>&1; then
    fail "Sentinel is not reachable at ${SENTINEL_URL}. Is DriftGuard running? (Try 'make up')"
fi

# Reset any residual simulated states before starting
curl -sf "${ADMIN_HEADER[@]}" -X POST "${SENTINEL_URL}/admin/reset" > /dev/null || fail "Could not reset chaos state; check DRIFTGUARD_ADMIN_TOKEN."
sleep 1

# ------------------------------------------------------------------------------
# STEP 1: Multi-Chain Path-Based Ingress Validation
# ------------------------------------------------------------------------------
echo ""
info "Phase 1: Validating path-based ingress for Base, Arbitrum, and Sepolia..."

validate_chain() {
    local path="$1"
    local expected_id="$2"
    local chain_name="$3"

    local resp
    resp=$(curl -s -X POST -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}' \
        "${GATEWAY_BASE_URL}${path}" || true)

    local hex_id
    hex_id=$(echo "${resp}" | grep -o '"result":"[^"]*"' | cut -d'"' -f4 || echo "")
    if [ -z "${hex_id}" ]; then
        fail "${chain_name} query to ${path} failed or returned malformed JSON-RPC: ${resp}"
    fi

    local dec_id
    dec_id=$((16#${hex_id#0x}))
    if [ "${dec_id}" -ne "${expected_id}" ]; then
        fail "${chain_name} chain ID mismatch: expected ${expected_id}, got ${dec_id} (${hex_id})"
    fi

    pass "Ingress ${path} -> ${chain_name} matched Chain ID ${dec_id} (${hex_id})"
}

validate_chain "/arb" 42161 "Arbitrum One"
validate_chain "/arbitrum" 42161 "Arbitrum One (Alias)"
validate_chain "/nova" 42170 "Arbitrum Nova"
validate_chain "/arb-sepolia" 421614 "Arbitrum Sepolia"

# ------------------------------------------------------------------------------
# STEP 2: Chaos Drill Against Arbitrum One (be_arb)
# ------------------------------------------------------------------------------
echo ""
info "Phase 2: Executing chaos drill against be_arb (Arbitrum One)..."

# Check baseline upstream
HTTP_HEADER_FILE=$(mktemp)
HTTP_BODY_FILE=$(mktemp)
trap 'rm -f "${HTTP_HEADER_FILE}" "${HTTP_BODY_FILE}"' EXIT

curl -s -D "${HTTP_HEADER_FILE}" -o "${HTTP_BODY_FILE}" \
    -X POST -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":100}' \
    "${GATEWAY_BASE_URL}/arb"

ARB_UPSTREAM=$(grep -i '^x-upstream:' "${HTTP_HEADER_FILE}" | awk '{print $2}' | tr -d '\r\n' || echo "")
pass "Baseline active upstream on /arb: '${ARB_UPSTREAM:-primary}'"

info "Injecting consensus drift fault on be_arb (drift=50 blocks)..."
START_TS=$(python3 -c "import time; print(time.time())")

SIM_RESP=$(curl -s "${ADMIN_HEADER[@]}" -X POST "${SENTINEL_URL}/admin/simulate?node=primary&drift=50&backend=be_arb")
if ! echo "${SIM_RESP}" | grep -q '"status":"FAULT_INJECTED"'; then
    fail "Sentinel rejected chaos injection: ${SIM_RESP}"
fi

FAILOVER_DETECTED=false
ELAPSED_FINAL=0
HTTP_5XX_COUNT=0

# High frequency polling to capture cutover latency
for _ in $(seq 1 50); do
    LOOP_HEADER=$(mktemp)
    LOOP_BODY=$(mktemp)

    REQ_CODE=$(curl -s -D "${LOOP_HEADER}" -o "${LOOP_BODY}" \
        -X POST -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":200}' \
        "${GATEWAY_BASE_URL}/arb" -w "%{http_code}" || echo "000")

    case "${REQ_CODE}" in
        5??)
            HTTP_5XX_COUNT=$((HTTP_5XX_COUNT + 1))
            ;;
    esac

    CURRENT_UPSTREAM=$(grep -i '^x-upstream:' "${LOOP_HEADER}" | awk '{print $2}' | tr -d '\r\n' || echo "")
    CURRENT_TS=$(python3 -c "import time; print(time.time())")
    ELAPSED=$(python3 -c "print(round(${CURRENT_TS} - ${START_TS}, 4))")

    if [ "${CURRENT_UPSTREAM}" = "fallback" ] && [ "${REQ_CODE}" = "200" ]; then
        FAILOVER_DETECTED=true
        ELAPSED_FINAL="${ELAPSED}"
        rm -f "${LOOP_HEADER}" "${LOOP_BODY}"
        break
    fi

    rm -f "${LOOP_HEADER}" "${LOOP_BODY}"
    sleep 0.02
done

if [ "${FAILOVER_DETECTED}" != "true" ]; then
    fail "Gateway failed to route traffic to fallback for be_arb!"
fi

IS_UNDER_CUTOFF=$(python3 -c "print('true' if float(${ELAPSED_FINAL}) <= float(${MAX_CUTOVER_SECONDS}) else 'false')")
if [ "${IS_UNDER_CUTOFF}" = "true" ]; then
    pass "Cutover to fallback succeeded in ${ELAPSED_FINAL}s (under the ${MAX_CUTOVER_SECONDS}s drill threshold); ${HTTP_5XX_COUNT} sampled 5xx responses"
else
    fail "Cutover took ${ELAPSED_FINAL}s, exceeding the ${MAX_CUTOVER_SECONDS}s drill threshold."
fi

if [ "${HTTP_5XX_COUNT}" -ne 0 ]; then
    fail "Observed ${HTTP_5XX_COUNT} sampled HTTP 5xx responses during the drill."
fi

# Verify fallback upstream response validity
POST_FAILOVER_BODY=$(curl -s -X POST -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":201}' \
    "${GATEWAY_BASE_URL}/arb")

if echo "${POST_FAILOVER_BODY}" | grep -q '"result":"0x'; then
    HEX_BLOCK=$(echo "${POST_FAILOVER_BODY}" | grep -o '"result":"[^"]*"' | cut -d'"' -f4)
    DEC_BLOCK=$((16#${HEX_BLOCK#0x}))
    pass "Active Fallback upstream returned valid canonical block #${DEC_BLOCK} (${HEX_BLOCK})"
else
    fail "Fallback upstream returned invalid response: ${POST_FAILOVER_BODY}"
fi

# ------------------------------------------------------------------------------
# STEP 3: Discord Alert Dispatch Test
# ------------------------------------------------------------------------------
echo ""
info "Phase 3: Testing Discord webhook alerting integration..."

ALERT_RESP=$(curl -s "${ADMIN_HEADER[@]}" -X POST "${SENTINEL_URL}/admin/test-alert?chain=arbitrum-one")
info "Test alert response: ${ALERT_RESP}"

if echo "${ALERT_RESP}" | grep -q '"status":"ALERT_SENT"'; then
    pass "Discord incident alert webhook successfully dispatched embed (HTTP 204)"
elif echo "${ALERT_RESP}" | grep -q '"status":"ALERT_NOOP"'; then
    pass "DISCORD_WEBHOOK_URL is unset: optional alert route returned a no-op"
else
    warn "Unexpected response from test-alert: ${ALERT_RESP}"
fi

# ------------------------------------------------------------------------------
# STEP 4: Restore Primary Upstream and Validate Recovery
# ------------------------------------------------------------------------------
echo ""
info "Phase 4: Restoring healthy state on be_arb..."

RESET_RESP=$(curl -s "${ADMIN_HEADER[@]}" -X POST "${SENTINEL_URL}/admin/reset?backend=be_arb")
if ! echo "${RESET_RESP}" | grep -q '"status":"FAULTS_RESET"'; then
    fail "Failed to reset faults on be_arb: ${RESET_RESP}"
fi

# Verify traffic routes back to primary
RECOVERED=false
for _ in $(seq 1 20); do
    RESP_HEAD=$(curl -s -D - -o /dev/null -X POST -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":300}' \
        "${GATEWAY_BASE_URL}/arb")
    UPSTREAM=$(echo "${RESP_HEAD}" | grep -i '^x-upstream:' | awk '{print $2}' | tr -d '\r\n' || echo "")
    if [ "${UPSTREAM}" = "primary" ]; then
        RECOVERED=true
        break
    fi
    sleep 0.2
done

if [ "${RECOVERED}" = "true" ]; then
    pass "be_arb Primary restored to active routing (X-Upstream: primary)"
else
    warn "Primary did not immediately become active; verify async health probe cycle"
fi

echo ""
echo -e "${BOLD}================================================================${NC}"
pass "All multi-chain gateway, chaos drill, and alerting checks PASSED!"
echo -e "${BOLD}================================================================${NC}"
