#!/usr/bin/env bash
# ==============================================================================
# Full DriftGuard Deployment Orchestrator for Node 2
# ==============================================================================

set -euo pipefail

NODE="dg-node2"
REPO_URL="https://github.com/maskalfreeup-glitch/driftguard.git"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DRIFTGUARD_DIR="$(dirname "${SCRIPT_DIR}")"

echo "=========================================================="
echo " Step 1: Testing SSH Connection to ${NODE}..."
echo "=========================================================="
if ! ssh -o ConnectTimeout=10 "${NODE}" "uname -a" 2>/dev/null; then
    echo "[ERROR] Cannot connect to ${NODE} via SSH."
    echo "Please verify instance status in Oracle Cloud Console."
    exit 1
fi

echo "=========================================================="
echo " Step 2: Provisioning Swap, Docker, and Firewall on ${NODE}..."
echo "=========================================================="
ssh "${NODE}" "sudo bash -s" < "${SCRIPT_DIR}/setup_node2.sh"

echo "=========================================================="
echo " Step 3: Cloning Repository & Syncing Production .env    "
echo "=========================================================="
ssh "${NODE}" "rm -rf ~/driftguard && git clone ${REPO_URL} ~/driftguard"
scp "${DRIFTGUARD_DIR}/.env" "${NODE}:~/driftguard/.env"

echo "=========================================================="
echo " Step 4: Building & Launching DriftGuard Containers       "
echo "=========================================================="
ssh "${NODE}" "cd ~/driftguard && sudo docker compose build && sudo docker compose up -d"

echo "=========================================================="
echo " Step 5: Verifying Swap Allocation & Docker Status        "
echo "=========================================================="
ssh "${NODE}" "free -h"
ssh "${NODE}" "sudo docker ps"

echo "=========================================================="
echo " Step 6: Probing Sentinel API on Node 2                   "
echo "=========================================================="
sleep 5
ssh "${NODE}" "curl -s http://localhost:8000/healthz | jq . || curl -s http://localhost:8000/status | jq ."

echo "=========================================================="
echo " [SUCCESS] DriftGuard Stack deployed successfully on Node 2!"
echo "=========================================================="
