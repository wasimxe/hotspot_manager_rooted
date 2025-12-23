# Android Hotspot Manager

A comprehensive web-based management system for Android mobile hotspot with advanced features including WiFi settings control, URL/IP blocking, network optimization, data usage tracking, and connected device management.

## Features

- Web-based interface on port 8080
- WiFi channel and TX power persistence
- Advanced URL/IP blocking with CIDR support
- Network optimization for maximum speed and stability
- Real-time data usage tracking per device
- Connected devices monitoring with MAC address tracking
- Automatic startup on boot
- All settings persist across restarts

## Screenshots

<p align="center">
  <img src="Screenshot 2025-12-24 011529.png" alt="Main Interface" width="800"/>
  <br><em>Main web interface showing WiFi settings and device management</em>
</p>

<p align="center">
  <img src="Screenshot 2025-12-24 011539.png" alt="URL Blocking" width="800"/>
  <br><em>Advanced URL/IP blocking with CIDR support</em>
</p>

<p align="center">
  <img src="Screenshot 2025-12-24 011610.png" alt="Data Usage & Devices" width="800"/>
  <br><em>Real-time data usage tracking and connected devices</em>
</p>

## Prerequisites

### Required Software

1. **Android Device with Root Access**
   - Rooted Android phone/tablet
   - Working hotspot capability

2. **Termux** (Install from F-Droid, NOT Google Play)
   - Download: https://f-droid.org/en/packages/com.termux/

3. **Termux:Boot** (For auto-start on device boot)
   - Download: https://f-droid.org/en/packages/com.termux.boot/

4. **Root Access Tools**
   - Magisk or SuperSU installed
   - `su` command working in Termux

## Installation

### Step 1: Install Required Packages

Open Termux and run:

```bash
pkg update
pkg upgrade
pkg install python tsu tcpdump sqlite
```

### Step 2: Extract Project Files

1. Copy the project zip file to your device
2. Extract to Termux home directory:

```bash
cd ~
unzip hotspot-manager.zip
chmod +x *.sh
chmod +x hotspot_gui/*.py
```

### Step 3: Setup Boot Scripts

```bash
mkdir -p ~/.termux/boot
chmod +x ~/.termux/boot/*.sh
```

### Step 4: Grant Root Permissions

Test root access:

```bash
su -c "id"
```

You should see `uid=0(root)`. If not, check your root setup.

### Step 5: Initial Configuration

Create required JSON files if they don't exist:

```bash
# WiFi settings
echo '{"channel": 11, "tx_power": 30}' > ~/wifi-settings.json

# Blocked URLs (will be created automatically by server)
touch ~/blocked_urls.json
```

## Starting the System

### Manual Start

#### Option 1: Using the Manager Script (Recommended)

```bash
~/hotspot-manager.sh start
```

Available commands:
- `start` - Start the hotspot server
- `stop` - Stop the hotspot server
- `restart` - Restart the hotspot server
- `status` - Check server status

#### Option 2: Direct Python Start

```bash
cd ~/hotspot_gui
python3 server.py &
```

### Automatic Start on Boot

1. Install and launch Termux:Boot app once (this enables boot functionality)
2. Reboot your device
3. Services will auto-start in this order:
   - Wait 10s → Start Hotspot Server (port 8080)
   - Wait 30s → Restore Firewall Rules
   - Wait 40s → Start WiFi Watchdog
   - Wait 50s → Apply Network Optimizations

## Accessing the Web Interface

1. Start your mobile hotspot
2. Connect your PC/device to the hotspot
3. Find your hotspot IP (usually `192.168.x.1`)
4. Open browser: `http://192.168.x.1:8080` (or your specific IP)

Common IPs:
- `http://192.168.43.1:8080`
- `http://192.168.68.1:8080`
- `http://192.168.50.1:8080`

## Using the Features

### WiFi Settings

**Channel Selection:**
- Choose WiFi channel (1-13)
- Recommended: Channel 11 for best compatibility
- Settings persist and are enforced every 30 seconds

**TX Power:**
- Set transmission power (0-30 dBm)
- Higher = better range, more power consumption
- Recommended: 30 dBm for maximum range

### URL/IP Blocking

#### Basic Blocking

1. Enter domain name (e.g., `example.com`)
2. Click "Block URL"
3. System auto-resolves IPs and blocks them

#### Advanced Blocking (Custom IP Ranges)

1. Click "Advanced +" button
2. Enter domain name
3. Enter IP ranges (one per line):
   ```
   157.240.0.0/16
   31.13.0.0/16
   104.18.26.120
   ```
4. Click "Block with Custom IPs"

#### Editing Blocked URLs

1. Find the domain in "Blocked URLs" section
2. Click "Edit" button
3. Modify IP ranges
4. Click "Update Blocking"

**Supported IP Formats:**
- Single IP: `104.18.26.120`
- CIDR notation: `157.240.0.0/16`
- Multiple ranges (one per line)

### Network Optimization

Click the "⚡ Boost" button to apply:

1. **Remove duplicate rules** - Fixes slow internet
2. **TCP BBR** - Advanced congestion control
3. **TCP Fast Open** - Faster connections
4. **Optimized buffers** - 16MB TCP windows
5. **Connection tracking** - Optimized for high traffic
6. **IPv6 disabled** - Reduces overhead
7. **And 7 more optimizations**

### Data Usage Tracking

- View real-time data usage per connected device
- Shows upload/download for each device
- Total usage statistics
- Automatic tracking (no configuration needed)

### Connected Devices

- See all devices connected to your hotspot
- Shows IP address, MAC address, hostname
- Real-time connection status
- Data usage per device

## File Structure

```
/data/data/com.termux/files/home/
├── hotspot_gui/
│   ├── server.py              # Main server (API + web interface)
│   ├── index.html             # Web interface
│   └── data_usage.db          # SQLite database for usage tracking
├── .termux/boot/
│   ├── 01-start-hotspot-server.sh      # Auto-start server
│   ├── 02-wifi-watchdog.sh             # Auto-start WiFi watchdog
│   └── 03-apply-network-optimizations.sh  # Auto-apply optimizations
├── hotspot-manager.sh         # Service management script
├── wifi-settings-watchdog.sh  # Monitors and enforces WiFi settings
├── ultimate-internet-booster.sh  # Network optimization script
├── learn-facebook-ips.sh      # Tool to capture and block specific IPs
├── wifi-settings.json         # WiFi preferences storage
├── blocked_urls.json          # Blocked domains and IP ranges
└── README.md                  # This file
```

## Configuration Files

### wifi-settings.json

```json
{
  "channel": 11,
  "tx_power": 30,
  "last_updated": "2025-12-24T00:00:00"
}
```

### blocked_urls.json

```json
{
  "example.com": {
    "ip_ranges": ["104.18.26.120", "104.18.27.120"],
    "ips": ["104.18.26.120", "104.18.27.120"],
    "is_ip_address": false,
    "blocked_at": "2025-12-24T00:00:00",
    "rules_count": 2
  }
}
```

## API Endpoints

### WiFi Management
- `GET /api/wifi-settings` - Get current WiFi settings
- `POST /api/set-channel` - Set WiFi channel
- `POST /api/set-tx-power` - Set TX power

### URL Blocking
- `GET /api/blocked-urls` - List all blocked URLs
- `POST /api/block-url` - Block URL (auto-resolve IPs)
- `POST /api/block-url-advanced` - Block with custom IP ranges
- `POST /api/update-blocked-url` - Update existing block
- `GET /api/get-blocked-url?url=example.com` - Get IP ranges for URL
- `POST /api/unblock-url` - Remove blocking

### Network Optimization
- `POST /api/boost-internet` - Apply all optimizations
- `GET /api/firewall-rules` - View current iptables rules

### Data Tracking
- `GET /api/data-usage` - Get data usage statistics
- `GET /api/connected-devices` - List connected devices

### System
- `POST /api/hotspot/start` - Start hotspot
- `POST /api/hotspot/stop` - Stop hotspot
- `GET /api/hotspot/status` - Check hotspot status

## Advanced Tools

### Learning Facebook IPs

If Facebook uses region-specific IPs not in standard ranges:

```bash
~/learn-facebook-ips.sh
```

This tool:
1. Monitors network for 30 seconds
2. Captures destination IPs you connect to
3. Shows captured IPs
4. Lets you select which are Facebook
5. Adds them to blocking automatically

Usage:
1. Run the script
2. Press ENTER to start monitoring
3. Visit Facebook from your PC during the 30 seconds
4. Choose which IPs to block

## Troubleshooting

### Server Won't Start

**Check if already running:**
```bash
ps aux | grep server.py
```

**Check port 8080:**
```bash
netstat -tulpn | grep 8080
```

**Kill existing server:**
```bash
pkill -f server.py
~/hotspot-manager.sh start
```

### Root Access Issues

**Test root:**
```bash
su -c "whoami"
```

Should return `root`. If not:
- Check if device is rooted
- Reinstall Magisk/SuperSU
- Grant Termux root permission in Magisk Manager

### WiFi Settings Not Persisting

**Check watchdog is running:**
```bash
ps aux | grep wifi-settings-watchdog
```

**Restart watchdog:**
```bash
pkill -f wifi-settings-watchdog
nohup ~/wifi-settings-watchdog.sh > /dev/null 2>&1 &
```

### URL Blocking Not Working

**Check iptables rules:**
```bash
su -c "iptables -L FORWARD -v -n | head -20"
```

**Check blocked IPs:**
```bash
cat ~/blocked_urls.json
```

**Verify blocking rules are at TOP:**
- DROP rules should appear before ACCEPT rules
- If not, click "⚡ Boost" button to fix order

**Region-specific IPs:**
- Some services use different IPs in different regions
- Use `learn-facebook-ips.sh` to capture actual IPs
- Add them using "Advanced +" blocking

### Internet Slow After Blocking

**Remove duplicate rules:**
```bash
~/ultimate-internet-booster.sh
```

**Check rule count:**
```bash
su -c "iptables -L FORWARD | wc -l"
```

Should be under 50 rules. If hundreds/thousands, run booster script.

### Boot Scripts Not Working

**Check Termux:Boot installed:**
- Open Termux:Boot app once to enable
- Reboot device

**Check boot scripts exist:**
```bash
ls -la ~/.termux/boot/
```

**Check permissions:**
```bash
chmod +x ~/.termux/boot/*.sh
```

**Manual boot test:**
```bash
~/.termux/boot/01-start-hotspot-server.sh
```

### Can't Access Web Interface

**Check server is running:**
```bash
~/hotspot-manager.sh status
```

**Check hotspot IP:**
```bash
ip addr show wlan0 | grep inet
```

**Try different browsers:**
- Chrome, Firefox, Edge

**Check firewall:**
```bash
su -c "iptables -L INPUT -v -n | grep 8080"
```

## Performance Tips

1. **Keep blocking rules under 50** - More rules = slower internet
2. **Use CIDR ranges** - Block 157.240.0.0/16 instead of individual IPs
3. **Run booster regularly** - Removes duplicates and optimizes
4. **Use channel 11** - Best balance of compatibility and performance
5. **Monitor data usage** - Identify heavy users
6. **Disable IPv6** - Already done by booster script

## Security Notes

1. **Web interface has NO authentication** - Only use on trusted hotspot
2. **Root access required** - Be careful with scripts
3. **Blocking is IP-based** - No DNS string matching (faster but less flexible)
4. **All traffic logged** - Data usage tracking stores all connections
5. **Boot scripts run as root** - Review before enabling

## Backup and Restore

### Backup

```bash
cd ~
tar -czf hotspot-backup-$(date +%Y%m%d).tar.gz \
  hotspot_gui/ \
  *.sh \
  wifi-settings.json \
  blocked_urls.json \
  .termux/boot/
```

### Restore

```bash
cd ~
tar -xzf hotspot-backup-YYYYMMDD.tar.gz
chmod +x *.sh
chmod +x .termux/boot/*.sh
```

## Uninstallation

```bash
# Stop services
~/hotspot-manager.sh stop
pkill -f wifi-settings-watchdog

# Remove boot scripts
rm -f ~/.termux/boot/01-start-hotspot-server.sh
rm -f ~/.termux/boot/02-wifi-watchdog.sh
rm -f ~/.termux/boot/03-apply-network-optimizations.sh

# Remove iptables rules
su -c "iptables -F FORWARD"

# Remove files (optional)
rm -rf ~/hotspot_gui
rm -f ~/hotspot-manager.sh
rm -f ~/wifi-settings-watchdog.sh
rm -f ~/ultimate-internet-booster.sh
rm -f ~/wifi-settings.json
rm -f ~/blocked_urls.json
```

## Support

This is a custom project. For issues:
1. Check troubleshooting section above
2. Review log files: `~/hotspot_gui/server.log` (if exists)
3. Check iptables rules: `su -c "iptables -L FORWARD -v -n"`
4. Verify root access: `su -c "id"`

## Version

- Created: 2025-12-24
- Last Updated: 2025-12-24
- Python Version: 3.x
- Tested on: Android 9+ with Termux

## License

Custom project - Use at your own risk. No warranty provided.

## Credits

Developed for Android hotspot management with focus on:
- Speed and stability
- Persistent settings
- IP-based blocking (no DNS overhead)
- Comprehensive device management
