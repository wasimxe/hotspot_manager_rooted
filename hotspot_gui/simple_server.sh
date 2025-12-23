#!/system/bin/sh
# Simple Hotspot GUI Server

PORT=8080
HTML_FILE="/data/data/com.termux/files/home/hotspot_gui/index.html"
BLOCKLIST="/data/data/com.termux/files/home/blocked_urls.txt"

touch "$BLOCKLIST"

# Serve content
serve() {
    while true; do
        {
            # Read request
            read -r REQUEST
            PATH=$(echo "$REQUEST" | awk '{print $2}')
            
            # Read headers until empty line
            while read -r line && [ "$line" != $'\r' ]; do
                :
            done
            
            # Handle requests
            case "$PATH" in
                "/"*)
                    # Serve HTML
                    echo "HTTP/1.1 200 OK"
                    echo "Content-Type: text/html; charset=UTF-8"
                    echo "Connection: close"
                    echo ""
                    cat "$HTML_FILE"
                    ;;
            esac
        } | nc -l -p $PORT -q 1
    done
}

echo "Server running on http://localhost:$PORT"
serve
