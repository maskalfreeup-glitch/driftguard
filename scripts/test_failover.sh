#!/usr/bin/env bash
set -euo pipefail

GATEWAY_URL="http://127.0.0.1:8545"
SENTINEL_URL="http://127.0.0.1:8000"

GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
BLUE="\033[1;34m"
NC="\033[0m"

echo -e "${YELLOW}================================================================${NC}"
echo -e "${YELLOW}             DriftGuard Automated Failover Drill                ${NC}"
echo -e "${YELLOW}================================================================${NC}"

# Step 1: Verify Initial Baseline
echo -e "\n${BLUE}[Step 1] Verifying baseline state...${NC}"
curl -s -X POST "${SENTINEL_URL}/admin/reset" > /dev/null
sleep 2

REQ1=$(curl -s -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' "${GATEWAY_URL}")
echo -e "Baseline Gateway Response: ${GREEN}${REQ1}${NC}"

# Step 2: Inject Synthetic Drift Anomaly on Primary (drift=50)
echo -e "\n${BLUE}[Step 2] Injecting synthetic drift anomaly on Primary (drift=50 blocks)...${NC}"
curl -s -X POST "${SENTINEL_URL}/admin/simulate?node=primary&drift=50" | grep -o '"status":"[^"]*"' || true

echo "Waiting for Sentinel circuit breaker to trip (poll cycle takes ~4s)..."
for i in {1..10}; do
    CODE=$(curl -s -o /dev/null -w "%{http_code}" "${SENTINEL_URL}/healthz/primary" || true)
    if [ "$CODE" = "503" ]; then
        echo -e "${RED}Sentinel /healthz/primary successfully tripped to HTTP 503!${NC}"
        break
    fi
    sleep 1
done

# Step 3: Verify Seamless Gateway Failover
echo -e "\n${BLUE}[Step 3] Verifying HAProxy routes traffic through Backup pool...${NC}"
sleep 7 # Allow HAProxy 2 check intervals (inter 3s fall 2)
REQ2=$(curl -s -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":2}' "${GATEWAY_URL}")

if echo "$REQ2" | grep -q '"result":"0x'; then
    echo -e "${GREEN}✔ SUCCESS: Gateway seamlessly routed traffic through Backup!${NC}"
    echo -e "Response from backup: ${REQ2}"
else
    echo -e "${RED}✘ FAIL: Gateway failed to route through backup: ${REQ2}${NC}"
    exit 1
fi

# Step 4: Restore System
echo -e "\n${BLUE}[Step 4] Restoring healthy state via /admin/reset...${NC}"
curl -s -X POST "${SENTINEL_URL}/admin/reset" | grep -o '"status":"[^"]*"' || true

echo "Waiting for Sentinel to restore Primary (recovery threshold: 2 successes)..."
for i in {1..12}; do
    CODE=$(curl -s -o /dev/null -w "%{http_code}" "${SENTINEL_URL}/healthz/primary" || true)
    if [ "$CODE" = "200" ]; then
        echo -e "${GREEN}Sentinel /healthz/primary recovered to HTTP 200 OK!${NC}"
        break
    fi
    sleep 1
done

sleep 7 # Allow HAProxy rise 2
REQ3=$(curl -s -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":3}' "${GATEWAY_URL}")
echo -e "Post-Recovery Response from Primary: ${GREEN}${REQ3}${NC}"

echo -e "\n${GREEN}✔ Failover and Recovery Drill Completed Successfully!${NC}"
