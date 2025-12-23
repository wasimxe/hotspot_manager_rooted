#!/usr/bin/env python3
"""
Hotspot GUI Web Server
Simple HTTP server with API endpoints for hotspot management
"""

import json
import subprocess
import os
import re
import socket
import urllib.request
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT = 8080
WEBROOT = "/data/data/com.termux/files/home/hotspot_gui"
BLOCKLIST = "/data/data/com.termux/files/home/blocked_urls.txt"
BLOCKLIST_JSON = "/data/data/com.termux/files/home/blocked_urls.json"
CACHE_FILE = "/data/data/com.termux/files/home/mac_cache.json"
DEVICE_INFO_FILE = "/data/data/com.termux/files/home/device_info.json"
MONITOR_CONFIG_FILE = "/data/data/com.termux/files/home/monitor_config.json"
MONITOR_LOG_FILE = "/data/data/com.termux/files/home/monitor_log.txt"

# Ensure blocklist exists
open(BLOCKLIST, 'a').close()

# Load device info (custom names, notes, etc.)
DEVICE_INFO = {}
try:
    if os.path.exists(DEVICE_INFO_FILE):
        with open(DEVICE_INFO_FILE, 'r') as f:
            DEVICE_INFO = json.load(f)
except:
    pass

# Load MAC lookup cache
MAC_LOOKUP_CACHE = {}
try:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            MAC_LOOKUP_CACHE = json.load(f)
except:
    pass

# Load monitoring configuration
MONITOR_CONFIG = {'enabled': False, 'max_logs': 500}
try:
    if os.path.exists(MONITOR_CONFIG_FILE):
        with open(MONITOR_CONFIG_FILE, 'r') as f:
            MONITOR_CONFIG = json.load(f)
except:
    pass

# Removed monitoring code - focusing on blocking/unblocking only

# MAC Vendor database (top vendors for device identification)
MAC_VENDORS = {
    '00:00:5e': 'ICANN',
    '00:01:42': 'Cisco',
    '00:03:93': 'Apple',
    '00:05:02': 'Apple',
    '00:0a:95': 'Apple',
    '00:0d:93': 'Apple',
    '00:10:18': 'Broadcom',
    '00:11:24': 'Apple',
    '00:13:72': 'Cisco',
    '00:14:51': 'Apple',
    '00:15:00': 'Cisco',
    '00:16:cb': 'Apple',
    '00:17:f2': 'Apple',
    '00:19:e3': 'Apple',
    '00:1b:63': 'Apple',
    '00:1c:b3': 'Apple',
    '00:1d:4f': 'Apple',
    '00:1e:52': 'Apple',
    '00:1e:c2': 'Apple',
    '00:1f:5b': 'Apple',
    '00:1f:f3': 'Apple',
    '00:21:e9': 'Apple',
    '00:22:41': 'Apple',
    '00:23:12': 'Apple',
    '00:23:32': 'Apple',
    '00:23:6c': 'Apple',
    '00:23:df': 'Apple',
    '00:24:36': 'Apple',
    '00:25:00': 'Apple',
    '00:25:4b': 'Apple',
    '00:25:bc': 'Apple',
    '00:26:08': 'Apple',
    '00:26:4a': 'Apple',
    '00:26:b0': 'Apple',
    '00:26:bb': 'Apple',
    '00:30:65': 'Apple',
    '00:50:e4': 'Apple',
    '04:0c:ce': 'Apple',
    '04:15:52': 'Apple',
    '04:26:65': 'Apple',
    '04:54:53': 'Apple',
    '08:00:07': 'Apple',
    '08:66:98': 'Apple',
    '08:70:45': 'Apple',
    '0c:3e:9f': 'Apple',
    '0c:74:c2': 'Apple',
    '10:9a:dd': 'Apple',
    '10:dd:b1': 'Apple',
    '14:10:9f': 'Apple',
    '14:5a:05': 'Apple',
    '14:8f:c6': 'Apple',
    '18:34:51': 'Apple',
    '18:3d:a2': 'Apple',
    '18:e7:f4': 'Apple',
    '1c:36:bb': 'Apple',
    '1c:5c:f2': 'Apple',
    '1c:ab:a7': 'Apple',
    '1c:e1:92': 'Samsung',
    '1c:90:ff': 'Samsung',
    '20:02:af': 'Apple',
    '20:7d:74': 'Apple',
    '20:ab:37': 'Apple',
    '20:c9:d0': 'Apple',
    '24:0a:64': 'Apple',
    '24:1e:eb': 'Apple',
    '24:5b:a7': 'Apple',
    '24:a0:74': 'Apple',
    '24:ab:81': 'Apple',
    '28:37:37': 'Apple',
    '28:5a:eb': 'Apple',
    '28:6a:b8': 'Apple',
    '28:a0:2b': 'Apple',
    '28:cf:da': 'Apple',
    '28:cf:e9': 'Apple',
    '28:e1:4c': 'Apple',
    '28:e7:cf': 'Apple',
    '2c:1f:23': 'Apple',
    '2c:33:61': 'Apple',
    '2c:36:f8': 'Apple',
    '2c:3a:e8': 'Samsung',
    '2c:be:08': 'Apple',
    '2c:f0:a2': 'Apple',
    '2c:f0:ee': 'Apple',
    '30:10:e4': 'Samsung',
    '30:35:ad': 'Apple',
    '30:3a:64': 'Apple',
    '30:63:6b': 'Samsung',
    '30:90:ab': 'Apple',
    '30:f7:72': 'Apple',
    '34:12:f9': 'Apple',
    '34:15:9e': 'Apple',
    '34:36:3b': 'Apple',
    '34:51:c9': 'Apple',
    '34:a3:95': 'Apple',
    '34:c0:59': 'Samsung',
    '34:e2:fd': 'Apple',
    '38:0f:4a': 'Apple',
    '38:48:4c': 'Apple',
    '38:89:2c': 'Samsung',
    '38:b5:4d': 'Apple',
    '38:c9:86': 'Apple',
    '3c:07:54': 'Apple',
    '3c:15:c2': 'Apple',
    '3c:2e:f9': 'Apple',
    '3c:d0:f8': 'Apple',
    '40:30:04': 'Apple',
    '40:3c:fc': 'Apple',
    '40:4d:7f': 'Apple',
    '40:6c:8f': 'Apple',
    '40:78:6a': 'Apple',
    '40:a6:d9': 'Apple',
    '40:b3:95': 'Apple',
    '40:cb:c0': 'Apple',
    '40:d3:2d': 'Apple',
    '44:00:10': 'Apple',
    '44:2a:60': 'Apple',
    '44:4c:0c': 'Apple',
    '44:d8:84': 'Apple',
    '44:fb:42': 'Apple',
    '48:3b:38': 'Apple',
    '48:43:7c': 'Apple',
    '48:4b:aa': 'Apple',
    '48:60:bc': 'Apple',
    '48:74:6e': 'Apple',
    '48:a1:95': 'Apple',
    '48:d7:05': 'Apple',
    '4c:32:75': 'Apple',
    '4c:3c:16': 'Samsung',
    '4c:57:ca': 'Apple',
    '4c:7c:5f': 'Apple',
    '4c:8d:79': 'Apple',
    '50:32:37': 'Apple',
    '50:8b:b9': 'Samsung',
    '50:ea:d6': 'Apple',
    '50:ed:3c': 'Samsung',
    '54:26:96': 'Apple',
    '54:2a:1b': 'Cisco',
    '54:72:4f': 'Apple',
    '54:9f:13': 'Apple',
    '54:ae:27': 'Apple',
    '54:e4:3a': 'Apple',
    '54:ea:a8': 'Apple',
    '58:00:e3': 'Cisco',
    '58:1f:aa': 'Apple',
    '58:2a:f7': 'Xiaomi',
    '58:40:4e': 'Apple',
    '58:55:ca': 'Apple',
    '58:b0:35': 'Apple',
    '5c:59:48': 'Apple',
    '5c:95:ae': 'Apple',
    '5c:96:9d': 'Apple',
    '5c:97:f3': 'Apple',
    '5c:f9:38': 'Apple',
    '60:03:08': 'Apple',
    '60:33:4b': 'Apple',
    '60:69:44': 'Apple',
    '60:92:17': 'Samsung',
    '60:c5:47': 'Apple',
    '60:d9:c7': 'Apple',
    '60:f8:1d': 'Apple',
    '60:fa:cd': 'Apple',
    '60:fb:42': 'Apple',
    '64:20:0c': 'Apple',
    '64:76:ba': 'Apple',
    '64:a3:cb': 'Apple',
    '64:b0:a6': 'Apple',
    '64:b9:e8': 'Apple',
    '64:e6:82': 'Apple',
    '68:5b:35': 'Apple',
    '68:64:4b': 'Apple',
    '68:96:7b': 'Apple',
    '68:9c:70': 'Apple',
    '68:a8:6d': 'Apple',
    '68:d9:3c': 'Apple',
    '68:fe:f7': 'Apple',
    '6c:19:c0': 'Apple',
    '6c:3e:6d': 'Apple',
    '6c:40:08': 'Apple',
    '6c:70:9f': 'Apple',
    '6c:72:20': 'Apple',
    '6c:94:66': 'Apple',
    '6c:96:cf': 'Apple',
    '70:11:24': 'Apple',
    '70:3e:ac': 'Samsung',
    '70:48:0f': 'Apple',
    '70:56:81': 'Apple',
    '70:73:cb': 'Apple',
    '70:a2:b3': 'Apple',
    '70:cd:60': 'Apple',
    '70:de:e2': 'Apple',
    '70:e7:2c': 'Apple',
    '70:ec:e4': 'Apple',
    '74:1b:b2': 'Apple',
    '74:81:14': 'Apple',
    '74:e1:b6': 'Apple',
    '74:e2:f5': 'Apple',
    '78:28:ca': 'Apple',
    '78:31:c1': 'Apple',
    '78:4f:43': 'Apple',
    '78:7b:8a': 'Apple',
    '78:a3:e4': 'Apple',
    '78:ca:39': 'Apple',
    '78:d7:5f': 'Apple',
    '78:fd:94': 'Apple',
    '7c:01:91': 'Apple',
    '7c:04:d0': 'Apple',
    '7c:11:be': 'Apple',
    '7c:50:49': 'Apple',
    '7c:6d:f8': 'Apple',
    '7c:c3:a1': 'Apple',
    '7c:c5:37': 'Apple',
    '7c:d1:c3': 'Apple',
    '7c:f0:5f': 'Apple',
    '80:00:0b': 'Oppo',
    '80:19:34': 'Apple',
    '80:1f:02': 'Samsung',
    '80:49:71': 'Apple',
    '80:4e:81': 'Samsung',
    '80:92:9f': 'Apple',
    '80:9b:20': 'Apple',
    '80:a2:35': 'Apple',
    '80:be:05': 'Apple',
    '80:d6:05': 'Apple',
    '80:e6:50': 'Apple',
    '84:38:35': 'Apple',
    '84:78:8b': 'Samsung',
    '84:85:06': 'Apple',
    '84:89:ad': 'Apple',
    '84:8e:0c': 'Apple',
    '84:fc:fe': 'Apple',
    '88:1f:a1': 'Apple',
    '88:53:95': 'Apple',
    '88:63:df': 'Apple',
    '88:66:5a': 'Apple',
    '88:6b:6e': 'Apple',
    '88:c6:63': 'Apple',
    '88:e8:7f': 'Apple',
    '8c:00:6d': 'Apple',
    '8c:29:37': 'Apple',
    '8c:2d:aa': 'Apple',
    '8c:58:77': 'Apple',
    '8c:7c:92': 'Apple',
    '8c:85:90': 'Apple',
    '8c:8e:f2': 'Apple',
    '90:27:e4': 'Apple',
    '90:72:40': 'Apple',
    '90:84:0d': 'Apple',
    '90:8d:6c': 'Apple',
    '90:9c:4a': 'Apple',
    '90:b0:ed': 'Apple',
    '90:b2:1f': 'Apple',
    '94:94:26': 'Apple',
    '94:bf:2d': 'Apple',
    '94:e9:6a': 'Apple',
    '94:f6:a3': 'Apple',
    '98:01:a7': 'Apple',
    '98:03:d8': 'Apple',
    '98:0c:82': 'Cisco',
    '98:5a:eb': 'Apple',
    '98:b8:e3': 'Apple',
    '98:d6:bb': 'Apple',
    '98:e0:d9': 'Apple',
    '98:f0:ab': 'Apple',
    '98:fe:94': 'Apple',
    '9c:04:eb': 'Apple',
    '9c:20:7b': 'Apple',
    '9c:29:76': 'Apple',
    '9c:35:eb': 'Apple',
    '9c:84:bf': 'Apple',
    '9c:f4:8e': 'Apple',
    'a0:18:28': 'Samsung',
    'a0:1b:29': 'Samsung',
    'a0:99:9b': 'Apple',
    'a0:d7:95': 'Apple',
    'a4:31:35': 'Apple',
    'a4:5e:60': 'Apple',
    'a4:67:06': 'Samsung',
    'a4:83:e7': 'Apple',
    'a4:b1:97': 'Apple',
    'a4:c3:61': 'Apple',
    'a4:d1:8c': 'Apple',
    'a8:20:66': 'Apple',
    'a8:5b:78': 'Apple',
    'a8:60:b6': 'Apple',
    'a8:66:7f': 'Apple',
    'a8:80:55': 'Vivo',
    'a8:86:dd': 'Apple',
    'a8:96:75': 'Apple',
    'a8:bb:cf': 'Apple',
    'a8:be:27': 'Apple',
    'a8:fa:d8': 'Apple',
    'ac:1f:74': 'Apple',
    'ac:29:3a': 'Apple',
    'ac:37:43': 'Apple',
    'ac:3c:0b': 'Apple',
    'ac:61:75': 'Samsung',
    'ac:7f:3e': 'Apple',
    'ac:87:a3': 'Apple',
    'ac:bc:32': 'Apple',
    'ac:cf:5c': 'Apple',
    'ac:de:48': 'Apple',
    'ac:e4:b5': 'Samsung',
    'b0:19:c6': 'Apple',
    'b0:34:95': 'Apple',
    'b0:65:bd': 'Apple',
    'b0:9f:ba': 'Apple',
    'b0:ca:68': 'Apple',
    'b4:18:d1': 'Apple',
    'b4:8b:19': 'Apple',
    'b4:f0:ab': 'Apple',
    'b4:f6:1c': 'Apple',
    'b8:09:8a': 'Apple',
    'b8:17:c2': 'Apple',
    'b8:41:a4': 'Apple',
    'b8:44:d9': 'Apple',
    'b8:5d:0a': 'Apple',
    'b8:63:4d': 'Apple',
    'b8:78:2e': 'Apple',
    'b8:c1:11': 'Apple',
    'b8:c7:5d': 'Apple',
    'b8:e8:56': 'Apple',
    'b8:f6:b1': 'Apple',
    'b8:ff:61': 'Apple',
    'bc:3b:af': 'Apple',
    'bc:52:b7': 'Apple',
    'bc:54:2f': 'Apple',
    'bc:67:1c': 'Apple',
    'bc:6c:21': 'Apple',
    'bc:92:6b': 'Apple',
    'bc:9f:ef': 'Apple',
    'c0:1a:da': 'Apple',
    'c0:63:94': 'Apple',
    'c0:84:7d': 'Apple',
    'c0:9a:d0': 'Apple',
    'c0:b6:58': 'Apple',
    'c0:cc:f8': 'Apple',
    'c0:ce:cd': 'Apple',
    'c0:d0:12': 'Samsung',
    'c0:f2:fb': 'Apple',
    'c4:2c:03': 'Apple',
    'c4:61:8b': 'Samsung',
    'c4:b3:01': 'Apple',
    'c8:1e:e7': 'Apple',
    'c8:2a:14': 'Apple',
    'c8:33:4b': 'Apple',
    'c8:60:00': 'Cisco',
    'c8:69:cd': 'Apple',
    'c8:85:50': 'Apple',
    'c8:89:f3': 'Apple',
    'c8:b5:b7': 'Apple',
    'c8:bc:c8': 'Apple',
    'c8:d0:83': 'Apple',
    'cc:08:8d': 'Apple',
    'cc:20:e8': 'Apple',
    'cc:25:ef': 'Apple',
    'cc:29:f5': 'Apple',
    'cc:2d:b7': 'Apple',
    'cc:3a:61': 'Samsung',
    'cc:44:63': 'Apple',
    'cc:4b:73': 'Samsung',
    'cc:78:5f': 'Apple',
    'cc:c7:60': 'Apple',
    'd0:03:4b': 'Apple',
    'd0:04:01': 'Apple',
    'd0:23:db': 'Apple',
    'd0:25:44': 'Apple',
    'd0:33:11': 'Apple',
    'd0:4f:7e': 'Apple',
    'd0:81:7a': 'Apple',
    'd0:a6:37': 'Apple',
    'd0:c5:f3': 'Apple',
    'd0:e1:40': 'Apple',
    'd4:61:9d': 'Apple',
    'd4:85:64': 'Apple',
    'd4:90:9c': 'Apple',
    'd4:9a:20': 'Apple',
    'd4:a3:3d': 'Apple',
    'd4:dc:cd': 'Apple',
    'd4:f4:6f': 'Apple',
    'd8:00:4d': 'Apple',
    'd8:1d:72': 'Apple',
    'd8:30:62': 'Apple',
    'd8:49:0b': 'Apple',
    'd8:5d:e2': 'Apple',
    'd8:96:95': 'Apple',
    'd8:9e:3f': 'Apple',
    'd8:a2:5e': 'Apple',
    'd8:bb:2c': 'Apple',
    'd8:cf:9c': 'Apple',
    'd8:d1:cb': 'Apple',
    'dc:0c:2d': 'Apple',
    'dc:2b:2a': 'Apple',
    'dc:2b:61': 'Apple',
    'dc:37:18': 'Samsung',
    'dc:3e:51': 'Samsung',
    'dc:41:e4': 'Samsung',
    'dc:56:e7': 'Apple',
    'dc:86:d8': 'Apple',
    'dc:9b:9c': 'Apple',
    'dc:a4:ca': 'Apple',
    'dc:a9:04': 'Apple',
    'dc:d3:a2': 'Apple',
    'dc:e5:5b': 'Samsung',
    'e0:05:c5': 'Apple',
    'e0:2a:82': 'Apple',
    'e0:33:8e': 'Apple',
    'e0:36:76': 'Samsung',
    'e0:5f:45': 'Apple',
    'e0:66:78': 'Apple',
    'e0:89:7e': 'Apple',
    'e0:ac:cb': 'Apple',
    'e0:b5:2d': 'Apple',
    'e0:b9:a5': 'Apple',
    'e0:b9:e5': 'Apple',
    'e0:c7:67': 'Apple',
    'e0:c9:7a': 'Apple',
    'e0:f5:c6': 'Apple',
    'e0:f8:47': 'Apple',
    'e4:25:e7': 'Apple',
    'e4:8b:7f': 'Apple',
    'e4:98:d6': 'Apple',
    'e4:9a:79': 'Apple',
    'e4:ce:8f': 'Apple',
    'e4:e4:ab': 'Apple',
    'e8:04:0b': 'Apple',
    'e8:06:88': 'Apple',
    'e8:2a:ea': 'Apple',
    'e8:40:f2': 'Apple',
    'e8:80:2e': 'Apple',
    'e8:8d:28': 'Apple',
    'ec:35:86': 'Apple',
    'ec:85:2f': 'Apple',
    'ec:a8:6b': 'Apple',
    'ec:f0:73': 'Samsung',
    'f0:18:98': 'Apple',
    'f0:24:75': 'Samsung',
    'f0:72:8c': 'Apple',
    'f0:98:9d': 'Apple',
    'f0:9f:c2': 'Apple',
    'f0:b4:79': 'Apple',
    'f0:c3:71': 'Samsung',
    'f0:cb:a1': 'Apple',
    'f0:d1:a9': 'Apple',
    'f0:db:e2': 'Apple',
    'f0:db:f8': 'Apple',
    'f0:dc:e2': 'Apple',
    'f0:f6:1c': 'Apple',
    'f4:0f:24': 'Apple',
    'f4:1b:a1': 'Apple',
    'f4:31:c3': 'Apple',
    'f4:37:b7': 'Apple',
    'f4:5c:89': 'Apple',
    'f4:f1:5a': 'Apple',
    'f4:f9:51': 'Apple',
    'f8:1e:df': 'Apple',
    'f8:27:93': 'Apple',
    'f8:2d:7c': 'Samsung',
    'f8:4f:ad': 'Samsung',
    'f8:95:c7': 'Apple',
    'f8:e9:4e': 'Apple',
    'fc:18:3c': 'Samsung',
    'fc:25:3f': 'Apple',
    'fc:2a:9c': 'Samsung',
    'fc:64:ba': 'Apple',
    'fc:e9:98': 'Apple',
    'fc:fc:48': 'Apple',
}

def save_mac_cache():
    """Save MAC lookup cache to file"""
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(MAC_LOOKUP_CACHE, f)
    except:
        pass

def save_device_info():
    """Save device info to file"""
    try:
        with open(DEVICE_INFO_FILE, 'w') as f:
            json.dump(DEVICE_INFO, f, indent=2)
    except:
        pass

def save_monitor_config():
    """Save monitoring configuration to file"""
    try:
        with open(MONITOR_CONFIG_FILE, 'w') as f:
            json.dump(MONITOR_CONFIG, f, indent=2)
    except:
        pass

# Monitoring functions removed - focusing on blocking only


def parse_dns_query(packet_data):
    """Parse DNS query from packet data to extract domain name"""
    try:
        # DNS query starts after UDP header (8 bytes) + IP header
        # This is a simplified parser for DNS queries
        if len(packet_data) < 12:
            return None

        # Skip DNS header (12 bytes)
        offset = 12
        domain_parts = []

        while offset < len(packet_data):
            length = packet_data[offset]
            if length == 0:
                break
            if length > 63:  # Invalid label length
                break
            offset += 1
            if offset + length > len(packet_data):
                break

            label = packet_data[offset:offset+length].decode('ascii', errors='ignore')
            domain_parts.append(label)
            offset += length

        if domain_parts:
            return '.'.join(domain_parts)
    except:
        pass
    return None


def monitor_traffic_thread():
    """Background thread to monitor network traffic using tcpdump with full packet capture"""
    global MONITOR_RUNNING, REQUEST_LOG
    import subprocess
    import threading

    MONITOR_RUNNING = True

    # Get hotspot interface
    hotspot_iface = None
    for iface in ['wlan0', 'swlan0', 'ap0', 'softap0']:
        try:
            result = subprocess.run(f"ip addr show {iface} 2>/dev/null | grep 'inet '",
                                  shell=True, capture_output=True, text=True, timeout=2)
            if result.stdout and '192.168' in result.stdout:
                hotspot_iface = iface
                break
        except:
            continue

    if not hotspot_iface:
        print("No hotspot interface found for monitoring")
        MONITOR_RUNNING = False
        return

    print(f"Starting traffic monitor on interface: {hotspot_iface}")

    # Start tcpdump with full packet capture (-A for ASCII, -s0 for full packets)
    # Capture DNS (port 53), HTTP (port 80), HTTPS (port 443)
    tcpdump_cmd = f"tcpdump -i {hotspot_iface} -l -n -A -s 0 'src net 192.168.0.0/16 and (port 53 or port 80 or port 443)' 2>/dev/null"

    try:
        process = subprocess.Popen(
            tcpdump_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        current_packet = []

        while MONITOR_RUNNING:
            try:
                line = process.stdout.readline()
                if not line:
                    break

                if not MONITOR_CONFIG.get('enabled', False):
                    time.sleep(1)
                    continue

                # Accumulate packet data
                if line.strip() and not line.startswith(' '):
                    # New packet starts
                    if current_packet:
                        parse_full_packet(current_packet)
                    current_packet = [line]
                else:
                    # Continuation of current packet
                    current_packet.append(line)

            except Exception as e:
                if MONITOR_RUNNING:
                    print(f"Monitor error: {e}")
                break

        # Process last packet
        if current_packet:
            parse_full_packet(current_packet)

        process.terminate()
        process.wait()

    except Exception as e:
        print(f"Failed to start traffic monitoring: {e}")

    MONITOR_RUNNING = False
    print("Traffic monitor stopped")


def parse_full_packet(packet_lines):
    """Parse full packet capture with HTTP headers"""
    try:
        if not packet_lines:
            return

        # First line contains: timestamp, IPs, ports
        header_line = packet_lines[0]
        parts = header_line.split()

        if len(parts) < 5:
            return

        # Extract IPs and ports
        src_full = parts[2]
        dst_full = parts[4].rstrip(':')

        src_parts = src_full.rsplit('.', 1)
        dst_parts = dst_full.rsplit('.', 1)

        if len(src_parts) != 2 or len(dst_parts) != 2:
            return

        src_ip = src_parts[0]
        dst_ip = dst_parts[0]
        dst_port = dst_parts[1]
        src_port = src_parts[1]

        # Only log traffic from hotspot clients
        if not src_ip.startswith('192.168'):
            return

        # Combine packet data
        packet_data = ''.join(packet_lines[1:])

        # Determine protocol
        protocol = 'UDP' if 'UDP' in header_line else 'TCP'

        # Parse based on port
        if dst_port == '53':
            # DNS Query
            domain = extract_dns_query(packet_data)
            blocked = is_request_blocked(dst_ip, dst_port, domain or '')
            log_request(src_ip, dst_ip, protocol, dst_port,
                       domain=domain or 'DNS Query', request_type='dns',
                       blocked=blocked)

        elif dst_port == '80':
            # HTTP Request - extract full details
            http_details = extract_http_request(packet_data)
            if http_details:
                blocked = is_request_blocked(dst_ip, dst_port, http_details.get('host', ''))
                log_request(
                    src_ip, dst_ip, protocol, dst_port,
                    domain=http_details.get('host', 'N/A'),
                    url=http_details.get('url', 'N/A'),
                    method=http_details.get('method', 'N/A'),
                    request_type='http',
                    blocked=blocked
                )
                # Store full request details in a separate structure
                if REQUEST_LOG:
                    REQUEST_LOG[-1]['request_headers'] = http_details.get('headers', '')
                    REQUEST_LOG[-1]['request_body'] = http_details.get('body', '')
                    REQUEST_LOG[-1]['full_url'] = f"http://{http_details.get('host', dst_ip)}{http_details.get('url', '/')}"

        elif dst_port == '443':
            # HTTPS Request - extract SNI from TLS handshake
            sni = extract_sni_from_tls(packet_data)
            blocked = is_request_blocked(dst_ip, dst_port, sni or '')
            log_request(
                src_ip, dst_ip, protocol, dst_port,
                domain=sni or dst_ip,
                request_type='https',
                blocked=blocked
            )
            if REQUEST_LOG and sni:
                REQUEST_LOG[-1]['full_url'] = f"https://{sni}/"
                REQUEST_LOG[-1]['tls_sni'] = sni

    except Exception as e:
        # Silently handle parse errors
        pass


def extract_dns_query(packet_data):
    """Extract domain name from DNS query"""
    try:
        # Look for common domain patterns in the packet
        import re
        # Simple regex to find domain-like strings
        matches = re.findall(r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}', packet_data)
        if matches:
            return matches[0]
    except:
        pass
    return None


def extract_http_request(packet_data):
    """Extract HTTP request details (method, URL, headers, body)"""
    try:
        lines = packet_data.split('\n')

        # Find HTTP request line (GET, POST, etc.)
        http_method = None
        http_url = None
        http_version = None

        for line in lines:
            line = line.strip()
            if line.startswith(('GET ', 'POST ', 'PUT ', 'DELETE ', 'HEAD ', 'OPTIONS ', 'PATCH ')):
                parts = line.split()
                if len(parts) >= 3:
                    http_method = parts[0]
                    http_url = parts[1]
                    http_version = parts[2]
                    break

        if not http_method:
            return None

        # Extract headers
        headers = {}
        host = None
        in_headers = False
        header_text = []

        for line in lines:
            line = line.strip()
            if line.startswith(('GET ', 'POST ', 'PUT ', 'DELETE ', 'HEAD ')):
                in_headers = True
                header_text.append(line)
                continue

            if in_headers:
                if ':' in line and not line.startswith(' '):
                    key, value = line.split(':', 1)
                    headers[key.strip()] = value.strip()
                    header_text.append(line)

                    if key.strip().lower() == 'host':
                        host = value.strip()
                elif line == '':
                    break

        return {
            'method': http_method,
            'url': http_url,
            'version': http_version,
            'host': host,
            'headers': '\n'.join(header_text),
            'body': ''
        }

    except:
        pass
    return None


def extract_sni_from_tls(packet_data):
    """Extract Server Name Indication from TLS Client Hello"""
    try:
        # Look for SNI in TLS handshake
        # SNI is typically readable in the ClientHello message
        import re
        # Simple pattern matching for domain names in TLS data
        matches = re.findall(r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}', packet_data)
        for match in matches:
            # Filter out common false positives
            if not any(x in match.lower() for x in ['mozilla', 'firefox', 'chrome', 'safari', 'windows']):
                return match
    except:
        pass
    return None


def is_request_blocked(dst_ip, port, domain=''):
    """Check if a request should be blocked based on current rules"""
    try:
        with open(BLOCKLIST, 'r') as f:
            blocked_domains = [line.strip().lower() for line in f if line.strip()]

        for blocked_domain in blocked_domains:
            if domain and blocked_domain in domain.lower():
                return True
    except:
        pass
    return False

def fetch_device_name_from_web(mac):
    """Fetch device name from macvendors.com API with permanent caching"""
    # Check cache first (permanent - never expires)
    if mac in MAC_LOOKUP_CACHE:
        cached = MAC_LOOKUP_CACHE[mac]
        cached_name = cached.get('name')
        if cached_name and cached_name != 'Unknown':
            return cached_name

    try:
        # Use macvendors.com API - simple and reliable
        url = f"https://api.macvendors.com/{mac}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        }

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            device_name = response.read().decode('utf-8').strip()

            # Validate the response
            if device_name and len(device_name) > 0:
                # Check if it's an error message
                if device_name.startswith('<!') or device_name.startswith('{') or 'error' in device_name.lower():
                    return None

                # Clean up the vendor name
                device_name = device_name.replace(' Inc.', '').replace(' Co.', '').replace(' Ltd.', '')
                device_name = device_name.replace(' Corporation', '').replace(' Corp.', '')
                device_name = device_name.replace(' Limited', '').replace(', Ltd', '')
                device_name = device_name.strip()

                # Cache the result permanently
                MAC_LOOKUP_CACHE[mac] = {
                    'name': device_name,
                    'timestamp': time.time(),
                    'source': 'api'
                }
                save_mac_cache()
                return device_name
    except Exception as e:
        # Cache the failure to avoid repeated API calls
        MAC_LOOKUP_CACHE[mac] = {
            'name': None,
            'timestamp': time.time(),
            'source': 'failed'
        }
        save_mac_cache()

    return None

class HotspotHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

    def _send_json(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_html(self, file_path):
        """Send HTML file"""
        try:
            with open(file_path, 'rb') as f:
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                self.wfile.write(f.read())
        except Exception as e:
            self.send_error(404)

    def _send_file(self, file_path, content_type):
        """Send generic file with specified content type"""
        try:
            with open(file_path, 'rb') as f:
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                if content_type == 'application/javascript':
                    self.send_header('Service-Worker-Allowed', '/')
                self.end_headers()
                self.wfile.write(f.read())
        except Exception as e:
            self.send_error(404)

    def _run_command(self, cmd):
        """Run shell command and return output"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            return result.stdout, result.returncode
        except Exception as e:
            return str(e), 1

    def _get_vendor_from_mac(self, mac):
        """Get device vendor from MAC address"""
        mac = mac.lower().replace('-', ':')
        oui = ':'.join(mac.split(':')[:3])
        return MAC_VENDORS.get(oui, 'Unknown')

    def _get_device_hostname(self, ip):
        """Try to get hostname from IP"""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname if hostname != ip else None
        except:
            return None

    def _get_connection_info(self, ip):
        """Get connection statistics for device"""
        try:
            # Get connection count
            output, _ = self._run_command(f"netstat -an 2>/dev/null | grep {ip} | wc -l")
            conn_count = output.strip() or "0"

            # Get traffic stats if available
            output, _ = self._run_command(f"iptables -L -v -n 2>/dev/null | grep {ip}")

            return {"connections": conn_count}
        except:
            return {"connections": "0"}

    def _get_devices(self):
        """Get connected hotspot devices with enhanced information"""
        devices = []

        # Detect hotspot interface
        hotspot_iface = None
        for iface in ['wlan0', 'swlan0', 'ap0', 'softap0']:
            output, _ = self._run_command(f"ip addr show {iface} 2>/dev/null | grep 'inet '")
            if output and '192.168' in output:
                hotspot_iface = iface
                break

        if not hotspot_iface:
            return {"devices": [], "interface": "none"}

        # Get devices from ARP table
        output, _ = self._run_command(f"ip neigh show dev {hotspot_iface}")

        for line in output.strip().split('\n'):
            if not line:
                continue

            parts = line.split()
            if len(parts) >= 4:
                ip = parts[0]
                # Check if this is an IPv4 address (skip IPv6)
                if not ':' in ip or ip.count(':') < 2:
                    # Find 'lladdr' keyword in the line (position varies)
                    try:
                        lladdr_index = parts.index('lladdr')
                        if len(parts) > lladdr_index + 2:
                            mac = parts[lladdr_index + 1]
                            state = parts[lladdr_index + 2]
                        else:
                            continue
                    except (ValueError, IndexError):
                        continue

                    # Only show active connections
                    if state in ['REACHABLE', 'STALE', 'DELAY', 'PROBE']:
                        # Get vendor from MAC
                        vendor = self._get_vendor_from_mac(mac)

                        # Try to fetch accurate device name from web
                        web_device_name = fetch_device_name_from_web(mac)

                        # Try to get hostname from system
                        hostname = self._get_device_hostname(ip)

                        # Try DHCP leases
                        if not hostname and os.path.exists('/data/misc/dhcp/dnsmasq.leases'):
                            lease_output, _ = self._run_command(f"grep -i {mac} /data/misc/dhcp/dnsmasq.leases 2>/dev/null")
                            if lease_output:
                                parts = lease_output.split()
                                if len(parts) > 3:
                                    hostname = parts[3]

                        # Get connection info
                        conn_info = self._get_connection_info(ip)

                        # Build device name (priority: custom > web lookup > hostname > vendor)
                        # Check if we have custom info for this device (by MAC address)
                        custom_info = DEVICE_INFO.get(mac, {})
                        custom_name = custom_info.get('name')
                        custom_notes = custom_info.get('notes', '')

                        if custom_name:
                            device_name = custom_name
                        elif web_device_name:
                            device_name = web_device_name
                        elif hostname:
                            device_name = hostname
                        else:
                            device_name = f"{vendor} Device"

                        devices.append({
                            "ip": ip,
                            "mac": mac,
                            "hostname": device_name,
                            "vendor": vendor,
                            "state": state,
                            "connections": conn_info.get("connections", "0"),
                            "custom_name": custom_name or "",
                            "notes": custom_notes
                        })

        return {"devices": devices, "interface": hotspot_iface}

    def _get_blocked_urls(self):
        """Get list of blocked URLs with their IP addresses"""
        blocked_list = []
        try:
            # Load from JSON (includes IPs)
            with open(BLOCKLIST_JSON, 'r') as f:
                blocked_data = json.load(f)

            for url, data in blocked_data.items():
                blocked_list.append({
                    "url": url,
                    "ips": data.get("ips", []),
                    "ip_ranges": data.get("ip_ranges", data.get("ips", [])),
                    "is_ip_address": data.get("is_ip_address", False),
                    "blocked_at": data.get("blocked_at", ""),
                    "rules_count": data.get("rules_count", 0)
                })
        except:
            # Fallback to old text file
            try:
                with open(BLOCKLIST, 'r') as f:
                    urls = [line.strip() for line in f if line.strip()]
                    for url in urls:
                        blocked_list.append({"url": url, "ips": [], "is_ip_address": False, "blocked_at": "", "rules_count": 0})
            except:
                pass

        return {"blocked_urls": blocked_list}

    def _resolve_domain_to_ips(self, domain):
        """Resolve domain to IP addresses using Python socket"""
        ips = []
        try:
            import socket
            # Get all IPv4 addresses for the domain
            addr_info = socket.getaddrinfo(domain, 80, socket.AF_INET)
            # Extract unique IPs
            ip_set = set()
            for info in addr_info:
                ip = info[4][0]
                ip_set.add(ip)
            ips = list(ip_set)
        except:
            pass
        return ips

    def _is_valid_ip(self, address):
        """Check if address is a valid IP"""
        parts = address.split('.')
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except:
            return False

    def _block_url(self, url):
        """FAST URL blocking using IP-based rules + lightweight DNS fallback"""
        if not url:
            return {"success": False, "message": "No URL provided"}

        # Clean and normalize input
        original_url = url
        url = url.strip().lower()
        url = re.sub(r'^https?://', '', url)
        url = re.sub(r'/.*$', '', url)
        url = re.sub(r':.*$', '', url)
        url = re.sub(r'^www\.', '', url)

        # Load existing blocks
        try:
            with open(BLOCKLIST_JSON, 'r') as f:
                blocked_data = json.load(f)
        except:
            blocked_data = {}

        # Check if already blocked
        if url in blocked_data:
            return {"success": False, "message": f"{url} is already blocked"}

        is_ip = self._is_valid_ip(url)
        blocked_ips = []
        rules_added = 0

        if is_ip:
            # Direct IP blocking (super fast)
            blocked_ips = [url]
        else:
            # Domain: resolve to IPs first
            resolved_ips = self._resolve_domain_to_ips(url)
            if resolved_ips:
                blocked_ips = resolved_ips
            else:
                # Couldn't resolve, will rely on DNS blocking only
                blocked_ips = []

        # FAST LAYER: Block by IP (90% of traffic blocked here, super fast)
        for ip in blocked_ips:
            # Remove old rule if exists (try both REJECT and DROP for cleanup)
            self._run_command(f'su -c "iptables -D FORWARD -d {ip} -j REJECT --reject-with icmp-host-unreachable" 2>/dev/null')
            self._run_command(f'su -c "iptables -D FORWARD -d {ip} -j DROP" 2>/dev/null')
            # Add IP block rule (VERY FAST - no deep packet inspection)
            result, code = self._run_command(f'su -c "iptables -I FORWARD 1 -d {ip} -j DROP" 2>&1')
            if code == 0:
                rules_added += 1

        # NO DNS STRING MATCHING - it slows down internet!
        # IP-only blocking for maximum speed

        # Save to JSON with IP mapping
        import datetime
        blocked_data[url] = {
            "ips": blocked_ips,
            "is_ip_address": is_ip,
            "blocked_at": datetime.datetime.now().isoformat(),
            "rules_count": rules_added
        }

        with open(BLOCKLIST_JSON, 'w') as f:
            json.dump(blocked_data, f, indent=2)

        # Also save to old blocklist file for compatibility
        try:
            with open(BLOCKLIST, 'r') as f:
                existing = [line.strip() for line in f]
        except:
            existing = []
        if url not in existing:
            with open(BLOCKLIST, 'a') as f:
                f.write(url + '\n')

        # Save iptables rules for persistence
        self._run_command('su -c "iptables-save > /data/data/com.termux/files/home/iptables-rules.txt"')

        ip_msg = f" ({len(blocked_ips)} IPs)" if blocked_ips else ""
        return {"success": True, "message": f"✓ Blocked {url}{ip_msg} - {rules_added} fast rules added"}

    def _block_url_advanced(self, url, ip_ranges):
        """Advanced blocking with custom IP ranges - NO DNS string matching for speed!"""
        if not url:
            return {"success": False, "message": "No URL provided"}

        url = url.strip().lower()

        try:
            with open(BLOCKLIST_JSON, 'r') as f:
                blocked_data = json.load(f)
        except:
            blocked_data = {}

        if url in blocked_data:
            return {"success": False, "message": f"{url} is already blocked. Use Edit to modify."}

        rules_added = 0

        # If no IP ranges provided, auto-resolve
        if not ip_ranges:
            resolved_ips = self._resolve_domain_to_ips(url)
            ip_ranges = resolved_ips if resolved_ips else []

        # Block each IP/range (CIDR supported: 157.240.0.0/16)
        for ip_range in ip_ranges:
            self._run_command(f'su -c "iptables -D FORWARD -d {ip_range} -j DROP" 2>/dev/null')
            result, code = self._run_command(f'su -c "iptables -I FORWARD 1 -d {ip_range} -j DROP" 2>&1')
            if code == 0:
                rules_added += 1

        import datetime
        blocked_data[url] = {
            "ip_ranges": ip_ranges,
            "ips": ip_ranges,
            "is_ip_address": self._is_valid_ip(url),
            "blocked_at": datetime.datetime.now().isoformat(),
            "rules_count": rules_added
        }

        with open(BLOCKLIST_JSON, 'w') as f:
            json.dump(blocked_data, f, indent=2)

        return {"success": True, "message": f"✓ Blocked {url} with {len(ip_ranges)} IP range(s)"}

    def _update_blocked_url(self, url, ip_ranges):
        """Update IP ranges for blocked URL"""
        if not url:
            return {"success": False, "message": "No URL provided"}

        url = url.strip().lower()

        try:
            with open(BLOCKLIST_JSON, 'r') as f:
                blocked_data = json.load(f)
        except:
            return {"success": False, "message": "Error loading blocked URLs"}

        if url not in blocked_data:
            return {"success": False, "message": f"{url} is not blocked"}

        # Remove old rules
        old_ranges = blocked_data[url].get("ip_ranges", blocked_data[url].get("ips", []))
        for ip_range in old_ranges:
            for i in range(10):
                result, code = self._run_command(f'su -c "iptables -D FORWARD -d {ip_range} -j DROP" 2>&1')
                if code != 0:
                    break

        # Add new rules
        rules_added = 0
        for ip_range in ip_ranges:
            result, code = self._run_command(f'su -c "iptables -I FORWARD 1 -d {ip_range} -j DROP" 2>&1')
            if code == 0:
                rules_added += 1

        import datetime
        blocked_data[url]["ip_ranges"] = ip_ranges
        blocked_data[url]["ips"] = ip_ranges
        blocked_data[url]["rules_count"] = rules_added
        blocked_data[url]["updated_at"] = datetime.datetime.now().isoformat()

        with open(BLOCKLIST_JSON, 'w') as f:
            json.dump(blocked_data, f, indent=2)

        return {"success": True, "message": f"✓ Updated {url} with {len(ip_ranges)} IP range(s)"}

    def _get_domain_variations(self, url):
        """Get known domain variations for popular sites"""
        variations = []

        # YouTube variations
        if 'youtube' in url:
            variations.extend(['youtu.be', 'youtubei.googleapis.com', 'ytimg.com', 'yt3.ggpht.com'])

        # Facebook variations
        elif 'facebook' in url:
            variations.extend(['fb.com', 'fbcdn.net', 'facebook.net', 'fb.me'])

        # Instagram variations
        elif 'instagram' in url:
            variations.extend(['cdninstagram.com', 'ig.me'])

        # Twitter/X variations
        elif 'twitter' in url or url == 'x.com':
            variations.extend(['twitter.com', 'x.com', 't.co', 'twimg.com'])

        # TikTok variations
        elif 'tiktok' in url:
            variations.extend(['tiktokcdn.com', 'tiktokv.com', 'musical.ly'])

        # WhatsApp variations
        elif 'whatsapp' in url:
            variations.extend(['wa.me'])

        # Netflix variations
        elif 'netflix' in url:
            variations.extend(['nflxext.com', 'nflximg.net', 'nflxvideo.net'])

        return variations

    def _unblock_url(self, url):
        """FAST URL unblocking - removes IP and DNS rules"""
        if not url:
            return {"success": False, "message": "No URL provided"}

        # Clean and normalize URL
        url = url.strip().lower()
        url = re.sub(r'^https?://', '', url)
        url = re.sub(r'/.*$', '', url)
        url = re.sub(r':.*$', '', url)
        url = re.sub(r'^www\.', '', url)

        # Load blocked data to get IPs
        try:
            with open(BLOCKLIST_JSON, 'r') as f:
                blocked_data = json.load(f)
        except:
            blocked_data = {}

        if url not in blocked_data:
            return {"success": False, "message": f"{url} is not in blocklist"}

        blocked_ips = blocked_data[url].get("ips", [])
        rules_removed = 0

        # Remove IP-based blocks (fast rules) - try both REJECT and DROP
        for ip in blocked_ips:
            for i in range(5):  # Try REJECT rules (old format)
                result, code = self._run_command(f'su -c "iptables -D FORWARD -d {ip} -j REJECT --reject-with icmp-host-unreachable" 2>&1')
                if code == 0:
                    rules_removed += 1
                else:
                    break
            for i in range(5):  # Try DROP rules (new format)
                result, code = self._run_command(f'su -c "iptables -D FORWARD -d {ip} -j DROP" 2>&1')
                if code == 0:
                    rules_removed += 1
                else:
                    break

        # DNS string blocking disabled for performance (IP-only blocking)

        # Remove from JSON
        del blocked_data[url]
        with open(BLOCKLIST_JSON, 'w') as f:
            json.dump(blocked_data, f, indent=2)

        # Remove from old blocklist file
        try:
            with open(BLOCKLIST, 'r') as f:
                lines = [line.strip() for line in f if line.strip()]
            with open(BLOCKLIST, 'w') as f:
                for line in lines:
                    if line != url:
                        f.write(line + '\n')
        except:
            pass

        # Save iptables rules for persistence
        self._run_command('su -c "iptables-save > /data/data/com.termux/files/home/iptables-rules.txt"')

        return {"success": True, "message": f"✓ Unblocked {url} ({rules_removed} rules removed)"}

    def _get_wifi_settings(self):
        """Get current WiFi hotspot settings"""
        try:
            # Read config with root access
            config_path = '/data/vendor/wifi/hostapd/hostapd_wlan0.conf'
            config, code = self._run_command(f'su -c "cat {config_path}"')

            if code != 0 or not config:
                return {"success": False, "message": "Could not read hostapd config"}

            # Parse current settings
            channel = 0
            tx_power = None  # No default - detect if not set

            for line in config.split('\n'):
                line = line.strip()
                if line.startswith('channel='):
                    try:
                        channel = int(line.split('=')[1])
                    except:
                        pass
                elif line.startswith('tx_power='):
                    try:
                        tx_power = int(line.split('=')[1])
                    except:
                        pass

            # If tx_power not found in config, add it with default value
            if tx_power is None:
                tx_power = 20
                self._run_command(f'su -c "echo \'tx_power={tx_power}\' >> {config_path}"')

            return {
                "success": True,
                "channel": channel,
                "tx_power": tx_power,
                "available_channels": list(range(1, 12)),  # 2.4GHz channels 1-11
                "available_powers": list(range(10, 31))  # 10-30 dBm
            }
        except Exception as e:
            return {"success": False, "message": f"Error reading WiFi settings: {str(e)}"}

    def _set_wifi_channel(self, channel):
        """Change WiFi hotspot channel (permanent, survives reboot)"""
        if not (1 <= channel <= 11):
            return {"success": False, "message": "Channel must be between 1 and 11"}

        try:
            # Read current config
            config_path = '/data/vendor/wifi/hostapd/hostapd_wlan0.conf'
            result, code = self._run_command(f'su -c "cat {config_path}"')
            if code != 0 or not result:
                return {"success": False, "message": "Could not read hostapd config"}

            # Replace channel value using sed
            sed_result, sed_code = self._run_command(f'su -c "sed -i \'s/^channel=.*/channel={channel}/\' {config_path}"')

            # Update op_class based on channel (2.4GHz band)
            if channel <= 11:
                op_class = 81 + ((channel - 1) // 4)  # 81-83 for channels 1-11
                self._run_command(f'su -c "sed -i \'s/^op_class=.*/op_class={op_class}/\' {config_path}"')

            # Verify the channel was set correctly
            verify, _ = self._run_command(f'su -c "grep \'^channel=\' {config_path}"')
            actual_channel = None
            if verify:
                try:
                    actual_channel = int(verify.split('=')[1].strip())
                except:
                    pass

            if actual_channel == channel:
                # Save user preference to JSON file for watchdog
                try:
                    import datetime
                    wifi_settings_file = '/data/data/com.termux/files/home/wifi-settings.json'
                    settings = {}
                    if os.path.exists(wifi_settings_file):
                        with open(wifi_settings_file, 'r') as f:
                            settings = json.load(f)
                    settings['channel'] = channel
                    settings['last_updated'] = datetime.datetime.now().isoformat()
                    with open(wifi_settings_file, 'w') as f:
                        json.dump(settings, f, indent=2)
                except:
                    pass

                return {
                    "success": True,
                    "message": f"✓ Channel set to {channel}. Restart WiFi hotspot to apply (turn off/on in settings)."
                }
            else:
                return {
                    "success": False,
                    "message": f"Channel setting failed. Expected {channel}, got {actual_channel}. Config may be read-only."
                }
        except Exception as e:
            return {"success": False, "message": f"Error setting channel: {str(e)}"}

    def _set_tx_power(self, power):
        """Set TX power in hostapd config"""
        if not (10 <= power <= 30):
            return {"success": False, "message": "Power must be between 10 and 30 dBm"}

        try:
            config_path = '/data/vendor/wifi/hostapd/hostapd_wlan0.conf'
            result, code = self._run_command(f'su -c "cat {config_path}"')

            if code != 0 or not result:
                return {"success": False, "message": "Could not read hostapd config"}

            # Check if tx_power line exists
            if 'tx_power=' in result:
                # Update existing tx_power line using sed
                self._run_command(f'su -c "sed -i \'s/^tx_power=.*/tx_power={power}/\' {config_path}"')
            else:
                # Add tx_power parameter after wpa_passphrase line (or at end)
                self._run_command(f'su -c "sed -i \'/^wpa_passphrase=/a tx_power={power}\' {config_path}"')

            # Verify it was set
            verify, _ = self._run_command(f'su -c "grep \'^tx_power=\' {config_path}"')
            actual_power = None
            if verify:
                try:
                    actual_power = int(verify.split('=')[1].strip())
                except:
                    pass

            if actual_power == power:
                # Save user preference to JSON file for watchdog
                try:
                    import datetime
                    wifi_settings_file = '/data/data/com.termux/files/home/wifi-settings.json'
                    settings = {}
                    if os.path.exists(wifi_settings_file):
                        with open(wifi_settings_file, 'r') as f:
                            settings = json.load(f)
                    settings['tx_power'] = power
                    settings['last_updated'] = datetime.datetime.now().isoformat()
                    with open(wifi_settings_file, 'w') as f:
                        json.dump(settings, f, indent=2)
                except:
                    pass

                return {
                    "success": True,
                    "message": f"✓ TX power set to {power} dBm. Restart WiFi hotspot to apply."
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to verify TX power setting. Check config manually."
                }
        except Exception as e:
            return {"success": False, "message": f"Error setting TX power: {str(e)}"}

    def _block_device(self, mac, ip):
        """Block a device"""
        self._run_command(f"iptables -D FORWARD -m mac --mac-source {mac} -j DROP 2>/dev/null")
        self._run_command(f"iptables -I FORWARD -m mac --mac-source {mac} -j DROP")
        self._run_command(f"iptables -D FORWARD -s {ip} -j DROP 2>/dev/null")
        self._run_command(f"iptables -I FORWARD -s {ip} -j DROP")
        return {"success": True, "message": "Blocked device"}

    def _save_device_info(self, mac, name, notes):
        """Save custom device information"""
        if not mac:
            return {"success": False, "message": "MAC address required"}

        # Update device info
        DEVICE_INFO[mac] = {
            "name": name.strip() if name else "",
            "notes": notes.strip() if notes else "",
            "updated": time.time()
        }

        # Save to file
        save_device_info()

        return {"success": True, "message": f"Saved info for {mac}"}

    def _setup_monitoring(self):
        """Set up traffic monitoring using background thread"""
        global MONITOR_THREAD, MONITOR_RUNNING
        import threading

        # Start monitoring thread if not already running
        if not MONITOR_RUNNING:
            MONITOR_THREAD = threading.Thread(target=monitor_traffic_thread, daemon=True)
            MONITOR_THREAD.start()
            print("Started traffic monitoring thread")

    def _teardown_monitoring(self):
        """Stop traffic monitoring"""
        global MONITOR_RUNNING
        MONITOR_RUNNING = False
        print("Stopped traffic monitoring")

    def _get_active_connections(self):
        """Get active connections from conntrack or netstat"""
        connections = []
        try:
            # Try to get connection tracking info
            output, code = self._run_command("cat /proc/net/ip_conntrack 2>/dev/null || cat /proc/net/nf_conntrack 2>/dev/null | head -100")

            if code == 0 and output:
                for line in output.strip().split('\n')[:50]:  # Limit to 50 most recent
                    parts = line.split()
                    if len(parts) > 4:
                        try:
                            # Parse conntrack entry
                            protocol = parts[0] if len(parts) > 0 else 'unknown'
                            src_ip = dst_ip = port = 'N/A'

                            # Extract src and dst from the line
                            for part in parts:
                                if part.startswith('src='):
                                    src_ip = part.split('=')[1]
                                elif part.startswith('dst=') and dst_ip == 'N/A':
                                    dst_ip = part.split('=')[1]
                                elif part.startswith('dport='):
                                    port = part.split('=')[1]

                            # Only log connections from hotspot clients (192.168.x.x)
                            if src_ip.startswith('192.168'):
                                log_request(src_ip, dst_ip, protocol, port)
                        except:
                            pass
        except:
            pass

        return {"success": True}

    def _boost_internet(self):
        """Internet Booster/Fixer - runs comprehensive optimization script"""
        try:
            # Run the ultimate booster script
            output, code = self._run_command("/data/data/com.termux/files/home/ultimate-internet-booster.sh 2>&1")

            if code != 0:
                return {"success": False, "message": "Booster script failed", "issues": [], "fixes": []}

            # Parse the result
            issues_count = 0
            fixes_count = 0
            issues_list = []
            fixes_list = []

            # Extract RESULT line
            for line in output.split('\n'):
                if line.startswith('RESULT:'):
                    parts = line.split(':')
                    if len(parts) >= 3:
                        issues_count = int(parts[1])
                        fixes_count = int(parts[2])

            # Parse log for details
            log_lines = output.split('\n')
            for line in log_lines:
                if 'Found ' in line or 'Missing ' in line or 'is disabled' in line or 'is NOT at top' in line:
                    issues_list.append(line.split('] ')[-1] if '] ' in line else line)
                elif line.strip().startswith('✓'):
                    fixes_list.append(line.split('] ')[-1].replace('✓ ', '') if '] ' in line else line.replace('✓ ', ''))

            if issues_count == 0:
                return {
                    "success": True,
                    "message": "✓ No issues found - internet is fully optimized!",
                    "issues": [],
                    "fixes": []
                }
            else:
                return {
                    "success": True,
                    "message": f"✓ Applied {fixes_count} optimizations and fixed {issues_count} issues!",
                    "issues": issues_list[:10],  # Limit to 10 for display
                    "fixes": fixes_list[:15]     # Limit to 15 for display
                }

        except Exception as e:
            return {"success": False, "message": f"Error during boost: {str(e)}", "issues": [], "fixes": []}

    def do_GET(self):
        """Handle GET requests"""
        path = urlparse(self.path).path

        if path == '/':
            self._send_html(os.path.join(WEBROOT, 'index.html'))
        elif path == '/blocked':
            self._send_html(os.path.join(WEBROOT, 'blocked.html'))
        elif path == '/api/devices':
            self._send_json(self._get_devices())
        elif path == '/api/data-usage':
            devices = self._get_devices()['devices']
            import datetime
            current_month = datetime.datetime.now().strftime('%B %Y')

            # Load saved usage data
            usage_file = '/data/data/com.termux/files/home/device_usage.json'
            try:
                with open(usage_file, 'r') as f:
                    raw_usage = json.load(f)
                # Normalize all MACs to uppercase and merge duplicates
                saved_usage = {}
                for mac, months in raw_usage.items():
                    mac_upper = mac.upper()
                    if mac_upper not in saved_usage:
                        saved_usage[mac_upper] = {}
                    for month, bytes_val in months.items():
                        if month not in saved_usage[mac_upper]:
                            saved_usage[mac_upper][month] = bytes_val
                        else:
                            saved_usage[mac_upper][month] = max(saved_usage[mac_upper][month], bytes_val)
            except:
                saved_usage = {}

            # DEVICE_INFO is already loaded globally, contains custom names

            # Format bytes function
            def format_bytes(b):
                if b < 1024:
                    return f"{b} B"
                elif b < 1024**2:
                    return f"{b/1024:.1f} KB"
                elif b < 1024**3:
                    return f"{b/(1024**2):.1f} MB"
                else:
                    return f"{b/(1024**3):.2f} GB"

            usage_data = []
            processed_macs = set()

            # Process currently connected devices
            for device in devices:
                mac = device['mac'].upper()  # Normalize to uppercase
                ip = device['ip']
                processed_macs.add(mac)

                # Ensure counting rules exist for this MAC (both directions)
                # FIXED: Incoming traffic doesn't have client MAC as source!
                # Outgoing: Match source IP + source MAC (client sending data)
                _, code_out = self._run_command(f"su -c 'iptables -C FORWARD -s {ip} -m mac --mac-source {mac} 2>/dev/null'")
                if code_out != 0:
                    self._run_command(f"su -c 'iptables -I FORWARD -s {ip} -m mac --mac-source {mac}'")

                # Incoming: Match destination IP only (return traffic has router's source MAC, not client's!)
                _, code_in = self._run_command(f"su -c 'iptables -C FORWARD -d {ip} 2>/dev/null'")
                if code_in != 0:
                    self._run_command(f"su -c 'iptables -I FORWARD -d {ip}'")

                # Get byte counters for this device
                result_in, _ = self._run_command(f"su -c 'iptables -L FORWARD -v -n -x 2>/dev/null | grep -w {ip} | grep -v \"0     0\"'")

                bytes_in = 0
                bytes_out = 0
                bytes_total = 0

                if result_in:
                    for line in result_in.strip().split('\n'):
                        parts = line.split()
                        # iptables format: pkts bytes target prot opt in out source destination [MAC MAC_ADDR]
                        if len(parts) >= 8:
                            try:
                                bytes_val = int(parts[1])
                                source_ip = parts[6]  # Column 7: source IP
                                dest_ip = parts[7]     # Column 8: destination IP

                                # Incoming: destination is this device
                                if dest_ip == ip or dest_ip.startswith(ip + '/'):
                                    bytes_in += bytes_val
                                # Outgoing: source is this device
                                elif source_ip == ip or source_ip.startswith(ip + '/'):
                                    bytes_out += bytes_val
                            except (ValueError, IndexError):
                                pass

                bytes_total = bytes_in + bytes_out

                # Initialize MAC in saved usage
                if mac not in saved_usage:
                    saved_usage[mac] = {}
                if current_month not in saved_usage[mac]:
                    saved_usage[mac][current_month] = 0

                # Update with maximum value seen (counters only increase)
                if bytes_total > saved_usage[mac][current_month]:
                    saved_usage[mac][current_month] = bytes_total
                else:
                    bytes_total = saved_usage[mac][current_month]

                usage_data.append({
                    'ip': ip,
                    'mac': mac,
                    'hostname': device.get('hostname', 'Unknown'),
                    'custom_name': device.get('custom_name', ''),
                    'usage': format_bytes(bytes_total),
                    'bytes': bytes_total,
                    'status': 'connected'
                })

            # Add offline devices from saved usage
            for mac, months in saved_usage.items():
                mac_upper = mac.upper()  # Normalize for comparison
                if mac_upper not in processed_macs and current_month in months:
                    bytes_total = months[current_month]

                    # Get custom name from DEVICE_INFO (try multiple cases)
                    mac_lower = mac_upper.lower()
                    device_info = DEVICE_INFO.get(mac_lower) or DEVICE_INFO.get(mac_upper) or DEVICE_INFO.get(mac) or {}
                    custom_name = device_info.get('name', '')

                    usage_data.append({
                        'ip': 'N/A',
                        'mac': mac_upper,
                        'hostname': custom_name if custom_name else 'Offline Device',
                        'custom_name': custom_name,
                        'usage': format_bytes(bytes_total),
                        'bytes': bytes_total,
                        'status': 'offline'
                    })

            # Save updated usage
            try:
                with open(usage_file, 'w') as f:
                    json.dump(saved_usage, f, indent=2)
            except:
                pass

            self._send_json({'month': current_month, 'devices': usage_data})
        elif path == '/api/blocked-urls':
            self._send_json(self._get_blocked_urls())
        elif path.startswith('/api/get-blocked-url'):
            from urllib.parse import parse_qs
            query = urlparse(self.path).query
            params = parse_qs(query)
            url = params.get('url', [''])[0]
            try:
                with open(BLOCKLIST_JSON, 'r') as f:
                    blocked_data = json.load(f)
                if url in blocked_data:
                    info = blocked_data[url]
                    self._send_json({
                        "success": True,
                        "url": url,
                        "ip_ranges": info.get("ip_ranges", info.get("ips", [])),
                        "blocked_at": info.get("blocked_at", "")
                    })
                else:
                    self._send_json({"success": False, "message": "URL not found"})
            except:
                self._send_json({"success": False, "message": "Error loading blocked URLs"})
        elif path == '/api/wifi-settings':
            self._send_json(self._get_wifi_settings())
        elif path == '/api/monitor-status':
            self._send_json({"enabled": MONITOR_CONFIG.get('enabled', False)})
        elif path.startswith('/api/monitor-logs'):
            # Parse query parameters for filtering and sorting
            query_params = parse_qs(urlparse(self.path).query)

            # Get filter parameters
            filter_ip = query_params.get('ip', [''])[0]
            filter_protocol = query_params.get('protocol', [''])[0]
            filter_type = query_params.get('type', [''])[0]
            filter_url = query_params.get('url', [''])[0].lower()
            search_query = query_params.get('search', [''])[0].lower()
            sort_by = query_params.get('sort', ['timestamp'])[0]
            sort_order = query_params.get('order', ['desc'])[0]
            blocked_only = query_params.get('blocked', ['false'])[0].lower() == 'true'

            # Pagination parameters
            page = int(query_params.get('page', ['1'])[0])
            per_page = int(query_params.get('per_page', ['50'])[0])

            # Filter logs
            filtered_logs = list(REQUEST_LOG)

            if filter_ip:
                filtered_logs = [log for log in filtered_logs
                               if log['src_ip'] == filter_ip or log['dst_ip'] == filter_ip]

            if filter_protocol:
                filtered_logs = [log for log in filtered_logs
                               if log['protocol'].lower() == filter_protocol.lower()]

            if filter_type:
                filtered_logs = [log for log in filtered_logs
                               if log['request_type'] == filter_type]

            if blocked_only:
                filtered_logs = [log for log in filtered_logs if log.get('blocked', False)]

            if filter_url:
                filtered_logs = [log for log in filtered_logs
                               if filter_url in str(log.get('domain', '')).lower()
                               or filter_url in str(log.get('url', '')).lower()
                               or filter_url in str(log.get('full_url', '')).lower()]

            if search_query:
                filtered_logs = [log for log in filtered_logs
                               if search_query in log['src_ip'].lower()
                               or search_query in log['dst_ip'].lower()
                               or search_query in str(log.get('domain', '')).lower()
                               or search_query in str(log.get('url', '')).lower()
                               or search_query in str(log.get('full_url', '')).lower()]

            # Sort logs
            reverse = (sort_order == 'desc')
            if sort_by in ['timestamp', 'src_ip', 'dst_ip', 'protocol', 'port']:
                filtered_logs.sort(key=lambda x: x.get(sort_by, ''), reverse=reverse)

            # Sort first, then reverse for newest first display
            if reverse:
                filtered_logs = list(reversed(filtered_logs))

            # Pagination
            total_filtered = len(filtered_logs)
            total_pages = (total_filtered + per_page - 1) // per_page if total_filtered > 0 else 1
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page

            paginated_logs = filtered_logs[start_idx:end_idx]

            # Get unique values for filter dropdowns
            unique_ips = sorted(set([log['src_ip'] for log in REQUEST_LOG]))
            unique_protocols = sorted(set([log['protocol'] for log in REQUEST_LOG]))
            unique_types = sorted(set([log['request_type'] for log in REQUEST_LOG]))

            self._send_json({
                "logs": paginated_logs,
                "total": len(REQUEST_LOG),
                "filtered": total_filtered,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "filters": {
                    "ips": unique_ips,
                    "protocols": unique_protocols,
                    "types": unique_types
                }
            })
        elif path.startswith('/api/request-details/'):
            # Get request details by ID
            request_id = path.split('/')[-1]
            try:
                req_id = int(request_id)
                for log in REQUEST_LOG:
                    if log.get('id') == req_id:
                        self._send_json({"success": True, "request": log})
                        return
                self._send_json({"success": False, "error": "Request not found"})
            except:
                self._send_json({"success": False, "error": "Invalid request ID"})
        elif path == '/manifest.json':
            self._send_file(os.path.join(WEBROOT, 'manifest.json'), 'application/manifest+json')
        elif path == '/sw.js':
            self._send_file(os.path.join(WEBROOT, 'sw.js'), 'application/javascript')
        elif path.startswith('/icon-'):
            # Serve icon files
            self._send_file(os.path.join(WEBROOT, path.lstrip('/')), 'image/png')
        else:
            self.send_error(404)

    def do_POST(self):
        """Handle POST requests"""
        path = urlparse(self.path).path

        # Read POST data
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'

        try:
            data = json.loads(post_data)
        except:
            data = {}

        if path == '/api/block-url':
            result = self._block_url(data.get('url', ''))
            self._send_json(result)
        elif path == '/api/block-url-advanced':
            result = self._block_url_advanced(data.get('url', ''), data.get('ip_ranges', []))
            self._send_json(result)
        elif path == '/api/update-blocked-url':
            result = self._update_blocked_url(data.get('url', ''), data.get('ip_ranges', []))
            self._send_json(result)
        elif path == '/api/unblock-url':
            result = self._unblock_url(data.get('url', ''))
            self._send_json(result)
        elif path == '/api/block-device':
            result = self._block_device(data.get('mac', ''), data.get('ip', ''))
            self._send_json(result)
        elif path == '/api/save-device-info':
            result = self._save_device_info(data.get('mac', ''), data.get('name', ''), data.get('notes', ''))
            self._send_json(result)
        elif path == '/api/reset-usage-all':
            # Reset iptables counters for all devices
            self._run_command('su -c "iptables -Z FORWARD"')
            # Clear usage file
            usage_file = '/data/data/com.termux/files/home/device_usage.json'
            try:
                with open(usage_file, 'w') as f:
                    json.dump({}, f)
            except:
                pass
            self._send_json({'success': True, 'message': 'All usage data reset'})
        elif path.startswith('/api/reset-usage/'):
            # Reset usage for specific MAC address
            mac = path.split('/')[-1].upper()  # Normalize to uppercase
            # Reset iptables counters for this MAC
            self._run_command(f'su -c "iptables -Z FORWARD"')  # Reset all (can't reset per-MAC)
            # Remove from usage file
            usage_file = '/data/data/com.termux/files/home/device_usage.json'
            try:
                with open(usage_file, 'r') as f:
                    saved_usage = json.load(f)
                # Remove all case variations
                keys_to_remove = [k for k in saved_usage.keys() if k.upper() == mac]
                for key in keys_to_remove:
                    del saved_usage[key]
                with open(usage_file, 'w') as f:
                    json.dump(saved_usage, f, indent=2)
            except:
                pass
            self._send_json({'success': True, 'message': 'Device usage reset'})
        elif path == '/api/set-channel':
            channel = data.get('channel', 0)
            result = self._set_wifi_channel(channel)
            self._send_json(result)
        elif path == '/api/set-txpower':
            power = data.get('power', 0)
            result = self._set_tx_power(power)
            self._send_json(result)
        elif path == '/api/monitor-toggle':
            global MONITOR_CONFIG, REQUEST_LOG
            enabled = data.get('enabled', False)
            MONITOR_CONFIG['enabled'] = enabled
            save_monitor_config()

            if enabled:
                # Clear existing logs when enabling
                REQUEST_LOG = []
                # Set up iptables logging (log all forwarded traffic)
                self._setup_monitoring()
                message = "Live monitoring enabled"
            else:
                # Remove iptables logging
                self._teardown_monitoring()
                message = "Live monitoring disabled"

            self._send_json({"success": True, "message": message, "enabled": enabled})
        elif path == '/api/monitor-clear':
            # Clear logs
            REQUEST_LOG[:] = []  # Clear the list in-place
            self._send_json({"success": True, "message": "Logs cleared"})
        elif path == '/api/boost-internet':
            # Internet Booster/Fixer - detect and fix common issues
            result = self._boost_internet()
            self._send_json(result)
        elif path == '/api/restart-server':
            self._send_json({"success": True, "message": "Server restarting..."})
            # Forceful restart - kill current process and start new one
            import sys
            import threading
            def restart():
                time.sleep(0.5)
                # Write restart script and execute it
                restart_cmd = f'''#!/bin/bash
pkill -9 python3
sleep 1
cd {WEBROOT}
nohup python3 server.py > /dev/null 2>&1 &
'''
                restart_file = '/data/data/com.termux/files/home/restart_hotspot.sh'
                with open(restart_file, 'w') as f:
                    f.write(restart_cmd)
                os.chmod(restart_file, 0o755)
                subprocess.Popen(['/bin/sh', restart_file])
                os._exit(0)
            threading.Thread(target=restart, daemon=True).start()
        else:
            self.send_error(404)

def reload_blocked_urls():
    """Reload all blocked URLs from blocklist file and apply iptables rules"""
    print("Reloading blocked URLs from blocklist...")
    try:
        # Load blocked URLs from JSON file
        if not os.path.exists(BLOCKLIST_JSON):
            print("No blocked URLs file found")
            return

        with open(BLOCKLIST_JSON, 'r') as f:
            blocked_urls = json.load(f)

        if not blocked_urls:
            print("No URLs currently blocked")
            return

        # Re-apply iptables rules for each blocked URL
        for url, info in blocked_urls.items():
            ips = info.get('ips', [])
            if not ips:
                print(f"  Skipping {url} - no IPs resolved")
                continue

            print(f"  Restoring blocks for {url} ({len(ips)} IPs)...")

            # Apply iptables rules for each IP
            for ip in ips:
                # Block both INPUT and FORWARD chains
                subprocess.run(f'su -c "iptables -D FORWARD -d {ip} -j DROP 2>/dev/null"', shell=True, capture_output=True)
                subprocess.run(f'su -c "iptables -I FORWARD -d {ip} -j DROP"', shell=True, capture_output=True)

                subprocess.run(f'su -c "iptables -D OUTPUT -d {ip} -j DROP 2>/dev/null"', shell=True, capture_output=True)
                subprocess.run(f'su -c "iptables -I OUTPUT -d {ip} -j DROP"', shell=True, capture_output=True)

            # DNS string blocking disabled for performance

            print(f"    ✓ Restored {len(ips)} IP blocks for {url}")

        print(f"✓ Reloaded {len(blocked_urls)} blocked URLs with {sum(len(info.get('ips', [])) for info in blocked_urls.values())} total IP blocks")
    except Exception as e:
        print(f"Error reloading blocked URLs: {e}")

def run_server():
    # Reload blocked URLs on startup
    reload_blocked_urls()

    server = HTTPServer(('0.0.0.0', PORT), HotspotHandler)
    print(f"Hotspot GUI Server running on port {PORT}")
    print(f"Access at: http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")

if __name__ == '__main__':
    run_server()

