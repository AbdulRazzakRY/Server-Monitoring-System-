# Server Monitoring System - Complete Project

## Overview

This project provides a comprehensive server monitoring solution that tracks CPU, memory, and disk usage, sending alerts via email and Slack when thresholds are exceeded. The system can be scheduled using either cron or systemd timers and includes both Bash and Python implementations.

## 🚀 Features

### Core Monitoring
- **CPU Usage**: Real-time CPU percentage and load averages
- **Memory Usage**: RAM and swap monitoring with detailed statistics  
- **Disk Usage**: Multi-partition monitoring with I/O statistics
- **Temperature Monitoring**: Hardware temperature sensors (Python version)
- **Process Monitoring**: Top processes by CPU and memory usage
- **Network Connectivity**: Connectivity tests to external hosts

### Alert System
- **Email Notifications**: HTML-formatted email alerts with detailed system information
- **Slack Integration**: Rich message formatting with color-coded severity levels
- **Threshold Configuration**: Customizable alert thresholds for all metrics
- **Alert Rate Limiting**: Prevents alert spam with cooldown periods
- **Escalation Rules**: Multi-level alert escalation (configurable)

### Scheduling Options
- **Cron Jobs**: Traditional cron-based scheduling with flexible timing
- **Systemd Timers**: Modern systemd timer integration with advanced features
- **One-shot Mode**: Manual execution or triggered monitoring
- **Continuous Mode**: Daemon-style continuous monitoring (Python version)

### Advanced Features
- **Configuration Management**: YAML and shell-based configuration files
- **Logging System**: Comprehensive logging with rotation and levels
- **Historical Data**: Metrics history tracking and analysis
- **Security**: Principle of least privilege with systemd security features
- **Resource Limits**: Memory and CPU limits for the monitoring process

## 📂 Project Structure

```
server-monitoring-system/
├── scripts/
│   ├── bash/
│   │   └── monitor_system.sh      # Bash monitoring script
│   └── python/
│       ├── monitor_system.py      # Python monitoring script
│       ├── requirements.txt       # Python dependencies
│       └── config.yaml           # Python configuration
├── config/
│   ├── monitoring.conf           # Bash configuration
│   ├── email_template.html       # HTML email template
│   └── slack_config.json        # Slack configuration
├── systemd/
│   ├── server-monitor.service    # Systemd service file
│   ├── server-monitor.timer      # Systemd timer file
│   └── server-monitor-oneshot.service  # One-shot service
├── cron/
│   ├── crontab_examples         # Cron configuration examples
│   └── install_cron.sh          # Cron installation script
├── logs/                        # Log files directory
├── docs/
│   ├── README.md               # This file
│   ├── INSTALLATION.md         # Installation guide
│   ├── CONFIGURATION.md        # Configuration guide
│   └── TROUBLESHOOTING.md      # Troubleshooting guide
├── tests/
│   ├── test_monitor.py         # Python unit tests
│   └── test_alerts.py          # Alert system tests
└── utils/
    ├── install.sh              # Main installation script
    ├── setup_systemd.sh        # Systemd setup script
    └── setup_email.sh          # Email configuration script
```

## 🛠️ Installation

### Quick Start

1. **Clone or Download the Project**
   ```bash
   # Create project directory
   sudo mkdir -p /opt/server-monitoring
   sudo chown $USER:$USER /opt/server-monitoring
   cd /opt/server-monitoring
   
   # Copy all project files here
   ```

2. **Run the Installation Script**
   ```bash
   chmod +x utils/install.sh
   ./utils/install.sh
   ```

3. **Configure Monitoring**
   ```bash
   # Edit configuration files
   nano config/config.yaml        # Python configuration
   nano config/monitoring.conf    # Bash configuration
   ```

4. **Choose Scheduling Method**
   
   **Option A: Systemd Timer (Recommended)**
   ```bash
   ./utils/setup_systemd.sh
   ```
   
   **Option B: Cron Job**
   ```bash
   ./cron/install_cron.sh
   ```

### Manual Installation

#### Prerequisites

**For Bash Script:**
- bash 4.0+
- Standard Unix tools (awk, bc, df, free, top, uptime, ps)
- mail or sendmail (for email alerts)
- curl (for Slack alerts)

**For Python Script:**
- Python 3.7+
- pip package manager

#### Step-by-Step Installation

1. **Install System Dependencies**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install -y python3 python3-pip mailutils curl bc
   
   # CentOS/RHEL
   sudo yum install -y python3 python3-pip mailx curl bc
   
   # Arch Linux
   sudo pacman -S python python-pip mailutils curl bc
   ```

2. **Install Python Dependencies**
   ```bash
   cd scripts/python
   pip3 install -r requirements.txt
   ```

3. **Create Monitoring User**
   ```bash
   sudo useradd -r -s /bin/false -d /opt/server-monitoring monitor
   sudo chown -R monitor:monitor /opt/server-monitoring
   ```

4. **Set Permissions**
   ```bash
   chmod +x scripts/bash/monitor_system.sh
   chmod +x scripts/python/monitor_system.py
   chmod +x utils/*.sh
   chmod +x cron/install_cron.sh
   ```

## ⚙️ Configuration

### Python Configuration (config/config.yaml)

```yaml
# Monitoring thresholds
thresholds:
  cpu_percent: 80.0
  memory_percent: 85.0  
  disk_percent: 90.0
  load_average: 2.0
  temperature: 70.0

# Email settings
email:
  enabled: true
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  use_tls: true
  username: "your-email@gmail.com"
  password: "your-app-password"
  from_address: "monitor@yourserver.com"
  to_addresses:
    - "admin@company.com"

# Slack settings
slack:
  enabled: false
  webhook_url: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
  channel: "#monitoring"
```

### Bash Configuration (config/monitoring.conf)

```bash
# Thresholds
CPU_THRESHOLD=80
MEMORY_THRESHOLD=85
DISK_THRESHOLD=90

# Email settings
EMAIL_ENABLED=true
EMAIL_TO="admin@company.com"

# Slack settings
SLACK_ENABLED=false
SLACK_WEBHOOK_URL=""
```

### Email Configuration

**Gmail Setup:**
1. Enable 2-factor authentication
2. Generate an app password: https://support.google.com/accounts/answer/185833
3. Use the app password in configuration

**Other SMTP Providers:**
- **Outlook**: smtp-mail.outlook.com, port 587
- **Yahoo**: smtp.mail.yahoo.com, port 587
- **Custom SMTP**: Configure your organization's SMTP settings

### Slack Configuration

1. **Create Slack App:**
   - Go to https://api.slack.com/apps
   - Create new app "From scratch"
   - Choose your workspace

2. **Enable Incoming Webhooks:**
   - Navigate to "Incoming Webhooks" in app settings
   - Activate incoming webhooks
   - Click "Add New Webhook to Workspace"
   - Select channel and authorize

3. **Copy Webhook URL:**
   - Copy the generated webhook URL
   - Add to configuration files

## 🚀 Usage

### Python Script Usage

```bash
# Run once and exit
python3 scripts/python/monitor_system.py

# Run continuously (daemon mode)  
python3 scripts/python/monitor_system.py --continuous

# Test mode (no alerts sent)
python3 scripts/python/monitor_system.py --test

# Custom configuration file
python3 scripts/python/monitor_system.py --config /path/to/config.yaml

# Show status report
python3 scripts/python/monitor_system.py --status

# Verbose output
python3 scripts/python/monitor_system.py --verbose

# Quiet mode
python3 scripts/python/monitor_system.py --quiet
```

### Bash Script Usage

```bash
# Run with default settings
./scripts/bash/monitor_system.sh

# Verbose output
./scripts/bash/monitor_system.sh --verbose

# Quiet mode (only alerts)
./scripts/bash/monitor_system.sh --quiet

# Test mode (no alerts)
./scripts/bash/monitor_system.sh --test

# Custom configuration
./scripts/bash/monitor_system.sh --config /path/to/config.conf

# Check configuration
./scripts/bash/monitor_system.sh --check-config

# Show version
./scripts/bash/monitor_system.sh --version
```

## ⏰ Scheduling

### Systemd Timer Setup

1. **Install Service Files**
   ```bash
   sudo cp systemd/server-monitor.service /etc/systemd/system/
   sudo cp systemd/server-monitor.timer /etc/systemd/system/
   ```

2. **Configure and Start**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable server-monitor.timer
   sudo systemctl start server-monitor.timer
   ```

3. **Check Status**
   ```bash
   sudo systemctl status server-monitor.timer
   sudo systemctl list-timers
   ```

### Cron Job Setup

1. **Install Cron Jobs**
   ```bash
   # Automatic installation
   ./cron/install_cron.sh
   
   # Manual installation
   crontab -e
   # Add: */5 * * * * /opt/server-monitoring/scripts/python/monitor_system.py
   ```

2. **Common Cron Schedules**
   ```bash
   # Every 5 minutes
   */5 * * * * /path/to/monitor_system.py
   
   # Every 10 minutes during business hours
   */10 8-18 * * 1-5 /path/to/monitor_system.py
   
   # Hourly
   0 * * * * /path/to/monitor_system.py
   
   # Daily at 2 AM
   0 2 * * * /path/to/monitor_system.py
   ```

## 📊 Monitoring Thresholds

### Recommended Thresholds

| Metric | Warning | Critical | Notes |
|--------|---------|----------|-------|
| CPU Usage | 80% | 90% | Sustained high CPU usage |
| Memory Usage | 85% | 95% | Available RAM percentage |
| Disk Usage | 90% | 95% | Per filesystem/partition |
| Load Average | 2.0 | 4.0 | Per CPU core |
| Temperature | 70°C | 80°C | Hardware sensors |

### Custom Thresholds

Adjust thresholds based on your environment:

**High-Performance Servers:**
- CPU: 70% warning, 85% critical
- Memory: 80% warning, 90% critical

**Development Servers:**
- CPU: 85% warning, 95% critical  
- Memory: 90% warning, 95% critical

**Database Servers:**
- Memory: 75% warning, 85% critical
- Disk: 85% warning, 90% critical

## 🔧 Customization

### Adding Custom Checks

**Python Script:**
```python
def custom_check(self) -> Dict:
    """Add custom monitoring logic"""
    # Your custom check logic here
    return {'status': 'ok', 'message': 'Custom check passed'}
```

**Bash Script:**
```bash
custom_check() {
    # Your custom check logic here
    local result=$(your_command)
    if [[ $result != "expected" ]]; then
        send_alert "CUSTOM" "Custom check failed: $result"
        return 1
    fi
    return 0
}
```

### Adding New Alert Channels

1. **SMS Alerts (Twilio)**
2. **Push Notifications (Pushbullet)**
3. **Discord Webhooks**
4. **Microsoft Teams**
5. **Custom HTTP Endpoints**

### Integration with Monitoring Tools

- **Prometheus**: Export metrics in Prometheus format
- **Grafana**: Create dashboards for visualization
- **Zabbix**: Send metrics to Zabbix server
- **Nagios**: NRPE plugin integration

## 🚨 Alert Examples

### Email Alert
```
Subject: [SERVER ALERT] 2 alert(s) on web-server-01

🚨 Server Alert - web-server-01
================================

High CPU Alert: CPU usage is at 85.2% (threshold: 80.0%)
High Memory Alert: Memory usage is at 92.1% (threshold: 85.0%)

System Summary:
- CPU Usage: 85.2%
- Memory Usage: 92.1%  
- Disk Usage: 67.3%
- Load Average: 3.45
- Uptime: 15 days, 4 hours, 23 minutes
```

### Slack Alert
```
🚨 Server Alert - web-server-01

2 alert(s) detected

🔥 High CPU: CPU usage is at 85.2%
🧠 High Memory: Memory usage is at 92.1%

CPU Usage: 85.2%
Memory Usage: 92.1%
```

## 🔍 Troubleshooting

### Common Issues

**1. Email Not Sending**
- Check SMTP configuration
- Verify credentials and app passwords
- Test with: `echo "test" | mail -s "test" admin@company.com`

**2. Slack Not Working**
- Verify webhook URL
- Check network connectivity
- Test with: `curl -X POST -H 'Content-type: application/json' --data '{"text":"Hello"}' YOUR_WEBHOOK_URL`

**3. Permission Errors**
- Ensure scripts are executable: `chmod +x script.sh`
- Check file ownership: `chown monitor:monitor /opt/server-monitoring`
- Verify log directory permissions

**4. Systemd Service Issues**
- Check service status: `systemctl status server-monitor`
- View logs: `journalctl -u server-monitor -f`
- Reload configuration: `systemctl daemon-reload`

**5. Cron Jobs Not Running**
- Check cron service: `systemctl status cron`
- Verify crontab: `crontab -l`
- Check cron logs: `tail -f /var/log/syslog | grep CRON`

### Debug Mode

**Python:**
```bash
python3 monitor_system.py --verbose --test
```

**Bash:**
```bash
./monitor_system.sh --verbose --test
```

### Log Analysis

```bash
# Monitor logs in real-time
tail -f logs/monitor.log

# Search for errors
grep ERROR logs/monitor.log

# View alert history
cat logs/alerts.log
```

## 🔒 Security Considerations

### File Permissions
```bash
# Secure configuration files
chmod 600 config/config.yaml config/monitoring.conf
chown monitor:monitor config/*

# Secure scripts
chmod 755 scripts/bash/monitor_system.sh
chmod 755 scripts/python/monitor_system.py
```

### Systemd Security
The systemd service includes security hardening:
- `NoNewPrivileges=true`
- `PrivateTmp=true`
- `ProtectSystem=strict`
- `ProtectHome=true`
- Resource limits

### Network Security
- Use TLS for email (SMTP over TLS)
- Verify Slack webhook URLs
- Consider firewall rules for outbound connections
- Use encrypted configuration for sensitive data

## 📈 Performance

### Resource Usage
- **Python Script**: ~50-100MB RAM, <1% CPU
- **Bash Script**: ~10-20MB RAM, <0.5% CPU
- **Log Files**: Rotated at 10MB, 5 backups maintained

### Optimization Tips
1. **Adjust Monitoring Interval**: Balance between responsiveness and resource usage
2. **Limit Historical Data**: Configure `history_size` in Python version
3. **Use Quiet Mode**: Reduce log verbosity in production
4. **Process Filtering**: Monitor only critical processes

## 🧪 Testing

### Unit Tests (Python)
```bash
cd tests
python3 -m pytest test_monitor.py -v
python3 -m pytest test_alerts.py -v
```

### Manual Testing
```bash
# Test monitoring without alerts
./scripts/python/monitor_system.py --test

# Test specific alert channels
./scripts/python/monitor_system.py --test-email
./scripts/python/monitor_system.py --test-slack

# Simulate high resource usage
stress --cpu 4 --timeout 60s  # High CPU
stress --vm 1 --vm-bytes 1G --timeout 60s  # High memory
```

## 📚 Additional Resources

### Documentation
- [Installation Guide](INSTALLATION.md)
- [Configuration Guide](CONFIGURATION.md)  
- [Troubleshooting Guide](TROUBLESHOOTING.md)

### External Links
- [Systemd Timer Documentation](https://www.freedesktop.org/software/systemd/man/systemd.timer.html)
- [Cron Documentation](https://man7.org/linux/man-pages/man5/crontab.5.html)
- [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks)
- [Gmail App Passwords](https://support.google.com/accounts/answer/185833)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues, questions, or contributions:
- Create an issue in the project repository
- Contact: admin@company.com
- Documentation: [Project Wiki](wiki-url)

---

**Happy Monitoring! 🚀**