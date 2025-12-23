#!/system/bin/sh
# Hotspot GUI API Server

PORT=8080
WEBROOT="/data/data/com.termux/files/home/hotspot_gui"
BLOCKLIST="/data/data/com.termux/files/home/blocked_urls.txt"

# Create blocklist if not exists
touch "$BLOCKLIST"

# Function to get connected devices
get_devices() {
    DEVICES="["
    FIRST=true
    
    # Detect hotspot interface
    for iface in wlan0 swlan0 ap0 softap0; do
        if ip addr show $iface 2>/dev/null | grep -q "192.168"; then
            HOTSPOT_IFACE=$iface
            break
        fi
    done
    
    if [ -z "$HOTSPOT_IFACE" ]; then
        echo '{"devices":[],"interface":"none"}'
        return
    fi
    
    # Get devices from ARP table
    ip neigh | grep "$HOTSPOT_IFACE" | while read line; do
        IP=$(echo $line | awk '{print $1}')
        MAC=$(echo $line | awk '{print $5}')
        STATE=$(echo $line | awk '{print $NF}')
        
        # Only include REACHABLE or STALE devices
        if echo "$STATE" | grep -qE "REACHABLE|STALE"; then
            # Try to get hostname from DHCP leases
            HOSTNAME="Unknown"
            if [ -f /data/misc/dhcp/dnsmasq.leases ]; then
                HOSTNAME=$(grep $MAC /data/misc/dhcp/dnsmasq.leases 2>/dev/null | awk '{print $4}')
                [ -z "$HOSTNAME" ] && HOSTNAME="Unknown"
            fi
            
            if [ "$FIRST" = true ]; then
                FIRST=false
            else
                DEVICES="$DEVICES,"
            fi
            
            DEVICES="$DEVICES{\"ip\":\"$IP\",\"mac\":\"$MAC\",\"hostname\":\"$HOSTNAME\"}"
        fi
    done
    
    echo "{\"devices\":$DEVICES],\"interface\":\"$HOTSPOT_IFACE\"}"
}

# Function to get blocked URLs
get_blocked_urls() {
    URLS="["
    FIRST=true
    
    while read url; do
        [ -z "$url" ] && continue
        
        if [ "$FIRST" = true ]; then
            FIRST=false
        else
            URLS="$URLS,"
        fi
        
        URLS="$URLS\"$url\""
    done < "$BLOCKLIST"
    
    echo "{\"urls\":$URLS]}"
}

# Function to block URL
block_url() {
    URL="$1"
    
    # Check if already blocked
    if grep -q "^$URL$" "$BLOCKLIST" 2>/dev/null; then
        echo "{\"success\":false,\"message\":\"URL already blocked\"}"
        return
    fi
    
    # Add to blocklist
    echo "$URL" >> "$BLOCKLIST"
    
    # Block via iptables
    IPS=$(nslookup "$URL" 2>/dev/null | grep "Address:" | grep -v "#" | awk '{print $2}' | grep -v ":")
    
    if [ -n "$IPS" ]; then
        for IP in $IPS; do
            iptables -D FORWARD -d $IP -j REJECT 2>/dev/null
            iptables -I FORWARD -d $IP -j REJECT 2>/dev/null
        done
        echo "{\"success\":true,\"message\":\"Blocked $URL\"}"
    else
        echo "{\"success\":true,\"message\":\"Added to blocklist but could not resolve IPs\"}"
    fi
}

# Function to unblock URL
unblock_url() {
    URL="$1"
    
    # Remove from blocklist
    grep -v "^$URL$" "$BLOCKLIST" > "${BLOCKLIST}.tmp"
    mv "${BLOCKLIST}.tmp" "$BLOCKLIST"
    
    # Unblock via iptables
    IPS=$(nslookup "$URL" 2>/dev/null | grep "Address:" | grep -v "#" | awk '{print $2}' | grep -v ":")
    
    if [ -n "$IPS" ]; then
        for IP in $IPS; do
            iptables -D FORWARD -d $IP -j REJECT 2>/dev/null
        done
    fi
    
    echo "{\"success\":true,\"message\":\"Unblocked $URL\"}"
}

# Function to block device
block_device() {
    MAC="$1"
    IP="$2"
    
    iptables -I FORWARD -m mac --mac-source "$MAC" -j DROP 2>/dev/null
    iptables -I FORWARD -s "$IP" -j DROP 2>/dev/null
    
    echo "{\"success\":true,\"message\":\"Blocked device\"}"
}

# Function to run optimizer
run_optimizer() {
    OUTPUT=$(sh /data/data/com.termux/files/home/hotspot_optimizer.sh 2>&1)
    
    if [ $? -eq 0 ]; then
        # Escape output for JSON
        OUTPUT_ESCAPED=$(echo "$OUTPUT" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')
        echo "{\"success\":true,\"output\":\"$OUTPUT_ESCAPED\"}"
    else
        echo "{\"success\":false,\"message\":\"Optimizer failed\"}"
    fi
}

# Parse URL and get endpoint
parse_request() {
    while read line; do
        echo "$line" >&2
        
        # Parse request line
        if echo "$line" | grep -q "^GET\|^POST"; then
            METHOD=$(echo "$line" | awk '{print $1}')
            PATH=$(echo "$line" | awk '{print $2}')
        fi
        
        # Read POST data
        if echo "$line" | grep -q "^Content-Length:"; then
            CONTENT_LENGTH=$(echo "$line" | tr -d '\r' | awk '{print $2}')
        fi
        
        # Empty line marks end of headers
        if [ "$line" = $'\r' ] || [ -z "$line" ]; then
            if [ "$METHOD" = "POST" ] && [ -n "$CONTENT_LENGTH" ]; then
                read -n "$CONTENT_LENGTH" POST_DATA
            fi
            break
        fi
    done
}

# Handle HTTP request
handle_request() {
    parse_request
    
    case "$PATH" in
        /)
            # Serve index.html
            echo "HTTP/1.1 200 OK"
            echo "Content-Type: text/html"
            echo ""
            cat "$WEBROOT/index.html"
            ;;
        /api/devices)
            # Get connected devices
            echo "HTTP/1.1 200 OK"
            echo "Content-Type: application/json"
            echo ""
            get_devices
            ;;
        /api/blocked-urls)
            # Get blocked URLs
            echo "HTTP/1.1 200 OK"
            echo "Content-Type: application/json"
            echo ""
            get_blocked_urls
            ;;
        /api/block-url)
            # Block URL
            URL=$(echo "$POST_DATA" | sed 's/.*"url":"\([^"]*\)".*/\1/')
            echo "HTTP/1.1 200 OK"
            echo "Content-Type: application/json"
            echo ""
            block_url "$URL"
            ;;
        /api/unblock-url)
            # Unblock URL
            URL=$(echo "$POST_DATA" | sed 's/.*"url":"\([^"]*\)".*/\1/')
            echo "HTTP/1.1 200 OK"
            echo "Content-Type: application/json"
            echo ""
            unblock_url "$URL"
            ;;
        /api/block-device)
            # Block device
            MAC=$(echo "$POST_DATA" | sed 's/.*"mac":"\([^"]*\)".*/\1/')
            IP=$(echo "$POST_DATA" | sed 's/.*"ip":"\([^"]*\)".*/\1/')
            echo "HTTP/1.1 200 OK"
            echo "Content-Type: application/json"
            echo ""
            block_device "$MAC" "$IP"
            ;;
        /api/optimize)
            # Run optimizer
            echo "HTTP/1.1 200 OK"
            echo "Content-Type: application/json"
            echo ""
            run_optimizer
            ;;
        *)
            # 404 Not Found
            echo "HTTP/1.1 404 Not Found"
            echo "Content-Type: application/json"
            echo ""
            echo '{"error":"Not found"}'
            ;;
    esac
}

# Start server
echo "Starting Hotspot GUI API Server on port $PORT..."
echo "Access the GUI at: http://localhost:$PORT"
echo "Press Ctrl+C to stop"
echo ""

while true; do
    handle_request | nc -l -p $PORT -q 1
done
