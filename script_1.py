# Create comprehensive bash monitoring script

bash_monitor_script = '''#!/bin/bash

# ===============================================================
# Server Monitoring Script (Bash Version)
# ===============================================================
# Description: Monitors CPU, Memory, and Disk usage
# Author: System Administrator
# Version: 1.0
# Last Modified: $(date +%Y-%m-%d)
# ===============================================================

# Configuration Section
# ===============================================================
SCRIPT_NAME="$(basename "$0")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
HOSTNAME=$(hostname)

# Load configuration file
CONFIG_FILE="${SCRIPT_DIR}/../../config/monitoring.conf"
if [[ -f "$CONFIG_FILE" ]]; then
    source "$CONFIG_FILE"
else
    echo "⚠️  Warning: Configuration file not found at $CONFIG_FILE"
    echo "Using default settings..."
fi

# Default Thresholds (used if config file not found)
CPU_THRESHOLD=${CPU_THRESHOLD:-80}
MEMORY_THRESHOLD=${MEMORY_THRESHOLD:-85} 
DISK_THRESHOLD=${DISK_THRESHOLD:-90}
LOAD_THRESHOLD=${LOAD_THRESHOLD:-2.0}

# Email Configuration
EMAIL_ENABLED=${EMAIL_ENABLED:-true}
SMTP_SERVER=${SMTP_SERVER:-"localhost"}
EMAIL_FROM=${EMAIL_FROM:-"monitor@$(hostname)"}
EMAIL_TO=${EMAIL_TO:-"admin@company.com"}

# Slack Configuration  
SLACK_ENABLED=${SLACK_ENABLED:-false}
SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL:-""}

# Logging Configuration
LOG_DIR="${SCRIPT_DIR}/../../logs"
LOG_FILE="${LOG_DIR}/monitor.log"
ALERT_LOG="${LOG_DIR}/alerts.log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
PURPLE='\\033[0;35m'
CYAN='\\033[0;36m'
NC='\\033[0m' # No Color

# ===============================================================
# Logging Functions
# ===============================================================

log_message() {
    local level="$1"
    local message="$2"
    echo "[$TIMESTAMP] [$level] $message" >> "$LOG_FILE"
}

log_alert() {
    local message="$1"
    echo "[$TIMESTAMP] [ALERT] $message" >> "$ALERT_LOG"
    log_message "ALERT" "$message"
}

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
    log_message "INFO" "$1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    log_message "WARNING" "$1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    log_message "ERROR" "$1"
}

print_alert() {
    echo -e "${RED}[ALERT]${NC} $1"
    log_alert "$1"
}

# ===============================================================
# System Information Functions
# ===============================================================

get_cpu_usage() {
    # Get CPU usage using top command
    local cpu_usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\\([0-9.]*\\)%* id.*/\\1/" | awk '{print 100 - $1}')
    
    # Alternative method using /proc/stat
    if [[ -z "$cpu_usage" ]] || [[ "$cpu_usage" == "100" ]]; then
        local cpu_line1=($(head -n1 /proc/stat))
        sleep 1
        local cpu_line2=($(head -n1 /proc/stat))
        
        local idle1=${cpu_line1[4]}
        local idle2=${cpu_line2[4]}
        
        local total1=0
        local total2=0
        
        for value in "${cpu_line1[@]:1}"; do
            ((total1 += value))
        done
        
        for value in "${cpu_line2[@]:1}"; do
            ((total2 += value))
        done
        
        local total_diff=$((total2 - total1))
        local idle_diff=$((idle2 - idle1))
        
        if [[ $total_diff -gt 0 ]]; then
            cpu_usage=$(awk "BEGIN {printf \"%.1f\", 100 * (($total_diff - $idle_diff) / $total_diff)}")
        else
            cpu_usage="0.0"
        fi
    fi
    
    echo "$cpu_usage"
}

get_memory_usage() {
    local memory_info
    memory_info=$(free | grep Mem)
    
    local total=$(echo "$memory_info" | awk '{print $2}')
    local used=$(echo "$memory_info" | awk '{print $3}')
    local available=$(echo "$memory_info" | awk '{print $7}')
    
    local usage_percent
    usage_percent=$(awk "BEGIN {printf \"%.1f\", ($used / $total) * 100}")
    
    echo "$usage_percent|$used|$total|$available"
}

get_disk_usage() {
    local disk_info=""
    local max_usage=0
    local critical_mount=""
    
    while IFS= read -r line; do
        if [[ $line == /dev/* ]]; then
            local mount_point=$(echo "$line" | awk '{print $6}')
            local usage_percent=$(echo "$line" | awk '{print $5}' | sed 's/%//')
            local used_space=$(echo "$line" | awk '{print $3}')
            local total_space=$(echo "$line" | awk '{print $2}')
            
            disk_info+="$mount_point:$usage_percent%($used_space/$total_space) "
            
            if [[ $usage_percent -gt $max_usage ]]; then
                max_usage=$usage_percent
                critical_mount="$mount_point"
            fi
        fi
    done < <(df -h)
    
    echo "$max_usage|$critical_mount|$disk_info"
}

get_load_average() {
    local load_avg
    load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    echo "$load_avg"
}

get_system_info() {
    local uptime_info
    uptime_info=$(uptime -p)
    
    local processes
    processes=$(ps aux | wc -l)
    
    local logged_users
    logged_users=$(who | wc -l)
    
    echo "$uptime_info|$processes|$logged_users"
}

# ===============================================================
# Network Functions
# ===============================================================

test_network_connectivity() {
    local test_hosts=("8.8.8.8" "1.1.1.1" "google.com")
    local failed_hosts=()
    
    for host in "${test_hosts[@]}"; do
        if ! ping -c 1 -W 2 "$host" >/dev/null 2>&1; then
            failed_hosts+=("$host")
        fi
    done
    
    if [[ ${#failed_hosts[@]} -gt 0 ]]; then
        return 1
    fi
    return 0
}

# ===============================================================
# Alert Functions
# ===============================================================

send_email_alert() {
    local subject="$1"
    local message="$2"
    
    if [[ "$EMAIL_ENABLED" == "true" ]]; then
        local email_body="Subject: $subject\\n\\n$message"
        
        if command -v mail >/dev/null 2>&1; then
            echo -e "$email_body" | mail -s "$subject" "$EMAIL_TO"
            print_status "Email alert sent to $EMAIL_TO"
        elif command -v sendmail >/dev/null 2>&1; then
            echo -e "$email_body" | sendmail "$EMAIL_TO"
            print_status "Email alert sent via sendmail to $EMAIL_TO"
        else
            print_error "No email client found (mail or sendmail)"
            return 1
        fi
    fi
}

send_slack_alert() {
    local message="$1"
    local color="$2"
    
    if [[ "$SLACK_ENABLED" == "true" && -n "$SLACK_WEBHOOK_URL" ]]; then
        local payload
        payload=$(cat << EOF
{
    "username": "ServerMonitor",
    "icon_emoji": ":warning:",
    "attachments": [
        {
            "color": "$color",
            "title": "🚨 Server Alert - $HOSTNAME",
            "text": "$message",
            "footer": "Server Monitoring System",
            "ts": $(date +%s)
        }
    ]
}
EOF
)
        
        if command -v curl >/dev/null 2>&1; then
            local response
            response=$(curl -s -X POST -H 'Content-type: application/json' \\
                --data "$payload" "$SLACK_WEBHOOK_URL")
            
            if [[ "$response" == "ok" ]]; then
                print_status "Slack alert sent successfully"
            else
                print_error "Failed to send Slack alert: $response"
            fi
        else
            print_error "curl command not found. Cannot send Slack alert."
        fi
    fi
}

send_alert() {
    local alert_type="$1"
    local message="$2"
    local color="${3:-danger}"
    
    local subject="[$alert_type] Server Alert - $HOSTNAME"
    local full_message="$message\\n\\nTimestamp: $TIMESTAMP\\nHostname: $HOSTNAME"
    
    print_alert "$alert_type: $message"
    
    # Send email alert
    send_email_alert "$subject" "$full_message"
    
    # Send Slack alert
    send_slack_alert "$full_message" "$color"
}

# ===============================================================
# Monitoring Functions
# ===============================================================

check_cpu_usage() {
    local cpu_usage
    cpu_usage=$(get_cpu_usage)
    
    printf "%-15s: %s%%\\n" "CPU Usage" "$cpu_usage"
    
    if (( $(echo "$cpu_usage > $CPU_THRESHOLD" | bc -l) )); then
        send_alert "HIGH CPU" "CPU usage is at $cpu_usage% (threshold: $CPU_THRESHOLD%)" "danger"
        return 1
    fi
    return 0
}

check_memory_usage() {
    local memory_data
    memory_data=$(get_memory_usage)
    
    IFS='|' read -r usage_percent used_mb total_mb available_mb <<< "$memory_data"
    
    local used_gb=$(awk "BEGIN {printf \"%.1f\", $used_mb/1024/1024}")
    local total_gb=$(awk "BEGIN {printf \"%.1f\", $total_mb/1024/1024}")
    local available_gb=$(awk "BEGIN {printf \"%.1f\", $available_mb/1024/1024}")
    
    printf "%-15s: %s%% (%s GB / %s GB used, %s GB available)\\n" \\
        "Memory Usage" "$usage_percent" "$used_gb" "$total_gb" "$available_gb"
    
    if (( $(echo "$usage_percent > $MEMORY_THRESHOLD" | bc -l) )); then
        send_alert "HIGH MEMORY" \\
            "Memory usage is at $usage_percent% (threshold: $MEMORY_THRESHOLD%) - $used_gb GB / $total_gb GB used" \\
            "danger"
        return 1
    fi
    return 0
}

check_disk_usage() {
    local disk_data
    disk_data=$(get_disk_usage)
    
    IFS='|' read -r max_usage critical_mount disk_details <<< "$disk_data"
    
    printf "%-15s: %s%% (Critical: %s)\\n" "Disk Usage" "$max_usage" "$critical_mount"
    echo "                Disk Details: $disk_details"
    
    if [[ $max_usage -gt $DISK_THRESHOLD ]]; then
        send_alert "HIGH DISK USAGE" \\
            "Disk usage is at $max_usage% on $critical_mount (threshold: $DISK_THRESHOLD%)" \\
            "danger"
        return 1
    fi
    return 0
}

check_load_average() {
    local load_avg
    load_avg=$(get_load_average)
    
    printf "%-15s: %s\\n" "Load Average" "$load_avg"
    
    if (( $(echo "$load_avg > $LOAD_THRESHOLD" | bc -l) )); then
        send_alert "HIGH LOAD" \\
            "System load average is $load_avg (threshold: $LOAD_THRESHOLD)" \\
            "warning"
        return 1
    fi
    return 0
}

check_network() {
    if test_network_connectivity; then
        printf "%-15s: %s\\n" "Network" "✅ OK"
        return 0
    else
        printf "%-15s: %s\\n" "Network" "❌ Issues Detected"
        send_alert "NETWORK ISSUE" "Network connectivity problems detected" "danger"
        return 1
    fi
}

display_system_info() {
    local sys_info
    sys_info=$(get_system_info)
    
    IFS='|' read -r uptime_info processes logged_users <<< "$sys_info"
    
    echo -e "${CYAN}=== System Information ===${NC}"
    printf "%-15s: %s\\n" "Hostname" "$HOSTNAME"
    printf "%-15s: %s\\n" "Timestamp" "$TIMESTAMP"
    printf "%-15s: %s\\n" "Uptime" "$uptime_info"
    printf "%-15s: %s\\n" "Processes" "$processes"
    printf "%-15s: %s\\n" "Logged Users" "$logged_users"
    echo
}

# ===============================================================
# Main Monitoring Function
# ===============================================================

run_monitoring() {
    local alerts_triggered=0
    
    echo -e "${BLUE}🔍 Starting Server Monitoring Check${NC}"
    echo "=================================================="
    
    display_system_info
    
    echo -e "${CYAN}=== Resource Usage ===${NC}"
    
    # Check CPU usage
    if ! check_cpu_usage; then
        ((alerts_triggered++))
    fi
    
    # Check Memory usage
    if ! check_memory_usage; then
        ((alerts_triggered++))
    fi
    
    # Check Disk usage
    if ! check_disk_usage; then
        ((alerts_triggered++))
    fi
    
    # Check Load Average
    if ! check_load_average; then
        ((alerts_triggered++))
    fi
    
    # Check Network
    if ! check_network; then
        ((alerts_triggered++))
    fi
    
    echo
    echo -e "${CYAN}=== Summary ===${NC}"
    if [[ $alerts_triggered -eq 0 ]]; then
        echo -e "${GREEN}✅ All systems normal - no alerts triggered${NC}"
        log_message "INFO" "Monitoring completed successfully - all systems normal"
    else
        echo -e "${RED}⚠️  $alerts_triggered alert(s) triggered${NC}"
        log_message "WARNING" "Monitoring completed with $alerts_triggered alert(s) triggered"
    fi
    
    echo "=================================================="
    return $alerts_triggered
}

# ===============================================================
# Utility Functions
# ===============================================================

show_usage() {
    cat << EOF
Usage: $SCRIPT_NAME [OPTIONS]

Server Monitoring Script - Monitors CPU, Memory, Disk usage and sends alerts

OPTIONS:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose output
    -q, --quiet            Quiet mode (only show alerts)
    -t, --test             Test mode (don't send alerts)
    -c, --config FILE      Use custom configuration file
    --check-config         Validate configuration
    --version              Show version information

EXAMPLES:
    $SCRIPT_NAME                    # Run with default settings
    $SCRIPT_NAME -v                # Run with verbose output
    $SCRIPT_NAME -q                # Run in quiet mode
    $SCRIPT_NAME -t                # Test mode (no alerts sent)
    $SCRIPT_NAME -c /path/config    # Use custom config file

For more information, see the documentation in docs/README.md
EOF
}

show_version() {
    echo "$SCRIPT_NAME version 1.0"
    echo "Server Monitoring System"
    echo "Built on $(date +%Y-%m-%d)"
}

check_dependencies() {
    local missing_deps=()
    local required_commands=("awk" "bc" "df" "free" "top" "uptime" "ps")
    
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        print_error "Missing required dependencies: ${missing_deps[*]}"
        echo "Please install the missing commands and try again."
        exit 1
    fi
}

validate_config() {
    local config_valid=true
    
    print_status "Validating configuration..."
    
    # Check thresholds
    if [[ ! $CPU_THRESHOLD =~ ^[0-9]+$ ]] || [[ $CPU_THRESHOLD -lt 1 ]] || [[ $CPU_THRESHOLD -gt 100 ]]; then
        print_error "Invalid CPU_THRESHOLD: must be between 1-100"
        config_valid=false
    fi
    
    if [[ ! $MEMORY_THRESHOLD =~ ^[0-9]+$ ]] || [[ $MEMORY_THRESHOLD -lt 1 ]] || [[ $MEMORY_THRESHOLD -gt 100 ]]; then
        print_error "Invalid MEMORY_THRESHOLD: must be between 1-100"  
        config_valid=false
    fi
    
    if [[ ! $DISK_THRESHOLD =~ ^[0-9]+$ ]] || [[ $DISK_THRESHOLD -lt 1 ]] || [[ $DISK_THRESHOLD -gt 100 ]]; then
        print_error "Invalid DISK_THRESHOLD: must be between 1-100"
        config_valid=false
    fi
    
    # Check email configuration
    if [[ "$EMAIL_ENABLED" == "true" ]]; then
        if [[ -z "$EMAIL_TO" ]]; then
            print_error "EMAIL_TO is required when EMAIL_ENABLED=true"
            config_valid=false
        fi
    fi
    
    # Check Slack configuration
    if [[ "$SLACK_ENABLED" == "true" ]]; then
        if [[ -z "$SLACK_WEBHOOK_URL" ]]; then
            print_error "SLACK_WEBHOOK_URL is required when SLACK_ENABLED=true"
            config_valid=false
        fi
    fi
    
    if [[ "$config_valid" == "true" ]]; then
        print_status "Configuration is valid"
        return 0
    else
        print_error "Configuration validation failed"
        return 1
    fi
}

# ===============================================================
# Signal Handlers
# ===============================================================

cleanup() {
    log_message "INFO" "Script terminated by user"
    exit 0
}

trap cleanup SIGINT SIGTERM

# ===============================================================
# Main Script Logic
# ===============================================================

main() {
    local verbose=false
    local quiet=false
    local test_mode=false
    local custom_config=""
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            -q|--quiet)
                quiet=true
                shift
                ;;
            -t|--test)
                test_mode=true
                EMAIL_ENABLED=false
                SLACK_ENABLED=false
                print_status "Running in test mode - alerts disabled"
                shift
                ;;
            -c|--config)
                custom_config="$2"
                shift 2
                ;;
            --check-config)
                validate_config
                exit $?
                ;;
            --version)
                show_version
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Load custom configuration if specified
    if [[ -n "$custom_config" ]]; then
        if [[ -f "$custom_config" ]]; then
            source "$custom_config"
            print_status "Loaded custom configuration: $custom_config"
        else
            print_error "Custom configuration file not found: $custom_config"
            exit 1
        fi
    fi
    
    # Check dependencies
    check_dependencies
    
    # Validate configuration
    if ! validate_config; then
        exit 1
    fi
    
    # Set output mode
    if [[ "$quiet" == "true" ]]; then
        exec 1>/dev/null
    fi
    
    # Run monitoring
    run_monitoring
    local exit_code=$?
    
    # Log completion
    log_message "INFO" "Monitoring script completed with exit code: $exit_code"
    
    exit $exit_code
}

# Run main function with all arguments
main "$@"
'''

print("✅ Created comprehensive Bash monitoring script")
print(f"📊 Script length: {len(bash_monitor_script)} characters")
print("🔧 Features included:")
print("  - CPU, Memory, Disk, Load Average monitoring")
print("  - Email and Slack alerts")
print("  - Configuration file support")
print("  - Logging system")
print("  - Command-line options")
print("  - Error handling and validation")
print("  - Network connectivity checks")

# Save the script
with open('bash_monitor_system.sh', 'w') as f:
    f.write(bash_monitor_script)

print("\n💾 Saved to: bash_monitor_system.sh")