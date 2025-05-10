# Create configuration files

# Python requirements.txt
requirements_txt = '''# Server Monitoring System - Python Dependencies
# ===============================================

# System monitoring
psutil>=5.9.0

# Configuration management
PyYAML>=6.0

# HTTP requests for Slack notifications  
requests>=2.28.0

# Optional: Enhanced email capabilities
# email-validator>=1.3.0

# Optional: Database logging
# SQLAlchemy>=1.4.0
# sqlite3  # Built-in with Python

# Optional: Advanced alerting
# twilio>=7.0.0  # For SMS alerts
# pushbullet.py>=0.12.0  # For push notifications

# Development dependencies (optional)
# pytest>=7.0.0
# black>=22.0.0
# flake8>=5.0.0
# mypy>=0.991
'''

# YAML configuration file
config_yaml = '''# Server Monitoring System Configuration
# =====================================

# Monitoring thresholds (percentages)
thresholds:
  cpu_percent: 80.0          # CPU usage threshold
  memory_percent: 85.0       # Memory usage threshold  
  disk_percent: 90.0         # Disk usage threshold
  load_average: 2.0          # Load average threshold
  temperature: 70.0          # Temperature threshold (Celsius)

# Monitoring settings
monitoring:
  interval: 300              # Check interval in seconds (5 minutes)
  check_network: true        # Enable network connectivity checks
  check_processes: true      # Enable process monitoring
  check_temperature: true    # Enable temperature monitoring
  history_size: 1000         # Number of historical records to keep

# Email notification settings
email:
  enabled: true
  smtp_server: "smtp.gmail.com"     # SMTP server
  smtp_port: 587                    # SMTP port
  use_tls: true                     # Use TLS encryption
  username: "your-email@gmail.com"  # SMTP username
  password: "your-app-password"     # SMTP password (use app password for Gmail)
  from_address: "monitor@yourserver.com"
  to_addresses:                     # List of recipient emails
    - "admin@company.com"
    - "ops-team@company.com"
  subject_prefix: "[SERVER ALERT]"

# Slack notification settings  
slack:
  enabled: false
  webhook_url: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
  channel: "#monitoring"
  username: "ServerBot"
  icon_emoji: ":warning:"

# Logging configuration
logging:
  level: "INFO"                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
  file: "monitor.log"              # Log file name (relative to logs/ directory)
  max_bytes: 10485760             # 10MB max log file size
  backup_count: 5                 # Number of backup log files
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Advanced settings (optional)
advanced:
  # Custom commands to run for additional checks
  custom_checks:
    - name: "disk_smart"
      command: "smartctl -H /dev/sda"
      enabled: false
    - name: "service_status"  
      command: "systemctl is-active nginx"
      enabled: false
  
  # Process monitoring whitelist/blacklist
  process_monitoring:
    high_cpu_threshold: 50.0      # Alert if process uses > 50% CPU
    high_memory_threshold: 20.0   # Alert if process uses > 20% memory
    monitor_specific_processes:   # Monitor these processes specifically
      - "nginx"
      - "mysql"
      - "postgresql"
      - "redis"
    
  # Network monitoring
  network_monitoring:
    test_hosts:                   # Hosts to test connectivity
      - "8.8.8.8"
      - "1.1.1.1"  
      - "google.com"
    timeout: 5                    # Ping timeout in seconds
    
  # Disk monitoring
  disk_monitoring:
    ignore_filesystems:           # Ignore these filesystem types
      - "tmpfs"
      - "devtmpfs"
      - "proc"
      - "sysfs"
    ignore_mountpoints:           # Ignore these mount points
      - "/dev/shm"
      - "/run"
      - "/sys/fs/cgroup"
'''

# Bash configuration file
monitoring_conf = '''#!/bin/bash
# Server Monitoring Configuration File
# ====================================

# Monitoring Thresholds
CPU_THRESHOLD=80
MEMORY_THRESHOLD=85
DISK_THRESHOLD=90
LOAD_THRESHOLD=2.0

# Email Configuration
EMAIL_ENABLED=true
SMTP_SERVER="localhost"
EMAIL_FROM="monitor@$(hostname)"
EMAIL_TO="admin@company.com"
EMAIL_SUBJECT_PREFIX="[SERVER ALERT]"

# Slack Configuration
SLACK_ENABLED=false
SLACK_WEBHOOK_URL=""
SLACK_CHANNEL="#monitoring"
SLACK_USERNAME="ServerBot"

# Logging Configuration
LOG_LEVEL="INFO"
LOG_RETENTION_DAYS=30

# Network Configuration
NETWORK_CHECK_ENABLED=true
NETWORK_TEST_HOSTS=("8.8.8.8" "1.1.1.1" "google.com")

# Advanced Settings
ALERT_COOLDOWN=300    # 5 minutes between duplicate alerts
MAX_ALERTS_PER_HOUR=10
ENABLE_PROCESS_MONITORING=true
ENABLE_TEMPERATURE_MONITORING=true

# Custom thresholds for specific mount points
# Format: MOUNTPOINT_THRESHOLD_<mount_point_safe_name>=percentage
MOUNTPOINT_THRESHOLD_ROOT=90        # /
MOUNTPOINT_THRESHOLD_HOME=85        # /home
MOUNTPOINT_THRESHOLD_VAR=95         # /var

# Process monitoring
HIGH_CPU_PROCESS_THRESHOLD=50
HIGH_MEMORY_PROCESS_THRESHOLD=20

# Service monitoring (optional)
SERVICES_TO_MONITOR=("nginx" "mysql" "postgresql" "redis-server")

# Notification preferences
SEND_SUMMARY_REPORTS=true
SUMMARY_REPORT_INTERVAL=3600  # 1 hour
SEND_OK_NOTIFICATIONS=false   # Send notifications when alerts clear

# System information to include in alerts
INCLUDE_SYSTEM_INFO=true
INCLUDE_TOP_PROCESSES=true
INCLUDE_DISK_IO_STATS=false
INCLUDE_NETWORK_STATS=false
'''

# Slack configuration JSON
slack_config_json = '''{
  "slack": {
    "webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
    "channel": "#monitoring",
    "username": "ServerBot",
    "icon_emoji": ":warning:",
    "enabled": false,
    "message_templates": {
      "high_cpu": "🔥 High CPU Alert: {value}% on {hostname}",
      "high_memory": "🧠 High Memory Alert: {value}% on {hostname}",
      "high_disk": "💾 High Disk Usage: {value}% on {mountpoint} ({hostname})",
      "high_load": "📊 High Load Average: {value} on {hostname}",
      "network_issue": "🌐 Network connectivity issues on {hostname}",
      "service_down": "🚫 Service {service} is down on {hostname}",
      "temperature_high": "🌡️ High temperature: {value}°C on {sensor} ({hostname})"
    },
    "color_scheme": {
      "critical": "#ff0000",
      "warning": "#ff9900", 
      "info": "#0099ff",
      "success": "#00ff00"
    }
  },
  "notification_rules": {
    "rate_limiting": {
      "enabled": true,
      "max_alerts_per_hour": 10,
      "cooldown_period": 300
    },
    "escalation": {
      "enabled": false,
      "levels": [
        {
          "threshold_minutes": 5,
          "channels": ["#monitoring"]
        },
        {
          "threshold_minutes": 15,
          "channels": ["#monitoring", "#critical-alerts"]
        },
        {
          "threshold_minutes": 30,
          "channels": ["#monitoring", "#critical-alerts"],
          "mention_users": ["@admin", "@ops-team"]
        }
      ]
    }
  }
}'''

# Email template HTML
email_template_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Server Alert</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }
        .header.critical {
            background: linear-gradient(135deg, #ff4757 0%, #c44569 100%);
        }
        .header.warning {
            background: linear-gradient(135deg, #ffa726 0%, #ff7043 100%);
        }
        .header h1 {
            margin: 0;
            font-size: 28px;
            font-weight: 300;
        }
        .header .hostname {
            font-size: 18px;
            opacity: 0.9;
            margin-top: 5px;
        }
        .content {
            padding: 30px;
        }
        .alert-summary {
            background-color: #f8f9fa;
            border-left: 4px solid #007bff;
            padding: 15px 20px;
            margin: 20px 0;
            border-radius: 0 4px 4px 0;
        }
        .alert-summary.critical {
            border-left-color: #dc3545;
            background-color: #f8d7da;
        }
        .alert-summary.warning {
            border-left-color: #ffc107;
            background-color: #fff3cd;
        }
        .alert-item {
            background-color: white;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 15px;
            margin: 10px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .alert-type {
            font-weight: bold;
            color: #495057;
            text-transform: uppercase;
            font-size: 12px;
            margin-bottom: 5px;
        }
        .alert-message {
            font-size: 16px;
            color: #212529;
            margin-bottom: 8px;
        }
        .alert-details {
            font-size: 14px;
            color: #6c757d;
        }
        .metrics-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background-color: white;
            border-radius: 6px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .metrics-table th {
            background-color: #495057;
            color: white;
            padding: 12px 15px;
            text-align: left;
            font-weight: 500;
        }
        .metrics-table td {
            padding: 12px 15px;
            border-bottom: 1px solid #e9ecef;
        }
        .metrics-table tr:last-child td {
            border-bottom: none;
        }
        .metric-value {
            font-weight: bold;
        }
        .metric-good { color: #28a745; }
        .metric-warning { color: #ffc107; }
        .metric-critical { color: #dc3545; }
        .footer {
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            font-size: 14px;
            color: #6c757d;
            border-top: 1px solid #e9ecef;
        }
        .timestamp {
            font-family: 'Courier New', monospace;
            background-color: #e9ecef;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 12px;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-good { background-color: #28a745; }
        .status-warning { background-color: #ffc107; }
        .status-critical { background-color: #dc3545; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header {{SEVERITY_CLASS}}">
            <h1>🚨 Server Alert</h1>
            <div class="hostname">{{HOSTNAME}}</div>
            <div class="timestamp">{{TIMESTAMP}}</div>
        </div>
        
        <div class="content">
            <div class="alert-summary {{SEVERITY_CLASS}}">
                <h3>Alert Summary</h3>
                <p><strong>{{ALERT_COUNT}} alert(s)</strong> detected on your server.</p>
            </div>
            
            <h3>Active Alerts</h3>
            {{ALERTS_HTML}}
            
            <h3>System Metrics</h3>
            <table class="metrics-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Current Value</th>
                        <th>Threshold</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {{METRICS_HTML}}
                </tbody>
            </table>
            
            <h3>System Information</h3>
            <table class="metrics-table">
                <tbody>
                    <tr>
                        <td><strong>Hostname</strong></td>
                        <td>{{HOSTNAME}}</td>
                    </tr>
                    <tr>
                        <td><strong>Uptime</strong></td>
                        <td>{{UPTIME}}</td>
                    </tr>
                    <tr>
                        <td><strong>Load Average</strong></td>
                        <td>{{LOAD_AVERAGE}}</td>
                    </tr>
                    <tr>
                        <td><strong>Total Processes</strong></td>
                        <td>{{PROCESS_COUNT}}</td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>This alert was generated by the Server Monitoring System.</p>
            <p>To stop receiving these alerts, please contact your system administrator.</p>
        </div>
    </div>
</body>
</html>'''

print("✅ Created configuration files:")
print("📄 requirements.txt - Python dependencies")
print("📄 config.yaml - YAML configuration") 
print("📄 monitoring.conf - Bash configuration")
print("📄 slack_config.json - Slack configuration")
print("📄 email_template.html - HTML email template")

# Save configuration files
config_files = {
    'requirements.txt': requirements_txt,
    'config.yaml': config_yaml,
    'monitoring.conf': monitoring_conf,
    'slack_config.json': slack_config_json,
    'email_template.html': email_template_html
}

for filename, content in config_files.items():
    with open(filename, 'w') as f:
        f.write(content)
    print(f"💾 Saved: {filename}")

print(f"\n📊 Total configuration files: {len(config_files)}")
print("🔧 Ready for deployment and customization!")