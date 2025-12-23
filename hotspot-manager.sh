#!/data/data/com.termux/files/usr/bin/bash

# Hotspot Manager Control Script
# Usage: ./hotspot-manager.sh [start|stop|restart|status]

SERVER_DIR="/data/data/com.termux/files/home/hotspot_gui"
LOG_FILE="/data/data/com.termux/files/home/hotspot_server.log"
PID_FILE="/data/data/com.termux/files/home/hotspot_server.pid"

start_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "Server is already running (PID: $PID)"
            return
        fi
    fi

    echo "Starting Hotspot Manager server..."
    cd "$SERVER_DIR" || exit 1
    nohup python3 server.py > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    sleep 2

    if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
        echo "✓ Server started successfully (PID: $(cat "$PID_FILE"))"
        echo "✓ Access at: http://localhost:8080"
    else
        echo "✗ Failed to start server. Check log: $LOG_FILE"
    fi
}

stop_server() {
    echo "Stopping Hotspot Manager server..."
    pkill -9 -f "python3.*server.py" 2>/dev/null
    rm -f "$PID_FILE"
    echo "✓ Server stopped"
}

restart_server() {
    stop_server
    sleep 1
    start_server
}

status_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "✓ Server is running (PID: $PID)"
            echo "  Access at: http://localhost:8080"
            return 0
        fi
    fi

    # Check if server is running but PID file is missing
    if pgrep -f "python3.*server.py" > /dev/null; then
        echo "⚠ Server is running but PID file is missing"
        pgrep -f "python3.*server.py"
        return 0
    fi

    echo "✗ Server is not running"
    return 1
}

case "$1" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        status_server
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the hotspot manager server"
        echo "  stop    - Stop the hotspot manager server"
        echo "  restart - Restart the hotspot manager server"
        echo "  status  - Check if server is running"
        exit 1
        ;;
esac
