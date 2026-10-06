#!/usr/bin/env bash
# ==============================================================================
# Setup Node 2 (Oracle Cloud VM.Standard.E2.1.Micro)
# Installs Swap, Docker CE, DriftGuard stack, and systemd services
# ==============================================================================

set -euo pipefail

echo "=========================================================="
echo " 1. Configuring 2GB Swap (Crucial for 500MB Micro VM)    "
echo "=========================================================="
if [[ ! -f /swapfile ]]; then
    echo "Creating 2GB swapfile..."
    dd if=/dev/zero of=/swapfile bs=1M count=2048 status=none
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    if ! grep -q "/swapfile" /etc/fstab; then
        echo "/swapfile swap swap defaults 0 0" >> /etc/fstab
    fi
    echo "Swap enabled:"
    free -h
else
    echo "Swapfile /swapfile already exists."
    swapon /swapfile 2>/dev/null || true
    free -h
fi

echo "=========================================================="
echo " 2. Installing Docker CE and Required Tools               "
echo "=========================================================="
dnf install -y dnf-plugins-core
dnf config-manager --add-repo=https://download.docker.com/linux/centos/docker-ce.repo || \
    curl -fsSL -o /etc/yum.repos.d/docker-ce.repo https://download.docker.com/linux/centos/docker-ce.repo

dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin git socat jq

systemctl enable --now docker
usermod -aG docker opc

echo "=========================================================="
echo " 3. Configuring Firewall Ports (80, 443, 8000, 8545)      "
echo "=========================================================="
firewall-cmd --permanent --add-port=80/tcp 2>/dev/null || true
firewall-cmd --permanent --add-port=443/tcp 2>/dev/null || true
firewall-cmd --permanent --add-port=8000/tcp 2>/dev/null || true
firewall-cmd --permanent --add-port=8545/tcp 2>/dev/null || true
firewall-cmd --reload 2>/dev/null || true

echo "=========================================================="
echo " [SUCCESS] System runtime and tools initialized!          "
echo "=========================================================="
