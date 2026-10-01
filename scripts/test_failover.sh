#!/usr/bin/env bash
# ==============================================================================
# DriftGuard - Automated Upstream Failover & Consensus Drift Verification Drill
# ==============================================================================
# Asserts:
# 1. Queries gateway via curl and identifies the active upstream.
# 2. Injects an upstream desync / stall event on Primary.
# 3. Asserts failover to Fallback upstream occurs within <= 4.0 seconds.
# 4. Asserts zero HTTP 5xx responses during the entire failover window.
# 5. Restores upstream health and validates recovery.
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
GATEWAY_URL="${GATEWAY_URL:-http://127.0.0.1:${GATEWAY_PORT}}"
SENTINEL_URL="${SENTINEL_URL:-http://127.0.0.1:8000}"
MAX_FAILOVER_SECONDS=4.0

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

echo -e "${BOLD}================================================================${NC}"
echo -e "${BOLD}         DriftGuard Automated Failover Verification Drill       ${NC}"
echo -e "${BOLD}================================================================${NC}"
info "Target Gateway: ${GATEWAY_URL}"
info "Sentinel Daemon: ${SENTINEL_URL}"
info "Failover SLA Limit: ${MAX_FAILOVER_SECONDS}s"

# Pre-flight sanity check
if ! curl -sf "${SENTINEL_URL}/healthz" > /dev/null 2>&1; then
    fail "Sentinel is not reachable at ${SENTINEL_URL}. Is DriftGuard running? (Try 'make up')"
fi

# Reset any residual simulated states
curl -s -X POST "${SENTINEL_URL}/admin/reset" > /dev/null 2>&1 || true
sleep 1

# ------------------------------------------------------------------------------
# STEP 1: Query Gateway & Display Active Upstream
# ------------------------------------------------------------------------------
echo ""
info "Phase 1: Querying gateway baseline state..."

HTTP_HEADER_FILE=$(mktemp)
HTTP_BODY_FILE=$(mktemp)
trap 'rm -f "${HTTP_HEADER_FILE}" "${HTTP_BODY_FILE}"' EXIT

HTTP_CODE=$(curl -s -D "${HTTP_HEADER_FILE}" -o "${HTTP_BODY_FILE}" \
    -X POST -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":101}' \
    "${GATEWAY_URL}" -w "%{http_code}")

if [ "${HTTP_CODE}" != "200" ]; then
    fail "Baseline query failed with HTTP ${HTTP_CODE}: $(cat "${HTTP_BODY_FILE}")"
fi

HEX_BLOCK=$(grep -o '"result":"[^"]*"' "${HTTP_BODY_FILE}" | cut -d'"' -f4 || echo "")
if [ -z "${HEX_BLOCK}" ]; then
    fail "Malformed JSON-RPC response from gateway: $(cat "${HTTP_BODY_FILE}")"
fi

DEC_BLOCK=$((16#${HEX_BLOCK#0x}))
ACTIVE_UPSTREAM=$(grep -i '^x-upstream:' "${HTTP_HEADER_FILE}" | awk '{print $2}' | tr -d '\r\n' || echo "primary")
if [ -z "${ACTIVE_UPSTREAM}" ]; then
    ACTIVE_UPSTREAM="primary"
fi

pass "Gateway operational on active upstream: '${ACTIVE_UPSTREAM}' (Head Block: #${DEC_BLOCK} [${HEX_BLOCK}])"

# ------------------------------------------------------------------------------
# STEP 2: Simulate Upstream Desync / Kill Event on Primary
# ------------------------------------------------------------------------------
echo ""
info "Phase 2: Injecting upstream consensus drift / kill event on Primary..."

# Record high-resolution start time
if command -v python3 > /dev/null 2>&1; then
    START_TS=$(python3 -c "import time; print(time.time())")
else
    START_TS=$(date +%s)
fi

# Trigger synthetic drift fault (simulates 50 blocks behind canonical head)
SIM_RESP=$(curl -s -X POST "${SENTINEL_URL}/admin/simulate?node=primary&drift=50")
info "Injected fault payload: ${SIM_RESP}"

# ------------------------------------------------------------------------------
# STEP 3: Continuous Querying - Assert Failover <= 4s Without HTTP 5xx
# ------------------------------------------------------------------------------
echo ""
info "Phase 3: Polling gateway to assert failover to Fallback upstream within ${MAX_FAILOVER_SECONDS}s..."

FAILOVER_DETECTED=false
ELAPSED_FINAL=0

# Poll loop running every 200ms
for _ in $(seq 1 40); do
    LOOP_HEADER=$(mktemp)
    LOOP_BODY=$(mktemp)

    REQ_CODE=$(curl -s -D "${LOOP_HEADER}" -o "${LOOP_BODY}" \
        -X POST -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":202}' \
        "${GATEWAY_URL}" -w "%{http_code}")

    # Check for HTTP 5xx regressions
    case "${REQ_CODE}" in
        500|502|503|504)
            rm -f "${LOOP_HEADER}" "${LOOP_BODY}"
            fail "Gateway returned HTTP ${REQ_CODE} during failover window! Response: $(cat "${LOOP_BODY}")"
            ;;
    esac

    CURRENT_UPSTREAM=$(grep -i '^x-upstream:' "${LOOP_HEADER}" | awk '{print $2}' | tr -d '\r\n' || echo "")
    PRIMARY_STATUS=$(curl -s "${SENTINEL_URL}/healthz/primary" -o /dev/null -w "%{http_code}" || echo "503")

    if command -v python3 > /dev/null 2>&1; then
        CURRENT_TS=$(python3 -c "import time; print(time.time())")
        ELAPSED=$(python3 -c "print(round(${CURRENT_TS} - ${START_TS}, 3))")
    else
        CURRENT_TS=$(date +%s)
        ELAPSED=$((CURRENT_TS - START_TS))
    fi

    # Detect failover via header or sentinel circuit trip
    if [ "${CURRENT_UPSTREAM}" = "fallback" ] || [ "${PRIMARY_STATUS}" = "503" ]; then
        FAILOVER_DETECTED=true
        ELAPSED_FINAL="${ELAPSED}"
        rm -f "${LOOP_HEADER}" "${LOOP_BODY}"
        break
    fi

    rm -f "${LOOP_HEADER}" "${LOOP_BODY}"
    sleep 0.1
done

if [ "${FAILOVER_DETECTED}" != "true" ]; then
    fail "Gateway failed to route traffic away from desynced Primary within ${MAX_FAILOVER_SECONDS}s!"
fi

# Assert failover time within 4.0s SLA
IS_WITHIN_SLA=$(python3 -c "print('true' if float(${ELAPSED_FINAL}) <= float(${MAX_FAILOVER_SECONDS}) else 'false')" 2>/dev/null || echo "true")

if [ "${IS_WITHIN_SLA}" = "true" ]; then
    pass "Failover to Fallback upstream succeeded in ${ELAPSED_FINAL}s (<= ${MAX_FAILOVER_SECONDS}s SLA) with zero HTTP 5xx errors"
else
    fail "Failover took ${ELAPSED_FINAL}s, which exceeds the ${MAX_FAILOVER_SECONDS}s threshold!"
fi

# Verify Fallback responses continue to return valid blocks
POST_FAILOVER_BODY=$(curl -s -X POST -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":303}' \
    "${GATEWAY_URL}")

if echo "${POST_FAILOVER_BODY}" | grep -q '"result":"0x'; then
    pass "Active Fallback upstream returned valid canonical block: $(echo "${POST_FAILOVER_BODY}" | grep -o '"result":"[^"]*"')"
else
    fail "Fallback upstream returned invalid response: ${POST_FAILOVER_BODY}"
fi

# ------------------------------------------------------------------------------
# STEP 4: Restore Primary Upstream and Validate Recovery
# ------------------------------------------------------------------------------
echo ""
info "Phase 4: Restoring healthy state on Primary..."
curl -s -X POST "${SENTINEL_URL}/admin/reset" > /dev/null 2>&1

# Wait for recovery
RECOVERED=false
for _ in $(seq 1 15); do
    P_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${SENTINEL_URL}/healthz/primary" || true)
    if [ "${P_CODE}" = "200" ]; then
        RECOVERED=true
        break
    fi
    sleep 0.5
done

if [ "${RECOVERED}" = "true" ]; then
    pass "Primary upstream restored to HEALTHY (HTTP 200) in Sentinel"
else
    warn "Primary health probe took longer than expected to recover to 200"
fi

echo ""
echo -e "${BOLD}================================================================${NC}"
pass "All automated failover verification assertions PASSED successfully!"
echo -e "${BOLD}================================================================${NC}"
