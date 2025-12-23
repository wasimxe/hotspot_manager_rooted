#!/data/data/com.termux/files/usr/bin/bash

# Start WiFi Settings Watchdog
# Wait for system to be ready
sleep 40

# Kill any existing watchdog
pkill -f "wifi-settings-watchdog.sh" 2>/dev/null

# Start watchdog in background
nohup /data/data/com.termux/files/home/wifi-settings-watchdog.sh > /dev/null 2>&1 &

echo "$(date): WiFi watchdog started" >> /data/data/com.termux/files/home/hotspot_boot.log
