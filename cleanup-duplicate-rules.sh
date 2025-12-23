#!/data/data/com.termux/files/usr/bin/bash
#
# Emergency cleanup script for duplicate iptables rules
# This script removes duplicate MAC-based counting rules that are killing performance
#

echo "================================================"
echo "Cleaning up duplicate iptables rules..."
echo "================================================"

# Count rules before
BEFORE=$(su -c "iptables -L FORWARD -n --line-numbers" 2>/dev/null | wc -l)
echo "Total FORWARD rules before: $BEFORE"

# Get unique MAC+IP combinations currently in use
echo ""
echo "Finding active devices..."
ACTIVE_DEVICES=$(su -c "ip neigh show dev wlan0" 2>/dev/null | grep "lladdr" | awk '{print $5":"$1}' | sort -u)

echo "Active devices found:"
echo "$ACTIVE_DEVICES"

# Flush all MAC-based counting rules (they'll be recreated by server when needed)
echo ""
echo "Removing all MAC-based counting rules..."
su -c "iptables-save" 2>/dev/null | grep -v "MAC" | su -c "iptables-restore" 2>/dev/null

# Count rules after
AFTER=$(su -c "iptables -L FORWARD -n --line-numbers" 2>/dev/null | wc -l)
echo ""
echo "Total FORWARD rules after: $AFTER"
echo "Removed: $((BEFORE - AFTER)) rules"

# Keep essential MASQUERADE and FORWARD rules
echo ""
echo "Ensuring essential forwarding rules..."

# Check if MASQUERADE exists
if ! su -c "iptables -t nat -C POSTROUTING -s 192.168.5.0/24 -o rmnet_data1 -j MASQUERADE" 2>/dev/null; then
    su -c "iptables -t nat -A POSTROUTING -s 192.168.5.0/24 -o rmnet_data1 -j MASQUERADE" 2>/dev/null
    echo "✓ Added MASQUERADE rule for 192.168.5.0/24"
fi

# Check if basic FORWARD rules exist
if ! su -c "iptables -C FORWARD -s 192.168.5.0/24 -o rmnet_data1 -j ACCEPT" 2>/dev/null; then
    su -c "iptables -A FORWARD -s 192.168.5.0/24 -o rmnet_data1 -j ACCEPT" 2>/dev/null
    echo "✓ Added FORWARD ACCEPT for outgoing"
fi

if ! su -c "iptables -C FORWARD -i rmnet_data1 -d 192.168.5.0/24 -m state --state RELATED,ESTABLISHED -j ACCEPT" 2>/dev/null; then
    su -c "iptables -A FORWARD -i rmnet_data1 -d 192.168.5.0/24 -m state --state RELATED,ESTABLISHED -j ACCEPT" 2>/dev/null
    echo "✓ Added FORWARD ACCEPT for incoming"
fi

echo ""
echo "================================================"
echo "Cleanup complete! Internet should be faster now"
echo "================================================"
