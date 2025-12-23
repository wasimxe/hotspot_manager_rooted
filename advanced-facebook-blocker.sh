#!/data/data/com.termux/files/usr/bin/bash
#
# Advanced Facebook Blocker
# Blocks Facebook completely by handling:
# 1. DNS over HTTPS (DoH)
# 2. Multiple Facebook IP ranges
# 3. SNI-based HTTPS blocking
# 4. All Facebook subdomains
#

echo "========================================"
echo "Advanced Facebook Blocker"
echo "========================================"

# Block common DoH servers (forces devices to use regular DNS)
echo "Blocking DNS over HTTPS servers..."
DOH_SERVERS=(
    "8.8.8.8"      # Google DNS
    "8.8.4.4"      # Google DNS
    "1.1.1.1"      # Cloudflare
    "1.0.0.1"      # Cloudflare
    "9.9.9.9"      # Quad9
    "149.112.112.112"  # Quad9
    "208.67.222.222"   # OpenDNS
    "208.67.220.220"   # OpenDNS
)

for doh in "${DOH_SERVERS[@]}"; do
    # Block HTTPS to DoH servers (port 443 and 853 for DNS over TLS)
    su -c "iptables -D FORWARD -d $doh -p tcp --dport 443 -j DROP" 2>/dev/null
    su -c "iptables -I FORWARD 1 -d $doh -p tcp --dport 443 -j DROP" 2>/dev/null
    su -c "iptables -D FORWARD -d $doh -p tcp --dport 853 -j DROP" 2>/dev/null
    su -c "iptables -I FORWARD 1 -d $doh -p tcp --dport 853 -j DROP" 2>/dev/null
    echo "  ✓ Blocked DoH to $doh"
done

# Force DNS to go through our DNS (redirect port 53 to local)
echo ""
echo "Forcing DNS through local resolver..."
su -c "iptables -t nat -D PREROUTING -i wlan0 -p udp --dport 53 -j DNAT --to-destination 192.168.5.1:53" 2>/dev/null
su -c "iptables -t nat -I PREROUTING -i wlan0 -p udp --dport 53 -j DNAT --to-destination 192.168.5.1:53" 2>/dev/null
su -c "iptables -t nat -D PREROUTING -i wlan0 -p tcp --dport 53 -j DNAT --to-destination 192.168.5.1:53" 2>/dev/null
su -c "iptables -t nat -I PREROUTING -i wlan0 -p tcp --dport 53 -j DNAT --to-destination 192.168.5.1:53" 2>/dev/null
echo "  ✓ DNS redirect configured"

# Block Facebook IP ranges (comprehensive list)
echo ""
echo "Blocking Facebook IP ranges..."
FACEBOOK_IPS=(
    "157.240.0.0/16"      # Main Facebook range
    "31.13.24.0/21"       # Facebook range
    "31.13.64.0/18"       # Facebook range
    "31.13.0.0/16"        # Facebook range
    "66.220.144.0/20"     # Facebook range
    "69.63.176.0/20"      # Facebook range
    "69.171.224.0/19"     # Facebook range
    "74.119.76.0/22"      # Facebook range
    "103.4.96.0/22"       # Facebook range
    "129.134.0.0/16"      # Facebook range
    "157.240.0.0/17"      # Facebook range
    "173.252.64.0/18"     # Facebook range
    "179.60.192.0/22"     # Facebook range
    "185.60.216.0/22"     # Facebook range
    "204.15.20.0/22"      # Facebook range
)

for ip_range in "${FACEBOOK_IPS[@]}"; do
    su -c "iptables -D FORWARD -d $ip_range -j DROP" 2>/dev/null
    su -c "iptables -I FORWARD 1 -d $ip_range -j DROP" 2>/dev/null
    echo "  ✓ Blocked $ip_range"
done

# Block Facebook domains via DNS (all variations)
echo ""
echo "Blocking Facebook DNS queries..."
FACEBOOK_DOMAINS=(
    "facebook.com"
    "fb.com"
    "fbcdn.net"
    "fbsbx.com"
    "m.facebook.com"
    "web.facebook.com"
    "mobile.facebook.com"
    "www.facebook.com"
    "l.facebook.com"
    "connect.facebook.net"
    "graph.facebook.com"
    "static.facebook.com"
    "messenger.com"
    "m.me"
    "instagram.com"
    "whatsapp.com"
)

for domain in "${FACEBOOK_DOMAINS[@]}"; do
    # DNS blocking (UDP and TCP)
    su -c "iptables -D FORWARD -p udp --dport 53 -m string --string \"$domain\" --algo bm -j DROP" 2>/dev/null
    su -c "iptables -I FORWARD 1 -p udp --dport 53 -m string --string \"$domain\" --algo bm -j DROP" 2>/dev/null
    su -c "iptables -D FORWARD -p tcp --dport 53 -m string --string \"$domain\" --algo bm -j DROP" 2>/dev/null
    su -c "iptables -I FORWARD 1 -p tcp --dport 53 -m string --string \"$domain\" --algo bm -j DROP" 2>/dev/null

    # HTTPS SNI blocking
    su -c "iptables -D FORWARD -p tcp --dport 443 -m string --string \"$domain\" --algo bm -j DROP" 2>/dev/null
    su -c "iptables -I FORWARD 1 -p tcp --dport 443 -m string --string \"$domain\" --algo bm -j DROP" 2>/dev/null

    echo "  ✓ Blocked $domain"
done

echo ""
echo "========================================"
echo "Facebook blocking complete!"
echo "- Blocked DoH servers"
echo "- Forced DNS through local"
echo "- Blocked ${#FACEBOOK_IPS[@]} IP ranges"
echo "- Blocked ${#FACEBOOK_DOMAINS[@]} domains"
echo "========================================"
