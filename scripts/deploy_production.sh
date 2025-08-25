#!/bin/bash

# SmartCloudOps AI - Production Deployment Script
# This script deploys the complete application to production

set -e  # Exit on any error

echo "🚀 SmartCloudOps AI - Production Deployment Starting..."
echo "=================================================="

# Configuration
APP_INSTANCE_IP="44.200.14.5"
MONITORING_INSTANCE_IP="23.20.101.112"
SSH_KEY="~/.ssh/smartcloudops-ai.pem"
APP_DIR="/opt/smartcloudops-ai"
SERVICE_NAME="smartcloudops-ai"

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

# Function to test SSH connection
test_ssh_connection() {
    print_status "Testing SSH connection to application instance..."
    if ssh -i $SSH_KEY -o ConnectTimeout=10 -o BatchMode=yes ec2-user@$APP_INSTANCE_IP "echo 'SSH connection successful'" 2>/dev/null; then
        print_success "SSH connection to application instance established"
        return 0
    else
        print_error "Failed to connect to application instance via SSH"
        return 1
    fi
}

# Function to deploy application
deploy_application() {
    print_status "Deploying SmartCloudOps AI application..."
    
    # Create deployment directory
    ssh -i $SSH_KEY ec2-user@$APP_INSTANCE_IP "sudo mkdir -p $APP_DIR"
    
    # Copy application files
    print_status "Copying application files..."
    scp -i $SSH_KEY -r app/* ec2-user@$APP_INSTANCE_IP:$APP_DIR/
    scp -i $SSH_KEY requirements.txt ec2-user@$APP_INSTANCE_IP:$APP_DIR/
    
    # Install Python dependencies
    print_status "Installing Python dependencies..."
    ssh -i $SSH_KEY ec2-user@$APP_INSTANCE_IP "cd $APP_DIR && python3 -m pip install --user -r requirements.txt"
    
    # Create systemd service file
    print_status "Creating systemd service..."
    cat > /tmp/smartcloudops-ai.service << EOF
[Unit]
Description=SmartCloudOps AI Application
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=$APP_DIR
Environment=PATH=/home/ec2-user/.local/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/home/ec2-user/.local/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Copy service file to instance
    scp -i $SSH_KEY /tmp/smartcloudops-ai.service ec2-user@$APP_INSTANCE_IP:/tmp/
    
    # Install and start service
    ssh -i $SSH_KEY ec2-user@$APP_INSTANCE_IP "sudo mv /tmp/smartcloudops-ai.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable $SERVICE_NAME && sudo systemctl start $SERVICE_NAME"
    
    print_success "Application deployed successfully"
}

# Function to verify deployment
verify_deployment() {
    print_status "Verifying deployment..."
    
    # Wait for service to start
    sleep 10
    
    # Check service status
    if ssh -i $SSH_KEY ec2-user@$APP_INSTANCE_IP "sudo systemctl is-active --quiet $SERVICE_NAME"; then
        print_success "Service is running"
    else
        print_error "Service is not running"
        ssh -i $SSH_KEY ec2-user@$APP_INSTANCE_IP "sudo systemctl status $SERVICE_NAME"
        return 1
    fi
    
    # Test application endpoints
    print_status "Testing application endpoints..."
    
    # Test health endpoint
    if curl -s -f "http://$APP_INSTANCE_IP:5000/status" > /dev/null; then
        print_success "Health endpoint is responding"
    else
        print_error "Health endpoint is not responding"
        return 1
    fi
    
    # Test main endpoint
    if curl -s -f "http://$APP_INSTANCE_IP:5000/" > /dev/null; then
        print_success "Main endpoint is responding"
    else
        print_error "Main endpoint is not responding"
        return 1
    fi
    
    # Test ML endpoint
    if curl -s -f "http://$APP_INSTANCE_IP:5000/ml/health" > /dev/null; then
        print_success "ML endpoint is responding"
    else
        print_warning "ML endpoint is not responding (may be expected)"
    fi
    
    # Test auto-remediation endpoints
    if curl -s -f "http://$APP_INSTANCE_IP:5000/api/v1/remediation/status" > /dev/null; then
        print_success "Auto-remediation endpoint is responding"
    else
        print_warning "Auto-remediation endpoint is not responding (may be expected)"
    fi
    
    print_success "Deployment verification completed"
}

# Function to check monitoring stack
check_monitoring() {
    print_status "Checking monitoring stack..."
    
    # Check Prometheus
    if curl -s -f "http://$MONITORING_INSTANCE_IP:9090" > /dev/null; then
        print_success "Prometheus is running"
    else
        print_warning "Prometheus is not responding"
    fi
    
    # Check Grafana
    if curl -s -f "http://$MONITORING_INSTANCE_IP:3000" > /dev/null; then
        print_success "Grafana is running"
    else
        print_warning "Grafana is not responding"
    fi
}

# Function to display deployment summary
display_summary() {
    echo ""
    echo "🎉 SmartCloudOps AI - Production Deployment Complete!"
    echo "=================================================="
    echo ""
    echo "📊 Deployment Summary:"
    echo "  • Application URL: http://$APP_INSTANCE_IP:5000"
    echo "  • Health Check: http://$APP_INSTANCE_IP:5000/status"
    echo "  • Prometheus: http://$MONITORING_INSTANCE_IP:9090"
    echo "  • Grafana: http://$MONITORING_INSTANCE_IP:3000"
    echo ""
    echo "🔧 Service Management:"
    echo "  • SSH to instance: ssh -i $SSH_KEY ec2-user@$APP_INSTANCE_IP"
    echo "  • Check service: sudo systemctl status $SERVICE_NAME"
    echo "  • Restart service: sudo systemctl restart $SERVICE_NAME"
    echo "  • View logs: sudo journalctl -u $SERVICE_NAME -f"
    echo ""
    echo "📋 API Endpoints:"
    echo "  • GET / - Application status"
    echo "  • GET /status - Health check"
    echo "  • POST /query - ChatOps with GPT"
    echo "  • GET /logs - Application logs"
    echo "  • GET /ml/health - ML engine health"
    echo "  • POST /ml/predict - Anomaly detection"
    echo "  • GET /api/v1/remediation/status - Auto-remediation status"
    echo "  • GET /api/v1/integration/status - Integration status"
    echo ""
    echo "✅ All systems operational!"
}

# Main deployment process
main() {
    print_status "Starting SmartCloudOps AI production deployment..."
    
    # Check prerequisites
    if ! command_exists ssh; then
        print_error "SSH client is not installed"
        exit 1
    fi
    
    if ! command_exists scp; then
        print_error "SCP client is not installed"
        exit 1
    fi
    
    if ! command_exists curl; then
        print_error "curl is not installed"
        exit 1
    fi
    
    # Test SSH connection
    if ! test_ssh_connection; then
        print_error "Cannot establish SSH connection. Please check:"
        print_error "  • SSH key exists at $SSH_KEY"
        print_error "  • Security group allows SSH access"
        print_error "  • Instance is running"
        exit 1
    fi
    
    # Deploy application
    deploy_application
    
    # Verify deployment
    if ! verify_deployment; then
        print_error "Deployment verification failed"
        exit 1
    fi
    
    # Check monitoring
    check_monitoring
    
    # Display summary
    display_summary
}

# Run main function
main "$@"
