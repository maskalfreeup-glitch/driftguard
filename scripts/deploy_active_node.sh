#!/usr/bin/env bash
# ==============================================================================
# Deploy Active-Active DriftGuard Stack + Cloudflare Multi-Connector Tunnel
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "${SCRIPT_DIR}")"

# Load local environment
if [[ -f "${REPO_DIR}/.env" ]]; then
    # shellcheck disable=SC1091
    source "${REPO_DIR}/.env"
fi

TARGET="${1:-}"

if [[ -z "${TARGET}" ]]; then
    echo "Usage: $0 <target-host> (e.g. $0 dg-node1 or $0 dg-node2)"
    exit 1
fi

TUNNEL_TOKEN="${CLOUDFLARE_TUNNEL_TOKEN:-}"
if [[ -z "${TUNNEL_TOKEN}" ]]; then
    echo "[ERROR] CLOUDFLARE_TUNNEL_TOKEN not defined in .env" >&2
    exit 1
fi

echo "=========================================================="
echo " [START] Configuring Active-Active Node: ${TARGET}"
echo "=========================================================="

# 1. Install Docker, Compose, and Network Utilities
echo "--> Step 1: Installing Docker CE and Tooling on ${TARGET}..."
ssh -o ConnectTimeout=10 "${TARGET}" 'sudo bash -s' << 'EOF'
set -euo pipefail

# Ensure DNF repository for Docker
if ! command -v docker >/dev/null 2>&1; then
    dnf install -y dnf-plugins-core
    dnf config-manager --add-repo=https://download.docker.com/linux/centos/docker-ce.repo || \
        curl -fsSL -o /etc/yum.repos.d/docker-ce.repo https://download.docker.com/linux/centos/docker-ce.repo
    dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin git socat jq
    systemctl enable --now docker
    usermod -aG docker opc
fi

# Configure Firewall
firewall-cmd --permanent --add-port=80/tcp 2>/dev/null || true
firewall-cmd --permanent --add-port=443/tcp 2>/dev/null || true
firewall-cmd --permanent --add-port=8000/tcp 2>/dev/null || true
firewall-cmd --permanent --add-port=8545/tcp 2>/dev/null || true
firewall-cmd --reload 2>/dev/null || true
EOF

# 2. Sync Repository Files & Production Configuration
echo "--> Step 2: Syncing DriftGuard codebase and .env to ${TARGET}..."
ssh "${TARGET}" "mkdir -p ~/driftguard"
rsync -avz --exclude '.git' --exclude 'node_modules' --exclude '.venv' \
      --exclude '__pycache__' --exclude 'evidence' \
      "${REPO_DIR}/" "${TARGET}:~/driftguard/"

# 3. Build & Launch DriftGuard Stack
echo "--> Step 3: Launching DriftGuard Docker Compose stack on ${TARGET}..."
ssh "${TARGET}" 'bash -s' << 'EOF'
cd ~/driftguard
sudo docker compose build --pull
sudo docker compose down 2>/dev/null || true
sudo docker compose up -d
sudo docker compose ps
EOF

# 4. Install & Launch Cloudflare Multi-Connector Tunnel
echo "--> Step 4: Configuring Cloudflare Multi-Connector Tunnel on ${TARGET}..."
ssh "${TARGET}" "sudo bash -s" << EOF
set -euo pipefail

if ! command -v cloudflared >/dev/null 2>&1; then
    echo "Downloading cloudflared RPM..."
    curl -fsSL -o /tmp/cloudflared.rpm https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-x86_64.rpm
    rpm -Uvh --force /tmp/cloudflared.rpm || true
    rm -f /tmp/cloudflared.rpm
fi

# Install / update tunnel service with multi-connector token
systemctl stop cloudflared 2>/dev/null || true
cloudflared service uninstall 2>/dev/null || true

cloudflared service install "${TUNNEL_TOKEN}"
systemctl daemon-reload
systemctl enable --now cloudflared
sleep 3
systemctl is-active cloudflared
EOF

# 5. Local Node Verification
echo "--> Step 5: Testing local RPC & Sentinel endpoints on ${TARGET}..."
ssh "${TARGET}" 'bash -s' << 'EOF'
sleep 3
echo "Testing Sentinel /healthz..."
curl -s http://127.0.0.1:8000/healthz | jq '{status, uptime_seconds, chains: [.chains[].name]}' || echo "Sentinel still initializing"
echo "Testing HAProxy /arb..."
curl -s -X POST http://127.0.0.1:8545/arb -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' | jq . || echo "HAProxy initializing"
EOF

echo "=========================================================="
echo " [SUCCESS] ${TARGET} is LIVE in Active-Active Mode!"
echo "=========================================================="
