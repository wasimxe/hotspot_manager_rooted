#!/data/data/com.termux/files/usr/bin/bash
#
# Facebook IP Learning Tool
# Captures actual IPs you connect to and lets you block them
#

echo "=========================================="
echo "Facebook IP Learning Tool"
echo "=========================================="
echo ""
echo "Instructions:"
echo "1. This will monitor your network for 30 seconds"
echo "2. Open Facebook on your PC during this time"
echo "3. Visit facebook.com, fb.com, web.facebook.com"
echo "4. Script will show you the IPs you connected to"
echo ""
read -p "Press ENTER when ready to start monitoring..."

echo ""
echo "Monitoring for 30 seconds..."
echo "ACCESS FACEBOOK NOW from your PC!"
echo ""

# Capture all destination IPs on port 80 and 443
TEMP_FILE="/tmp/captured_ips.txt"
timeout 30 su -c "tcpdump -i wlan0 -n -l 'tcp port 80 or tcp port 443' 2>/dev/null" | \
    grep -oE 'IP [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+ > ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)' | \
    awk '{print $4}' | sort -u > "$TEMP_FILE"

echo ""
echo "=========================================="
echo "Captured IPs:"
echo "=========================================="

if [ -s "$TEMP_FILE" ]; then
    cat -n "$TEMP_FILE"

    echo ""
    echo "=========================================="
    echo "Which IPs are Facebook?"
    echo "=========================================="
    echo ""
    echo "Options:"
    echo "1. Add ALL captured IPs to Facebook blocking"
    echo "2. Let me select specific IPs"
    echo "3. Exit (manual selection via web interface)"
    echo ""
    read -p "Choose (1-3): " choice

    case $choice in
        1)
            echo ""
            echo "Adding all IPs to Facebook blocking..."

            # Read IPs and add to Facebook block
            python3 << PYEOF
import json

# Load blocked URLs
try:
    with open('/data/data/com.termux/files/home/blocked_urls.json', 'r') as f:
        blocked = json.load(f)
except:
    blocked = {}

# Read captured IPs
with open('$TEMP_FILE', 'r') as f:
    ips = [line.strip() for line in f if line.strip()]

# Add to facebook.com
if 'facebook.com' not in blocked:
    blocked['facebook.com'] = {'ip_ranges': [], 'ips': [], 'is_ip_address': False, 'blocked_at': '', 'rules_count': 0}

for ip in ips:
    if ip not in blocked['facebook.com']['ip_ranges']:
        blocked['facebook.com']['ip_ranges'].append(ip)
        blocked['facebook.com']['ips'].append(ip)

# Save
with open('/data/data/com.termux/files/home/blocked_urls.json', 'w') as f:
    json.dump(blocked, f, indent=2)

print(f"Added {len(ips)} IPs to Facebook blocking")
PYEOF

            # Add iptables rules
            while IFS= read -r ip; do
                su -c "iptables -I FORWARD 1 -d $ip -j DROP" 2>/dev/null
                echo "  ✓ Blocked $ip"
            done < "$TEMP_FILE"

            echo ""
            echo "Done! Try accessing Facebook now - it should be blocked!"
            ;;
        2)
            echo ""
            echo "Use the web interface Edit button to add specific IPs"
            echo "Go to: URL Blocking > facebook.com > Edit"
            ;;
        *)
            echo "Exiting. Use web interface to add IPs manually."
            ;;
    esac
else
    echo "No IPs captured! Make sure you accessed Facebook during monitoring."
fi

rm -f "$TEMP_FILE"
