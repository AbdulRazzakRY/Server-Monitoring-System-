#!/bin/bash

# Server Monitoring - Cron Installation Script
# =============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
MONITOR_USER="${MONITOR_USER:-monitor}"
CRON_INTERVAL="${CRON_INTERVAL:-5}"

echo -e "${BLUE}🕐 Server Monitoring - Cron Setup${NC}"
echo "=================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    print_warning "Running as root. Will set up system-wide cron job."
    SYSTEM_WIDE=true
else
    print_status "Running as user $(whoami). Will set up user cron job."
    SYSTEM_WIDE=false
fi

# Validate project structure
if [[ ! -f "$PROJECT_ROOT/scripts/python/monitor_system.py" ]]; then
    print_error "Python monitoring script not found at $PROJECT_ROOT/scripts/python/monitor_system.py"
    exit 1
fi

if [[ ! -f "$PROJECT_ROOT/scripts/bash/monitor_system.sh" ]]; then
    print_error "Bash monitoring script not found at $PROJECT_ROOT/scripts/bash/monitor_system.sh"
    exit 1
fi

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Install cron jobs for server monitoring

OPTIONS:
    -h, --help              Show this help message
    -i, --interval MINUTES  Set monitoring interval (default: 5 minutes)
    -u, --user USERNAME     Set monitoring user (default: monitor)
    -s, --script TYPE       Script type: bash|python|both (default: python)
    -t, --test             Test mode - show what would be installed
    --system-wide          Install system-wide cron job (requires root)
    --remove               Remove existing cron jobs

EXAMPLES:
    $0                      # Install Python monitoring every 5 minutes
    $0 -i 10 -s bash       # Install Bash monitoring every 10 minutes  
    $0 -s both             # Install both Python and Bash monitoring
    $0 --remove            # Remove all monitoring cron jobs
    $0 --test              # Show what would be installed without installing

EOF
}

# Parse command line arguments
SCRIPT_TYPE="python"
TEST_MODE=false
REMOVE_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -i|--interval)
            CRON_INTERVAL="$2"
            shift 2
            ;;
        -u|--user)
            MONITOR_USER="$2"
            shift 2
            ;;
        -s|--script)
            SCRIPT_TYPE="$2"
            shift 2
            ;;
        -t|--test)
            TEST_MODE=true
            shift
            ;;
        --system-wide)
            SYSTEM_WIDE=true
            shift
            ;;
        --remove)
            REMOVE_MODE=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate parameters
if [[ ! "$CRON_INTERVAL" =~ ^[0-9]+$ ]]; then
    print_error "Invalid interval: $CRON_INTERVAL (must be a number)"
    exit 1
fi

if [[ "$SCRIPT_TYPE" != "bash" && "$SCRIPT_TYPE" != "python" && "$SCRIPT_TYPE" != "both" ]]; then
    print_error "Invalid script type: $SCRIPT_TYPE (must be bash, python, or both)"
    exit 1
fi

# Function to remove existing cron jobs
remove_cron_jobs() {
    print_status "Removing existing server monitoring cron jobs..."

    if [[ "$SYSTEM_WIDE" == "true" ]]; then
        # Remove system-wide cron file
        if [[ -f /etc/cron.d/server-monitoring ]]; then
            rm -f /etc/cron.d/server-monitoring
            print_status "Removed system-wide cron file"
        fi
    else
        # Remove user cron jobs
        crontab -l 2>/dev/null | grep -v "server-monitoring\|monitor_system" | crontab - 2>/dev/null || true
        print_status "Removed user cron jobs"
    fi
}

# Function to create cron entry
create_cron_entry() {
    local script_path="$1"
    local description="$2"

    # Create cron time specification
    if [[ $CRON_INTERVAL -eq 1 ]]; then
        CRON_TIME="* * * * *"  # Every minute
    else
        CRON_TIME="*/$CRON_INTERVAL * * * *"  # Every N minutes
    fi

    # Create full cron entry
    local cron_entry="$CRON_TIME $script_path 2>&1 | logger -t server-monitor"

    echo "# $description"
    echo "$cron_entry"
    echo ""
}

# Function to install cron jobs
install_cron_jobs() {
    print_status "Installing server monitoring cron jobs..."
    print_status "Interval: every $CRON_INTERVAL minute(s)"
    print_status "Script type: $SCRIPT_TYPE"

    if [[ "$SYSTEM_WIDE" == "true" ]]; then
        # Create system-wide cron file
        local cron_file="/etc/cron.d/server-monitoring"

        cat > "$cron_file" << EOF
# Server Monitoring System Cron Jobs
# Generated on $(date)
# Interval: every $CRON_INTERVAL minute(s)

SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
MAILTO=admin@company.com

EOF

        if [[ "$SCRIPT_TYPE" == "python" || "$SCRIPT_TYPE" == "both" ]]; then
            create_cron_entry "$PROJECT_ROOT/scripts/python/monitor_system.py" "Python monitoring script" >> "$cron_file"
        fi

        if [[ "$SCRIPT_TYPE" == "bash" || "$SCRIPT_TYPE" == "both" ]]; then
            create_cron_entry "$PROJECT_ROOT/scripts/bash/monitor_system.sh" "Bash monitoring script" >> "$cron_file"
        fi

        # Set proper permissions
        chmod 644 "$cron_file"
        print_status "Created system-wide cron file: $cron_file"

    else
        # Create user cron entries
        local temp_cron=$(mktemp)

        # Get existing crontab (if any)
        crontab -l 2>/dev/null > "$temp_cron" || echo "# User crontab" > "$temp_cron"

        # Add monitoring entries
        echo "" >> "$temp_cron"
        echo "# Server Monitoring System - Added $(date)" >> "$temp_cron"

        if [[ "$SCRIPT_TYPE" == "python" || "$SCRIPT_TYPE" == "both" ]]; then
            create_cron_entry "$PROJECT_ROOT/scripts/python/monitor_system.py" "Python monitoring script" >> "$temp_cron"
        fi

        if [[ "$SCRIPT_TYPE" == "bash" || "$SCRIPT_TYPE" == "both" ]]; then
            create_cron_entry "$PROJECT_ROOT/scripts/bash/monitor_system.sh" "Bash monitoring script" >> "$temp_cron"
        fi

        # Install new crontab
        crontab "$temp_cron"
        rm -f "$temp_cron"

        print_status "Updated user crontab for $(whoami)"
    fi
}

# Function to show what would be installed
show_test_mode() {
    print_status "TEST MODE - Showing what would be installed:"
    echo ""

    if [[ "$SCRIPT_TYPE" == "python" || "$SCRIPT_TYPE" == "both" ]]; then
        create_cron_entry "$PROJECT_ROOT/scripts/python/monitor_system.py" "Python monitoring script"
    fi

    if [[ "$SCRIPT_TYPE" == "bash" || "$SCRIPT_TYPE" == "both" ]]; then
        create_cron_entry "$PROJECT_ROOT/scripts/bash/monitor_system.sh" "Bash monitoring script"
    fi

    echo "Installation method: $(if [[ "$SYSTEM_WIDE" == "true" ]]; then echo "System-wide (/etc/cron.d/)"; else echo "User crontab"; fi)"
}

# Main execution
if [[ "$REMOVE_MODE" == "true" ]]; then
    remove_cron_jobs
    print_status "✅ Cron jobs removed successfully"
elif [[ "$TEST_MODE" == "true" ]]; then
    show_test_mode
else
    # Check if user exists (for system-wide installation)
    if [[ "$SYSTEM_WIDE" == "true" && ! id "$MONITOR_USER" &>/dev/null ]]; then
        print_warning "User $MONITOR_USER does not exist. Consider creating it first."
    fi

    # Make scripts executable
    chmod +x "$PROJECT_ROOT/scripts/bash/monitor_system.sh" 2>/dev/null || true
    chmod +x "$PROJECT_ROOT/scripts/python/monitor_system.py" 2>/dev/null || true

    install_cron_jobs
    print_status "✅ Cron jobs installed successfully"

    echo ""
    print_status "Next steps:"
    echo "  1. Verify cron installation: $(if [[ "$SYSTEM_WIDE" == "true" ]]; then echo "cat /etc/cron.d/server-monitoring"; else echo "crontab -l"; fi)"
    echo "  2. Check cron logs: tail -f /var/log/syslog | grep server-monitor"
    echo "  3. Test the monitoring: $PROJECT_ROOT/scripts/python/monitor_system.py --test"
fi
