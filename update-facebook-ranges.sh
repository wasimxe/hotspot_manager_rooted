#!/data/data/com.termux/files/usr/bin/bash
# Add missing Facebook IP range

echo "Adding 91.33.0.0/16 to Facebook blocking..."

# Add to iptables
su -c "iptables -I FORWARD 1 -d 91.33.0.0/16 -j DROP" 2>/dev/null

# Update JSON
python3 << 'PYEOF'
import json

with open('/data/data/com.termux/files/home/blocked_urls.json', 'r') as f:
    blocked = json.load(f)

if 'facebook.com' in blocked:
    if '91.33.0.0/16' not in blocked['facebook.com']['ip_ranges']:
        blocked['facebook.com']['ip_ranges'].append('91.33.0.0/16')
        blocked['facebook.com']['ips'].append('91.33.0.0/16')
        blocked['facebook.com']['rules_count'] += 1

    with open('/data/data/com.termux/files/home/blocked_urls.json', 'w') as f:
        json.dump(blocked, f, indent=2)
    
    print("✓ Added 91.33.0.0/16 to Facebook blocking")
PYEOF

echo "Done! Facebook should be blocked now."
