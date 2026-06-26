#!/bin/bash
# === ANON SETUP SCRIPT ===
# Run with: chmod +x /home/kali/anon_setup.sh && sudo /home/kali/anon_setup.sh

echo "[1] MAC Randomize..."
for iface in $(ip link show | grep -E "^[0-9]+: (e|w)" | awk -F: '{print $2}' | tr -d ' '); do
  ip link set "$iface" down 2>/dev/null
  macchanger -r "$iface" 2>/dev/null
  ip link set "$iface" up 2>/dev/null
  echo "  $iface: $(ip link show $iface 2>/dev/null | grep ether | awk '{print $2}')"
done

echo "[2] DNS Lock..."
echo "nameserver 127.0.0.1" > /etc/resolv.conf
systemctl disable systemd-resolved 2>/dev/null
systemctl stop systemd-resolved 2>/dev/null
echo "  DNS locked to 127.0.0.1"

echo "[3] Hostname Randomize..."
NEWHOST="anon-$(shuf -i 1000-9999 -n 1)"
hostnamectl set-hostname "$NEWHOST" 2>/dev/null || hostname "$NEWHOST" 2>/dev/null
echo "  Hostname: $(hostname)"

echo ""
echo "Anon setup complete. Reboot recommended."
