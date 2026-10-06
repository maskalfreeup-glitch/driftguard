#!/usr/bin/env bash
# ==============================================================================
# Deploy DriftGuard VPS Sentinel Agent to Remote Oracle VPS
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "${SCRIPT_DIR}")"

# Load local environment for DISCORD_WEBHOOK_URL
if [[ -f "${REPO_DIR}/.env" ]]; then
    # shellcheck disable=SC1091
    source "${REPO_DIR}/.env"
fi

WEBHOOK_URL="${DISCORD_VPS_WEBHOOK_URL:-${DISCORD_WEBHOOK_URL:-}}"
TARGET="${1:-}"

if [[ -z "${TARGET}" ]]; then
    echo "Usage: $0 <ssh-host-alias-or-ip> (e.g., $0 dg-node1 or $0 dg-node2)"
    exit 1
fi

if [[ -z "${WEBHOOK_URL}" ]]; then
    echo "[ERROR] No DISCORD_WEBHOOK_URL or DISCORD_VPS_WEBHOOK_URL found in ${REPO_DIR}/.env" >&2
    exit 1
fi

echo "=========================================================="
echo " Deploying VPS Sentinel to: ${TARGET}"
echo " Webhook: ${WEBHOOK_URL:0:45}..."
echo "=========================================================="

# 1. Copy vps_agent.sh to remote host
echo "--> Uploading vps_agent.sh to ${TARGET}..."
scp -o ConnectTimeout=10 "${SCRIPT_DIR}/vps_agent.sh" "${TARGET}:/tmp/vps_agent.sh"

# 2. Configure environment, permissions, and systemd timers on remote host
echo "--> Configuring systemd services and timers on ${TARGET}..."
ssh -o ConnectTimeout=10 "${TARGET}" << EOF
sudo mv /tmp/vps_agent.sh /usr/local/bin/vps_agent.sh
sudo chmod +x /usr/local/bin/vps_agent.sh

# Write configuration
sudo mkdir -p /etc
cat << 'ENVFILE' | sudo tee /etc/vps_agent.env > /dev/null
NODE_NAME="${TARGET}"
DISCORD_VPS_WEBHOOK_URL="${WEBHOOK_URL}"
RAM_WARN_PCT=80
RAM_CRIT_PCT=90
DISK_WARN_PCT=85
DISK_CRIT_PCT=92
CPU_WARN_LOAD=1.8
CPU_CRIT_LOAD=3.0
ENVFILE
sudo chmod 644 /etc/vps_agent.env

# 1. Periodic Metric Checker (runs every 5 minutes)
cat << 'SERVICE' | sudo tee /etc/systemd/system/vps-agent.service > /dev/null
[Unit]
Description=DriftGuard VPS Health Sentinel Checker
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/vps_agent.sh check
StandardOutput=journal
StandardError=journal
SERVICE

cat << 'TIMER' | sudo tee /etc/systemd/system/vps-agent.timer > /dev/null
[Unit]
Description=Run VPS Health Sentinel every 5 minutes

[Timer]
OnBootSec=2min
OnUnitActiveSec=5min
AccuracySec=30s

[Install]
WantedBy=timers.target
TIMER

# 2. Boot / Reboot Alert Service
cat << 'BOOTSERVICE' | sudo tee /etc/systemd/system/vps-boot-alert.service > /dev/null
[Unit]
Description=DriftGuard VPS Reboot Notification
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStartPre=/bin/sleep 10
ExecStart=/usr/local/bin/vps_agent.sh boot

[Install]
WantedBy=multi-user.target
BOOTSERVICE

# 3. Daily Health Snapshot Report (runs once a day at 09:00 UTC)
cat << 'DAILYSERVICE' | sudo tee /etc/systemd/system/vps-daily-report.service > /dev/null
[Unit]
Description=DriftGuard VPS Daily Health Report

[Service]
Type=oneshot
ExecStart=/usr/local/bin/vps_agent.sh report
DAILYSERVICE

cat << 'DAILYTIMER' | sudo tee /etc/systemd/system/vps-daily-report.timer > /dev/null
[Unit]
Description=Run VPS Daily Report at 09:00 UTC

[Timer]
OnCalendar=*-*-* 09:00:00 UTC
Persistent=true

[Install]
WantedBy=timers.target
DAILYTIMER

# Reload and enable systemd units
sudo systemctl daemon-reload
sudo systemctl enable --now vps-agent.timer
sudo systemctl enable vps-boot-alert.service
sudo systemctl enable --now vps-daily-report.timer

# Send initial test verification alert
echo "--> Sending test alert from remote instance..."
/usr/local/bin/vps_agent.sh test
EOF

echo "=========================================================="
echo " [SUCCESS] VPS Sentinel installed and active on ${TARGET}!"
echo "=========================================================="
