#!/data/data/com.termux/files/usr/bin/bash
# Quick restart script for hotspot server

echo "Stopping old server..."
pkill -9 python3

echo "Starting new server..."
cd /data/data/com.termux/files/home/hotspot_gui
python3 server.py > ~/hotspot.log 2>&1 &

sleep 2
if ps aux | grep -v grep | grep "python3 server.py" > /dev/null; then
    echo "✓ Server restarted on port 8080"
    echo "✓ Access: http://localhost:8080"
else
    echo "✗ Failed to start"
    tail -20 ~/hotspot.log
fi
