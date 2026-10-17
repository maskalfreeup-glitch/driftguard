#!/usr/bin/env bash
set -euo pipefail

# DriftGuard - Automated Telemetry Service Installer
# Sets up systemd timer or cron job for 15-second EVM consensus probes.

MODE="${1:-timer}" # Options: timer, daemon, cron, test
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=========================================================="
echo " DriftGuard Telemetry Service Installer"
echo " Project Directory: ${PROJECT_DIR}"
echo " Mode: ${MODE}"
echo "=========================================================="

# 1. Setup local database storage directory
if [ "$(id -u)" -eq 0 ]; then
    mkdir -p /var/lib/driftguard
    chmod 777 /var/lib/driftguard
    echo "✓ Initialized /var/lib/driftguard directory."
else
    if sudo -n true 2>/dev/null; then
        sudo mkdir -p /var/lib/driftguard
        sudo chmod 777 /var/lib/driftguard
        echo "✓ Initialized /var/lib/driftguard directory (via sudo)."
    else
        mkdir -p "${HOME}/.driftguard"
        echo "ℹ Non-root execution: fallback database available at ${HOME}/.driftguard"
    fi
fi

# 2. Check HAProxy socket symlink
if [ ! -e "/var/run/haproxy.sock" ]; then
    DOCKER_SOCK="/var/lib/docker/volumes/driftguard_haproxy_socket/_data/admin.sock"
    if [ -S "${DOCKER_SOCK}" ]; then
        if [ "$(id -u)" -eq 0 ]; then
            ln -sf "${DOCKER_SOCK}" /var/run/haproxy.sock
            echo "✓ Linked HAProxy socket to /var/run/haproxy.sock"
        elif sudo -n true 2>/dev/null; then
            sudo ln -sf "${DOCKER_SOCK}" /var/run/haproxy.sock
            echo "✓ Linked HAProxy socket to /var/run/haproxy.sock (via sudo)"
        fi
    fi
fi

# 3. Configure service based on chosen mode
if [ "${MODE}" = "timer" ]; then
    echo "Configuring systemd 15-second timer..."
    if [ "$(id -u)" -eq 0 ]; then
        cp "${PROJECT_DIR}/deploy/driftguard-telemetry.service" /etc/systemd/system/
        cp "${PROJECT_DIR}/deploy/driftguard-telemetry.timer" /etc/systemd/system/
        systemctl daemon-reload
        systemctl enable --now driftguard-telemetry.timer
        echo "✓ Systemd timer enabled and started."
        systemctl status driftguard-telemetry.timer --no-pager || true
    else
        USER_SYSTEMD_DIR="${HOME}/.config/systemd/user"
        mkdir -p "${USER_SYSTEMD_DIR}"
        
        # Adjust user service path
        sed -e "s|/home/opc/driftguard|${PROJECT_DIR}|g" \
            -e "s|User=root||g" \
            "${PROJECT_DIR}/deploy/driftguard-telemetry.service" > "${USER_SYSTEMD_DIR}/driftguard-telemetry.service"
            
        cp "${PROJECT_DIR}/deploy/driftguard-telemetry.timer" "${USER_SYSTEMD_DIR}/"
        systemctl --user daemon-reload
        systemctl --user enable --now driftguard-telemetry.timer
        echo "✓ User-level systemd timer enabled and active."
        systemctl --user status driftguard-telemetry.timer --no-pager || true
    fi

elif [ "${MODE}" = "daemon" ]; then
    echo "Configuring systemd continuous daemon..."
    if [ "$(id -u)" -eq 0 ]; then
        cp "${PROJECT_DIR}/deploy/driftguard-telemetry-daemon.service" /etc/systemd/system/
        systemctl daemon-reload
        systemctl enable --now driftguard-telemetry-daemon.service
        echo "✓ Telemetry daemon started."
        systemctl status driftguard-telemetry-daemon.service --no-pager || true
    else
        USER_SYSTEMD_DIR="${HOME}/.config/systemd/user"
        mkdir -p "${USER_SYSTEMD_DIR}"
        sed -e "s|/home/opc/driftguard|${PROJECT_DIR}|g" \
            -e "s|User=root||g" \
            "${PROJECT_DIR}/deploy/driftguard-telemetry-daemon.service" > "${USER_SYSTEMD_DIR}/driftguard-telemetry-daemon.service"
        systemctl --user daemon-reload
        systemctl --user enable --now driftguard-telemetry-daemon.service
        echo "✓ User-level telemetry daemon started."
        systemctl --user status driftguard-telemetry-daemon.service --no-pager || true
    fi

elif [ "${MODE}" = "cron" ]; then
    echo "Installing 15-second cron entries..."
    (crontab -l 2>/dev/null | grep -v "collector.py" || true; cat "${PROJECT_DIR}/deploy/crontab-telemetry.cron") | crontab -
    echo "✓ Crontab configured to execute probes every 15 seconds."

elif [ "${MODE}" = "test" ]; then
    echo "Running validation test probe..."
    python3 "${PROJECT_DIR}/collector.py" --once --mock-fallback
    echo ""
    python3 "${PROJECT_DIR}/report_24h.py"
fi

echo "=========================================================="
echo " Setup complete!"
echo " Run 'python3 report_24h.py' anytime to view the 24h summary."
echo "=========================================================="
