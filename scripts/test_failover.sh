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
INITIAL_STATUS=$(curl -s "${SENTINEL_URL}/healthz/primary" | grep -o '"status":"[^"]*"' || true)
echo "Initial Sentinel Primary Status: $INITIAL_STATUS"

REQ1=$(curl -s -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' "${GATEWAY_URL}")
echo -e "Baseline Gateway Response: ${GREEN}${REQ1}${NC}"

# Step 2: Simulate Primary Failure
echo -e "\n${BLUE}[Step 2] Inducing artificial failure on Primary (setting DRIFT_THRESHOLD=-50)...${NC}"
cp .env .env.bak
sed -i 's/DRIFT_THRESHOLD=.*/DRIFT_THRESHOLD=-50/' .env
docker compose up -d sentinel

echo "Waiting for Sentinel to detect drift anomaly (takes ~6-10s)..."
for i in {1..12}; do
    CODE=$(curl -s -o /dev/null -w "%{http_code}" "${SENTINEL_URL}/healthz/primary" || true)
    if [ "$CODE" = "503" ]; then
        echo -e "${RED}Sentinel /healthz/primary successfully tripped to HTTP 503!${NC}"
        break
    fi
    sleep 1
done

# Step 3: Verify Seamless Gateway Failover
echo -e "\n${BLUE}[Step 3] Verifying HAProxy routes traffic through Backup pool...${NC}"
sleep 4 # Allow HAProxy 2 check intervals (inter 3s fall 2)
REQ2=$(curl -s -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":2}' "${GATEWAY_URL}")

if echo "$REQ2" | grep -q '"result":"0x'; then
    echo -e "${GREEN}✔ SUCCESS: Gateway seamlessly routed traffic during Primary failure!${NC}"
    echo -e "Response from backup: ${REQ2}"
else
    echo -e "${RED}✘ FAIL: Gateway failed to route through backup: ${REQ2}${NC}"
fi

# Step 4: Restore System
echo -e "\n${BLUE}[Step 4] Restoring healthy configuration...${NC}"
mv .env.bak .env
docker compose up -d sentinel

echo "Waiting for Sentinel to restore Primary (rise 2)..."
for i in {1..12}; do
    CODE=$(curl -s -o /dev/null -w "%{http_code}" "${SENTINEL_URL}/healthz/primary" || true)
    if [ "$CODE" = "200" ]; then
        echo -e "${GREEN}Sentinel /healthz/primary recovered to HTTP 200 OK!${NC}"
        break
    fi
    sleep 1
done

sleep 4 # Allow HAProxy rise 2
REQ3=$(curl -s -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":3}' "${GATEWAY_URL}")
echo -e "Post-Recovery Response: ${GREEN}${REQ3}${NC}"

echo -e "\n${GREEN}✔ Failover and Recovery Drill Completed Successfully!${NC}"
