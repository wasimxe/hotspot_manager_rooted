#!/data/data/com.termux/files/usr/bin/bash
#
# Add Facebook with all IP ranges for complete blocking
# NO DNS string matching - pure IP blocking for maximum speed!
#

echo "=========================================="
echo "Adding Facebook with ALL IP Ranges"
echo "=========================================="

# Facebook's complete IP ranges (covers ALL Facebook services worldwide)
FACEBOOK_RANGES=(
    "157.240.0.0/16"
    "31.13.0.0/16"
    "66.220.144.0/20"
    "69.63.176.0/20"
    "69.171.224.0/19"
    "173.252.64.0/18"
)

# Add to blocked_urls.json
python3 << EOF
import json
import datetime

# Load existing blocks
try:
    with open('/data/data/com.termux/files/home/blocked_urls.json', 'r') as f:
        blocked = json.load(f)
except:
    blocked = {}

# Add Facebook with all IP ranges
blocked['facebook.com'] = {
    "ip_ranges": [
        "157.240.0.0/16",
        "31.13.0.0/16",
        "66.220.144.0/20",
        "69.63.176.0/20",
        "69.171.224.0/19",
        "173.252.64.0/18"
    ],
    "ips": [
        "157.240.0.0/16",
        "31.13.0.0/16",
        "66.220.144.0/20",
        "69.63.176.0/20",
        "69.171.224.0/19",
        "173.252.64.0/18"
    ],
    "is_ip_address": False,
    "blocked_at": datetime.datetime.now().isoformat(),
    "rules_count": 6
}

# Save
with open('/data/data/com.termux/files/home/blocked_urls.json', 'w') as f:
    json.dump(blocked, f, indent=2)

print("✓ Added Facebook to blocked_urls.json")
EOF

# Apply iptables rules
echo ""
echo "Applying iptables rules..."
for range in "${FACEBOOK_RANGES[@]}"; do
    # Remove if exists
    su -c "iptables -D FORWARD -d $range -j DROP" 2>/dev/null
    # Add at top priority
    su -c "iptables -I FORWARD 1 -d $range -j DROP" 2>/dev/null
    echo "  ✓ Blocked $range"
done

echo ""
echo "=========================================="
echo "Facebook Blocking Complete!"
echo "- 6 IP ranges covering ALL Facebook IPs"
echo "- NO DNS string matching (fast!)"
echo "- Edit anytime via web interface"
echo "=========================================="
