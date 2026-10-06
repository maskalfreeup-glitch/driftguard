#!/usr/bin/env bash
# ==============================================================================
# DriftGuard VPS Sentinel Agent
# Lightweight, zero-dependency monitoring and Discord alerting agent
# Tailored for Oracle Cloud Infrastructure (OCI) micro instances (1 OCPU, 1 GB RAM)
# ==============================================================================

set -euo pipefail

# Load environment configuration if available
if [[ -f "/etc/vps_agent.env" ]]; then
    # shellcheck disable=SC1091
    source "/etc/vps_agent.env"
elif [[ -f "$(dirname "$0")/../.env" ]]; then
    # shellcheck disable=SC1091
    source "$(dirname "$0")/../.env"
elif [[ -f "./.env" ]]; then
    # shellcheck disable=SC1091
    source "./.env"
fi

# Safety guard: prevent accidental execution and metric leaking on local development machines
CURRENT_HOST="$(hostname 2>/dev/null || echo '')"
if [[ "${CURRENT_HOST}" == *"ThinkPad"* ]] && [[ "${2:-}" != "--force-local" ]]; then
    echo "[GUARD] vps_agent.sh is designed to run on the remote Oracle VPS instances, not on your local machine (${CURRENT_HOST})."
    echo "To deploy to a remote VPS, use: ./scripts/deploy_vps_agent.sh dg-node1 (or dg-node2)"
    exit 0
fi

# Configuration & Defaults
WEBHOOK_URL="${DISCORD_VPS_WEBHOOK_URL:-${DISCORD_WEBHOOK_URL:-}}"
NODE_NAME="${NODE_NAME:-$(hostname -s 2>/dev/null || hostname)}"
IP_ADDR="$(curl -s -m 2 http://169.254.169.254/opc/v1/vnics/ 2>/dev/null | grep -o '"publicIp": *"[^"]*"' | head -n1 | cut -d'"' -f4 || curl -s -m 2 ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')"

RAM_WARN_PCT="${RAM_WARN_PCT:-80}"
RAM_CRIT_PCT="${RAM_CRIT_PCT:-90}"
DISK_WARN_PCT="${DISK_WARN_PCT:-85}"
DISK_CRIT_PCT="${DISK_CRIT_PCT:-92}"
CPU_WARN_LOAD="${CPU_WARN_LOAD:-1.8}"
CPU_CRIT_LOAD="${CPU_CRIT_LOAD:-3.0}"
CONTAINERS_TO_CHECK="${CONTAINERS_TO_CHECK:-driftguard-sentinel driftguard-haproxy driftguard-redis}"

STATE_FILE="/tmp/vps_agent_state.env"
TIMESTAMP="$(date -u +"%Y-%m-%d %H:%M:%S UTC")"
ISO_TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

# Colors for Discord Embeds
COLOR_CRITICAL=14689316  # Red (0xE02424)
COLOR_WARNING=16096779   # Amber (0xF59E0B)
COLOR_SUCCESS=3261581    # Green (0x31C48D)
COLOR_INFO=3900150       # Blue (0x3B82F6)

dispatch_discord() {
    local title="$1"
    local desc="$2"
    local color="$3"
    local fields_json="$4"

    if [[ -z "${WEBHOOK_URL}" ]]; then
        echo "[ERROR] No DISCORD_WEBHOOK_URL or DISCORD_VPS_WEBHOOK_URL specified." >&2
        return 1
    fi

    local payload
    payload=$(cat <<EOF
{
  "username": "DriftGuard VPS Sentinel",
  "avatar_url": "https://raw.githubusercontent.com/ethereum/ethereum-org-website/master/src/assets/assets-page/eth-diamond-purple.png",
  "embeds": [
    {
      "title": "${title}",
      "description": "${desc}",
      "color": ${color},
      "fields": ${fields_json},
      "footer": {
        "text": "DriftGuard Node Sentinel • ${NODE_NAME} (${IP_ADDR})"
      },
      "timestamp": "${ISO_TIMESTAMP}"
    }
  ]
}
EOF
)

    curl -s -X POST -H "Content-Type: application/json" \
         -d "${payload}" "${WEBHOOK_URL}" > /dev/null 2>&1 || true
}

get_ram_stats() {
    # Returns: Total_MB Used_MB Percent
    free -m | awk 'NR==2{printf "%d %d %.1f", $2, $3, ($3*100/$2)}'
}

get_disk_stats() {
    # Returns: Total_G Used_G Percent
    df -h / | awk 'NR==2{printf "%s %s %d", $2, $3, $5}'
}

get_cpu_load() {
    # Returns: 1min load average
    awk '{print $1}' /proc/loadavg
}

get_uptime_str() {
    uptime -p 2>/dev/null || uptime | awk -F'( |,|:)+' '{print $6,"hrs",$7,"min"}'
}

get_docker_status() {
    if ! command -v docker >/dev/null 2>&1; then
        echo "Docker not installed"
        return
    fi
    local issues=()
    for c in ${CONTAINERS_TO_CHECK}; do
        if docker ps -a --format '{{.Names}}' | grep -qw "^${c}$"; then
            local state
            state="$(docker inspect -f '{{.State.Status}}' "${c}" 2>/dev/null || echo "unknown")"
            if [[ "${state}" != "running" ]]; then
                issues+=("❌ \`${c}\` is ${state}")
            fi
        fi
    done
    if [[ ${#issues[@]} -eq 0 ]]; then
        echo "All core containers healthy"
    else
        local IFS=", "
        echo "${issues[*]}"
    fi
}

cmd_test() {
    echo "Sending test alert to Discord..."
    local fields
    fields=$(cat <<EOF
[
  {"name": "🖥️ Node", "value": "\`${NODE_NAME}\`", "inline": true},
  {"name": "🌐 Public IP", "value": "\`${IP_ADDR}\`", "inline": true},
  {"name": "⏱️ Uptime", "value": "$(get_uptime_str)", "inline": true},
  {"name": "⚙️ Status", "value": "Test probe completed successfully.", "inline": false}
]
EOF
)
    dispatch_discord "🧪 Test Alert — DriftGuard VPS Sentinel" \
                     "Webhook integration check from **${NODE_NAME}**." \
                     "${COLOR_INFO}" "${fields}"
    echo "Test alert dispatched."
}

cmd_boot() {
    echo "Sending reboot notification to Discord..."
    local kernel
    kernel="$(uname -r)"
    local fields
    fields=$(cat <<EOF
[
  {"name": "🖥️ Host", "value": "\`${NODE_NAME}\` (\`${IP_ADDR}\`)", "inline": true},
  {"name": "🐧 Kernel", "value": "\`${kernel}\`", "inline": true},
  {"name": "⏱️ Boot Time", "value": "${TIMESTAMP}", "inline": false}
]
EOF
)
    dispatch_discord "🔄 System Boot Event — ${NODE_NAME}" \
                     "The VPS instance has started or rebooted." \
                     "${COLOR_INFO}" "${fields}"
}

cmd_report() {
    echo "Generating comprehensive health report for Discord..."
    read -r total_ram used_ram ram_pct <<< "$(get_ram_stats)"
    read -r total_disk used_disk disk_pct <<< "$(get_disk_stats)"
    local load
    load="$(get_cpu_load)"
    local uptime_val
    uptime_val="$(get_uptime_str)"
    local docker_val
    docker_val="$(get_docker_status)"

    local fields
    fields=$(cat <<EOF
[
  {"name": "🖥️ Node / IP", "value": "\`${NODE_NAME}\` (\`${IP_ADDR}\`)", "inline": true},
  {"name": "⏱️ Uptime", "value": "${uptime_val}", "inline": true},
  {"name": "🧠 RAM Usage", "value": "${used_ram} MB / ${total_ram} MB (**${ram_pct}%**)", "inline": true},
  {"name": "📈 CPU Load (1m)", "value": "**${load}**", "inline": true},
  {"name": "💾 Root Disk", "value": "${used_disk} / ${total_ram} (**${disk_pct}%**)", "inline": true},
  {"name": "🐳 Docker Containers", "value": "${docker_val}", "inline": false}
]
EOF
)
    dispatch_discord "📊 VPS Health Snapshot — ${NODE_NAME}" \
                     "Periodic system metrics report from Oracle Cloud VPS." \
                     "${COLOR_SUCCESS}" "${fields}"
    echo "Health snapshot dispatched."
}

cmd_check() {
    read -r total_ram used_ram ram_pct <<< "$(get_ram_stats)"
    read -r total_disk used_disk disk_pct <<< "$(get_disk_stats)"
    local load
    load="$(get_cpu_load)"
    local docker_val
    docker_val="$(get_docker_status)"

    local alert_level="OK"
    local alert_reasons=()

    # RAM Evaluation (float comparison with awk)
    if awk "BEGIN {exit !(${ram_pct} >= ${RAM_CRIT_PCT})}"; then
        alert_level="CRITICAL"
        alert_reasons+=("RAM critical: ${used_ram}MB/${total_ram}MB (${ram_pct}%)")
    elif awk "BEGIN {exit !(${ram_pct} >= ${RAM_WARN_PCT})}"; then
        [[ "${alert_level}" != "CRITICAL" ]] && alert_level="WARNING"
        alert_reasons+=("RAM high: ${used_ram}MB/${total_ram}MB (${ram_pct}%)")
    fi

    # Disk Evaluation
    if [[ "${disk_pct}" -ge "${DISK_CRIT_PCT}" ]]; then
        alert_level="CRITICAL"
        alert_reasons+=("Disk critical: ${used_disk}/${total_disk} (${disk_pct}%)")
    elif [[ "${disk_pct}" -ge "${DISK_WARN_PCT}" ]]; then
        [[ "${alert_level}" != "CRITICAL" ]] && alert_level="WARNING"
        alert_reasons+=("Disk high: ${used_disk}/${total_disk} (${disk_pct}%)")
    fi

    # CPU Evaluation
    if awk "BEGIN {exit !(${load} >= ${CPU_CRIT_LOAD})}"; then
        alert_level="CRITICAL"
        alert_reasons+=("CPU Load critical: ${load} (1m avg)")
    elif awk "BEGIN {exit !(${load} >= ${CPU_WARN_LOAD})}"; then
        [[ "${alert_level}" != "CRITICAL" ]] && alert_level="WARNING"
        alert_reasons+=("CPU Load elevated: ${load} (1m avg)")
    fi

    # Docker Evaluation
    if [[ "${docker_val}" != "All core containers healthy" && "${docker_val}" != "Docker not installed" ]]; then
        alert_level="CRITICAL"
        alert_reasons+=("Containers unhealthy: ${docker_val}")
    fi

    # State management to prevent notification spam
    local prev_state="OK"
    if [[ -f "${STATE_FILE}" ]]; then
        # shellcheck disable=SC1090
        source "${STATE_FILE}"
    fi

    if [[ "${alert_level}" != "OK" ]]; then
        if [[ "${prev_state}" != "${alert_level}" ]]; then
            local color="${COLOR_WARNING}"
            local prefix="⚠️ WARNING"
            if [[ "${alert_level}" == "CRITICAL" ]]; then
                color="${COLOR_CRITICAL}"
                prefix="🚨 CRITICAL ALERT"
            fi

            local issues_str
            issues_str=$(printf "• %s\n" "${alert_reasons[@]}")

            local fields
            fields=$(cat <<EOF
[
  {"name": "🖥️ Node", "value": "\`${NODE_NAME}\` (\`${IP_ADDR}\`)", "inline": true},
  {"name": "🧠 RAM Usage", "value": "${used_ram}MB / ${total_ram}MB (**${ram_pct}%**)", "inline": true},
  {"name": "📈 CPU Load", "value": "**${load}**", "inline": true},
  {"name": "💾 Disk Space", "value": "${used_disk} / ${total_disk} (**${disk_pct}%**)", "inline": true},
  {"name": "🔍 Issues Detected", "value": "${issues_str}", "inline": false}
]
EOF
)
            dispatch_discord "${prefix}: ${NODE_NAME}" \
                             "Resource threshold triggered on Oracle Cloud instance." \
                             "${color}" "${fields}"
            echo "LAST_STATE=\"${alert_level}\"" > "${STATE_FILE}"
        fi
    else
        # If previously alerted and now healthy, send recovery notification
        if [[ "${prev_state}" != "OK" && "${prev_state}" != "" ]]; then
            local fields
            fields=$(cat <<EOF
[
  {"name": "🖥️ Node", "value": "\`${NODE_NAME}\` (\`${IP_ADDR}\`)", "inline": true},
  {"name": "🧠 RAM Usage", "value": "${used_ram}MB / ${total_ram}MB (${ram_pct}%)", "inline": true},
  {"name": "💾 Disk Space", "value": "${used_disk} / ${total_disk} (${disk_pct}%)", "inline": true},
  {"name": "📈 CPU Load", "value": "${load}", "inline": true}
]
EOF
)
            dispatch_discord "✅ RECOVERY: ${NODE_NAME} Healthy" \
                             "All system metrics and services have returned to nominal levels." \
                             "${COLOR_SUCCESS}" "${fields}"
            echo "LAST_STATE=\"OK\"" > "${STATE_FILE}"
        fi
    fi
}

# Entrypoint routing
ACTION="${1:-check}"
case "${ACTION}" in
    check)
        cmd_check
        ;;
    report)
        cmd_report
        ;;
    boot)
        cmd_boot
        ;;
    test)
        cmd_test
        ;;
    *)
        echo "Usage: $0 [check|report|boot|test]"
        exit 1
        ;;
esac
