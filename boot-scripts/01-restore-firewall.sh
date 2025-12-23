#!/data/data/com.termux/files/usr/bin/bash

# Wait for system to be ready
sleep 30

# Restore iptables rules
su -c "iptables-restore < /data/data/com.termux/files/home/iptables-rules.txt"

# Start hotspot server
cd /data/data/com.termux/files/home/hotspot_gui
nohup python3 server.py > /data/data/com.termux/files/home/hotspot_server.log 2>&1 &

