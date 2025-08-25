#!/bin/bash

# SmartCloudOps AI - Maintenance and Monitoring Script
# This script provides comprehensive maintenance and monitoring capabilities

set -e  # Exit on any error

echo "🔧 SmartCloudOps AI - Maintenance and Monitoring"
echo "==============================================="

# Configuration
APP_INSTANCE_IP="44.200.14.5"
MONITORING_INSTANCE_IP="23.20.101.112"
SSH_KEY="~/.ssh/smartcloudops-ai.pem"
APP_DIR="/opt/smartcloudops-ai"
SERVICE_NAME="smartcloudops-ai"
LOG_DIR="/var/log/smartcloudops-ai"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check application health
check_application_health() {
    print_status "Checking application health..."
    
    # Check if application is responding
    if curl -s -f "http://$APP_INSTANCE_IP:5000/status" > /dev/null 2>&1; then
        print_success "Application is responding"
        
        # Get detailed status
        STATUS_RESPONSE=$(curl -s "http://$APP_INSTANCE_IP:5000/status")
        echo "   Status: $STATUS_RESPONSE"
    else
        print_error "Application is not responding"
        return 1
    fi
    
    # Check ML engine health
    if curl -s -f "http://$APP_INSTANCE_IP:5000/ml/health" > /dev/null 2>&1; then
        print_success "ML engine is healthy"
    else
        print_warning "ML engine health check failed"
    fi
    
    # Check auto-remediation status
    if curl -s -f "http://$APP_INSTANCE_IP:5000/api/v1/remediation/status" > /dev/null 2>&1; then
        print_success "Auto-remediation system is operational"
    else
        print_warning "Auto-remediation system health check failed"
    fi
}

# Function to check monitoring stack
check_monitoring_stack() {
    print_status "Checking monitoring stack..."
    
    # Check Prometheus
    if curl -s -f "http://$MONITORING_INSTANCE_IP:9090" > /dev/null 2>&1; then
        print_success "Prometheus is running"
        
        # Check if metrics are being collected
        if curl -s "http://$APP_INSTANCE_IP:5000/metrics" | grep -q "smartcloudops"; then
            print_success "Application metrics are being collected"
        else
            print_warning "Application metrics collection may be incomplete"
        fi
    else
        print_error "Prometheus is not responding"
    fi
    
    # Check Grafana
    if curl -s -f "http://$MONITORING_INSTANCE_IP:3000" > /dev/null 2>&1; then
        print_success "Grafana is running"
    else
        print_error "Grafana is not responding"
    fi
}

# Function to check system resources
check_system_resources() {
    print_status "Checking system resources..."
    
    # Check if we can SSH to the instance
    if command_exists ssh; then
        print_status "Checking application instance resources..."
        
        # Get CPU usage
        CPU_USAGE=$(ssh -i $SSH_KEY -o ConnectTimeout=5 ec2-user@$APP_INSTANCE_IP "top -bn1 | grep 'Cpu(s)' | awk '{print \$2}' | cut -d'%' -f1" 2>/dev/null || echo "N/A")
        echo "   CPU Usage: ${CPU_USAGE}%"
        
        # Get memory usage
        MEMORY_USAGE=$(ssh -i $SSH_KEY -o ConnectTimeout=5 ec2-user@$APP_INSTANCE_IP "free | grep Mem | awk '{printf \"%.1f\", \$3/\$2 * 100.0}'" 2>/dev/null || echo "N/A")
        echo "   Memory Usage: ${MEMORY_USAGE}%"
        
        # Get disk usage
        DISK_USAGE=$(ssh -i $SSH_KEY -o ConnectTimeout=5 ec2-user@$APP_INSTANCE_IP "df -h / | awk 'NR==2 {print \$5}'" 2>/dev/null || echo "N/A")
        echo "   Disk Usage: ${DISK_USAGE}"
        
        # Check if service is running
        if ssh -i $SSH_KEY -o ConnectTimeout=5 ec2-user@$APP_INSTANCE_IP "sudo systemctl is-active --quiet $SERVICE_NAME" 2>/dev/null; then
            print_success "Application service is running"
        else
            print_error "Application service is not running"
        fi
    else
        print_warning "SSH not available - skipping resource checks"
    fi
}

# Function to check logs
check_logs() {
    print_status "Checking application logs..."
    
    if command_exists ssh; then
        # Check recent logs
        print_status "Recent application logs:"
        ssh -i $SSH_KEY -o ConnectTimeout=5 ec2-user@$APP_INSTANCE_IP "sudo journalctl -u $SERVICE_NAME --since '1 hour ago' --no-pager | tail -10" 2>/dev/null || echo "   Unable to retrieve logs"
        
        # Check for errors
        ERROR_COUNT=$(ssh -i $SSH_KEY -o ConnectTimeout=5 ec2-user@$APP_INSTANCE_IP "sudo journalctl -u $SERVICE_NAME --since '1 hour ago' | grep -i error | wc -l" 2>/dev/null || echo "0")
        echo "   Errors in last hour: $ERROR_COUNT"
        
        if [ "$ERROR_COUNT" -gt 0 ]; then
            print_warning "Errors detected in recent logs"
        else
            print_success "No errors in recent logs"
        fi
    else
        print_warning "SSH not available - skipping log checks"
    fi
}

# Function to perform backup
perform_backup() {
    print_status "Performing system backup..."
    
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup application code
    print_status "Backing up application code..."
    cp -r app/ "$BACKUP_DIR/"
    cp -r tests/ "$BACKUP_DIR/"
    cp -r scripts/ "$BACKUP_DIR/"
    cp -r terraform/ "$BACKUP_DIR/"
    cp *.md "$BACKUP_DIR/"
    
    # Backup configuration
    print_status "Backing up configuration..."
    cp app/requirements.txt "$BACKUP_DIR/"
    
    # Create backup manifest
    cat > "$BACKUP_DIR/backup_manifest.txt" << EOF
SmartCloudOps AI Backup Manifest
Generated: $(date)
Backup ID: $(date +%Y%m%d_%H%M%S)

Contents:
- Application code (app/)
- Test suite (tests/)
- Scripts (scripts/)
- Infrastructure (terraform/)
- Documentation (*.md)
- Dependencies (requirements.txt)

System Status:
- Application: $(curl -s "http://$APP_INSTANCE_IP:5000/status" 2>/dev/null || echo "Unknown")
- Prometheus: $(curl -s -f "http://$MONITORING_INSTANCE_IP:9090" > /dev/null 2>&1 && echo "Running" || echo "Not responding")
- Grafana: $(curl -s -f "http://$MONITORING_INSTANCE_IP:3000" > /dev/null 2>&1 && echo "Running" || echo "Not responding")
EOF
    
    print_success "Backup completed: $BACKUP_DIR"
}

# Function to update application
update_application() {
    print_status "Updating application..."
    
    if command_exists ssh; then
        # Stop service
        print_status "Stopping application service..."
        ssh -i $SSH_KEY ec2-user@$APP_INSTANCE_IP "sudo systemctl stop $SERVICE_NAME" 2>/dev/null || print_warning "Could not stop service"
        
        # Backup current version
        print_status "Backing up current version..."
        ssh -i $SSH_KEY ec2-user@$APP_INSTANCE_IP "cp -r $APP_DIR ${APP_DIR}_backup_$(date +%Y%m%d_%H%M%S)" 2>/dev/null || print_warning "Could not create backup"
        
        # Copy new files
        print_status "Copying new application files..."
        scp -i $SSH_KEY -r app/* ec2-user@$APP_INSTANCE_IP:$APP_DIR/ 2>/dev/null || print_error "Failed to copy files"
        
        # Update dependencies
        print_status "Updating dependencies..."
        ssh -i $SSH_KEY ec2-user@$APP_INSTANCE_IP "cd $APP_DIR && python3 -m pip install --user -r requirements.txt" 2>/dev/null || print_error "Failed to update dependencies"
        
        # Start service
        print_status "Starting application service..."
        ssh -i $SSH_KEY ec2-user@$APP_INSTANCE_IP "sudo systemctl start $SERVICE_NAME" 2>/dev/null || print_error "Failed to start service"
        
        # Verify update
        sleep 5
        if curl -s -f "http://$APP_INSTANCE_IP:5000/status" > /dev/null 2>&1; then
            print_success "Application updated successfully"
        else
            print_error "Application update failed"
        fi
    else
        print_error "SSH not available - cannot update application"
    fi
}

# Function to restart services
restart_services() {
    print_status "Restarting services..."
    
    if command_exists ssh; then
        # Restart application service
        print_status "Restarting application service..."
        ssh -i $SSH_KEY ec2-user@$APP_INSTANCE_IP "sudo systemctl restart $SERVICE_NAME" 2>/dev/null || print_error "Failed to restart application service"
        
        # Wait for service to start
        sleep 10
        
        # Verify restart
        if curl -s -f "http://$APP_INSTANCE_IP:5000/status" > /dev/null 2>&1; then
            print_success "Application service restarted successfully"
        else
            print_error "Application service restart failed"
        fi
    else
        print_error "SSH not available - cannot restart services"
    fi
}

# Function to generate health report
generate_health_report() {
    print_status "Generating health report..."
    
    REPORT_FILE="health_report_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$REPORT_FILE" << EOF
SmartCloudOps AI Health Report
Generated: $(date)

=== SYSTEM STATUS ===
Application Instance: $APP_INSTANCE_IP
Monitoring Instance: $MONITORING_INSTANCE_IP

=== APPLICATION HEALTH ===
EOF
    
    # Check application health and append to report
    if curl -s -f "http://$APP_INSTANCE_IP:5000/status" > /dev/null 2>&1; then
        echo "Application: RUNNING" >> "$REPORT_FILE"
        curl -s "http://$APP_INSTANCE_IP:5000/status" >> "$REPORT_FILE" 2>/dev/null || echo "Status: Unable to retrieve" >> "$REPORT_FILE"
    else
        echo "Application: NOT RESPONDING" >> "$REPORT_FILE"
    fi
    
    cat >> "$REPORT_FILE" << EOF

=== MONITORING STACK ===
EOF
    
    # Check monitoring stack and append to report
    if curl -s -f "http://$MONITORING_INSTANCE_IP:9090" > /dev/null 2>&1; then
        echo "Prometheus: RUNNING" >> "$REPORT_FILE"
    else
        echo "Prometheus: NOT RESPONDING" >> "$REPORT_FILE"
    fi
    
    if curl -s -f "http://$MONITORING_INSTANCE_IP:3000" > /dev/null 2>&1; then
        echo "Grafana: RUNNING" >> "$REPORT_FILE"
    else
        echo "Grafana: NOT RESPONDING" >> "$REPORT_FILE"
    fi
    
    cat >> "$REPORT_FILE" << EOF

=== TEST RESULTS ===
EOF
    
    # Run tests and append results
    if python -m pytest tests/ --tb=no -q 2>/dev/null; then
        echo "Test Suite: ALL TESTS PASSING" >> "$REPORT_FILE"
    else
        echo "Test Suite: SOME TESTS FAILED" >> "$REPORT_FILE"
    fi
    
    cat >> "$REPORT_FILE" << EOF

=== RECOMMENDATIONS ===
EOF
    
    # Generate recommendations based on health checks
    if ! curl -s -f "http://$APP_INSTANCE_IP:5000/status" > /dev/null 2>&1; then
        echo "- Application is not responding. Check service status and logs." >> "$REPORT_FILE"
    fi
    
    if ! curl -s -f "http://$MONITORING_INSTANCE_IP:9090" > /dev/null 2>&1; then
        echo "- Prometheus is not responding. Check monitoring instance." >> "$REPORT_FILE"
    fi
    
    if ! curl -s -f "http://$MONITORING_INSTANCE_IP:3000" > /dev/null 2>&1; then
        echo "- Grafana is not responding. Check monitoring instance." >> "$REPORT_FILE"
    fi
    
    print_success "Health report generated: $REPORT_FILE"
}

# Function to display maintenance menu
display_menu() {
    echo ""
    echo "🔧 SmartCloudOps AI - Maintenance Menu"
    echo "====================================="
    echo ""
    echo "1. Check Application Health"
    echo "2. Check Monitoring Stack"
    echo "3. Check System Resources"
    echo "4. Check Application Logs"
    echo "5. Perform System Backup"
    echo "6. Update Application"
    echo "7. Restart Services"
    echo "8. Generate Health Report"
    echo "9. Run All Health Checks"
    echo "0. Exit"
    echo ""
    echo "Enter your choice (0-9): "
}

# Function to run all health checks
run_all_health_checks() {
    print_status "Running comprehensive health checks..."
    
    check_application_health
    check_monitoring_stack
    check_system_resources
    check_logs
    
    print_success "All health checks completed"
}

# Main maintenance process
main() {
    if [ $# -eq 0 ]; then
        # Interactive mode
        while true; do
            display_menu
            read -r choice
            
            case $choice in
                1) check_application_health ;;
                2) check_monitoring_stack ;;
                3) check_system_resources ;;
                4) check_logs ;;
                5) perform_backup ;;
                6) update_application ;;
                7) restart_services ;;
                8) generate_health_report ;;
                9) run_all_health_checks ;;
                0) echo "Exiting..."; exit 0 ;;
                *) echo "Invalid choice. Please try again." ;;
            esac
            
            echo ""
            echo "Press Enter to continue..."
            read -r
        done
    else
        # Command line mode
        case $1 in
            "health") check_application_health ;;
            "monitoring") check_monitoring_stack ;;
            "resources") check_system_resources ;;
            "logs") check_logs ;;
            "backup") perform_backup ;;
            "update") update_application ;;
            "restart") restart_services ;;
            "report") generate_health_report ;;
            "all") run_all_health_checks ;;
            *) echo "Usage: $0 [health|monitoring|resources|logs|backup|update|restart|report|all]"; exit 1 ;;
        esac
    fi
}

# Run main function
main "$@"
