#!/bin/bash

# Server Monitoring System - Installation Script
# ==============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INSTALL_DIR="${INSTALL_DIR:-/opt/server-monitoring}"
MONITOR_USER="${MONITOR_USER:-monitor}"
MONITOR_GROUP="${MONITOR_GROUP:-monitor}"

print_header() {
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                 Server Monitoring System                     ║${NC}"
    echo -e "${BLUE}║                    Installation Script                       ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${CYAN}[i]${NC} $1"
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Install the Server Monitoring System

OPTIONS:
    -h, --help              Show this help message
    -d, --install-dir DIR   Installation directory (default: /opt/server-monitoring)
    -u, --user USER         Monitoring user (default: monitor)
    -g, --group GROUP       Monitoring group (default: monitor)
    --no-user              Don't create monitoring user
    --no-deps              Skip dependency installation
    --python-only          Install only Python version
    --bash-only            Install only Bash version
    --systemd              Setup systemd service and timer
    --cron                 Setup cron jobs
    --test                 Test installation without making changes

EXAMPLES:
    $0                          # Full installation with defaults
    $0 -d /home/monitor         # Install to custom directory
    $0 --python-only --systemd  # Python version with systemd
    $0 --bash-only --cron       # Bash version with cron
    $0 --test                   # Test run without changes

EOF
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root for system installation"
        print_info "Run with: sudo $0"
        exit 1
    fi
}

detect_os() {
    if [[ -f /etc/os-release ]]; then
        source /etc/os-release
        OS_ID="$ID"
        OS_VERSION="$VERSION_ID"
        OS_NAME="$PRETTY_NAME"
    else
        OS_ID="unknown"
        OS_VERSION="unknown"
        OS_NAME="Unknown Linux"
    fi

    print_info "Detected OS: $OS_NAME"
}

install_dependencies() {
    print_status "Installing system dependencies..."

    case "$OS_ID" in
        ubuntu|debian)
            apt-get update
            apt-get install -y python3 python3-pip python3-venv \
                             mailutils curl bc procps coreutils \
                             systemd-cron rsyslog
            ;;
        centos|rhel|fedora)
            if command -v dnf >/dev/null 2>&1; then
                dnf install -y python3 python3-pip \
                             mailx curl bc procps-ng coreutils \
                             systemd cronie rsyslog
            else
                yum install -y python3 python3-pip \
                             mailx curl bc procps-ng coreutils \
                             systemd cronie rsyslog
            fi
            ;;
        arch)
            pacman -Sy --noconfirm python python-pip \
                                  mailutils curl bc procps-ng coreutils \
                                  systemd cronie rsyslog
            ;;
        *)
            print_warning "Unknown OS. Please install dependencies manually:"
            print_info "  - python3, python3-pip"
            print_info "  - mailutils/mailx, curl, bc"
            print_info "  - procps, coreutils, systemd"
            ;;
    esac
}

create_user() {
    if [[ "$CREATE_USER" == "false" ]]; then
        return 0
    fi

    print_status "Creating monitoring user and group..."

    # Create group if it doesn't exist
    if ! getent group "$MONITOR_GROUP" >/dev/null 2>&1; then
        groupadd -r "$MONITOR_GROUP"
        print_status "Created group: $MONITOR_GROUP"
    fi

    # Create user if it doesn't exist
    if ! id "$MONITOR_USER" >/dev/null 2>&1; then
        useradd -r -g "$MONITOR_GROUP" -d "$INSTALL_DIR" \
               -s /bin/false -c "Server Monitoring User" "$MONITOR_USER"
        print_status "Created user: $MONITOR_USER"
    else
        print_info "User $MONITOR_USER already exists"
    fi
}

create_directories() {
    print_status "Creating directory structure..."

    local dirs=(
        "$INSTALL_DIR"
        "$INSTALL_DIR/scripts/bash"
        "$INSTALL_DIR/scripts/python"
        "$INSTALL_DIR/config"
        "$INSTALL_DIR/logs"
        "$INSTALL_DIR/systemd"
        "$INSTALL_DIR/cron"
        "$INSTALL_DIR/docs"
        "$INSTALL_DIR/tests"
        "$INSTALL_DIR/utils"
    )

    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
        print_status "Created directory: $dir"
    done
}

install_files() {
    print_status "Installing monitoring files..."

    # Copy scripts
    if [[ "$INSTALL_TYPE" == "python" || "$INSTALL_TYPE" == "both" ]]; then
        cp "$PROJECT_ROOT/scripts/python/"* "$INSTALL_DIR/scripts/python/" 2>/dev/null || true
        chmod +x "$INSTALL_DIR/scripts/python/monitor_system.py"
    fi

    if [[ "$INSTALL_TYPE" == "bash" || "$INSTALL_TYPE" == "both" ]]; then  
        cp "$PROJECT_ROOT/scripts/bash/"* "$INSTALL_DIR/scripts/bash/" 2>/dev/null || true
        chmod +x "$INSTALL_DIR/scripts/bash/monitor_system.sh"
    fi

    # Copy configuration files
    cp "$PROJECT_ROOT/config/"* "$INSTALL_DIR/config/" 2>/dev/null || true

    # Copy systemd files
    cp "$PROJECT_ROOT/systemd/"* "$INSTALL_DIR/systemd/" 2>/dev/null || true

    # Copy cron files
    cp "$PROJECT_ROOT/cron/"* "$INSTALL_DIR/cron/" 2>/dev/null || true
    chmod +x "$INSTALL_DIR/cron/install_cron.sh"

    # Copy documentation
    cp "$PROJECT_ROOT/docs/"* "$INSTALL_DIR/docs/" 2>/dev/null || true
    cp "$PROJECT_ROOT/README"* "$INSTALL_DIR/docs/" 2>/dev/null || true

    # Copy utilities
    cp "$PROJECT_ROOT/utils/"* "$INSTALL_DIR/utils/" 2>/dev/null || true
    chmod +x "$INSTALL_DIR/utils/"*.sh 2>/dev/null || true

    # Copy tests
    cp "$PROJECT_ROOT/tests/"* "$INSTALL_DIR/tests/" 2>/dev/null || true
}

install_python_deps() {
    if [[ "$INSTALL_TYPE" == "bash" ]]; then
        return 0
    fi

    print_status "Installing Python dependencies..."

    # Create virtual environment
    python3 -m venv "$INSTALL_DIR/venv"
    source "$INSTALL_DIR/venv/bin/activate"

    # Upgrade pip
    pip install --upgrade pip

    # Install requirements
    if [[ -f "$INSTALL_DIR/scripts/python/requirements.txt" ]]; then
        pip install -r "$INSTALL_DIR/scripts/python/requirements.txt"
        print_status "Python dependencies installed"
    else
        print_warning "requirements.txt not found, installing basic dependencies"
        pip install psutil pyyaml requests
    fi

    deactivate
}

set_permissions() {
    print_status "Setting file permissions..."

    # Set ownership
    chown -R "$MONITOR_USER:$MONITOR_GROUP" "$INSTALL_DIR"

    # Set directory permissions
    find "$INSTALL_DIR" -type d -exec chmod 755 {} \;

    # Set file permissions
    find "$INSTALL_DIR" -type f -exec chmod 644 {} \;

    # Set executable permissions for scripts
    find "$INSTALL_DIR" -name "*.sh" -exec chmod 755 {} \;
    find "$INSTALL_DIR" -name "*.py" -exec chmod 755 {} \;

    # Secure configuration files
    chmod 600 "$INSTALL_DIR/config/"*.conf 2>/dev/null || true
    chmod 600 "$INSTALL_DIR/config/"*.yaml 2>/dev/null || true
    chmod 600 "$INSTALL_DIR/config/"*.json 2>/dev/null || true

    # Set log directory permissions
    chmod 755 "$INSTALL_DIR/logs"
    chown "$MONITOR_USER:$MONITOR_GROUP" "$INSTALL_DIR/logs"
}

setup_systemd() {
    if [[ "$SETUP_SYSTEMD" != "true" ]]; then
        return 0
    fi

    print_status "Setting up systemd service and timer..."

    # Copy service files
    cp "$INSTALL_DIR/systemd/server-monitor.service" /etc/systemd/system/
    cp "$INSTALL_DIR/systemd/server-monitor.timer" /etc/systemd/system/

    # Update service file with correct paths
    sed -i "s|/opt/server-monitoring|$INSTALL_DIR|g" /etc/systemd/system/server-monitor.service
    sed -i "s|User=monitor|User=$MONITOR_USER|g" /etc/systemd/system/server-monitor.service
    sed -i "s|Group=monitor|Group=$MONITOR_GROUP|g" /etc/systemd/system/server-monitor.service

    # Reload systemd
    systemctl daemon-reload

    # Enable but don't start yet
    systemctl enable server-monitor.timer

    print_status "Systemd service and timer configured"
    print_info "Start with: systemctl start server-monitor.timer"
}

setup_cron() {
    if [[ "$SETUP_CRON" != "true" ]]; then
        return 0
    fi

    print_status "Setting up cron job..."

    # Run cron installation script
    cd "$INSTALL_DIR"
    ./cron/install_cron.sh --system-wide --user "$MONITOR_USER" --script python

    print_status "Cron job configured"
}

run_tests() {
    print_status "Running installation tests..."

    local test_passed=true

    # Test Python script (if installed)
    if [[ "$INSTALL_TYPE" == "python" || "$INSTALL_TYPE" == "both" ]]; then
        print_info "Testing Python monitoring script..."
        if sudo -u "$MONITOR_USER" "$INSTALL_DIR/scripts/python/monitor_system.py" --test >/dev/null 2>&1; then
            print_status "Python script test passed"
        else
            print_error "Python script test failed"
            test_passed=false
        fi
    fi

    # Test Bash script (if installed)
    if [[ "$INSTALL_TYPE" == "bash" || "$INSTALL_TYPE" == "both" ]]; then
        print_info "Testing Bash monitoring script..."
        if sudo -u "$MONITOR_USER" "$INSTALL_DIR/scripts/bash/monitor_system.sh" --test >/dev/null 2>&1; then
            print_status "Bash script test passed"
        else
            print_error "Bash script test failed"
            test_passed=false
        fi
    fi

    # Test systemd (if configured)
    if [[ "$SETUP_SYSTEMD" == "true" ]]; then
        print_info "Testing systemd configuration..."
        if systemctl is-enabled server-monitor.timer >/dev/null 2>&1; then
            print_status "Systemd timer is enabled"
        else
            print_error "Systemd timer is not enabled"
            test_passed=false
        fi
    fi

    if [[ "$test_passed" == "true" ]]; then
        print_status "All tests passed!"
    else
        print_warning "Some tests failed. Check configuration."
    fi
}

print_summary() {
    echo ""
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║                    Installation Complete!                    ║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    print_status "Installation Summary:"
    echo "  📍 Installation Directory: $INSTALL_DIR"
    echo "  👤 Monitoring User: $MONITOR_USER"
    echo "  📦 Installation Type: $INSTALL_TYPE"

    if [[ "$SETUP_SYSTEMD" == "true" ]]; then
        echo "  ⏲️  Systemd Timer: Configured"
    fi

    if [[ "$SETUP_CRON" == "true" ]]; then
        echo "  ⏰ Cron Job: Configured"
    fi

    echo ""
    print_info "Next Steps:"

    echo "  1. Edit configuration files:"
    echo "     - $INSTALL_DIR/config/config.yaml (Python)"
    echo "     - $INSTALL_DIR/config/monitoring.conf (Bash)"

    echo "  2. Configure email and Slack settings"

    if [[ "$SETUP_SYSTEMD" == "true" ]]; then
        echo "  3. Start monitoring service:"
        echo "     sudo systemctl start server-monitor.timer"
        echo "     sudo systemctl status server-monitor.timer"
    fi

    if [[ "$SETUP_CRON" == "true" ]]; then  
        echo "  3. Check cron job:"
        echo "     crontab -l"
        echo "     tail -f /var/log/syslog | grep server-monitor"
    fi

    echo "  4. Test the monitoring:"
    echo "     sudo -u $MONITOR_USER $INSTALL_DIR/scripts/python/monitor_system.py --test"

    echo "  5. View logs:"
    echo "     tail -f $INSTALL_DIR/logs/monitor.log"

    echo ""
    print_status "Installation completed successfully! 🎉"
}

main() {
    # Default values
    CREATE_USER=true
    INSTALL_DEPS=true
    INSTALL_TYPE="both"  # bash, python, both
    SETUP_SYSTEMD=false
    SETUP_CRON=false
    TEST_MODE=false

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -d|--install-dir)
                INSTALL_DIR="$2"
                shift 2
                ;;
            -u|--user)
                MONITOR_USER="$2"
                shift 2
                ;;
            -g|--group)
                MONITOR_GROUP="$2"
                shift 2
                ;;
            --no-user)
                CREATE_USER=false
                shift
                ;;
            --no-deps)
                INSTALL_DEPS=false
                shift
                ;;
            --python-only)
                INSTALL_TYPE="python"
                shift
                ;;
            --bash-only)
                INSTALL_TYPE="bash"
                shift
                ;;
            --systemd)
                SETUP_SYSTEMD=true
                shift
                ;;
            --cron)
                SETUP_CRON=true
                shift
                ;;
            --test)
                TEST_MODE=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    # Show header
    print_header

    # Test mode
    if [[ "$TEST_MODE" == "true" ]]; then
        print_warning "Running in test mode - no changes will be made"
        print_info "Would install to: $INSTALL_DIR"
        print_info "Would create user: $MONITOR_USER"
        print_info "Installation type: $INSTALL_TYPE"
        return 0
    fi

    # Check root permissions
    check_root

    # Detect OS
    detect_os

    # Install dependencies
    if [[ "$INSTALL_DEPS" == "true" ]]; then
        install_dependencies
    fi

    # Create user and group
    create_user

    # Create directories
    create_directories

    # Install files
    install_files

    # Install Python dependencies
    install_python_deps

    # Set permissions
    set_permissions

    # Setup systemd
    setup_systemd

    # Setup cron
    setup_cron

    # Run tests
    run_tests

    # Print summary
    print_summary
}

# Run main function with all arguments
main "$@"
