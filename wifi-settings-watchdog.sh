#!/data/data/com.termux/files/usr/bin/bash
#
# WiFi Settings Watchdog
# Monitors and enforces user-preferred WiFi channel and TX power settings
# Runs in background and re-applies settings every 30 seconds
#

CONFIG_FILE="/data/data/com.termux/files/home/wifi-settings.json"
HOSTAPD_CONF="/data/vendor/wifi/hostapd/hostapd_wlan0.conf"
LOG_FILE="/data/data/com.termux/files/home/wifi-watchdog.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $@" | tee -a "$LOG_FILE"
}

restart_hotspot() {
    log "Restarting hotspot to apply changes..."

    # Method 1: Try using svc command (most reliable)
    if su -c "svc wifi disable" 2>/dev/null && sleep 2 && su -c "svc wifi enable" 2>/dev/null; then
        log "✓ Hotspot restarted via svc command"
        return 0
    fi

    # Method 2: Try killing and restarting hostapd
    if su -c "killall hostapd" 2>/dev/null && sleep 2; then
        log "✓ Hotspot restarted via hostapd kill"
        return 0
    fi

    log "⚠ Could not restart hotspot automatically - please restart manually"
    return 1
}

apply_settings() {
    # Read user preferences from JSON
    if [ ! -f "$CONFIG_FILE" ]; then
        log "No config file found, skipping..."
        return
    fi

    PREFERRED_CHANNEL=$(grep -o '"channel":[[:space:]]*[0-9]*' "$CONFIG_FILE" | grep -o '[0-9]*')
    PREFERRED_POWER=$(grep -o '"tx_power":[[:space:]]*[0-9]*' "$CONFIG_FILE" | grep -o '[0-9]*')

    if [ -z "$PREFERRED_CHANNEL" ] || [ -z "$PREFERRED_POWER" ]; then
        log "Could not parse config file"
        return
    fi

    # Check current settings in hostapd config
    CURRENT_CHANNEL=$(su -c "grep '^channel=' $HOSTAPD_CONF 2>/dev/null" | cut -d= -f2)
    CURRENT_POWER=$(su -c "grep '^tx_power=' $HOSTAPD_CONF 2>/dev/null" | cut -d= -f2)

    CHANGED=0

    # Fix channel if different
    if [ "$CURRENT_CHANNEL" != "$PREFERRED_CHANNEL" ]; then
        log "Channel mismatch! Current: $CURRENT_CHANNEL, Preferred: $PREFERRED_CHANNEL - FIXING..."
        su -c "sed -i 's/^channel=.*/channel=$PREFERRED_CHANNEL/' $HOSTAPD_CONF" 2>/dev/null
        CHANGED=1
    fi

    # Fix TX power if different
    if [ "$CURRENT_POWER" != "$PREFERRED_POWER" ]; then
        log "TX Power mismatch! Current: $CURRENT_POWER, Preferred: $PREFERRED_POWER - FIXING..."

        # Check if tx_power line exists
        if su -c "grep -q '^tx_power=' $HOSTAPD_CONF" 2>/dev/null; then
            su -c "sed -i 's/^tx_power=.*/tx_power=$PREFERRED_POWER/' $HOSTAPD_CONF" 2>/dev/null
        else
            # Add tx_power after wpa_passphrase line
            su -c "sed -i '/^wpa_passphrase=/a tx_power=$PREFERRED_POWER' $HOSTAPD_CONF" 2>/dev/null
        fi
        CHANGED=1
    fi

    if [ $CHANGED -eq 1 ]; then
        log "✓ Settings corrected in config file (will apply on next hotspot restart)"
        # DO NOT auto-restart hotspot - prevents disconnections!
        # Settings will apply automatically on next manual restart or mobile reboot
    fi
}

log "========================================="
log "WiFi Settings Watchdog Started"
log "========================================="

# Run continuously
while true; do
    apply_settings
    sleep 30
done
