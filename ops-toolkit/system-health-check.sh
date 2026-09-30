#!/usr/bin/env bash
set -euo pipefail

# Lightweight Linux system health report for troubleshooting/admin work.
# Safe by default: read-only commands, no configuration changes.

section() {
  printf '\n===== %s =====\n' "$1"
}

section "HOST"
printf 'Hostname: %s\n' "$(hostname)"
printf 'Kernel:   %s\n' "$(uname -r)"
printf 'Uptime:   %s\n' "$(uptime -p 2>/dev/null || uptime)"

section "CPU / LOAD"
printf 'CPUs: %s\n' "$(nproc)"
uptime

section "MEMORY"
free -h

section "FILESYSTEMS"
df -hT -x tmpfs -x devtmpfs

section "TOP CPU PROCESSES"
ps -eo pid,user,comm,%cpu,%mem --sort=-%cpu | head -n 11

section "TOP MEMORY PROCESSES"
ps -eo pid,user,comm,%cpu,%mem --sort=-%mem | head -n 11

section "NETWORK ADDRESSES"
ip -brief address 2>/dev/null || true

section "ROUTING"
ip route 2>/dev/null || true

section "LISTENING PORTS"
ss -lntup 2>/dev/null || ss -lnt 2>/dev/null || true

section "FAILED SYSTEMD UNITS"
if command -v systemctl >/dev/null 2>&1; then
  systemctl --failed --no-pager || true
else
  echo "systemd not available"
fi

section "RECENT HIGH-PRIORITY LOGS"
if command -v journalctl >/dev/null 2>&1; then
  journalctl -p warning -n 20 --no-pager 2>/dev/null || true
else
  echo "journalctl not available"
fi

printf '\nHealth check completed.\n'
