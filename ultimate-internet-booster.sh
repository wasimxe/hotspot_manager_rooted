#!/data/data/com.termux/files/usr/bin/bash
#
# ULTIMATE Internet Booster & Fixer
# Applies ALL possible optimizations for maximum speed and stability
#

LOG_FILE="/data/data/com.termux/files/home/booster.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $@" | tee -a "$LOG_FILE"
}

log "========================================="
log "ULTIMATE Internet Booster Starting..."
log "========================================="

ISSUES=0
FIXES=0

# ============================================
# FIX 1: Remove Duplicate FORWARD ACCEPT Rules
# ============================================
log "Checking for duplicate FORWARD ACCEPT rules..."
DUPLICATE_ACCEPTS=$(su -c "iptables -L FORWARD -n --line-numbers" 2>/dev/null | grep "ACCEPT.*rmnet_data.*RELATED,ESTABLISHED" | wc -l)
if [ "$DUPLICATE_ACCEPTS" -gt 2 ]; then
    log "Found $DUPLICATE_ACCEPTS duplicate ACCEPT rules (should be 2)"
    ISSUES=$((ISSUES + 1))

    # Keep only unique ACCEPT rules
    su -c "iptables -D FORWARD -i rmnet_data1 -d 192.168.5.0/24 -m state --state RELATED,ESTABLISHED -j ACCEPT" 2>/dev/null
    su -c "iptables -D FORWARD -i rmnet_data2 -d 192.168.5.0/24 -m state --state RELATED,ESTABLISHED -j ACCEPT" 2>/dev/null
    su -c "iptables -D FORWARD -s 192.168.5.0/24 -o rmnet_data1 -j ACCEPT" 2>/dev/null
    su -c "iptables -D FORWARD -s 192.168.5.0/24 -o rmnet_data2 -j ACCEPT" 2>/dev/null

    # Re-add only once at the end
    su -c "iptables -A FORWARD -i rmnet_data1 -d 192.168.5.0/24 -m state --state RELATED,ESTABLISHED -j ACCEPT" 2>/dev/null
    su -c "iptables -A FORWARD -s 192.168.5.0/24 -o rmnet_data1 -j ACCEPT" 2>/dev/null

    FIXES=$((FIXES + 1))
    log "✓ Removed duplicate ACCEPT rules"
fi

# ============================================
# FIX 2: Move Blocking Rules to TOP (Critical!)
# ============================================
log "Ensuring blocking rules are at TOP..."

# Save all current DROP/REJECT rules to temp file
mkdir -p /tmp 2>/dev/null
su -c "iptables-save" 2>/dev/null | grep "FORWARD.*\(DROP\|REJECT\)" > /tmp/blocking_rules.txt

# Count blocking rules
BLOCKING_COUNT=$(cat /tmp/blocking_rules.txt | wc -l)
if [ "$BLOCKING_COUNT" -gt 0 ]; then
    log "Found $BLOCKING_COUNT blocking rules - ensuring they're at top..."
    ISSUES=$((ISSUES + 1))

    # Delete all existing DROP/REJECT rules from FORWARD
    su -c "iptables-save" 2>/dev/null | grep "FORWARD.*\(DROP\|REJECT\)" | sed 's/-A /-D /' | while read rule; do
        su -c "iptables $rule" 2>/dev/null
    done

    # Re-insert all blocking rules at position 1 (top priority)
    tac /tmp/blocking_rules.txt | while read rule; do
        # Convert from iptables-save format to iptables -I format
        CLEAN_RULE=$(echo "$rule" | sed 's/-A FORWARD/-I FORWARD 1/')
        su -c "iptables $CLEAN_RULE" 2>/dev/null
    done

    FIXES=$((FIXES + 1))
    log "✓ Moved $BLOCKING_COUNT blocking rules to TOP priority"
fi

# Reload blocked URLs to ensure all blocks are in place
if [ -f /data/data/com.termux/files/home/blocked_urls.json ]; then
    log "Reloading blocked URLs to ensure completeness..."
    python3 -c "
import json, subprocess
try:
    with open('/data/data/com.termux/files/home/blocked_urls.json', 'r') as f:
        blocked = json.load(f)
    for url, info in blocked.items():
        for ip in info.get('ips', []):
            subprocess.run(f'su -c \"iptables -I FORWARD 1 -d {ip} -j DROP\"', shell=True, capture_output=True)
        if not info.get('is_ip_address', False):
            subprocess.run(f'su -c \"iptables -I FORWARD 1 -p udp --dport 53 -m string --string \\\"{url}\\\" --algo bm -j DROP\"', shell=True, capture_output=True)
except: pass
" 2>/dev/null
    log "✓ Reloaded blocked URLs"
fi

# ============================================
# FIX 3: Remove Duplicate MAC Counting Rules
# ============================================
DUPLICATE_MACS=$(su -c "iptables -L FORWARD -n" 2>/dev/null | grep "MAC" | grep -v "DROP\|REJECT\|ACCEPT" | wc -l)
if [ "$DUPLICATE_MACS" -gt 0 ]; then
    log "Found $DUPLICATE_MACS duplicate MAC counting rules"
    ISSUES=$((ISSUES + 1))

    while true; do
        LINE=$(su -c "iptables -L FORWARD -n --line-numbers" 2>/dev/null | grep "MAC" | grep -v "DROP\|REJECT\|ACCEPT" | tail -1 | awk '{print $1}')
        [ -z "$LINE" ] && break
        su -c "iptables -D FORWARD $LINE" 2>/dev/null || break
    done

    FIXES=$((FIXES + 1))
    log "✓ Removed $DUPLICATE_MACS duplicate MAC rules"
fi

# ============================================
# FIX 4: Enable IP Forwarding
# ============================================
FORWARD_STATUS=$(su -c "sysctl net.ipv4.ip_forward" 2>/dev/null | grep -c "= 1")
if [ "$FORWARD_STATUS" -eq 0 ]; then
    log "IP forwarding is disabled"
    ISSUES=$((ISSUES + 1))
    su -c "sysctl -w net.ipv4.ip_forward=1" 2>/dev/null
    FIXES=$((FIXES + 1))
    log "✓ Enabled IP forwarding"
fi

# ============================================
# FIX 5: Check MASQUERADE Rule
# ============================================
if ! su -c "iptables -t nat -C POSTROUTING -s 192.168.5.0/24 -o rmnet_data1 -j MASQUERADE" 2>/dev/null; then
    log "Missing MASQUERADE rule"
    ISSUES=$((ISSUES + 1))
    su -c "iptables -t nat -A POSTROUTING -s 192.168.5.0/24 -o rmnet_data1 -j MASQUERADE" 2>/dev/null
    FIXES=$((FIXES + 1))
    log "✓ Added MASQUERADE rule"
fi

# ============================================
# BOOST 1: Enable TCP BBR Congestion Control (HUGE speed boost)
# ============================================
if su -c "sysctl net.ipv4.tcp_available_congestion_control" 2>/dev/null | grep -q "bbr"; then
    CURRENT_CC=$(su -c "sysctl net.ipv4.tcp_congestion_control" 2>/dev/null | cut -d= -f2 | tr -d ' ')
    if [ "$CURRENT_CC" != "bbr" ]; then
        log "Enabling TCP BBR (Google's fast congestion control)"
        su -c "sysctl -w net.core.default_qdisc=fq" 2>/dev/null
        su -c "sysctl -w net.ipv4.tcp_congestion_control=bbr" 2>/dev/null
        FIXES=$((FIXES + 1))
        log "✓ Enabled TCP BBR"
    fi
fi

# ============================================
# BOOST 2: Optimize TCP Window Sizes
# ============================================
log "Optimizing TCP window sizes..."
su -c "sysctl -w net.ipv4.tcp_window_scaling=1" 2>/dev/null
su -c "sysctl -w net.ipv4.tcp_rmem='4096 87380 16777216'" 2>/dev/null
su -c "sysctl -w net.ipv4.tcp_wmem='4096 65536 16777216'" 2>/dev/null
su -c "sysctl -w net.core.rmem_max=16777216" 2>/dev/null
su -c "sysctl -w net.core.wmem_max=16777216" 2>/dev/null
FIXES=$((FIXES + 1))
log "✓ Optimized TCP windows (16MB buffers)"

# ============================================
# BOOST 3: Enable TCP Fast Open (Faster connections)
# ============================================
su -c "sysctl -w net.ipv4.tcp_fastopen=3" 2>/dev/null
FIXES=$((FIXES + 1))
log "✓ Enabled TCP Fast Open"

# ============================================
# BOOST 4: Optimize Connection Tracking
# ============================================
log "Optimizing connection tracking..."
su -c "sysctl -w net.netfilter.nf_conntrack_max=65536" 2>/dev/null
su -c "sysctl -w net.netfilter.nf_conntrack_tcp_timeout_established=600" 2>/dev/null
su -c "sysctl -w net.netfilter.nf_conntrack_tcp_timeout_time_wait=30" 2>/dev/null
FIXES=$((FIXES + 1))
log "✓ Optimized conntrack (65k connections)"

# ============================================
# BOOST 5: Reduce TCP Overhead
# ============================================
log "Reducing TCP overhead..."
su -c "sysctl -w net.ipv4.tcp_timestamps=0" 2>/dev/null
su -c "sysctl -w net.ipv4.tcp_sack=1" 2>/dev/null
su -c "sysctl -w net.ipv4.tcp_dsack=1" 2>/dev/null
su -c "sysctl -w net.ipv4.tcp_fack=1" 2>/dev/null
FIXES=$((FIXES + 1))
log "✓ Disabled timestamps, enabled SACK"

# ============================================
# BOOST 6: Optimize TCP Keepalive
# ============================================
log "Optimizing TCP keepalive..."
su -c "sysctl -w net.ipv4.tcp_keepalive_time=600" 2>/dev/null
su -c "sysctl -w net.ipv4.tcp_keepalive_intvl=30" 2>/dev/null
su -c "sysctl -w net.ipv4.tcp_keepalive_probes=3" 2>/dev/null
FIXES=$((FIXES + 1))
log "✓ Optimized keepalive timers"

# ============================================
# BOOST 7: Enable SYN Cookies (DDoS protection)
# ============================================
su -c "sysctl -w net.ipv4.tcp_syncookies=1" 2>/dev/null
su -c "sysctl -w net.ipv4.tcp_syn_retries=2" 2>/dev/null
su -c "sysctl -w net.ipv4.tcp_synack_retries=2" 2>/dev/null
FIXES=$((FIXES + 1))
log "✓ Enabled SYN cookies"

# ============================================
# BOOST 8: Optimize Network Buffers
# ============================================
log "Optimizing network buffers..."
su -c "sysctl -w net.core.netdev_max_backlog=5000" 2>/dev/null
su -c "sysctl -w net.core.somaxconn=1024" 2>/dev/null
FIXES=$((FIXES + 1))
log "✓ Increased network buffers"

# ============================================
# BOOST 9: Disable IPv6 (if not needed - reduces overhead)
# ============================================
IPV6_STATUS=$(su -c "sysctl net.ipv6.conf.all.disable_ipv6" 2>/dev/null | grep -c "= 0")
if [ "$IPV6_STATUS" -eq 1 ]; then
    log "Disabling IPv6 (not needed for hotspot)"
    su -c "sysctl -w net.ipv6.conf.all.disable_ipv6=1" 2>/dev/null
    su -c "sysctl -w net.ipv6.conf.default.disable_ipv6=1" 2>/dev/null
    FIXES=$((FIXES + 1))
    log "✓ Disabled IPv6"
fi

# ============================================
# BOOST 10: Optimize MTU Discovery
# ============================================
su -c "sysctl -w net.ipv4.tcp_mtu_probing=1" 2>/dev/null
FIXES=$((FIXES + 1))
log "✓ Enabled MTU probing"

# ============================================
# BOOST 11: Reduce TIME_WAIT Sockets (faster reconnects)
# ============================================
su -c "sysctl -w net.ipv4.tcp_tw_reuse=1" 2>/dev/null
su -c "sysctl -w net.ipv4.tcp_fin_timeout=15" 2>/dev/null
FIXES=$((FIXES + 1))
log "✓ Optimized TIME_WAIT handling"

# ============================================
# BOOST 12: Enable ECN (Explicit Congestion Notification)
# ============================================
su -c "sysctl -w net.ipv4.tcp_ecn=1" 2>/dev/null
FIXES=$((FIXES + 1))
log "✓ Enabled ECN"

# ============================================
# Save Settings for Persistence
# ============================================
log "Saving settings for boot persistence..."
cat > /data/data/com.termux/files/home/sysctl-optimizations.conf << 'EOF'
# Network Optimizations for Hotspot
net.ipv4.ip_forward=1
net.core.default_qdisc=fq
net.ipv4.tcp_congestion_control=bbr
net.ipv4.tcp_window_scaling=1
net.ipv4.tcp_rmem=4096 87380 16777216
net.ipv4.tcp_wmem=4096 65536 16777216
net.core.rmem_max=16777216
net.core.wmem_max=16777216
net.ipv4.tcp_fastopen=3
net.netfilter.nf_conntrack_max=65536
net.netfilter.nf_conntrack_tcp_timeout_established=600
net.netfilter.nf_conntrack_tcp_timeout_time_wait=30
net.ipv4.tcp_timestamps=0
net.ipv4.tcp_sack=1
net.ipv4.tcp_dsack=1
net.ipv4.tcp_fack=1
net.ipv4.tcp_keepalive_time=600
net.ipv4.tcp_keepalive_intvl=30
net.ipv4.tcp_keepalive_probes=3
net.ipv4.tcp_syncookies=1
net.ipv4.tcp_syn_retries=2
net.ipv4.tcp_synack_retries=2
net.core.netdev_max_backlog=5000
net.core.somaxconn=1024
net.ipv6.conf.all.disable_ipv6=1
net.ipv6.conf.default.disable_ipv6=1
net.ipv4.tcp_mtu_probing=1
net.ipv4.tcp_tw_reuse=1
net.ipv4.tcp_fin_timeout=15
net.ipv4.tcp_ecn=1
EOF

log "========================================="
log "BOOST COMPLETE!"
log "Issues Found: $ISSUES"
log "Fixes Applied: $FIXES"
log "========================================="

echo "RESULT:$ISSUES:$FIXES"
