# Create comprehensive Python monitoring script

python_monitor_script = '''#!/usr/bin/env python3
"""
===============================================================
Server Monitoring Script (Python Version)
===============================================================
Description: Advanced server monitoring with CPU, Memory, Disk usage tracking
Author: System Administrator  
Version: 2.0
Dependencies: psutil, pyyaml, requests
===============================================================
"""

import os
import sys
import time
import json
import logging
import argparse
import smtplib
import subprocess
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

try:
    import psutil
    import yaml
    import requests
except ImportError as e:
    print(f"❌ Missing required dependency: {e}")
    print("🔧 Install with: pip install -r requirements.txt")
    sys.exit(1)

# ===============================================================
# Configuration and Constants
# ===============================================================

class Config:
    """Configuration management class"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.script_dir = Path(__file__).parent.absolute()
        self.project_root = self.script_dir.parent.parent
        
        # Default configuration
        self.defaults = {
            'thresholds': {
                'cpu_percent': 80.0,
                'memory_percent': 85.0,
                'disk_percent': 90.0,
                'load_average': 2.0,
                'temperature': 70.0  # Celsius
            },
            'monitoring': {
                'interval': 300,  # 5 minutes
                'check_network': True,
                'check_processes': True,
                'check_temperature': True,
                'history_size': 1000
            },
            'email': {
                'enabled': True,
                'smtp_server': 'localhost',
                'smtp_port': 587,
                'use_tls': True,
                'username': '',
                'password': '',
                'from_address': 'monitor@localhost',
                'to_addresses': ['admin@company.com'],
                'subject_prefix': '[SERVER ALERT]'
            },
            'slack': {
                'enabled': False,
                'webhook_url': '',
                'channel': '#monitoring',
                'username': 'ServerBot',
                'icon_emoji': ':warning:'
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/monitor.log',
                'max_bytes': 10485760,  # 10MB
                'backup_count': 5,
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        }
        
        # Load configuration
        config_path = config_file or self.project_root / 'config' / 'config.yaml'
        self.config = self.load_config(config_path)
        
    def load_config(self, config_path: Path) -> Dict:
        """Load configuration from YAML file"""
        try:
            if config_path.exists():
                with open(config_path, 'r') as f:
                    user_config = yaml.safe_load(f) or {}
                
                # Merge with defaults
                config = self.defaults.copy()
                self._deep_update(config, user_config)
                return config
            else:
                logging.warning(f"Config file not found: {config_path}. Using defaults.")
                return self.defaults
                
        except Exception as e:
            logging.error(f"Error loading config: {e}. Using defaults.")
            return self.defaults
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict) -> None:
        """Recursively update nested dictionaries"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def get(self, *keys) -> Any:
        """Get nested configuration value"""
        result = self.config
        for key in keys:
            result = result.get(key, {})
        return result

# ===============================================================
# Logging Setup
# ===============================================================

def setup_logging(config: Config) -> logging.Logger:
    """Configure logging system"""
    
    log_config = config.get('logging')
    log_dir = config.project_root / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / log_config.get('file', 'monitor.log')
    
    # Create rotating file handler
    from logging.handlers import RotatingFileHandler
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=log_config.get('max_bytes', 10485760),
        backupCount=log_config.get('backup_count', 5)
    )
    
    # Create console handler
    console_handler = logging.StreamHandler()
    
    # Create formatter
    formatter = logging.Formatter(log_config.get('format'))
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Configure logger
    logger = logging.getLogger('ServerMonitor')
    logger.setLevel(getattr(logging, log_config.get('level', 'INFO')))
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# ===============================================================
# System Monitoring Classes
# ===============================================================

class SystemMonitor:
    """Main system monitoring class"""
    
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.hostname = os.uname().nodename
        self.start_time = datetime.now()
        self.history: List[Dict] = []
        
        # Initialize notification handlers
        self.email_handler = EmailNotifier(config, logger) if config.get('email', 'enabled') else None
        self.slack_handler = SlackNotifier(config, logger) if config.get('slack', 'enabled') else None
        
    def get_cpu_info(self) -> Dict:
        """Get detailed CPU information"""
        try:
            # Get CPU percentages per core and overall
            cpu_percent = psutil.cpu_percent(interval=1, percpu=False)
            cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
            
            # Get CPU frequency
            cpu_freq = psutil.cpu_freq()
            freq_current = cpu_freq.current if cpu_freq else 0
            freq_max = cpu_freq.max if cpu_freq else 0
            
            # Get load averages
            load_avg = os.getloadavg()
            
            # Get CPU count
            cpu_count = psutil.cpu_count()
            cpu_count_logical = psutil.cpu_count(logical=True)
            
            return {
                'percent': round(cpu_percent, 1),
                'per_core': [round(core, 1) for core in cpu_per_core],
                'load_average': {
                    '1min': round(load_avg[0], 2),
                    '5min': round(load_avg[1], 2), 
                    '15min': round(load_avg[2], 2)
                },
                'frequency': {
                    'current': round(freq_current, 1) if freq_current else 0,
                    'max': round(freq_max, 1) if freq_max else 0
                },
                'count': {
                    'physical': cpu_count,
                    'logical': cpu_count_logical
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting CPU info: {e}")
            return {'percent': 0, 'error': str(e)}
    
    def get_memory_info(self) -> Dict:
        """Get detailed memory information"""
        try:
            # Virtual memory
            mem = psutil.virtual_memory()
            
            # Swap memory
            swap = psutil.swap_memory()
            
            return {
                'virtual': {
                    'total': mem.total,
                    'available': mem.available,
                    'used': mem.used,
                    'free': mem.free,
                    'percent': round(mem.percent, 1),
                    'cached': getattr(mem, 'cached', 0),
                    'buffers': getattr(mem, 'buffers', 0)
                },
                'swap': {
                    'total': swap.total,
                    'used': swap.used,
                    'free': swap.free,
                    'percent': round(swap.percent, 1) if swap.total > 0 else 0
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting memory info: {e}")
            return {'virtual': {'percent': 0}, 'error': str(e)}
    
    def get_disk_info(self) -> Dict:
        """Get detailed disk information"""
        try:
            disk_info = {}
            
            # Get disk usage for all mounted filesystems
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    
                    disk_info[partition.mountpoint] = {
                        'device': partition.device,
                        'fstype': partition.fstype,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': round((usage.used / usage.total) * 100, 1) if usage.total > 0 else 0
                    }
                except (PermissionError, OSError):
                    continue
            
            # Get disk I/O statistics
            try:
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    disk_info['io'] = {
                        'read_bytes': disk_io.read_bytes,
                        'write_bytes': disk_io.write_bytes,
                        'read_count': disk_io.read_count,
                        'write_count': disk_io.write_count
                    }
            except Exception:
                pass
            
            return disk_info
        except Exception as e:
            self.logger.error(f"Error getting disk info: {e}")
            return {'error': str(e)}
    
    def get_network_info(self) -> Dict:
        """Get network information"""
        try:
            network_info = {}
            
            # Network I/O statistics
            net_io = psutil.net_io_counters()
            if net_io:
                network_info['io'] = {
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv,
                    'errin': net_io.errin,
                    'errout': net_io.errout,
                    'dropin': net_io.dropin,
                    'dropout': net_io.dropout
                }
            
            # Network connections
            connections = psutil.net_connections()
            network_info['connections'] = {
                'established': len([c for c in connections if c.status == 'ESTABLISHED']),
                'listen': len([c for c in connections if c.status == 'LISTEN']),
                'total': len(connections)
            }
            
            return network_info
        except Exception as e:
            self.logger.error(f"Error getting network info: {e}")
            return {'error': str(e)}
    
    def get_process_info(self) -> Dict:
        """Get process information"""
        try:
            processes = []
            
            # Get top processes by CPU and memory
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'username']):
                try:
                    proc_info = proc.info
                    if proc_info['cpu_percent'] > 0 or proc_info['memory_percent'] > 1:
                        processes.append({
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'cpu_percent': round(proc_info['cpu_percent'], 1),
                            'memory_percent': round(proc_info['memory_percent'], 1),
                            'username': proc_info['username']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            return {
                'total': len(psutil.pids()),
                'top_cpu': processes[:10],
                'top_memory': sorted(processes, key=lambda x: x['memory_percent'], reverse=True)[:10]
            }
        except Exception as e:
            self.logger.error(f"Error getting process info: {e}")
            return {'error': str(e)}
    
    def get_temperature_info(self) -> Dict:
        """Get temperature information"""
        try:
            temperatures = {}
            
            if hasattr(psutil, 'sensors_temperatures'):
                temps = psutil.sensors_temperatures()
                for name, entries in temps.items():
                    temperatures[name] = []
                    for entry in entries:
                        temp_info = {
                            'label': entry.label or 'N/A',
                            'current': entry.current,
                            'high': entry.high,
                            'critical': entry.critical
                        }
                        temperatures[name].append(temp_info)
            
            return temperatures
        except Exception as e:
            self.logger.error(f"Error getting temperature info: {e}")
            return {'error': str(e)}
    
    def test_network_connectivity(self) -> Dict:
        """Test network connectivity"""
        test_hosts = ['8.8.8.8', '1.1.1.1', 'google.com']
        results = {}
        
        for host in test_hosts:
            try:
                start_time = time.time()
                response = os.system(f"ping -c 1 -W 2 {host} >/dev/null 2>&1")
                end_time = time.time()
                
                results[host] = {
                    'reachable': response == 0,
                    'response_time': round((end_time - start_time) * 1000, 2) if response == 0 else None
                }
            except Exception as e:
                results[host] = {'reachable': False, 'error': str(e)}
        
        return results
    
    def collect_metrics(self) -> Dict:
        """Collect all system metrics"""
        timestamp = datetime.now()
        
        metrics = {
            'timestamp': timestamp.isoformat(),
            'hostname': self.hostname,
            'uptime': str(datetime.now() - self.start_time),
            'cpu': self.get_cpu_info(),
            'memory': self.get_memory_info(),
            'disk': self.get_disk_info(),
            'network': self.get_network_info()
        }
        
        # Optional checks based on configuration
        if self.config.get('monitoring', 'check_processes'):
            metrics['processes'] = self.get_process_info()
            
        if self.config.get('monitoring', 'check_temperature'):
            metrics['temperature'] = self.get_temperature_info()
            
        if self.config.get('monitoring', 'check_network'):
            metrics['connectivity'] = self.test_network_connectivity()
        
        return metrics
    
    def check_thresholds(self, metrics: Dict) -> List[Dict]:
        """Check if metrics exceed configured thresholds"""
        alerts = []
        thresholds = self.config.get('thresholds')
        
        # CPU threshold
        cpu_percent = metrics.get('cpu', {}).get('percent', 0)
        if cpu_percent > thresholds.get('cpu_percent', 80):
            alerts.append({
                'type': 'cpu_high',
                'severity': 'critical' if cpu_percent > 90 else 'warning',
                'message': f"High CPU usage: {cpu_percent}%",
                'value': cpu_percent,
                'threshold': thresholds.get('cpu_percent')
            })
        
        # Memory threshold
        memory_percent = metrics.get('memory', {}).get('virtual', {}).get('percent', 0)
        if memory_percent > thresholds.get('memory_percent', 85):
            alerts.append({
                'type': 'memory_high',
                'severity': 'critical' if memory_percent > 95 else 'warning',
                'message': f"High memory usage: {memory_percent}%",
                'value': memory_percent,
                'threshold': thresholds.get('memory_percent')
            })
        
        # Disk thresholds
        disk_info = metrics.get('disk', {})
        for mountpoint, info in disk_info.items():
            if isinstance(info, dict) and 'percent' in info:
                disk_percent = info['percent']
                if disk_percent > thresholds.get('disk_percent', 90):
                    alerts.append({
                        'type': 'disk_high',
                        'severity': 'critical' if disk_percent > 95 else 'warning',
                        'message': f"High disk usage on {mountpoint}: {disk_percent}%",
                        'value': disk_percent,
                        'threshold': thresholds.get('disk_percent'),
                        'mountpoint': mountpoint
                    })
        
        # Load average threshold  
        load_1min = metrics.get('cpu', {}).get('load_average', {}).get('1min', 0)
        if load_1min > thresholds.get('load_average', 2.0):
            alerts.append({
                'type': 'load_high',
                'severity': 'warning',
                'message': f"High load average: {load_1min}",
                'value': load_1min,
                'threshold': thresholds.get('load_average')
            })
        
        # Temperature thresholds
        temp_info = metrics.get('temperature', {})
        for sensor_name, sensors in temp_info.items():
            if isinstance(sensors, list):
                for sensor in sensors:
                    if isinstance(sensor, dict) and 'current' in sensor:
                        temp = sensor['current']
                        if temp > thresholds.get('temperature', 70):
                            alerts.append({
                                'type': 'temperature_high',
                                'severity': 'critical' if temp > 80 else 'warning',
                                'message': f"High temperature on {sensor_name}: {temp}°C",
                                'value': temp,
                                'threshold': thresholds.get('temperature')
                            })
        
        # Network connectivity
        connectivity = metrics.get('connectivity', {})
        unreachable_hosts = [host for host, info in connectivity.items() if not info.get('reachable', True)]
        if unreachable_hosts:
            alerts.append({
                'type': 'network_connectivity',
                'severity': 'warning',
                'message': f"Network connectivity issues: {', '.join(unreachable_hosts)}",
                'hosts': unreachable_hosts
            })
        
        return alerts

# ===============================================================
# Notification Classes
# ===============================================================

class EmailNotifier:
    """Email notification handler"""
    
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config.get('email')
        self.logger = logger
    
    def send_alert(self, alerts: List[Dict], metrics: Dict) -> bool:
        """Send email alert"""
        try:
            if not self.config.get('enabled', False):
                return True
            
            # Create email content
            subject = f"{self.config.get('subject_prefix', '[ALERT]')} {len(alerts)} alert(s) on {metrics['hostname']}"
            
            body = self._create_email_body(alerts, metrics)
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.config.get('from_address', 'monitor@localhost')
            msg['To'] = ', '.join(self.config.get('to_addresses', []))
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.config.get('smtp_server'), self.config.get('smtp_port', 587)) as server:
                if self.config.get('use_tls', True):
                    server.starttls()
                
                username = self.config.get('username')
                password = self.config.get('password')
                if username and password:
                    server.login(username, password)
                
                server.send_message(msg)
            
            self.logger.info(f"Email alert sent successfully to {msg['To']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
            return False
    
    def _create_email_body(self, alerts: List[Dict], metrics: Dict) -> str:
        """Create HTML email body"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f44336; color: white; padding: 10px; border-radius: 5px; }}
                .alert {{ margin: 10px 0; padding: 10px; border-left: 4px solid #f44336; background-color: #ffebee; }}
                .warning {{ border-left-color: #ff9800; background-color: #fff3e0; }}
                .info {{ border-left-color: #2196f3; background-color: #e3f2fd; }}
                table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🚨 Server Alert - {metrics['hostname']}</h2>
                <p>Timestamp: {metrics['timestamp']}</p>
            </div>
            
            <h3>Alerts ({len(alerts)})</h3>
        """
        
        for alert in alerts:
            severity_class = alert.get('severity', 'warning')
            html += f"""
            <div class="alert {severity_class}">
                <strong>{alert['type'].upper()}:</strong> {alert['message']}
            </div>
            """
        
        html += f"""
            <h3>System Summary</h3>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>CPU Usage</td><td>{metrics.get('cpu', {}).get('percent', 'N/A')}%</td></tr>
                <tr><td>Memory Usage</td><td>{metrics.get('memory', {}).get('virtual', {}).get('percent', 'N/A')}%</td></tr>
                <tr><td>Load Average (1min)</td><td>{metrics.get('cpu', {}).get('load_average', {}).get('1min', 'N/A')}</td></tr>
                <tr><td>Uptime</td><td>{metrics.get('uptime', 'N/A')}</td></tr>
            </table>
        </body>
        </html>
        """
        
        return html

class SlackNotifier:
    """Slack notification handler"""
    
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config.get('slack')
        self.logger = logger
    
    def send_alert(self, alerts: List[Dict], metrics: Dict) -> bool:
        """Send Slack alert"""
        try:
            if not self.config.get('enabled', False) or not self.config.get('webhook_url'):
                return True
            
            # Create Slack payload
            payload = {
                'username': self.config.get('username', 'ServerBot'),
                'icon_emoji': self.config.get('icon_emoji', ':warning:'),
                'channel': self.config.get('channel', '#monitoring'),
                'attachments': [self._create_attachment(alerts, metrics)]
            }
            
            # Send to Slack
            response = requests.post(
                self.config.get('webhook_url'),
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("Slack alert sent successfully")
                return True
            else:
                self.logger.error(f"Slack alert failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send Slack alert: {e}")
            return False
    
    def _create_attachment(self, alerts: List[Dict], metrics: Dict) -> Dict:
        """Create Slack attachment"""
        severity_colors = {
            'critical': '#f44336',
            'warning': '#ff9800', 
            'info': '#2196f3'
        }
        
        # Determine overall severity
        overall_severity = 'info'
        if any(alert.get('severity') == 'critical' for alert in alerts):
            overall_severity = 'critical'
        elif any(alert.get('severity') == 'warning' for alert in alerts):
            overall_severity = 'warning'
        
        # Create fields
        fields = []
        for alert in alerts[:5]:  # Limit to 5 alerts
            fields.append({
                'title': alert['type'].replace('_', ' ').title(),
                'value': alert['message'],
                'short': True
            })
        
        # Add summary fields
        fields.extend([
            {
                'title': 'CPU Usage',
                'value': f"{metrics.get('cpu', {}).get('percent', 'N/A')}%",
                'short': True
            },
            {
                'title': 'Memory Usage', 
                'value': f"{metrics.get('memory', {}).get('virtual', {}).get('percent', 'N/A')}%",
                'short': True
            }
        ])
        
        return {
            'color': severity_colors.get(overall_severity, '#2196f3'),
            'title': f'🚨 Server Alert - {metrics["hostname"]}',
            'text': f'{len(alerts)} alert(s) detected',
            'fields': fields,
            'footer': 'Server Monitoring System',
            'ts': int(time.time())
        }

# ===============================================================
# Main Application Class
# ===============================================================

class ServerMonitorApp:
    """Main application class"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config = Config(config_file)
        self.logger = setup_logging(self.config)
        self.monitor = SystemMonitor(self.config, self.logger)
        self.running = False
    
    def run_once(self, send_alerts: bool = True) -> Dict:
        """Run monitoring once and return results"""
        self.logger.info("Starting monitoring check...")
        
        # Collect metrics
        metrics = self.monitor.collect_metrics()
        
        # Check thresholds
        alerts = self.monitor.check_thresholds(metrics)
        
        # Send alerts if any found
        if alerts and send_alerts:
            self.logger.warning(f"Found {len(alerts)} alert(s)")
            
            # Send email alerts
            if self.monitor.email_handler:
                self.monitor.email_handler.send_alert(alerts, metrics)
            
            # Send Slack alerts
            if self.monitor.slack_handler:
                self.monitor.slack_handler.send_alert(alerts, metrics)
        
        # Add to history
        result = {
            'metrics': metrics,
            'alerts': alerts,
            'alert_count': len(alerts)
        }
        
        self.monitor.history.append(result)
        
        # Limit history size
        max_history = self.config.get('monitoring', 'history_size')
        if len(self.monitor.history) > max_history:
            self.monitor.history = self.monitor.history[-max_history:]
        
        self.logger.info(f"Monitoring check completed. Alerts: {len(alerts)}")
        return result
    
    def run_continuous(self) -> None:
        """Run monitoring continuously"""
        interval = self.config.get('monitoring', 'interval')
        self.logger.info(f"Starting continuous monitoring (interval: {interval}s)")
        
        self.running = True
        try:
            while self.running:
                self.run_once()
                time.sleep(interval)
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Monitoring error: {e}")
        finally:
            self.running = False
    
    def stop(self) -> None:
        """Stop monitoring"""
        self.running = False
    
    def get_status_report(self) -> str:
        """Get formatted status report"""
        if not self.monitor.history:
            return "No monitoring data available"
        
        latest = self.monitor.history[-1]
        metrics = latest['metrics']
        alerts = latest['alerts']
        
        report = f"""
🖥️  Server Status Report - {metrics['hostname']}
{'='*50}
📅 Timestamp: {metrics['timestamp']}
⏰ Uptime: {metrics['uptime']}

📊 System Resources:
  🔥 CPU Usage: {metrics.get('cpu', {}).get('percent', 'N/A')}%
  🧠 Memory Usage: {metrics.get('memory', {}).get('virtual', {}).get('percent', 'N/A')}%
  💾 Swap Usage: {metrics.get('memory', {}).get('swap', {}).get('percent', 'N/A')}%
  📊 Load Average: {metrics.get('cpu', {}).get('load_average', {}).get('1min', 'N/A')}

💿 Disk Usage:
"""
        
        # Add disk information
        disk_info = metrics.get('disk', {})
        for mountpoint, info in disk_info.items():
            if isinstance(info, dict) and 'percent' in info:
                report += f"  📁 {mountpoint}: {info['percent']}% ({info.get('fstype', 'unknown')})\n"
        
        # Add alerts
        if alerts:
            report += f"\n🚨 Active Alerts ({len(alerts)}):\n"
            for alert in alerts:
                severity_emoji = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(alert.get('severity', 'info'), '⚪')
                report += f"  {severity_emoji} {alert['message']}\n"
        else:
            report += "\n✅ No active alerts\n"
        
        return report

# ===============================================================
# Command Line Interface
# ===============================================================

def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description='Advanced Server Monitoring System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Run once and exit
  %(prog)s --continuous             # Run continuously  
  %(prog)s --test                   # Test mode (no alerts)
  %(prog)s --config custom.yaml     # Use custom config
  %(prog)s --status                 # Show status report
        """
    )
    
    parser.add_argument(
        '-c', '--config',
        type=str,
        help='Configuration file path'
    )
    
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run continuously (daemon mode)'
    )
    
    parser.add_argument(
        '--test',
        action='store_true', 
        help='Test mode - no alerts sent'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show status report and exit'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Quiet mode - minimal output'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Server Monitor 2.0'
    )
    
    return parser

def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        # Create application
        app = ServerMonitorApp(args.config)
        
        # Adjust logging level based on arguments
        if args.verbose:
            app.logger.setLevel(logging.DEBUG)
        elif args.quiet:
            app.logger.setLevel(logging.WARNING)
        
        # Handle different run modes
        if args.status:
            # Show status report
            print(app.get_status_report())
            
        elif args.continuous:
            # Run continuously
            try:
                app.run_continuous()
            except KeyboardInterrupt:
                print("\n👋 Monitoring stopped")
                
        else:
            # Run once
            send_alerts = not args.test
            if args.test:
                app.logger.info("Running in test mode - alerts disabled")
            
            result = app.run_once(send_alerts)
            
            if not args.quiet:
                print(app.get_status_report())
            
            # Exit with error code if alerts found
            sys.exit(1 if result['alert_count'] > 0 else 0)
            
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
'''

print("✅ Created advanced Python monitoring script")
print(f"📊 Script length: {len(python_monitor_script)} characters")
print("🔧 Advanced features included:")
print("  - Object-oriented design")
print("  - YAML configuration") 
print("  - Comprehensive system metrics")
print("  - Email and Slack notifications")
print("  - Logging with rotation")
print("  - Command-line interface")
print("  - Continuous and one-shot modes")
print("  - Temperature monitoring")
print("  - Process monitoring") 
print("  - Network connectivity tests")
print("  - Historical data tracking")

# Save the script
with open('python_monitor_system.py', 'w') as f:
    f.write(python_monitor_script)

print("\n💾 Saved to: python_monitor_system.py")