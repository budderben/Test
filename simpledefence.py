#!/usr/bin/env python3
"""
Enhanced Defensive Cybersecurity Assistant
Author: Assistant
Version: 3.1
License: Educational Use Only
Focus: System hardening, monitoring, and defensive security measures with direct execution
"""

import subprocess
import json
import re
import sys
import os
import signal
import psutil
import socket
import shutil
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path


class DefensiveCyberAssistant:
    """Enhanced defensive cybersecurity assistant with direct command execution"""

    def __init__(self):
        # Initialize logging
        self._setup_logging()

        # Initialize data structures
        self.security_tools = self.load_security_tools()
        self.session_history = []
        self.config = self.load_config()
        self.alerts = []
        self.safe_commands = self._initialize_safe_commands()
        self.background_monitors = {}

        # Check if running with appropriate permissions
        self.is_root = os.geteuid() == 0

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Initialize monitoring threads if enabled
        if self.config.get('enable_background_monitoring', False):
            self._start_background_monitoring()

        # Display startup messages
        self._display_startup()

    def _setup_logging(self):
        """Setup comprehensive logging system"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'defensive_security.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('DefensiveCyberAssistant')

    def _signal_handler(self, signum, frame):
        """Handle interrupt signals gracefully"""
        print("\n\n🛡️  Shutting down safely...")
        self._stop_background_monitoring()
        self._safe_exit()

    def _safe_exit(self):
        """Safe exit with optional history export"""
        try:
            if self.session_history:
                export = input("📝 Export security session history? (y/N): ").strip().lower()
                if export == 'y':
                    filename = input("Enter filename (or press Enter for default): ").strip()
                    if not filename:
                        filename = f"security_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    print(self.export_history(filename))
        except:
            pass

        self.logger.info("Defensive Cybersecurity Assistant shutting down")
        print("🛡️  Stay secure! Goodbye!")
        sys.exit(0)

    def _initialize_safe_commands(self) -> Dict[str, Dict[str, Any]]:
        """Initialize safe commands that can be executed directly"""
        return {
            'system_update': {
                'commands': ['apt', 'update', '&&', 'apt', 'upgrade', '-y'],
                'requires_root': True,
                'description': 'Update system packages',
                'risk_level': 'low',
                'confirmation_required': True,
                'timeout': 600
            },
            'security_update': {
                'commands': ['apt', 'update', '&&', 'apt', 'upgrade', '-y', '--security'],
                'requires_root': True,
                'description': 'Install only security updates',
                'risk_level': 'low',
                'confirmation_required': True,
                'timeout': 600
            },
            'install_fail2ban': {
                'commands': ['apt', 'install', '-y', 'fail2ban'],
                'requires_root': True,
                'description': 'Install fail2ban intrusion prevention',
                'risk_level': 'low',
                'confirmation_required': True,
                'timeout': 300,
                'post_install': 'configure_fail2ban'
            },
            'configure_fail2ban': {
                'commands': ['systemctl', 'enable', 'fail2ban', '&&', 'systemctl', 'start', 'fail2ban'],
                'requires_root': True,
                'description': 'Configure and start fail2ban service',
                'risk_level': 'low',
                'confirmation_required': False,
                'timeout': 60
            },
            'install_clamav': {
                'commands': ['apt', 'install', '-y', 'clamav', 'clamav-daemon', 'clamav-freshclam'],
                'requires_root': True,
                'description': 'Install ClamAV antivirus',
                'risk_level': 'low',
                'confirmation_required': True,
                'timeout': 300,
                'post_install': 'configure_clamav'
            },
            'configure_clamav': {
                'commands': ['systemctl', 'enable', 'clamav-freshclam', '&&', 'systemctl', 'start', 'clamav-freshclam'],
                'requires_root': True,
                'description': 'Configure ClamAV automatic updates',
                'risk_level': 'low',
                'confirmation_required': False,
                'timeout': 60
            },
            'install_lynis': {
                'commands': ['apt', 'install', '-y', 'lynis'],
                'requires_root': True,
                'description': 'Install Lynis security auditing tool',
                'risk_level': 'low',
                'confirmation_required': True,
                'timeout': 300
            },
            'install_rkhunter': {
                'commands': ['apt', 'install', '-y', 'rkhunter'],
                'requires_root': True,
                'description': 'Install RKHunter rootkit scanner',
                'risk_level': 'low',
                'confirmation_required': True,
                'timeout': 300,
                'post_install': 'configure_rkhunter'
            },
            'configure_rkhunter': {
                'commands': ['rkhunter', '--update', '&&', 'rkhunter', '--propupd'],
                'requires_root': True,
                'description': 'Update RKHunter database and properties',
                'risk_level': 'low',
                'confirmation_required': False,
                'timeout': 180
            },
            'enable_ufw': {
                'commands': ['ufw', 'enable'],
                'requires_root': True,
                'description': 'Enable UFW firewall',
                'risk_level': 'medium',
                'confirmation_required': True,
                'timeout': 30
            },
            'configure_ufw_basic': {
                'commands': ['ufw', '--force', 'reset', '&&', 'ufw', 'default', 'deny', 'incoming', '&&',
                           'ufw', 'default', 'allow', 'outgoing', '&&', 'ufw', 'allow', 'ssh', '&&',
                           'ufw', 'allow', 'http', '&&', 'ufw', 'allow', 'https', '&&', 'ufw', 'enable'],
                'requires_root': True,
                'description': 'Configure UFW with secure default rules',
                'risk_level': 'medium',
                'confirmation_required': True,
                'timeout': 60
            },
            'update_clamav': {
                'commands': ['freshclam'],
                'requires_root': True,
                'description': 'Update ClamAV virus definitions',
                'risk_level': 'low',
                'confirmation_required': False,
                'timeout': 300
            },
            'scan_rootkits': {
                'commands': ['rkhunter', '--check', '--sk', '--report-warnings-only'],
                'requires_root': True,
                'description': 'Run rootkit scan with RKHunter',
                'risk_level': 'low',
                'confirmation_required': False,
                'timeout': 600
            },
            'security_audit': {
                'commands': ['lynis', 'audit', 'system', '--quick', '--no-colors'],
                'requires_root': True,
                'description': 'Run quick security audit with Lynis',
                'risk_level': 'low',
                'confirmation_required': False,
                'timeout': 300
            },
            'security_audit_full': {
                'commands': ['lynis', 'audit', 'system', '--no-colors'],
                'requires_root': True,
                'description': 'Run comprehensive security audit with Lynis',
                'risk_level': 'low',
                'confirmation_required': True,
                'timeout': 900
            },
            'virus_scan_home': {
                'commands': ['clamscan', '-r', '--bell', '-i', '--log=/var/log/clamav/scan_home.log', os.path.expanduser('~')],
                'requires_root': False,
                'description': 'Scan home directory for viruses',
                'risk_level': 'low',
                'confirmation_required': False,
                'timeout': 1800
            },
            'virus_scan_system': {
                'commands': ['clamscan', '-r', '--bell', '-i', '--log=/var/log/clamav/scan_system.log', '/'],
                'requires_root': True,
                'description': 'Full system virus scan (very slow)',
                'risk_level': 'low',
                'confirmation_required': True,
                'timeout': 7200
            },
            'check_rootkits_chkrootkit': {
                'commands': ['chkrootkit', '-q'],
                'requires_root': True,
                'description': 'Check for rootkits with chkrootkit',
                'risk_level': 'low',
                'confirmation_required': False,
                'timeout': 600
            },
            'harden_ssh': {
                'commands': ['python3', '-c', 'from __main__ import DefensiveCyberAssistant; DefensiveCyberAssistant.harden_ssh_config()'],
                'requires_root': True,
                'description': 'Harden SSH configuration',
                'risk_level': 'medium',
                'confirmation_required': True,
                'timeout': 60
            },
            'install_aide': {
                'commands': ['apt', 'install', '-y', 'aide'],
                'requires_root': True,
                'description': 'Install AIDE file integrity monitor',
                'risk_level': 'low',
                'confirmation_required': True,
                'timeout': 300,
                'post_install': 'configure_aide'
            },
            'configure_aide': {
                'commands': ['aideinit', '&&', 'mv', '/var/lib/aide/aide.db.new', '/var/lib/aide/aide.db'],
                'requires_root': True,
                'description': 'Initialize AIDE database',
                'risk_level': 'low',
                'confirmation_required': False,
                'timeout': 900
            },
            'check_aide': {
                'commands': ['aide', '--check'],
                'requires_root': True,
                'description': 'Check file integrity with AIDE',
                'risk_level': 'low',
                'confirmation_required': False,
                'timeout': 600
            }
        }

    def _display_startup(self):
        """Display enhanced startup information"""
        print("=" * 75)
        print("🛡️  DEFENSIVE CYBERSECURITY ASSISTANT v3.1")
        print("=" * 75)
        print("🔒 Focus: Advanced system hardening, monitoring & protection")
        print(f"🛠️  Security tools loaded: {len(self.security_tools)}")
        print(f"🔑 Running as: {'Root (Full Access)' if self.is_root else 'Regular User (Limited)'}")
        if self.is_root:
            print("⚡ All security commands available for direct execution")
        else:
            print("⚠️  Run with 'sudo' for complete functionality")

        if self.config.get('enable_background_monitoring', False):
            print("📡 Background monitoring: ENABLED")
        else:
            print("📡 Background monitoring: DISABLED (enable in config)")

        print("📋 Type 'help' for commands | 'auto-harden' for quick setup")
        print("=" * 75)

        # Quick system status check
        self._display_quick_status()

    def _display_quick_status(self):
        """Display comprehensive quick system security status"""
        try:
            status_items = []

            # Firewall status
            firewall_status = self._check_firewall_status()
            status_items.append(firewall_status)

            # Update status
            update_status = self._check_update_status()
            status_items.append(update_status)

            # System load
            load_status = self._check_system_load()
            status_items.append(load_status)

            # Security services
            services_status = self._check_security_services()
            status_items.extend(services_status)

            print("🔍 Quick Security Status:")
            for item in status_items:
                print(f"   {item}")
            print()

        except Exception as e:
            self.logger.error(f"Could not perform quick status check: {e}")
            print(f"⚠️  Could not perform quick status check: {e}\n")

    def _check_firewall_status(self) -> str:
        """Check firewall status"""
        try:
            result = subprocess.run(['ufw', 'status'], capture_output=True, text=True, timeout=5)
            if 'Status: active' in result.stdout:
                return "🟢 Firewall: Active (UFW)"
            else:
                return "🟡 Firewall: Inactive"
        except:
            try:
                result = subprocess.run(['iptables', '-L'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and len(result.stdout.split('\n')) > 10:
                    return "🟢 Firewall: Active (iptables)"
                else:
                    return "🟡 Firewall: Basic/Default"
            except:
                return "🔍 Firewall: Unknown"

    def _check_update_status(self) -> str:
        """Check system update status"""
        try:
            result = subprocess.run(['apt', 'list', '--upgradable'],
                                  capture_output=True, text=True, timeout=15)
            update_count = len([line for line in result.stdout.split('\n') if 'upgradable' in line]) - 1
            if update_count > 0:
                return f"🟡 Updates: {update_count} available"
            else:
                return "🟢 Updates: System current"
        except:
            return "🔍 Updates: Unable to check"

    def _check_system_load(self) -> str:
        """Check system load"""
        try:
            load_avg = os.getloadavg()[0]
            cpu_count = os.cpu_count()
            load_percent = (load_avg / cpu_count) * 100

            if load_percent > 80:
                return f"🟡 Load: High ({load_avg:.1f})"
            elif load_percent > 50:
                return f"🟠 Load: Medium ({load_avg:.1f})"
            else:
                return f"🟢 Load: Normal ({load_avg:.1f})"
        except:
            return "🔍 Load: Unknown"

    def _check_security_services(self) -> List[str]:
        """Check security services status"""
        services = []
        security_services = {
            'fail2ban': 'Intrusion Prevention',
            'clamav-daemon': 'Antivirus',
            'ssh': 'SSH Service'
        }

        for service, description in security_services.items():
            try:
                result = subprocess.run(['systemctl', 'is-active', service],
                                      capture_output=True, text=True, timeout=3)
                if result.stdout.strip() == 'active':
                    services.append(f"🟢 {description}: Running")
                else:
                    services.append(f"🔴 {description}: Stopped")
            except:
                services.append(f"🔍 {description}: Unknown")

        return services

    def _start_background_monitoring(self):
        """Start background monitoring threads"""
        if not self.config.get('enable_background_monitoring', False):
            return

        # System monitoring thread
        system_thread = threading.Thread(target=self._system_monitor, daemon=True)
        system_thread.start()
        self.background_monitors['system'] = system_thread

        # Log monitoring thread
        log_thread = threading.Thread(target=self._log_monitor, daemon=True)
        log_thread.start()
        self.background_monitors['logs'] = log_thread

        self.logger.info("Background monitoring started")

    def _stop_background_monitoring(self):
        """Stop background monitoring threads"""
        self.config['enable_background_monitoring'] = False
        self.logger.info("Background monitoring stopped")

    def _system_monitor(self):
        """Background system monitoring"""
        while self.config.get('enable_background_monitoring', False):
            try:
                # Monitor system resources
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent
                disk_percent = psutil.disk_usage('/').percent

                # Check thresholds
                thresholds = self.config.get('alert_thresholds', {})

                if cpu_percent > thresholds.get('cpu_usage', 85):
                    self._add_alert(f"High CPU usage detected: {cpu_percent:.1f}%")

                if memory_percent > thresholds.get('memory_usage', 90):
                    self._add_alert(f"High memory usage detected: {memory_percent:.1f}%")

                if disk_percent > thresholds.get('disk_usage', 85):
                    self._add_alert(f"High disk usage detected: {disk_percent:.1f}%")

                # Sleep for monitoring interval
                time.sleep(self.config.get('monitor_intervals', {}).get('system', 600))

            except Exception as e:
                self.logger.error(f"System monitoring error: {e}")
                time.sleep(60)

    def _log_monitor(self):
        """Background log monitoring"""
        auth_log = '/var/log/auth.log'
        if not os.path.exists(auth_log):
            return

        # Track last position in log file
        last_position = 0
        if os.path.exists(auth_log):
            last_position = os.path.getsize(auth_log)

        while self.config.get('enable_background_monitoring', False):
            try:
                if os.path.exists(auth_log):
                    current_size = os.path.getsize(auth_log)

                    if current_size > last_position:
                        # Read new log entries
                        with open(auth_log, 'r') as f:
                            f.seek(last_position)
                            new_content = f.read()

                        # Check for security events
                        failed_attempts = len(re.findall(r'Failed password', new_content))
                        invalid_users = len(re.findall(r'Invalid user', new_content))

                        if failed_attempts > 5:
                            self._add_alert(f"Multiple failed login attempts detected: {failed_attempts}")

                        if invalid_users > 3:
                            self._add_alert(f"Invalid user attempts detected: {invalid_users}")

                        # Check for other suspicious patterns
                        self._check_suspicious_log_patterns(new_content)

                        last_position = current_size

                time.sleep(self.config.get('monitor_intervals', {}).get('logs', 30))

            except Exception as e:
                self.logger.error(f"Log monitoring error: {e}")
                time.sleep(60)

    def _check_suspicious_log_patterns(self, log_content: str):
        """Check for suspicious patterns in log content"""
        patterns = {
            'sudo abuse': r'sudo:.*COMMAND=.*\(root\)',
            'root login': r'sshd.*Accepted.*root',
            'cron modification': r'crontab.*\+',
            'passwd change': r'passwd.*changed',
            'suid changes': r'chmod.*[+s]',
        }

        for alert_name, pattern in patterns.items():
            if re.search(pattern, log_content, re.IGNORECASE):
                self._add_alert(f"Suspicious activity detected: {alert_name}")

    @staticmethod
    def harden_ssh_config():
        """Harden SSH configuration"""
        ssh_config_path = "/etc/ssh/sshd_config"
        backup_path = f"{ssh_config_path}.bak.{int(time.time())}"

        try:
            # Backup current config
            shutil.copy2(ssh_config_path, backup_path)
            print(f"✅ Backed up SSH config to {backup_path}")

            # Read current config
            with open(ssh_config_path, 'r') as f:
                lines = f.readlines()

            # Security settings to enforce
            security_settings = {
                'PermitRootLogin': 'no',
                'PasswordAuthentication': 'no',
                'PermitEmptyPasswords': 'no',
                'X11Forwarding': 'no',
                'MaxAuthTries': '3',
                'ClientAliveInterval': '300',
                'ClientAliveCountMax': '0',
                'AllowTcpForwarding': 'no',
                'GatewayPorts': 'no',
                'UsePrivilegeSeparation': 'yes',
                'Protocol': '2',
                'LoginGraceTime': '60',
                'PrintLastLog': 'yes',
                'TCPKeepAlive': 'no'
            }

            # Modify or add settings
            modified = False
            new_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('#') or not stripped:
                    new_lines.append(line)
                    continue

                key = stripped.split()[0]
                if key in security_settings:
                    new_lines.append(f"{key} {security_settings[key]}\n")
                    modified = True
                    del security_settings[key]  # Remove from pending
                else:
                    new_lines.append(line)

            # Add remaining settings
            if security_settings:
                new_lines.append("\n# Added by DefensiveCyberAssistant\n")
                for key, value in security_settings.items():
                    new_lines.append(f"{key} {value}\n")
                modified = True

            if modified:
                with open(ssh_config_path, 'w') as f:
                    f.writelines(new_lines)

                # Test SSH config and restart
                result = subprocess.run(['sshd', '-t'], capture_output=True)
                if result.returncode == 0:
                    subprocess.run(['systemctl', 'restart', 'ssh'], check=True)
                    print("✅ SSH configuration hardened and service restarted")
                    return True
                else:
                    print("❌ Invalid SSH configuration. Restoring backup...")
                    shutil.copy2(backup_path, ssh_config_path)
                    return False
            else:
                print("ℹ️  SSH configuration already hardened")
                return True

        except Exception as e:
            print(f"❌ Error hardening SSH: {e}")
            return False

    def load_config(self) -> Dict[str, Any]:
        """Load or create default configuration"""
        config_path = Path("config.json")
        default_config = {
            "enable_background_monitoring": False,
            "alert_thresholds": {
                "cpu_usage": 85,
                "memory_usage": 90,
                "disk_usage": 85
            },
            "monitor_intervals": {
                "system": 600,  # 10 minutes
                "logs": 30      # 30 seconds
            },
            "auto_harden_profile": "balanced",
            "history_retention_days": 30
        }

        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return {**default_config, **json.load(f)}
            except Exception as e:
                self.logger.warning(f"Could not load config: {e}. Using defaults.")
                return default_config
        else:
            # Create default config
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            self.logger.info("Created default configuration file: config.json")
            return default_config

    def load_security_tools(self) -> List[str]:
        """Load list of available security tools (for future expansion)"""
        # This can be extended to dynamically detect installed tools
        return [
            "lynis", "rkhunter", "chkrootkit", "clamav",
            "fail2ban", "ufw", "aide", "auditd"
        ]

    def run_command(self, command_key: str) -> bool:
        """Execute a predefined safe command"""
        if command_key not in self.safe_commands:
            print(f"❌ Command '{command_key}' not found")
            return False

        cmd_info = self.safe_commands[command_key]

        # Check root requirement
        if cmd_info['requires_root'] and not self.is_root:
            print("❌ This command requires root privileges. Run with sudo.")
            return False

        # Confirmation if required
        if cmd_info.get('confirmation_required', False):
            confirm = input(f"⚠️  {cmd_info['description']} - Proceed? (y/N): ").strip().lower()
            if confirm != 'y':
                print("❌ Operation cancelled by user")
                return False

        print(f"🔧 Executing: {cmd_info['description']}...")
        self.logger.info(f"Executing command: {command_key}")

        try:
            # Join command parts for shell execution
            cmd_str = ' '.join(cmd_info['commands'])

            # Execute with timeout
            result = subprocess.run(
                cmd_str,
                shell=True,
                capture_output=True,
                text=True,
                timeout=cmd_info.get('timeout', 300)
            )

            if result.returncode == 0:
                print(f"✅ Success: {cmd_info['description']}")
                self.logger.info(f"Command completed successfully: {command_key}")

                # Execute post-install if specified
                if 'post_install' in cmd_info:
                    print("🔄 Running post-install step...")
                    self.run_command(cmd_info['post_install'])

                # Record in history
                self.session_history.append({
                    'command': command_key,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'success',
                    'output_preview': result.stdout[:500] if result.stdout else "No output"
                })
                return True
            else:
                error_msg = result.stderr[:1000] if result.stderr else "Unknown error"
                print(f"❌ Failed: {error_msg}")
                self.logger.error(f"Command failed: {command_key} - {error_msg}")

                self.session_history.append({
                    'command': command_key,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'failed',
                    'error': error_msg
                })
                return False

        except subprocess.TimeoutExpired:
            print(f"⏰ Command timed out after {cmd_info.get('timeout', 300)} seconds")
            self.logger.error(f"Command timeout: {command_key}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            self.logger.error(f"Command exception: {command_key} - {e}")
            return False

    def _add_alert(self, message: str):
        """Add security alert"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'acknowledged': False
        }
        self.alerts.append(alert)
        self.logger.warning(f"SECURITY ALERT: {message}")
        print(f"\n🚨 SECURITY ALERT: {message}\n")

    def auto_harden(self):
        """Perform automatic system hardening based on profile"""
        print("🚀 Starting automatic system hardening...")

        steps = [
            'system_update',
            'security_update',
            'install_fail2ban',
            'install_clamav',
            'install_lynis',
            'install_rkhunter',
            'install_aide',
            'configure_ufw_basic',
            'harden_ssh'
        ]

        success_count = 0
        for step in steps:
            print(f"\n📌 Step: {self.safe_commands[step]['description']}")
            if self.run_command(step):
                success_count += 1

        print(f"\n✅ Auto-hardening complete: {success_count}/{len(steps)} steps successful")
        print("🛡️  System is now significantly more secure!")

    def export_history(self, filename: str) -> str:
        """Export session history to file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.session_history, f, indent=2)
            return f"✅ Session history exported to {filename}"
        except Exception as e:
            return f"❌ Failed to export history: {e}"

    def show_help(self):
        """Display available commands"""
        print("\n" + "="*50)
        print("📋 AVAILABLE COMMANDS")
        print("="*50)
        print("help           - Show this help")
        print("auto-harden    - Run automatic hardening")
        print("status         - Show system security status")
        print("alerts         - Show active security alerts")
        print("history        - Show command history")
        print("export         - Export session history")
        print("config         - Show current configuration")
        print("exit/quit      - Exit the assistant")
        print("\nSecurity Commands (use 'run <command>'):")
        for cmd, info in self.safe_commands.items():
            risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(info['risk_level'], "⚪")
            print(f"  {risk_emoji} {cmd:<25} - {info['description']}")
        print("="*50)

    def show_status(self):
        """Show detailed system security status"""
        print("\n📊 SYSTEM SECURITY STATUS")
        print("="*50)
        self._display_quick_status()

        # Show active alerts
        if self.alerts:
            print("\n🚨 ACTIVE ALERTS:")
            for alert in self.alerts:
                if not alert['acknowledged']:
                    print(f"   [{alert['timestamp']}] {alert['message']}")

    def show_alerts(self):
        """Show all security alerts"""
        if not self.alerts:
            print("✅ No active security alerts")
            return

        print("\n🚨 SECURITY ALERTS")
        print("="*50)
        for i, alert in enumerate(self.alerts, 1):
            status = "🔴 UNACKNOWLEDGED" if not alert['acknowledged'] else "🟢 ACKNOWLEDGED"
            print(f"{i}. [{alert['timestamp']}] {status}")
            print(f"   {alert['message']}")
            print()

    def show_history(self):
        """Show command execution history"""
        if not self.session_history:
            print("ℹ️  No command history yet")
            return

        print("\n📋 COMMAND HISTORY")
        print("="*70)
        for entry in self.session_history:
            status_icon = "✅" if entry['status'] == 'success' else "❌"
            print(f"{status_icon} [{entry['timestamp']}] {entry['command']}")
            if entry.get('output_preview'):
                print(f"   Output: {entry['output_preview'][:100]}...")
            elif entry.get('error'):
                print(f"   Error: {entry['error'][:100]}...")
            print()

    def run(self):
        """Main command loop"""
        while True:
            try:
                cmd = input("\n🔒 Enter command: ").strip()

                if not cmd:
                    continue
                elif cmd in ['exit', 'quit', 'q']:
                    self._safe_exit()
                elif cmd == 'help':
                    self.show_help()
                elif cmd == 'auto-harden':
                    self.auto_harden()
                elif cmd == 'status':
                    self.show_status()
                elif cmd == 'alerts':
                    self.show_alerts()
                elif cmd == 'history':
                    self.show_history()
                elif cmd == 'config':
                    print(json.dumps(self.config, indent=2))
                elif cmd.startswith('export'):
                    parts = cmd.split(maxsplit=1)
                    filename = parts[1] if len(parts) > 1 else ""
                    if not filename:
                        filename = f"security_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    print(self.export_history(filename))
                elif cmd.startswith('run '):
                    command_key = cmd[4:].strip()
                    self.run_command(command_key)
                else:
                    print(f"❓ Unknown command: '{cmd}'. Type 'help' for available commands.")

            except KeyboardInterrupt:
                continue
            except EOFError:
                self._safe_exit()
            except Exception as e:
                self.logger.error(f"Unexpected error in main loop: {e}")
                print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    assistant = DefensiveCyberAssistant()
    assistant.run()