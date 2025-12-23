#!/system/bin/sh
# Minimal HTTP Server for Hotspot GUI

PORT=8080
HTML="/data/data/com.termux/files/home/hotspot_gui/index.html"
BLOCKLIST="/data/data/com.termux/files/home/blocked_urls.txt"

touch "$BLOCKLIST"

# Get devices as JSON
get_devices() {
    echo -n '{"devices":['
    
    # Find hotspot interface
    IFACE=""
    for i in wlan0 swlan0 ap0 softap0; do
        if ip addr show $i 2>/dev/null | grep -q "192.168"; then
            IFACE=$i
            break
        fi
    done
    
    if [ -z "$IFACE" ]; then
        echo '],"interface":"none"}'
        return
    fi
    
    # Get devices
    FIRST=1
    ip neigh | grep "$IFACE" | while IFS= read -r line; do
        IP=$(echo "$line" | awk '{print $1}')
        MAC=$(echo "$line" | awk '{print $5}')
        STATE=$(echo "$line" | awk '{print $NF}')
        
        if echo "$STATE" | grep -qE "REACHABLE|STALE"; then
            [ $FIRST -eq 0 ] && echo -n ","
            echo -n "{\"ip\":\"$IP\",\"mac\":\"$MAC\",\"hostname\":\"Device\"}"
            FIRST=0
        fi
    done
    
    echo "],"interface\":\"$IFACE\"}"
}

# Get blocked URLs as JSON
get_urls() {
    echo -n '{"urls":['
    FIRST=1
    while IFS= read -r url; do
        [ -z "$url" ] && continue
        [ $FIRST -eq 0 ] && echo -n ","
        echo -n "\"$url\""
        FIRST=0
    done < "$BLOCKLIST"
    echo ']}'
}

# HTTP response
respond() {
    METHOD="$1"
    PATH="$2"
    
    case "$PATH" in
        "/")
            echo "HTTP/1.1 200 OK"
            echo "Content-Type: text/html"
            echo "Connection: close"
            echo ""
            cat "$HTML"
            ;;
        "/api/devices")
            echo "HTTP/1.1 200 OK"
            echo "Content-Type: application/json"
            echo "Connection: close"
            echo ""
            get_devices
            ;;
        "/api/blocked-urls")
            echo "HTTP/1.1 200 OK"
            echo "Content-Type: application/json"
            echo "Connection: close"
            echo ""
            get_urls
            ;;
        *)
            echo "HTTP/1.1 404 Not Found"
            echo "Content-Type: text/plain"
            echo "Connection: close"
            echo ""
            echo "Not found"
            ;;
    esac
}

# Main server loop
echo "Starting server on port $PORT..."
while true; do
    {
        read -r REQUEST
        METHOD=$(echo "$REQUEST" | awk '{print $1}')
        PATH=$(echo "$REQUEST" | awk '{print $2}')
        
        # Skip headers
        while read -r line; do
            [ "$line" = $'\r' ] || [ -z "$line" ] && break
        done
        
        respond "$METHOD" "$PATH"
    } | nc -l -p $PORT -q 1 > /dev/null 2>&1
done
