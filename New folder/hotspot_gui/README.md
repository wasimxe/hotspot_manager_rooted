# Hotspot Manager - Mobile Hotspot Control & Monitoring

A powerful web-based hotspot management system for rooted Android devices that allows you to monitor connected devices, block URLs, and track live network traffic through your mobile hotspot.

## Features

- **Connected Device Monitoring**: View all devices connected to your hotspot with detailed information
- **URL/Domain Blocking**: Block specific websites and domains for all connected devices
- **Live Traffic Monitoring**: Real-time monitoring of network requests (optional, toggleable)
- **Device Management**:
  - Custom device names and notes
  - MAC address vendor detection
  - Connection statistics
  - Block/unblock individual devices
- **PWA Support**: Install as a Progressive Web App on your home screen
- **Responsive Design**: Works on mobile and desktop browsers

## Requirements

- Rooted Android device
- Termux app installed
- Python 3 installed in Termux
- Root access (su/Magisk)
- Active mobile hotspot

## Installation

### 1. Install Termux (if not already installed)
Download Termux from F-Droid: https://f-droid.org/packages/com.termux/

### 2. Install Dependencies in Termux

```bash
# Update packages
pkg update && pkg upgrade

# Install Python
pkg install python

# Install root access (if not already available)
pkg install tsu
```

### 3. Extract the Project

```bash
# Navigate to home directory
cd ~

# If you have the zip file, extract it
unzip hotspot_manager.zip

# Or manually create the directory and copy files
mkdir -p ~/hotspot_gui
cd ~/hotspot_gui
```

### 4. Copy Project Files

Transfer all files from the zip to `/data/data/com.termux/files/home/hotspot_gui/`:
- `server.py` - Main server script
- `index.html` - Web interface
- `blocked.html` - Blocked page shown to users (optional)
- `manifest.json` - PWA manifest (optional)
- `sw.js` - Service worker (optional)

### 5. Start the Server

```bash
cd ~/hotspot_gui
python3 server.py
```

The server will start on port 8080 and display:
```
Reloading blocked URLs from blocklist...
Hotspot GUI Server running on port 8080
Access at: http://localhost:8080
```

### 6. Access the Interface

Open your browser and navigate to:
- **On the device**: `http://localhost:8080`
- **From connected devices**: `http://192.168.43.1:8080` (or your hotspot IP)

## Usage

### Blocking URLs

1. Go to the "URL Blocking" tab
2. Enter a domain name (e.g., `facebook.com`, `youtube.com`)
3. Click "Block"
4. The system will block:
   - DNS queries (UDP/TCP port 53)
   - HTTP traffic (port 80)
   - HTTPS traffic (port 443)
   - Known domain variations

### Managing Devices

1. Go to the "Connected Devices" tab
2. View all connected devices with IP, MAC, and vendor information
3. Click "Edit" to add custom names and notes
4. Click "Block" to block a specific device

### Live Traffic Monitoring

1. Go to the "Live Monitor" tab
2. Toggle the switch to enable monitoring
3. View real-time network connections from all hotspot clients
4. Connections refresh every 3 seconds automatically
5. Click "Clear Logs" to reset the log buffer
6. **Note**: Monitoring only captures traffic while enabled

## Running as a Background Service

### Option 1: Using nohup

```bash
cd ~/hotspot_gui
nohup python3 server.py > server.log 2>&1 &
```

### Option 2: Using Termux:Boot (Recommended)

1. Install Termux:Boot from F-Droid
2. Create startup script:

```bash
mkdir -p ~/.termux/boot
nano ~/.termux/boot/start-hotspot-manager.sh
```

3. Add the following content:

```bash
#!/data/data/com.termux/files/usr/bin/bash
cd /data/data/com.termux/files/home/hotspot_gui
python3 server.py > /data/data/com.termux/files/home/hotspot.log 2>&1 &
```

4. Make it executable:

```bash
chmod +x ~/.termux/boot/start-hotspot-manager.sh
```

5. Reboot your device - the server will start automatically

## Stopping the Server

```bash
# Find the process ID
ps aux | grep server.py

# Kill the process
kill -9 <PID>

# Or kill all Python processes (use with caution)
pkill -9 -f server.py
```

## Configuration Files

All configuration files are stored in `/data/data/com.termux/files/home/`:

- `blocked_urls.txt` - List of blocked URLs (one per line)
- `device_info.json` - Custom device names and notes
- `mac_cache.json` - Cached MAC vendor lookups
- `monitor_config.json` - Live monitoring settings

## Troubleshooting

### Server won't start
- Ensure you have root access: `su` should work
- Check if port 8080 is available: `netstat -tlnp | grep 8080`
- Check Python installation: `python3 --version`

### URL blocking not working
- Verify iptables rules: `su -c "iptables -L FORWARD -v"`
- Check if the URL is in blocklist: `cat ~/blocked_urls.txt`
- Restart the server to reload rules

### Can't access from other devices
- Verify hotspot IP: `ip addr show wlan0`
- Ensure the server is listening on 0.0.0.0: `netstat -tlnp | grep 8080`
- Check firewall rules

### Live monitoring shows no traffic
- Enable monitoring using the toggle switch
- Verify conntrack is available: `cat /proc/net/nf_conntrack`
- Traffic only shows from hotspot clients (192.168.x.x)

## How It Works

### URL Blocking
The system uses iptables to block URLs at multiple layers:
1. **DNS blocking**: Blocks DNS queries containing the domain
2. **HTTP redirect**: Redirects HTTP requests to a blocked page
3. **HTTPS blocking**: Drops HTTPS connections (can't show custom page due to encryption)

### Live Monitoring
Reads connection tracking data from `/proc/net/nf_conntrack` to capture active connections from hotspot clients in real-time.

## Security Notes

- This tool requires root access to modify iptables
- Only run on trusted networks
- URLs are blocked system-wide for all hotspot users
- Live monitoring captures metadata only (IP, port, protocol)
- No packet inspection or deep packet analysis

## Uninstallation

```bash
# Stop the server
pkill -9 -f server.py

# Remove files
rm -rf ~/hotspot_gui

# Remove configuration files (optional)
rm -f ~/blocked_urls.txt ~/device_info.json ~/mac_cache.json ~/monitor_config.json

# Remove startup script (if using Termux:Boot)
rm -f ~/.termux/boot/start-hotspot-manager.sh
```

## Credits

Built with Python 3, vanilla JavaScript, and modern CSS. No external dependencies required.

## License

Free to use and modify for personal use.
