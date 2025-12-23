#!/system/bin/sh
# Working HTTP Server without Python

PORT=8080
WEBROOT="/data/data/com.termux/files/home/hotspot_gui"

serve_request() {
    # Read the request line
    read method path proto
    
    # Skip all headers
    while read line; do
        line=$(echo "$line" | tr -d '\r\n')
        [ -z "$line" ] && break
    done
    
    # Route handling
    case "$path" in
        "/")
            echo "HTTP/1.0 200 OK"
            echo "Content-Type: text/html"
            echo ""
            cat "$WEBROOT/index.html"
            ;;
        "/api/devices")
            echo "HTTP/1.0 200 OK"
            echo "Content-Type: application/json"
            echo "Access-Control-Allow-Origin: *"
            echo ""
            
            # Get hotspot interface
            IFACE="wlan0"
            
            # Build JSON
            echo -n '{"devices":['
            FIRST=1
            ip neigh show dev $IFACE 2>/dev/null | while read ip dev mac rest; do
                if echo "$rest" | grep -qE "REACHABLE|STALE"; then
                    [ $FIRST -eq 0 ] && echo -n ","
                    echo -n "{\"ip\":\"$ip\",\"mac\":\"$mac\",\"hostname\":\"Device\"}"
                    FIRST=0
                fi
            done
            echo "],"interface\":\"$IFACE\"}"
            ;;
        "/api/blocked-urls")
            echo "HTTP/1.0 200 OK"
            echo "Content-Type: application/json"
            echo "Access-Control-Allow-Origin: *"
            echo ""
            
            echo -n '{"urls":['
            FIRST=1
            if [ -f /data/data/com.termux/files/home/blocked_urls.txt ]; then
                while read url; do
                    [ -z "$url" ] && continue
                    [ $FIRST -eq 0 ] && echo -n ","
                    echo -n "\"$url\""
                    FIRST=0
                done < /data/data/com.termux/files/home/blocked_urls.txt
            fi
            echo ']}'
            ;;
        *)
            echo "HTTP/1.0 404 Not Found"
            echo "Content-Type: text/plain"
            echo ""
            echo "Not found"
            ;;
    esac
}

echo "Starting server on port $PORT..."
echo "Access at: http://localhost:$PORT"

while true; do
    serve_request | nc -l -p $PORT 2>/dev/null
done
