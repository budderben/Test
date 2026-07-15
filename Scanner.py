from scapy.all import ARP, Ether, srp
import socket

def guess_role(ip, mac):
    ip_end = ip.split('.')[-1]

    # Router detection
    if ip_end == "1" or ip_end == "254":
        return "Router / Gateway"

    mac_prefix = mac.upper().replace(":", "")
    vendor = mac_prefix[:6]

    known_vendors = {
        "F4F5E8": "Android Phone",
        "A8BB50": "Android Phone",
        "FCE998": "iPhone",
        "D8C4E9": "iPhone",
        "B827EB": "Raspberry Pi",
        "00163E": "Cisco Device",
        "D4C1FC": "Huawei Router",
        "AC9E17": "TP-Link Router"
    }

    if vendor in known_vendors:
        return known_vendors[vendor]

    # Try hostname
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        if "android" in hostname.lower():
            return "Android Phone"
        if "iphone" in hostname.lower() or "ios" in hostname.lower():
            return "iPhone"
        if "desktop" in hostname.lower() or "pc" in hostname.lower():
            return "Laptop/Desktop"
    except:
        pass

    return "Unknown Device"


def scan_network(ip_range):
    print(f"\nScanning network: {ip_range}")
    print("-" * 50)

    arp = ARP(pdst=ip_range)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether/arp

    result = srp(packet, timeout=3, verbose=0)[0]
    devices = []

    for sent, received in result:
        ip = received.psrc
        mac = received.hwsrc
        role = guess_role(ip, mac)

        devices.append({
            "ip": ip,
            "mac": mac,
            "role": role
        })

    return devices


def display_results(devices):
    print("\n📡 Network Devices Found:\n")
    print("{:<16}  {:<20}  {}".format("IP Address", "MAC Address", "Device Role"))
    print("-" * 60)

    for device in devices:
        print("{:<16}  {:<20}  {}".format(device['ip'], device['mac'], device['role']))

    print("\nDone.\n")


# 🔥 MAIN
if __name__ == "__main__":
    # Your typical range will be 192.168.1.0/24
    target_range = "192.168.1.0/24"
    devices = scan_network(target_range)
    display_results(devices)
