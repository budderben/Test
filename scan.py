#!/usr/bin/env python3
"""
Advanced Network Scanner
Discovers devices on local network and identifies their roles
"""

from scapy.all import ARP, Ether, srp
import socket
import argparse
import json
import os
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
import time

# Expanded vendor database (OUI prefixes)
KNOWN_VENDORS = {
    # Apple
    "FCE998": "iPhone", "D8C4E9": "iPhone", "5C95AE": "iPhone",
    "A4C361": "iPhone", "BC926B": "iPhone", "7C04D0": "iPhone",
    "409C28": "iPhone", "F0B479": "iPhone", "C82A14": "iPhone",
    "3CD0F8": "iPad", "A85C2C": "iPad", "F4F15A": "iPad",
    "A4B197": "MacBook", "3C2EFF": "MacBook", "88E9FE": "MacBook",
    "AC87A3": "iMac", "78A3E4": "Mac Mini",
    
    # Android/Samsung
    "F4F5E8": "Android Phone", "A8BB50": "Android Phone",
    "2C8158": "Samsung Phone", "E4B021": "Samsung Phone",
    "C8F230": "Samsung Phone", "7C11BE": "Samsung Phone",
    "34E2FD": "Samsung Phone", "18D6C7": "Samsung Phone",
    
    # Raspberry Pi
    "B827EB": "Raspberry Pi", "DCA632": "Raspberry Pi",
    "E45F01": "Raspberry Pi", "DC3A14": "Raspberry Pi",
    
    # Network Equipment
    "00163E": "Cisco Device", "001C0E": "Cisco Device",
    "D4C1FC": "Huawei Router", "A0F3C1": "Huawei Router",
    "AC9E17": "TP-Link Router", "F4EC38": "TP-Link Router",
    "5065F3": "TP-Link Router", "C46E1F": "TP-Link Router",
    "0019E0": "Netgear Router", "A040A0": "Netgear Router",
    "E0469A": "Netgear Router", "B07FB9": "Netgear Router",
    "2C3033": "D-Link Router", "1CAFF7": "D-Link Router",
    "00055D": "D-Link Device", "001346": "D-Link Device",
    
    # Smart Home
    "B47C9C": "Amazon Echo", "F0D2F1": "Amazon Echo",
    "A002DC": "Google Home", "F4F5D8": "Google Home",
    "54AF97": "Ring Device", "DC4427": "Roku Device",
    "D820B1": "Chromecast", "54605F": "Fire TV",
    "001D9D": "Sony TV", "000D93": "Sony TV",
    "3C2EF9": "LG TV", "B0EE45": "LG TV",
    
    # Gaming
    "7CD30D": "PlayStation", "A45E60": "PlayStation",
    "98B6E9": "Xbox", "F4C795": "Xbox",
    "00A794": "Nintendo Switch", "B83755": "Nintendo Switch",
    
    # Printers
    "001CF0": "HP Printer", "D8D385": "HP Printer",
    "00156D": "Canon Printer", "D0C5F3": "Canon Printer",
    "00C0EE": "Brother Printer", "3C2AF4": "Brother Printer",
}


class NetworkScanner:
    def __init__(self, ip_range: str, timeout: int = 3, port_scan: bool = True):
        self.ip_range = ip_range
        self.timeout = timeout
        self.port_scan = port_scan
        self.devices = []
        
    def scan_arp(self) -> List[Dict]:
        """Perform ARP scan to discover devices"""
        print(f"\n🔍 Scanning network: {self.ip_range}")
        print("=" * 70)
        
        arp = ARP(pdst=self.ip_range)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether / arp
        
        result = srp(packet, timeout=self.timeout, verbose=0)[0]
        devices = []
        
        for sent, received in result:
            devices.append({
                "ip": received.psrc,
                "mac": received.hwsrc,
                "timestamp": datetime.now().isoformat()
            })
        
        print(f"✓ Found {len(devices)} devices")
        return devices
    
    def check_port(self, ip: str, port: int, timeout: float = 0.3) -> bool:
        """Check if a specific port is open"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def scan_common_ports(self, ip: str) -> Dict[str, bool]:
        """Scan common ports to identify device type"""
        if not self.port_scan:
            return {}
            
        common_ports = {
            22: "SSH",
            23: "Telnet",
            80: "HTTP",
            443: "HTTPS",
            445: "SMB",
            631: "Printer",
            3389: "RDP",
            5000: "UPnP",
            8080: "HTTP-Alt",
            8443: "HTTPS-Alt",
            9100: "Printer-Raw"
        }
        
        open_ports = {}
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_port = {
                executor.submit(self.check_port, ip, port): (port, name)
                for port, name in common_ports.items()
            }
            
            for future in as_completed(future_to_port):
                port, name = future_to_port[future]
                if future.result():
                    open_ports[port] = name
        
        return open_ports
    
    def get_hostname(self, ip: str) -> Optional[str]:
        """Attempt to resolve hostname"""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except:
            return None
    
    def identify_device_role(self, ip: str, mac: str, open_ports: Dict, hostname: Optional[str]) -> str:
        """Identify device role based on multiple factors"""
        ip_end = ip.split('.')[-1]
        
        # Router detection
        if ip_end in ["1", "254"] or 443 in open_ports:
            return "🌐 Router / Gateway"
        
        # Check MAC vendor database
        mac_prefix = mac.upper().replace(":", "")[:6]
        if mac_prefix in KNOWN_VENDORS:
            vendor_type = KNOWN_VENDORS[mac_prefix]
            
            # Enhance with port information
            if "Router" in vendor_type and (80 in open_ports or 443 in open_ports):
                return f"🌐 {vendor_type}"
            elif "Phone" in vendor_type or "iPhone" in vendor_type:
                return f"📱 {vendor_type}"
            elif "iPad" in vendor_type or "Tablet" in vendor_type:
                return f"📱 {vendor_type}"
            elif "Mac" in vendor_type or "iMac" in vendor_type:
                return f"💻 {vendor_type}"
            elif "Raspberry Pi" in vendor_type:
                if 22 in open_ports:
                    return "🔧 Raspberry Pi (SSH)"
                return f"🔧 {vendor_type}"
            elif "Printer" in vendor_type or 631 in open_ports or 9100 in open_ports:
                return f"🖨️  {vendor_type}"
            elif "Echo" in vendor_type or "Home" in vendor_type:
                return f"🏠 {vendor_type}"
            elif "TV" in vendor_type or "Chromecast" in vendor_type or "Roku" in vendor_type:
                return f"📺 {vendor_type}"
            elif "PlayStation" in vendor_type or "Xbox" in vendor_type or "Switch" in vendor_type:
                return f"🎮 {vendor_type}"
            else:
                return f"📦 {vendor_type}"
        
        # Port-based detection
        if 631 in open_ports or 9100 in open_ports:
            return "🖨️  Network Printer"
        if 3389 in open_ports:
            return "💻 Windows Desktop (RDP)"
        if 22 in open_ports and 80 not in open_ports:
            return "🖥️  Linux Server/Device"
        if 445 in open_ports:
            return "💻 Windows Device (SMB)"
        if 80 in open_ports and 443 in open_ports:
            return "🌐 Web Server"
        
        # Hostname-based detection
        if hostname:
            hostname_lower = hostname.lower()
            if "android" in hostname_lower:
                return "📱 Android Phone"
            if "iphone" in hostname_lower or "ios" in hostname_lower:
                return "📱 iPhone"
            if "ipad" in hostname_lower:
                return "📱 iPad"
            if "desktop" in hostname_lower or "pc" in hostname_lower:
                return "💻 Desktop Computer"
            if "laptop" in hostname_lower:
                return "💻 Laptop"
            if "printer" in hostname_lower:
                return "🖨️  Printer"
            if "pi" in hostname_lower or "raspberry" in hostname_lower:
                return "🔧 Raspberry Pi"
        
        return "❓ Unknown Device"
    
    def enrich_device_info(self, device: Dict) -> Dict:
        """Enrich device information with hostname and port scan"""
        ip = device["ip"]
        mac = device["mac"]
        
        # Get hostname
        hostname = self.get_hostname(ip)
        device["hostname"] = hostname if hostname else "N/A"
        
        # Scan ports
        open_ports = self.scan_common_ports(ip)
        device["open_ports"] = open_ports
        
        # Identify role
        device["role"] = self.identify_device_role(ip, mac, open_ports, hostname)
        
        return device
    
    def scan(self) -> List[Dict]:
        """Main scan method"""
        # Perform ARP scan
        self.devices = self.scan_arp()
        
        if not self.devices:
            print("\n⚠️  No devices found. Check your network range.")
            return []
        
        # Enrich device information
        print(f"\n🔬 Analyzing devices...")
        enriched_devices = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self.enrich_device_info, device) for device in self.devices]
            
            for i, future in enumerate(as_completed(futures), 1):
                device = future.result()
                enriched_devices.append(device)
                print(f"   Progress: {i}/{len(self.devices)}", end="\r")
        
        print("\n✓ Analysis complete")
        
        # Sort by IP address
        enriched_devices.sort(key=lambda x: tuple(map(int, x['ip'].split('.'))))
        
        return enriched_devices


def display_results(devices: List[Dict], verbose: bool = False):
    """Display scan results in a formatted table"""
    print("\n" + "=" * 70)
    print("📡 NETWORK SCAN RESULTS")
    print("=" * 70)
    
    if verbose:
        for device in devices:
            print(f"\n{device['role']}")
            print(f"  IP Address:  {device['ip']}")
            print(f"  MAC Address: {device['mac']}")
            print(f"  Hostname:    {device['hostname']}")
            
            if device['open_ports']:
                ports_str = ", ".join([f"{port} ({name})" for port, name in device['open_ports'].items()])
                print(f"  Open Ports:  {ports_str}")
            
            print("-" * 70)
    else:
        print(f"\n{'IP Address':<16}  {'MAC Address':<18}  {'Hostname':<25}  {'Device Role'}")
        print("-" * 100)
        
        for device in devices:
            hostname = device['hostname'][:24] if len(device['hostname']) > 24 else device['hostname']
            print(f"{device['ip']:<16}  {device['mac']:<18}  {hostname:<25}  {device['role']}")
    
    print("\n" + "=" * 70)
    print(f"Total devices found: {len(devices)}")
    print("=" * 70 + "\n")


def save_results(devices: List[Dict], output_format: str = "json"):
    """Save scan results to file"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if output_format == "json":
        filename = f"network_scan_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(devices, f, indent=2)
    elif output_format == "csv":
        filename = f"network_scan_{timestamp}.csv"
        import csv
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['ip', 'mac', 'hostname', 'role', 'open_ports'])
            writer.writeheader()
            for device in devices:
                device_copy = device.copy()
                device_copy['open_ports'] = str(device['open_ports'])
                writer.writerow(device_copy)
    elif output_format == "txt":
        filename = f"network_scan_{timestamp}.txt"
        with open(filename, 'w') as f:
            for device in devices:
                f.write(f"IP: {device['ip']}\n")
                f.write(f"MAC: {device['mac']}\n")
                f.write(f"Hostname: {device['hostname']}\n")
                f.write(f"Role: {device['role']}\n")
                f.write(f"Open Ports: {device['open_ports']}\n")
                f.write("-" * 50 + "\n")
    
    print(f"💾 Results saved to: {filename}")


def check_permissions():
    """Check if script has necessary permissions"""
    if os.name != 'nt' and os.geteuid() != 0:
        print("⚠️  This script requires root/administrator privileges")
        print("Run with: sudo python3 network_scanner.py")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Advanced Network Scanner - Discover and identify devices on your network",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Scan default range (192.168.1.0/24)
  %(prog)s -r 10.0.0.0/24              # Scan custom range
  %(prog)s -v                           # Verbose output with port details
  %(prog)s -o json                      # Save results to JSON file
  %(prog)s --no-port-scan               # Skip port scanning (faster)
        """
    )
    
    parser.add_argument('-r', '--range', default='172.16.16.1/24',
                        help='IP range to scan (default: 172.16.16.1/24)')
    parser.add_argument('-t', '--timeout', type=int, default=3,
                        help='Timeout for ARP requests in seconds (default: 3)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Show detailed information including open ports')
    parser.add_argument('-o', '--output', choices=['json', 'csv', 'txt'],
                        help='Save results to file (json, csv, or txt)')
    parser.add_argument('--no-port-scan', action='store_true',
                        help='Skip port scanning for faster results')
    
    args = parser.parse_args()
    
    # Check permissions
    check_permissions()
    
    # Run scan
    start_time = time.time()
    scanner = NetworkScanner(
        ip_range=args.range,
        timeout=args.timeout,
        port_scan=not args.no_port_scan
    )
    devices = scanner.scan()
    
    # Display results
    if devices:
        display_results(devices, verbose=args.verbose)
        
        # Save if requested
        if args.output:
            save_results(devices, args.output)
    
    elapsed_time = time.time() - start_time
    print(f"⏱️  Scan completed in {elapsed_time:.2f} seconds\n")


if __name__ == "__main__":
    main()
