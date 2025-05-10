# Create project structure for server monitoring system

import os

# Define the project structure
project_structure = {
    "server-monitoring-system/": {
        "scripts/": [
            "bash/monitor_system.sh",
            "python/monitor_system.py", 
            "python/requirements.txt",
            "python/config.yaml"
        ],
        "config/": [
            "monitoring.conf",
            "email_template.html",
            "slack_config.json"
        ],
        "systemd/": [
            "server-monitor.service",
            "server-monitor.timer"
        ],
        "cron/": [
            "crontab_examples",
            "install_cron.sh"
        ],
        "logs/": [
            ".gitkeep"
        ],
        "docs/": [
            "README.md",
            "INSTALLATION.md", 
            "CONFIGURATION.md",
            "TROUBLESHOOTING.md"
        ],
        "tests/": [
            "test_monitor.py",
            "test_alerts.py"
        ],
        "utils/": [
            "install.sh",
            "setup_systemd.sh",
            "setup_email.sh"
        ]
    }
}

# Function to display the project structure
def display_structure(structure, indent=0):
    for key, value in structure.items():
        print("  " * indent + f"📁 {key}")
        if isinstance(value, dict):
            display_structure(value, indent + 1)
        elif isinstance(value, list):
            for item in value:
                print("  " * (indent + 1) + f"📄 {item}")

print("🚀 Server Monitoring System - Project Structure")
print("=" * 50)
display_structure(project_structure)

print("\n📊 Project Components:")
print("✅ Bash monitoring script")
print("✅ Python monitoring script with advanced features") 
print("✅ Email and Slack notification system")
print("✅ Cron and Systemd scheduling")
print("✅ Configuration management")
print("✅ Comprehensive documentation")
print("✅ Installation automation")
print("✅ Test suite")