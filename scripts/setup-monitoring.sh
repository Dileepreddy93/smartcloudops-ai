#!/bin/bash
# SmartCloudOps AI - Production Monitoring Setup
# Deploy Prometheus and monitoring infrastructure

set -euo pipefail

echo "🚀 Setting up Production Monitoring Infrastructure..."

# Configuration
PROMETHEUS_VERSION="2.45.0"
PROMETHEUS_PORT="9090"
GRAFANA_PORT="3000"
PROMETHEUS_CONFIG="/etc/prometheus"
PROMETHEUS_DATA="/var/lib/prometheus"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   log_error "This script should not be run as root for security reasons"
   exit 1
fi

# Install Prometheus
install_prometheus() {
    log_info "Installing Prometheus ${PROMETHEUS_VERSION}..."
    
    # Download and extract Prometheus
    cd /tmp
    wget -q "https://github.com/prometheus/prometheus/releases/download/v${PROMETHEUS_VERSION}/prometheus-${PROMETHEUS_VERSION}.linux-amd64.tar.gz"
    tar xzf "prometheus-${PROMETHEUS_VERSION}.linux-amd64.tar.gz"
    
    # Move binaries
    sudo mv "prometheus-${PROMETHEUS_VERSION}.linux-amd64/prometheus" /usr/local/bin/
    sudo mv "prometheus-${PROMETHEUS_VERSION}.linux-amd64/promtool" /usr/local/bin/
    
    # Create prometheus user and directories
    sudo useradd --no-create-home --shell /bin/false prometheus || true
    sudo mkdir -p ${PROMETHEUS_CONFIG} ${PROMETHEUS_DATA}
    sudo chown prometheus:prometheus ${PROMETHEUS_CONFIG} ${PROMETHEUS_DATA}
    
    # Cleanup
    rm -rf "prometheus-${PROMETHEUS_VERSION}.linux-amd64"*
    
    log_info "✅ Prometheus installed successfully"
}

# Create Prometheus configuration
create_prometheus_config() {
    log_info "Creating Prometheus configuration..."
    
    sudo tee ${PROMETHEUS_CONFIG}/prometheus.yml > /dev/null <<EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "smartcloudops_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'smartcloudops-ai'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'docker'
    static_configs:
      - targets: ['localhost:9323']
EOF

    # Create alerting rules
    sudo tee ${PROMETHEUS_CONFIG}/smartcloudops_rules.yml > /dev/null <<EOF
groups:
  - name: smartcloudops.rules
    rules:
      - alert: SmartCloudOpsDown
        expr: up{job="smartcloudops-ai"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "SmartCloudOps AI is down"
          description: "SmartCloudOps AI has been down for more than 1 minute."

      - alert: HighCPUUsage
        expr: rate(process_cpu_seconds_total{job="smartcloudops-ai"}[5m]) * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is above 80% for more than 5 minutes."

      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes{job="smartcloudops-ai"} / 1024 / 1024 > 400
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage detected"
          description: "Memory usage is above 400MB for more than 5 minutes."

      - alert: MLModelAccuracyDrop
        expr: ml_model_accuracy{job="smartcloudops-ai"} < 0.8
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "ML Model accuracy dropped"
          description: "ML Model accuracy is below 80%."
EOF

    sudo chown -R prometheus:prometheus ${PROMETHEUS_CONFIG}
    log_info "✅ Prometheus configuration created"
}

# Create systemd service
create_prometheus_service() {
    log_info "Creating Prometheus systemd service..."
    
    sudo tee /etc/systemd/system/prometheus.service > /dev/null <<EOF
[Unit]
Description=Prometheus Monitoring System
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
Restart=always
RestartSec=5s
ExecStart=/usr/local/bin/prometheus \\
  --config.file=${PROMETHEUS_CONFIG}/prometheus.yml \\
  --storage.tsdb.path=${PROMETHEUS_DATA} \\
  --web.console.templates=/etc/prometheus/consoles \\
  --web.console.libraries=/etc/prometheus/console_libraries \\
  --web.listen-address=0.0.0.0:${PROMETHEUS_PORT} \\
  --web.enable-lifecycle \\
  --log.level=info

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable prometheus
    log_info "✅ Prometheus service created"
}

# Install Node Exporter
install_node_exporter() {
    log_info "Installing Node Exporter..."
    
    cd /tmp
    NODE_EXPORTER_VERSION="1.6.1"
    wget -q "https://github.com/prometheus/node_exporter/releases/download/v${NODE_EXPORTER_VERSION}/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz"
    tar xzf "node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz"
    sudo mv "node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64/node_exporter" /usr/local/bin/
    
    # Create node_exporter user
    sudo useradd --no-create-home --shell /bin/false node_exporter || true
    
    # Create systemd service
    sudo tee /etc/systemd/system/node_exporter.service > /dev/null <<EOF
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
Restart=always
RestartSec=5s
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable node_exporter
    
    # Cleanup
    rm -rf "node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64"*
    
    log_info "✅ Node Exporter installed"
}

# Configure firewall
configure_firewall() {
    log_info "Configuring firewall for monitoring..."
    
    # Check if ufw is available
    if command -v ufw >/dev/null 2>&1; then
        sudo ufw allow ${PROMETHEUS_PORT}/tcp comment "Prometheus"
        sudo ufw allow 9100/tcp comment "Node Exporter"
        sudo ufw allow ${GRAFANA_PORT}/tcp comment "Grafana"
        log_info "✅ UFW firewall rules added"
    else
        log_warn "UFW not found, please configure firewall manually"
        log_warn "Required ports: ${PROMETHEUS_PORT}, 9100, ${GRAFANA_PORT}"
    fi
}

# Start services
start_services() {
    log_info "Starting monitoring services..."
    
    sudo systemctl start prometheus
    sudo systemctl start node_exporter
    
    # Wait for services to start
    sleep 5
    
    # Check service status
    if sudo systemctl is-active --quiet prometheus; then
        log_info "✅ Prometheus is running on port ${PROMETHEUS_PORT}"
    else
        log_error "❌ Failed to start Prometheus"
        sudo systemctl status prometheus --no-pager
        exit 1
    fi
    
    if sudo systemctl is-active --quiet node_exporter; then
        log_info "✅ Node Exporter is running on port 9100"
    else
        log_error "❌ Failed to start Node Exporter"
        sudo systemctl status node_exporter --no-pager
        exit 1
    fi
}

# Health check
health_check() {
    log_info "Performing health check..."
    
    # Check Prometheus
    if curl -s "http://localhost:${PROMETHEUS_PORT}/-/healthy" > /dev/null; then
        log_info "✅ Prometheus health check passed"
    else
        log_error "❌ Prometheus health check failed"
        exit 1
    fi
    
    # Check Node Exporter
    if curl -s "http://localhost:9100/metrics" | head -1 > /dev/null; then
        log_info "✅ Node Exporter metrics available"
    else
        log_error "❌ Node Exporter health check failed"
        exit 1
    fi
    
    log_info "🎉 Monitoring infrastructure setup complete!"
    log_info "📊 Prometheus UI: http://$(hostname -I | awk '{print $1}'):${PROMETHEUS_PORT}"
    log_info "📈 Metrics endpoint: http://$(hostname -I | awk '{print $1}'):9100/metrics"
}

# Main execution
main() {
    log_info "Starting SmartCloudOps AI Monitoring Setup..."
    
    install_prometheus
    create_prometheus_config
    create_prometheus_service
    install_node_exporter
    configure_firewall
    start_services
    health_check
    
    log_info "✅ Production monitoring infrastructure is ready!"
}

# Run main function
main "$@"
