import subprocess
import json
import re
from datetime import datetime
import os
import sys
from typing import Dict, List, Optional, Any

class CyberSecAssistant:
    def __init__(self):
        self.kali_tools = self.load_tools_data()
        self.session_history = []
        
        print("🔒 Cybersecurity Assistant for Kali Linux Tools")
        print("⚠️  For educational and authorized testing purposes only!")
        print("📋 Type 'help' to see available commands")
    
    def load_tools_data(self) -> Dict[str, Dict[str, Any]]:
        """Load tools data from JSON file if available, otherwise use default"""
        tools_file = "kali_tools.json"
        
        # Define the complete tools dataset
        default_tools = {
            'nmap': {
                'description': 'Network discovery and security auditing tool',
                'basic_usage': 'nmap [options] [target]',
                'common_commands': [
                    'nmap -sS target_ip  # SYN scan (stealth scan)',
                    'nmap -sU target_ip  # UDP scan',
                    'nmap -A target_ip   # Aggressive scan (OS & version detection)',
                    'nmap -sV target_ip  # Version detection',
                    'nmap -O target_ip   # OS detection',
                    'nmap -p 1-1000 target_ip  # Scan specific port range',
                    'nmap -sC target_ip  # Default script scan',
                    'nmap --script vuln target_ip  # Run vulnerability scripts'
                ],
                'categories': ['reconnaissance', 'enumeration', 'network']
            },

            'netcat': {
                'description': 'Swiss-army tool for reading/writing raw network connections (TCP/UDP)',
                'basic_usage': 'nc [options] host port',
                'common_commands': [
                    'nc -lvp 4444  # Listen on TCP port 4444 (verbose)',
                    'nc target_ip 80  # Connect to target on port 80',
                    'nc -u target_ip 53  # UDP connection to port 53',
                    'nc -zv target_ip 1-1000  # Port scan (zero-I/O)',
                    'echo "hello" | nc target_ip 1234  # Send data to remote port'
                ],
                'categories': ['network', 'post-exploitation', 'debugging']
            },

            'wireshark': {
                'description': 'Graphical network protocol analyzer for packet inspection',
                'basic_usage': 'wireshark (use tshark for CLI: tshark [options])',
                'common_commands': [
                    'wireshark  # Launch GUI to capture/analyze packets',
                    'tshark -i eth0 -w capture.pcap  # Capture to file using CLI',
                    'tshark -r capture.pcap -Y "http"  # Filter read for HTTP packets',
                    'wireshark -k -i eth0  # Start capturing immediately in GUI'
                ],
                'categories': ['network', 'forensics', 'analysis']
            },

            'tcpdump': {
                'description': 'Command-line packet analyzer and capture tool',
                'basic_usage': 'tcpdump [options] [expression]',
                'common_commands': [
                    'tcpdump -i eth0  # Capture on interface eth0',
                    'tcpdump -i eth0 -w out.pcap  # Write capture to file',
                    'tcpdump -r out.pcap  # Read capture file',
                    'tcpdump -nn -s 0 -v port 80  # Verbose capture for HTTP traffic',
                    'tcpdump -i any "tcp and port 22"  # Filter by expression'
                ],
                'categories': ['network', 'forensics', 'analysis']
            },

            'aircrack-ng': {
                'description': 'Suite for wireless network auditing (capture, crack WPA/WEP)',
                'basic_usage': 'aircrack-ng [options] <capturefile>',
                'common_commands': [
                    'airmon-ng start wlan0  # Put card into monitor mode',
                    'airodump-ng wlan0mon  # Capture wireless traffic',
                    'aireplay-ng --deauth 10 -a AP_MAC wlan0mon  # Send deauths (testing)',
                    'aircrack-ng -w wordlist.txt capture.cap  # Crack captured handshake',
                    'airmon-ng stop wlan0mon  # Stop monitor mode'
                ],
                'categories': ['wireless', 'reconnaissance', 'password-recovery']
            },

            'metasploit-framework': {
                'description': 'Modular penetration testing framework (exploitation & post-exploitation)',
                'basic_usage': 'msfconsole  # Launch Metasploit console',
                'common_commands': [
                    'msfconsole  # Start interactive Metasploit',
                    'search type:exploit name  # Search for modules',
                    'use exploit/windows/smb/ms17_010_eternalblue  # Select a module',
                    'set RHOST target_ip  # Set target host',
                    'run / exploit  # Execute exploit (when configured)'
                ],
                'categories': ['exploitation', 'post-exploitation', 'framework']
            },

            'burpsuite': {
                'description': 'Web application security testing proxy and toolkit',
                'basic_usage': 'burpsuite (use in conjunction with browser proxy settings)',
                'common_commands': [
                    'Start Burp and configure browser proxy to 127.0.0.1:8080',
                    'Use Proxy -> Intercept to view/modify requests',
                    'Scanner (Professional) to automatically identify web vulnerabilities',
                    'Repeater to manually modify and re-send requests for testing'
                ],
                'categories': ['web-apps', 'proxy', 'analysis']
            },

            'sqlmap': {
                'description': 'Automated tool for detecting and exploiting SQL injection flaws',
                'basic_usage': 'sqlmap -u "http://target/page.php?id=1" [options]',
                'common_commands': [
                    'sqlmap -u "http://target/vuln.php?id=1" --dbs  # Enumerate databases',
                    'sqlmap -u "URL" -p id --dump  # Dump table contents',
                    'sqlmap -u "URL" --risk=3 --level=5  # Increase test intensity',
                    'sqlmap -u "URL" --os-shell  # Attempt to get an OS shell (requires vuln)'
                ],
                'categories': ['web-apps', 'exploitation', 'database']
            },

            'nikto': {
                'description': 'Web server scanner that checks for dangerous files, outdated software, and misconfigurations',
                'basic_usage': 'nikto -h target_host',
                'common_commands': [
                    'nikto -h http://target  # Basic scan',
                    'nikto -h target -output nikto_results.txt  # Save results',
                    'nikto -h target -Plugins "all"  # Run all plugins',
                    'nikto -h target -Tuning x  # Tune tests (e.g., 1=files, 2=serv headers)'
                ],
                'categories': ['web-apps', 'vulnerability-scanning', 'enumeration']
            },

            'john': {
                'description': 'John the Ripper — password cracking tool for offline hashes',
                'basic_usage': 'john [options] <hashfile>',
                'common_commands': [
                    'john --wordlist=wordlist.txt hashes.txt  # Wordlist attack',
                    'john --show hashes.txt  # Show cracked passwords',
                    'john --format=md5 hashes.txt  # Specify hash format',
                    'john --incremental hashes.txt  # Brute-force mode'
                ],
                'categories': ['password-cracking', 'forensics', 'offline-analysis']
            },

            'hashcat': {
                'description': 'High-performance password recovery tool that leverages GPU acceleration',
                'basic_usage': 'hashcat -m <hash_type> -a <attack_mode> hashfile wordlist',
                'common_commands': [
                    'hashcat -m 0 -a 0 hash.txt rockyou.txt  # MD5 straight wordlist',
                    'hashcat -m 1000 -a 3 hash.txt ?a?a?a?a?a  # NTLM brute-force',
                    'hashcat --show hash.txt  # Show cracked hashes',
                    'hashcat -b  # Benchmark modes'
                ],
                'categories': ['password-cracking', 'gpu-acceleration', 'forensics']
            },

            'hydra': {
                'description': 'Online password cracking tool for attacking network authentication services (ssh, ftp, http, etc.)',
                'basic_usage': 'hydra -L users.txt -P passwords.txt target service',
                'common_commands': [
                    'hydra -l admin -P rockyou.txt target ssh  # Single user SSH attack',
                    'hydra -L users.txt -P pass.txt ftp://target  # FTP attack with lists',
                    'hydra -s 2222 -t 4 target ssh  # Specify port and threads',
                    'hydra -S -V target https-get /login  # HTTPS form example'
                ],
                'categories': ['credential-stuffing', 'brute-force', 'network']
            },

            'gobuster': {
                'description': 'Directory and DNS busting tool to discover hidden web paths and virtual hosts',
                'basic_usage': 'gobuster dir -u <url> -w <wordlist>',
                'common_commands': [
                    'gobuster dir -u http://target -w /usr/share/wordlists/dirb/common.txt',
                    'gobuster dns -d example.com -w subdomains.txt  # DNS subdomain enumeration',
                    'gobuster dir -u https://target -w wordlist.txt -x php,html,txt  # Extensions',
                    'gobuster vhost -u http://target -w vhosts.txt  # Virtual host discovery'
                ],
                'categories': ['reconnaissance', 'web-apps', 'enumeration']
            },

            'dirb': {
                'description': 'Simple web content scanner that brute-forces directories and files',
                'basic_usage': 'dirb <url> [wordlist]',
                'common_commands': [
                    'dirb http://target /usr/share/wordlists/common.txt  # Basic directory scan',
                    'dirb https://target -S  # Silent mode, less verbose',
                    'dirb http://target -X .php,.html  # Check specific extensions'
                ],
                'categories': ['web-apps', 'reconnaissance', 'enumeration']
            },

            'masscan': {
                'description': 'Extremely fast network port scanner (can scan the Internet in minutes)',
                'basic_usage': 'masscan [target] -p [port-range] --rate [rate]',
                'common_commands': [
                    'masscan 10.0.0.0/8 -p80,443 --rate=1000  # Fast scan of ports 80/443',
                    'masscan target -p1-65535 --rate=10000  # Full port range (high rate)',
                    'masscan -oX results.xml target  # Output results as XML'
                ],
                'categories': ['reconnaissance', 'network', 'scanning']
            },

            'openvas': {
                'description': 'Open-source vulnerability scanning and management (now Greenbone Vulnerability Manager - GVM)',
                'basic_usage': 'gvm-launch / gvm-manage-certs and use web UI (gvm) for scans',
                'common_commands': [
                    'gvm-setup  # Initial setup (varies by distro)',
                    'gvm-start  # Start services',
                    'Use GVM web UI to create targets, tasks and run vulnerability scans',
                    'gvm-check-setup  # Verify installation status'
                ],
                'categories': ['vulnerability-management', 'scanning', 'compliance']
            },

            'smbclient': {
                'description': 'FTP-like client to access SMB/CIFS resources on Windows/Samba servers',
                'basic_usage': 'smbclient //[host]/[share] -U username',
                'common_commands': [
                    'smbclient -L //target -U ""  # List shares (anonymous)',
                    'smbclient //target/share -U user  # Connect to share interactively',
                    'smbclient -N //target/share  # Connect without password (if allowed)',
                    'smbclient --option=clientNTLMv2=0 //target  # Tweak options for legacy shares'
                ],
                'categories': ['network', 'file-sharing', 'enumeration']
            },

            'enum4linux': {
                'description': 'Tool for enumerating Windows and Samba information (users, groups, shares)',
                'basic_usage': 'enum4linux [options] target',
                'common_commands': [
                    'enum4linux -a target  # Full enumeration (shares, users, OS info)',
                    'enum4linux -U target  # Enumerate users',
                    'enum4linux -S target  # Enumerate shares'
                ],
                'categories': ['enumeration', 'windows', 'reconnaissance']
            },

            'snort': {
                'description': 'Network intrusion detection and prevention system (packet inspection with rules)',
                'basic_usage': 'snort -c /etc/snort/snort.conf -i eth0',
                'common_commands': [
                    'snort -A console -q -c /etc/snort/snort.conf -i eth0  # Run in console mode',
                    'snort -c /etc/snort/snort.conf -T  # Test configuration',
                    'snort -l /var/log/snort -c /etc/snort/snort.conf  # Logging directory'
                ],
                'categories': ['intrusion-detection', 'network', 'monitoring']
            },

            'ettercap': {
                'description': 'Comprehensive suite for man-in-the-middle attacks on LAN (ARP spoofing, sniffing, filtering)',
                'basic_usage': 'ettercap -T -q -i interface  # Text mode; use GUI for GUI mode',
                'common_commands': [
                    'ettercap -T -i eth0 -M arp:remote /target1/ /target2/  # ARP MITM between two hosts',
                    'ettercap -G  # Launch GUI version for interactive use',
                    'ettercap -T -i eth0 -r capture.pcap  # Read from capture file'
                ],
                'categories': ['man-in-the-middle', 'network', 'sniffing']
            },

            'proxychains': {
                'description': 'Forces any TCP connection made by any application to follow through proxy (SOCKS/HTTP)',
                'basic_usage': 'proxychains <application> [args]',
                'common_commands': [
                    'proxychains firefox  # Launch Firefox through proxy chain',
                    'proxychains nmap -sT target  # Use proxy chains with nmap TCP connect scan',
                    'Edit /etc/proxychains.conf to configure proxies (socks4/socks5/http)'
                ],
                'categories': ['anonymity', 'proxying', 'operational-security']
            },
            
            # Original tools from the previous implementation
            'metasploit': {
                'description': 'Penetration testing framework',
                'basic_usage': 'msfconsole',
                'common_commands': [
                    'search exploit_name  # Search for exploits',
                    'use exploit/path/to/exploit  # Select exploit',
                    'show options  # Show exploit options',
                    'set RHOSTS target_ip  # Set target IP',
                    'set LHOST attacker_ip  # Set listener IP',
                    'exploit  # Run the exploit',
                    'sessions -l  # List active sessions',
                    'sessions -i 1  # Interact with session 1'
                ],
                'categories': ['exploitation', 'post-exploitation', 'framework']
            },
            
            'wireshark': {
                'description': 'Network packet analyzer',
                'basic_usage': 'wireshark [interface]',
                'common_commands': [
                    'wireshark -i eth0  # Capture on ethernet interface',
                    'tshark -i eth0  # Command-line version',
                    'tshark -r capture.pcap  # Read from file',
                    'tshark -i eth0 -w output.pcap  # Write to file',
                    'tshark -Y "http"  # Filter HTTP traffic'
                ],
                'categories': ['network', 'forensics', 'analysis']
            },
            
            'burpsuite': {
                'description': 'Web application security testing tool',
                'basic_usage': 'burpsuite',
                'common_commands': [
                    'Configure proxy settings in browser (127.0.0.1:8080)',
                    'Use Proxy tab to intercept HTTP requests',
                    'Send requests to Repeater for manual testing',
                    'Use Intruder for automated attacks',
                    'Scanner for automated vulnerability detection'
                ],
                'categories': ['web-apps', 'proxy', 'analysis']
            },
            
            'sqlmap': {
                'description': 'Automatic SQL injection exploitation tool',
                'basic_usage': 'sqlmap -u "URL" [options]',
                'common_commands': [
                    'sqlmap -u "http://target.com/page?id=1"  # Basic scan',
                    'sqlmap -u "URL" --dbs  # Enumerate databases',
                    'sqlmap -u "URL" -D database --tables  # List tables',
                    'sqlmap -u "URL" -D database -T table --columns  # List columns',
                    'sqlmap -u "URL" -D database -T table --dump  # Dump table data',
                    'sqlmap -u "URL" --os-shell  # Get OS shell'
                ],
                'categories': ['web-apps', 'exploitation', 'database']
            },
            
            'john': {
                'description': 'Password cracking tool',
                'basic_usage': 'john [options] password_file',
                'common_commands': [
                    'john passwords.txt  # Basic cracking',
                    'john --wordlist=rockyou.txt passwords.txt  # Dictionary attack',
                    'john --incremental passwords.txt  # Brute force',
                    'john --show passwords.txt  # Show cracked passwords',
                    'john --format=md5 hashes.txt  # Crack MD5 hashes'
                ],
                'categories': ['password-cracking', 'forensics', 'offline-analysis']
            },
            
            'hashcat': {
                'description': 'Advanced password recovery tool',
                'basic_usage': 'hashcat [options] hash_file wordlist',
                'common_commands': [
                    'hashcat -m 0 hashes.txt rockyou.txt  # MD5 cracking',
                    'hashcat -m 1000 hashes.txt rockyou.txt  # NTLM cracking',
                    'hashcat -a 3 -m 0 hash.txt ?l?l?l?l  # Brute force (4 lowercase)',
                    'hashcat --show hash.txt  # Show cracked hashes',
                    'hashcat -m 1800 hashes.txt wordlist.txt  # SHA-512 Unix'
                ],
                'categories': ['password-cracking', 'gpu-acceleration', 'forensics']
            },
            
            'aircrack-ng': {
                'description': 'WiFi security auditing tool suite',
                'basic_usage': 'airmon-ng, airodump-ng, aireplay-ng, aircrack-ng',
                'common_commands': [
                    'airmon-ng start wlan0  # Enable monitor mode',
                    'airodump-ng wlan0mon  # Scan for networks',
                    'airodump-ng -c 6 --bssid AA:BB:CC:DD:EE:FF -w output wlan0mon  # Target specific AP',
                    'aireplay-ng -0 5 -a AA:BB:CC:DD:EE:FF wlan0mon  # Deauth attack',
                    'aircrack-ng -w wordlist.txt output-01.cap  # Crack WPA/WPA2'
                ],
                'categories': ['wireless', 'reconnaissance', 'password-recovery']
            },
            
            'nikto': {
                'description': 'Web server vulnerability scanner',
                'basic_usage': 'nikto -h target',
                'common_commands': [
                    'nikto -h http://target.com  # Basic scan',
                    'nikto -h target.com -p 80,443  # Scan specific ports',
                    'nikto -h target.com -o output.txt  # Save output',
                    'nikto -h target.com -T 2  # Specific test category'
                ],
                'categories': ['web-apps', 'vulnerability-scanning', 'enumeration']
            },
            
            'gobuster': {
                'description': 'Directory and file brute-forcing tool',
                'basic_usage': 'gobuster [mode] [options]',
                'common_commands': [
                    'gobuster dir -u http://target.com -w /usr/share/wordlists/dirb/common.txt',
                    'gobuster dir -u http://target.com -w wordlist.txt -x php,html,txt',
                    'gobuster dns -d target.com -w subdomains.txt  # DNS enumeration',
                    'gobuster vhost -u http://target.com -w vhosts.txt  # Virtual host discovery'
                ],
                'categories': ['reconnaissance', 'web-apps', 'enumeration']
            },
            
            'hydra': {
                'description': 'Network authentication brute-forcer',
                'basic_usage': 'hydra [options] target service',
                'common_commands': [
                    'hydra -l admin -P passwords.txt target.com ssh  # SSH brute force',
                    'hydra -L users.txt -P passwords.txt target.com ftp  # FTP brute force',
                    'hydra -l admin -P passwords.txt target.com http-post-form "/login:user=^USER^&pass=^PASS^:Invalid"',
                    'hydra -L users.txt -P passwords.txt target.com smb  # SMB brute force',
                    'hydra -l admin -p password target.com rdp  # RDP login test'
                ],
                'categories': ['credential-stuffing', 'brute-force', 'network']
            },
            
            'ffuf': {
                'description': 'Fast web fuzzer written in Go',
                'basic_usage': 'ffuf [options]',
                'common_commands': [
                    'ffuf -u http://target.com/FUZZ -w wordlist.txt  # Directory fuzzing',
                    'ffuf -u http://target.com/script.php?FUZZ=test -w params.txt  # Parameter fuzzing',
                    'ffuf -u http://FUZZ.target.com -w subdomains.txt  # Subdomain fuzzing',
                    'ffuf -u http://target.com/FUZZ -w wordlist.txt -fc 404  # Filter 404 responses',
                    'ffuf -u http://target.com/FUZZ -w wordlist.txt -e .php,.html,.txt  # Extension fuzzing'
                ],
                'categories': ['web-apps', 'enumeration', 'fuzzing']
            },
            
            'dirb': {
                'description': 'Web content scanner for finding hidden directories',
                'basic_usage': 'dirb <url> [wordlist]',
                'common_commands': [
                    'dirb http://target.com  # Basic directory scan',
                    'dirb http://target.com /usr/share/dirb/wordlists/common.txt',
                    'dirb http://target.com -X .php,.html  # Scan specific extensions',
                    'dirb http://target.com -a "Mozilla/5.0"  # Custom user agent',
                    'dirb http://target.com -o output.txt  # Save results to file'
                ],
                'categories': ['web-apps', 'reconnaissance', 'enumeration']
            },
            
            'enum4linux': {
                'description': 'Tool for enumerating Linux and Windows systems via SMB',
                'basic_usage': 'enum4linux [options] target',
                'common_commands': [
                    'enum4linux target.com  # Basic enumeration',
                    'enum4linux -a target.com  # All enumeration (-U -M -N -I -P -G -r -o -n -i)',
                    'enum4linux -U target.com  # Users enumeration',
                    'enum4linux -S target.com  # Share enumeration',
                    'enum4linux -P target.com  # Password policy information'
                ],
                'categories': ['enumeration', 'windows', 'reconnaissance']
            },
            
            'wpscan': {
                'description': 'WordPress vulnerability scanner',
                'basic_usage': 'wpscan --url [URL] [options]',
                'common_commands': [
                    'wpscan --url http://target.com  # Basic WordPress scan',
                    'wpscan --url http://target.com --enumerate u  # Enumerate users',
                    'wpscan --url http://target.com --enumerate p  # Enumerate plugins',
                    'wpscan --url http://target.com --enumerate t  # Enumerate themes',
                    'wpscan --url http://target.com --passwords passwords.txt --usernames admin'
                ],
                'categories': ['web-apps', 'vulnerability-scanning', 'enumeration']
            },
            
            'masscan': {
                'description': 'High-speed port scanner',
                'basic_usage': 'masscan [options] <IP/range>',
                'common_commands': [
                    'masscan -p1-10000 192.168.1.0/24 --rate=1000  # Fast port scan',
                    'masscan -p80,443 192.168.1.0/24  # Scan specific ports',
                    'masscan -p1-65535 target.com --rate=10000  # Full port scan',
                    'masscan --top-ports 1000 192.168.1.0/24  # Scan top 1000 ports',
                    'masscan -p80 0.0.0.0/0 --rate=10000 --exclude 255.255.255.255'
                ],
                'categories': ['reconnaissance', 'network', 'scanning']
            },
            
            'recon-ng': {
                'description': 'Web reconnaissance framework',
                'basic_usage': 'recon-ng',
                'common_commands': [
                    'workspaces create target_company  # Create new workspace',
                    'modules search  # Search available modules',
                    'modules load recon/domains-hosts/brute_hosts  # Load module',
                    'info  # Show module information',
                    'options set SOURCE target.com  # Set target domain',
                    'run  # Execute the module'
                ],
                'categories': ['reconnaissance', 'osint', 'framework']
            },
            
            'maltego': {
                'description': 'OSINT and graphical link analysis tool',
                'basic_usage': 'maltego (GUI application)',
                'common_commands': [
                    'Start with Person/Domain/Email entity',
                    'Right-click entity -> Run Transform',
                    'Use built-in transforms for reconnaissance',
                    'Create custom transforms for specific needs',
                    'Export graphs and data for reporting'
                ],
                'categories': ['osint', 'visualization', 'reconnaissance']
            },
            
            'responder': {
                'description': 'LLMNR, NBT-NS and MDNS poisoner',
                'basic_usage': 'responder -I [interface] [options]',
                'common_commands': [
                    'responder -I eth0  # Basic LLMNR/NBT-NS poisoning',
                    'responder -I eth0 -w  # Enable WPAD rogue proxy',
                    'responder -I eth0 -f  # Force NTLM authentication',
                    'responder -I eth0 -v  # Verbose mode',
                    'responder -I eth0 -A  # Analyze mode (no poisoning)'
                ],
                'categories': ['network', 'man-in-the-middle', 'enumeration']
            },
            
            'crunch': {
                'description': 'Wordlist generator',
                'basic_usage': 'crunch <min> <max> [character set] [options]',
                'common_commands': [
                    'crunch 6 8 0123456789  # Generate 6-8 digit numbers',
                    'crunch 4 4 -f /usr/share/crunch/charset.lst mixalpha  # Use charset file',
                    'crunch 1 8 -t password@@@  # Pattern-based generation',
                    'crunch 8 8 abcdefghijklmnopqrstuvwxyz -o wordlist.txt',
                    'crunch 6 6 0123456789 | aircrack-ng -w - -b target.cap  # Pipe to aircrack'
                ],
                'categories': ['password-cracking', 'wordlist-generation', 'utilities']
            },
            
            'searchsploit': {
                'description': 'Exploit database search tool',
                'basic_usage': 'searchsploit [search term]',
                'common_commands': [
                    'searchsploit apache 2.4  # Search for Apache 2.4 exploits',
                    'searchsploit -m 12345  # Mirror/copy exploit to current directory',
                    'searchsploit -x 12345  # Examine exploit without copying',
                    'searchsploit --exclude="dos"  # Exclude DoS exploits',
                    'searchsploit -w apache  # Show URLs for online viewing'
                ],
                'categories': ['exploitation', 'vulnerability-research', 'utilities']
            },
            
            'social-engineer-toolkit': {
                'description': 'Social engineering penetration testing framework',
                'basic_usage': 'setoolkit or se-toolkit',
                'common_commands': [
                    '1) Spear-Phishing Attack Vectors',
                    '2) Website Attack Vectors',
                    '3) Infectious Media Generator',
                    '4) Create a Payload and Listener',
                    '5) Mass Mailer Attack'
                ],
                'categories': ['social-engineering', 'exploitation', 'framework']
            }
        }
        
        try:
            if os.path.exists(tools_file):
                with open(tools_file, 'r') as f:
                    return json.load(f)
            else:
                # Create the file with default data
                with open(tools_file, 'w') as f:
                    json.dump(default_tools, f, indent=2)
                return default_tools
        except Exception as e:
            print(f"Warning: Could not load tools data: {e}")
            return default_tools
    
    def save_tools_data(self):
        """Save tools data to JSON file"""
        try:
            with open("kali_tools.json", 'w') as f:
                json.dump(self.kali_tools, f, indent=2)
        except Exception as e:
            print(f"Error saving tools data: {e}")
    
    def add_to_history(self, command: str, result: str):
        """Add command to session history"""
        self.session_history.append({
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'result': result[:500] + '...' if len(result) > 500 else result  # Limit result size
        })
        # Keep only last 100 commands
        if len(self.session_history) > 100:
            self.session_history.pop(0)
    
    def export_history(self, filename: str = "cybersec_session.json"):
        """Export session history to file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.session_history, f, indent=2)
            return f"📝 History exported to {filename}"
        except Exception as e:
            return f"❌ Error exporting history: {e}"
    
    def get_man_page_info(self, tool_name: str) -> Optional[Dict[str, str]]:
        """Get information from man page with improved parsing"""
        try:
            result = subprocess.run(['man', tool_name], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                man_content = result.stdout
                
                # Extract key sections using regex
                name_match = re.search(r'NAME\s*\n\s*([^\n]+?)\s*\-+\s*([^\n]+)', man_content, re.IGNORECASE)
                synopsis_match = re.search(r'SYNOPSIS\s*\n([\s\S]+?)(?=\n[A-Z]+\s*\n|$)', man_content, re.IGNORECASE)
                
                description = "No description available"
                synopsis = "No synopsis available"
                
                if name_match:
                    description = f"{name_match.group(1).strip()} - {name_match.group(2).strip()}"
                
                if synopsis_match:
                    synopsis_lines = synopsis_match.group(1).strip().split('\n')
                    # Clean up synopsis lines
                    synopsis = ' '.join([line.strip() for line in synopsis_lines if line.strip()])
                    # Limit length
                    synopsis = synopsis[:300] + '...' if len(synopsis) > 300 else synopsis
                
                return {
                    'description': description,
                    'synopsis': synopsis,
                    'source': 'man page'
                }
        except subprocess.TimeoutExpired:
            return {'error': 'Man page lookup timed out'}
        except Exception as e:
            return {'error': f'Error accessing man page: {e}'}
        
        return None
    
    def get_help_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information from tool's help command with improved parsing"""
        help_commands = [
            [tool_name, '--help'],
            [tool_name, '-h'],
            [tool_name, 'help'],
            [tool_name, '-?'],
            [tool_name, '--usage']
        ]
        
        for cmd in help_commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                output = result.stdout if result.stdout else result.stderr
                
                if output and len(output.strip()) > 20:
                    # Extract description and usage with better parsing
                    lines = output.split('\n')
                    description = ""
                    usage = ""
                    
                    # Look for description in first few non-empty lines
                    for line in lines[:10]:
                        stripped = line.strip()
                        if stripped and not stripped.startswith('Usage:') and not stripped.startswith('usage:'):
                            description = stripped
                            break
                    
                    # Look for usage pattern
                    for line in lines:
                        if re.match(r'^(Usage|usage|USAGE):', line):
                            usage = line
                            break
                        if tool_name in line and any(c in line for c in ['[', '<', '-']):
                            usage = line
                            break
                    
                    if not usage:
                        usage = f"{tool_name} [options]"
                    
                    return {
                        'description': description or "Tool help available",
                        'usage': usage,
                        'source': 'help command',
                        'help_output': '\n'.join(lines[:20])  # First 20 lines
                    }
            except subprocess.TimeoutExpired:
                continue
            except Exception:
                continue
        
        return None
    
    def check_tool_availability(self, tool_name: str) -> Optional[str]:
        """Check if a tool is installed and available"""
        try:
            result = subprocess.run(['which', tool_name], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
            
            # Try alternative approach for Windows (if running in WSL)
            if sys.platform == "win32" or "microsoft" in os.uname().release.lower():
                result = subprocess.run(['where.exe', tool_name], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return result.stdout.strip().split('\n')[0]
        except:
            pass
        return None
    
    def explain_tool(self, tool_name: str) -> str:
        """Explain a cybersecurity tool with dynamic lookup"""
        original_tool_name = tool_name
        tool_name = tool_name.lower()
        
        # First check internal database
        if tool_name in self.kali_tools:
            tool = self.kali_tools[tool_name]
            explanation = f"""
🔧 {tool_name.upper()} (Internal Database)
📝 Description: {tool['description']}
💻 Basic Usage: {tool['basic_usage']}

🎯 Common Commands:
"""
            for cmd in tool['common_commands']:
                explanation += f"   {cmd}\n"
            
            if 'categories' in tool:
                explanation += f"\n🏷️  Categories: {', '.join(tool['categories'])}\n"
            
            return explanation
        
        # Tool not in internal database - try dynamic lookup
        print(f"🔍 Tool '{tool_name}' not in database. Searching system...")
        
        # Check if tool is installed
        tool_path = self.check_tool_availability(tool_name)
        if not tool_path:
            return f"""
❌ Tool '{tool_name}' not found in database or system.

💡 Suggestions:
   • Install it: sudo apt install {tool_name} or pkg install {tool_name}
   • Check spelling: {tool_name}
   • Try: tools (to see available tools in database)
   • Try: search {tool_name} (to search for similar tools)
"""
        
        # Tool is installed - gather information
        explanation = f"🔧 {tool_name.upper()} (System Lookup)\n"
        explanation += f"📍 Location: {tool_path}\n\n"
        
        # Try different sources of information
        info_sources = []
        
        # Try man page first
        man_info = self.get_man_page_info(tool_name)
        if man_info and 'error' not in man_info:
            info_sources.append(man_info)
            explanation += f"📖 Description: {man_info['description']}\n"
            explanation += f"💻 Synopsis: {man_info['synopsis']}\n"
        elif man_info and 'error' in man_info:
            explanation += f"⚠️  Man page: {man_info['error']}\n"
        
        # Try help command
        help_info = self.get_help_info(tool_name)
        if help_info:
            info_sources.append(help_info)
            if not man_info or 'error' in man_info:  # Only show if we don't have man page info
                explanation += f"📖 Description: {help_info['description']}\n"
                explanation += f"💻 Usage: {help_info['usage']}\n"
        
        # Add help output if available
        if help_info and 'help_output' in help_info:
            explanation += f"\n🛠️  Help Output Preview:\n"
            explanation += f"```\n{help_info['help_output'][:500]}{'...' if len(help_info['help_output']) > 500 else ''}\n```\n"
        
        # Show sources used
        if info_sources:
            sources = [info['source'] for info in info_sources]
            explanation += f"\n🔍 Information gathered from: {', '.join(sources)}"
        else:
            explanation += "\n❓ No detailed information found, but tool is installed."
        
        # Add suggestions for more info
        explanation += f"""

💡 For more information, try:
   • man {tool_name}
   • {tool_name} --help
   • {tool_name} -h
"""
        
        return explanation
    
    def build_command(self, tool_name: str, attack_type: str, target: Optional[str] = None, 
                     options: Optional[List[str]] = None) -> str:
        """Build specific commands for different attack types with options"""
        tool_name = tool_name.lower()
        attack_type = attack_type.lower()
        options = options or []
        
        # Base command template
        base_cmd = ""
        
        if tool_name == 'nmap':
            if 'port' in attack_type or 'scan' in attack_type:
                if 'stealth' in attack_type or 'syn' in attack_type:
                    base_cmd = f"nmap -sS {target or '[target_ip]'}"
                elif 'udp' in attack_type:
                    base_cmd = f"nmap -sU {target or '[target_ip]'}"
                elif 'aggressive' in attack_type:
                    base_cmd = f"nmap -A {target or '[target_ip]'}"
                elif 'version' in attack_type:
                    base_cmd = f"nmap -sV {target or '[target_ip]'}"
                else:
                    base_cmd = f"nmap -sS -p 1-1000 {target or '[target_ip]'}"
            
            elif 'vuln' in attack_type:
                base_cmd = f"nmap --script vuln {target or '[target_ip]'}"
            
            # Add output options
            if '-o' in options or 'output' in options:
                base_cmd += " -oN scan_results.txt"
                
        elif tool_name == 'sqlmap':
            if 'basic' in attack_type:
                base_cmd = f'sqlmap -u "http://{target or "[target.com]"}/page?id=1"'
            elif 'database' in attack_type or 'db' in attack_type:
                base_cmd = f'sqlmap -u "http://{target or "[target.com]"}/page?id=1" --dbs'
            elif 'table' in attack_type:
                base_cmd = f'sqlmap -u "http://{target or "[target.com]"}/page?id=1" -D [database] --tables'
            elif 'dump' in attack_type:
                base_cmd = f'sqlmap -u "http://{target or "[target.com]"}/page?id=1" -D [database] -T [table] --dump'
            elif 'os-shell' in attack_type:
                base_cmd = f'sqlmap -u "http://{target or "[target.com]"}/page?id=1" --os-shell'
        
        # Add common options
        if 'verbose' in options:
            base_cmd += " -v"
        if 'very-verbose' in options:
            base_cmd += " -vv"
        
        if base_cmd:
            return base_cmd + "  # " + attack_type.replace('_', ' ').title() + " command"
        
        return f"❌ Could not build command for {tool_name} with attack type '{attack_type}'"
    
    def get_wordlists(self) -> str:
        """Show common wordlist locations with improved formatting"""
        wordlists = """
📚 Common Kali Linux Wordlists:

🔤 General:
   /usr/share/wordlists/rockyou.txt (passwords) - 14M entries
   /usr/share/wordlists/dirb/common.txt (directories) - 4.6K entries
   /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt - 220K entries

🌐 Web:
   /usr/share/wordlists/wfuzz/general/common.txt - 950 entries
   /usr/share/wordlists/dirb/big.txt - 20K entries
   /usr/share/wordlists/dirbuster/directory-list-1.0.txt - 70K entries

🔐 Passwords:
   /usr/share/wordlists/rockyou.txt - 14M entries
   /usr/share/wordlists/fasttrack.txt - 222 entries
   /usr/share/john/password.lst - 3.5K entries

📡 Network:
   /usr/share/wordlists/metasploit/unix_users.txt - 72 entries
   /usr/share/wordlists/nmap.lst - 1.5K entries

🔍 Finding more wordlists:
   find /usr/share -name "*wordlist*" -type f 2>/dev/null
   locate *.txt | grep -i wordlist
   ls -la /usr/share/wordlists/

💡 Tip: You can create custom wordlists with crunch or cewl!
"""
        return wordlists
    
    def ethical_reminder(self) -> str:
        """Remind about ethical usage with updated information"""
        return """
⚖️  ETHICAL USAGE REMINDER:

✅ Legal and Authorized Testing:
   • Penetration testing on your own systems
   • Bug bounty programs with proper scope
   • Educational lab environments (TryHackMe, HackTheBox, VulnHub)
   • Red team exercises with written authorization
   • CTF (Capture The Flag) competitions

❌ Illegal Activities (DON'T DO):
   • Attacking systems without permission
   • Unauthorized network scanning
   • Password cracking on systems you don't own
   • WiFi attacks on networks you don't own
   • Disrupting services (DoS/DDoS)

📜 Always ensure you have:
   1. Written authorization before testing
   2. Proper scope documentation
   3. Legal permission from system owners
   4. Understanding of applicable laws (CFAA, Computer Misuse Act, etc.)

🔐 Responsible Disclosure:
   • Report vulnerabilities to vendors/organizations
   • Follow responsible disclosure timelines
   • Don't exploit vulnerabilities without permission

🎓 Use these tools responsibly for learning and legitimate security testing!
        """
    
    def process_command(self, command: str) -> str:
        """Process user commands with improved parsing and functionality"""
        command = command.lower().strip()
        self.add_to_history(command, "")  # Add to history before processing
        
        # Basic commands
        if command in ["time", "date"]:
            now = datetime.now()
            if command == "time":
                result = f"🕐 Current time: {now.strftime('%I:%M:%S %p')}"
            else:
                result = f"📅 Today is: {now.strftime('%A, %B %d, %Y')}"
            self.add_to_history(command, result)
            return result
        
        # Tool explanations
        elif command.startswith(("explain ", "what is ")):
            tool_name = command.split(" ", 2)[-1].strip()
            result = self.explain_tool(tool_name)
            self.add_to_history(command, result)
            return result
        
        # Command building
        elif command.startswith(("build ", "create ")):
            parts = command.split()
            if len(parts) >= 3:
                tool_name = parts[1]
                attack_type = " ".join(parts[2:])
                result = self.build_command(tool_name, attack_type)
            else:
                result = "❓ Usage: build [tool] [attack_type] or create [tool] [attack_type]"
            self.add_to_history(command, result)
            return result
        
        # Wordlists
        elif "wordlist" in command or "dictionary" in command:
            result = self.get_wordlists()
            self.add_to_history(command, result)
            return result
        
        # Search functionality
        elif command.startswith("search "):
            search_term = command.replace("search ", "").strip()
            result = self.search_tools(search_term)
            self.add_to_history(command, result)
            return result
        
        # Advanced help for specific tools
        elif command.startswith("man "):
            tool_name = command.replace("man ", "").strip()
            result = self.get_detailed_man_info(tool_name)
            self.add_to_history(command, result)
            return result
        
        elif command.startswith("help "):
            tool_name = command.replace("help ", "").strip()
            result = self.get_detailed_help_info(tool_name)
            self.add_to_history(command, result)
            return result
        
        # List tools
        elif command in ["tools", "list"]:
            tools_list = "🛠️  Available Tools:\n"
            for tool, info in self.kali_tools.items():
                tools_list += f"   • {tool.upper()}: {info['description']}\n"
            self.add_to_history(command, tools_list)
            return tools_list
        
        # Ethical reminder
        elif "ethical" in command or "legal" in command:
            result = self.ethical_reminder()
            self.add_to_history(command, result)
            return result
        
        # History commands
        elif command == "history":
            if not self.session_history:
                return "📝 No commands in history yet."
            
            history_str = "📝 Command History:\n"
            for i, item in enumerate(self.session_history[-10:], 1):  # Show last 10 commands
                history_str += f"{i}. {item['timestamp']} - {item['command']}\n"
            return history_str
        
        elif command.startswith("export history"):
            filename = command.replace("export history", "").strip()
            if not filename:
                filename = f"cybersec_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            result = self.export_history(filename)
            self.add_to_history(command, result)
            return result
        
        # Help
        elif command == "help":
            help_text = """
🔒 Cybersecurity Assistant Commands:

📖 Tool Information:
   • explain [tool] - Get detailed info (searches system if not in database)
   • what is [tool] - Same as explain
   • tools - List all available tools in database
   • search [term] - Search for tools by name or description
   • man [tool] - Show detailed man page information
   • help [tool] - Show tool's help output

🛠️  Command Building:
   • build [tool] [attack_type] - Build specific commands
   • create [tool] [attack_type] - Same as build

📚 Resources:
   • wordlists - Show common wordlist locations
   • ethical - Important legal/ethical guidelines

📝 Session Management:
   • history - Show command history
   • export history [filename] - Export history to JSON file

🎯 Examples:
   • explain nmap
   • search password
   • man nmap
   • help sqlmap
   • build nmap port_scan
   • create sqlmap basic_attack

⚠️  Remember: Only use on authorized systems!
            """
            self.add_to_history(command, help_text)
            return help_text
        
        # Greetings
        elif any(word in command for word in ["hello", "hi", "hey"]):
            result = "👋 Hello! I'm your cybersecurity assistant. I can help explain Kali Linux tools and build commands for authorized testing. Try 'help' for options!"
            self.add_to_history(command, result)
            return result
        
        # Exit
        elif command in ["exit", "quit", "bye", "goodbye"]:
            result = "🔒 Stay ethical and keep learning! Goodbye!"
            self.add_to_history(command, result)
            return result
        
        # Default
        else:
            result = f"🤔 I don't understand '{command}'. Try 'help' to see what I can do, or 'explain [tool_name]' for tool info."
            self.add_to_history(command, result)
            return result

    def search_tools(self, search_term: str) -> str:
        """Search for tools by name, description, or category"""
        search_term = search_term.lower()
        results = []
        
        # Search in internal database
        for tool, info in self.kali_tools.items():
            # Check name
            if search_term in tool.lower():
                results.append(f"🔧 {tool.upper()}: {info['description']}")
                continue
                
            # Check description
            if search_term in info['description'].lower():
                results.append(f"🔧 {tool.upper()}: {info['description']}")
                continue
                
            # Check categories if they exist
            if 'categories' in info:
                for category in info['categories']:
                    if search_term in category.lower():
                        results.append(f"🔧 {tool.upper()} ({category}): {info['description']}")
                        break
        
        # Search installed tools on system
        try:
            # Search with whereis command
            result = subprocess.run(['whereis', search_term], capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                whereis_output = result.stdout.strip()
                if ':' in whereis_output:
                    paths = whereis_output.split(':', 1)[1].strip()
                    if paths:
                        results.append(f"🔍 System found: {whereis_output}")
        except:
            pass
        
        # Search with apt/pkg
        try:
            if sys.platform != "win32":
                result = subprocess.run(['apt', 'search', search_term], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')[:5]  # First 5 results
                    for line in lines:
                        if search_term in line.lower() and '/' in line:
                            results.append(f"📦 Package: {line.strip()}")
        except:
            try:
                result = subprocess.run(['pkg', 'search', search_term], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')[:5]
                    for line in lines:
                        if search_term in line.lower():
                            results.append(f"📦 Termux Package: {line.strip()}")
            except:
                pass
        
        if results:
            return f"🔍 Search results for '{search_term}':\n\n" + '\n'.join(results[:10])  # Limit to 10 results
        else:
            return f"❌ No results found for '{search_term}'. Try different keywords or 'tools' to see available tools."
    
    def get_detailed_man_info(self, tool_name: str) -> str:
        """Get detailed man page information with improved parsing"""
        try:
            result = subprocess.run(['man', tool_name], capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                man_content = result.stdout
                
                # Parse man page sections
                sections = {}
                current_section = ""
                
                lines = man_content.split('\n')
                for line in lines:
                    stripped = line.strip()
                    if stripped and stripped.isupper() and not stripped.startswith(' '):
                        current_section = stripped
                        sections[current_section] = []
                    elif current_section and line.strip():
                        sections[current_section].append(line)
                
                # Format output
                output = f"📖 MAN PAGE: {tool_name.upper()}\n\n"
                
                # Show key sections
                important_sections = ['NAME', 'SYNOPSIS', 'DESCRIPTION', 'OPTIONS', 'EXAMPLES']
                for section in important_sections:
                    if section in sections:
                        output += f"🔸 {section}:\n"
                        content = '\n'.join(sections[section][:10])  # First 10 lines
                        output += f"{content[:800]}{'...' if len(content) > 800 else ''}\n\n"
                
                return output
            else:
                return f"❌ No man page found for '{tool_name}'"
        except subprocess.TimeoutExpired:
            return f"❌ Man page lookup for '{tool_name}' timed out"
        except Exception as e:
            return f"❌ Error accessing man page: {e}"
    
    def get_detailed_help_info(self, tool_name: str) -> str:
        """Get detailed help information from tool with improved parsing"""
        help_commands = [
            [tool_name, '--help'],
            [tool_name, '-h'],
            [tool_name, 'help'],
            [tool_name, '--usage']
        ]
        
        for cmd in help_commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                if result.returncode == 0 or result.stderr:
                    help_output = result.stdout if result.stdout else result.stderr
                    if help_output and len(help_output.strip()) > 20:
                        return f"""
🛠️  HELP: {tool_name.upper()}

{help_output[:1500]}{'...' if len(help_output) > 1500 else ''}

💡 Full help: {tool_name} --help
"""
            except subprocess.TimeoutExpired:
                continue
            except Exception:
                continue
        
        return f"❌ No help information found for '{tool_name}'"

def main():
    assistant = CyberSecAssistant()
    
    # Show ethical reminder on startup
    print(assistant.ethical_reminder())
    
    while True:
        try:
            user_input = input("\n🔒 CyberSec> ").strip()
            
            if not user_input:
                continue
                
            response = assistant.process_command(user_input)
            print(response)
            
            if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
                # Offer to export history before exiting
                export = input("📝 Export command history? (y/N): ").strip().lower()
                if export == 'y':
                    filename = input("Enter filename (or press Enter for default): ").strip()
                    if not filename:
                        filename = f"cybersec_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    print(assistant.export_history(filename))
                break
                
        except KeyboardInterrupt:
            print("\n\n🔒 Stay safe and ethical! Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()