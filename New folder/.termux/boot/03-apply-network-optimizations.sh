#!/data/data/com.termux/files/usr/bin/bash

# Apply Network Optimizations on Boot
# Wait for system to be fully ready
sleep 50

# Apply sysctl optimizations
if [ -f /data/data/com.termux/files/home/sysctl-optimizations.conf ]; then
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ "$key" =~ ^#.*$ ]] && continue
        [ -z "$key" ] && continue

        # Apply setting
        su -c "sysctl -w ${key}=${value}" 2>/dev/null
    done < /data/data/com.termux/files/home/sysctl-optimizations.conf

    echo "$(date): Network optimizations applied" >> /data/data/com.termux/files/home/hotspot_boot.log
fi

# Run full booster script to ensure everything is optimal
/data/data/com.termux/files/home/ultimate-internet-booster.sh >> /data/data/com.termux/files/home/hotspot_boot.log 2>&1

echo "$(date): Internet booster completed" >> /data/data/com.termux/files/home/hotspot_boot.log
