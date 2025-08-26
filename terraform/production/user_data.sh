#!/bin/bash

# SmartCloudOps AI - Production EC2 User Data Script
# This script sets up the application server on EC2 instances

set -e

# Log all output
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

echo "🚀 SmartCloudOps AI - Production Server Setup"
echo "============================================="

# Update system
echo "📦 Updating system packages..."
yum update -y

# Install required packages
echo "📦 Installing required packages..."
yum install -y \
    docker \
    git \
    python3 \
    python3-pip \
    python3-devel \
    gcc \
    postgresql \
    redis \
    curl \
    wget \
    unzip \
    jq

# Start and enable Docker
echo "🐳 Setting up Docker..."
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
echo "🐳 Installing Docker Compose..."
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create application directory
echo "📁 Setting up application directory..."
mkdir -p /opt/smartcloudops
cd /opt/smartcloudops

# Clone application (in production, you'd use a deployment package)
echo "📥 Setting up application..."
# git clone https://github.com/your-org/smartcloudops-ai.git .
# For now, we'll create a basic structure

# Create environment file
echo "🔧 Creating environment configuration..."
cat > /opt/smartcloudops/.env << EOF
# Production Environment Configuration
FLASK_ENV=production
FLASK_DEBUG=False

# Database Configuration
DB_HOST=${db_host}
DB_NAME=${db_name}
DB_USER=${db_username}
DB_PASSWORD=${db_password}
DATABASE_URL=postgresql://${db_username}:${db_password}@${db_host}:5432/${db_name}

# Redis Configuration
REDIS_HOST=${redis_host}
REDIS_PORT=${redis_port}
REDIS_PASSWORD=${redis_password:-}
REDIS_URL=redis://:${redis_password:-}@${redis_host}:${redis_port}/0

# Application Configuration
SECRET_KEY=${secret_key}
ADMIN_API_KEY=${admin_api_key}
ML_API_KEY=${ml_api_key}
READONLY_API_KEY=${readonly_api_key}
API_KEY_SALT=${api_key_salt}

# AWS Configuration
AWS_DEFAULT_REGION=${aws_region}
S3_BUCKET_NAME=${s3_bucket_name}

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
LOG_LEVEL=INFO

# Security
ALLOWED_ORIGINS=${allowed_origins}
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# ML Configuration
ML_MODEL_PATH=/app/ml_models
MODEL_UPDATE_INTERVAL=3600
EOF

# Set proper permissions
chmod 600 /opt/smartcloudops/.env

# Create Docker Compose file for the application
echo "🐳 Creating Docker Compose configuration..."
cat > /opt/smartcloudops/docker-compose.yml << EOF
version: '3.8'

services:
  smartcloudops-app:
    image: smartcloudops-ai:latest
    container_name: smartcloudops-app
    ports:
      - "5000:5000"
    environment:
      - ENVIRONMENT=production
      - FLASK_ENV=production
      - FLASK_APP=app.main_secure:app
      - PYTHONPATH=/app
    env_file:
      - .env
    volumes:
      - /opt/smartcloudops/logs:/app/logs
      - /opt/smartcloudops/ml_models:/app/ml_models
      - /opt/smartcloudops/data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  prometheus:
    image: prom/prometheus:latest
    container_name: smartcloudops-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: smartcloudops-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${grafana_admin_password}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards
    restart: unless-stopped
    depends_on:
      - prometheus

volumes:
  prometheus_data:
    driver: local
  grafana_data:
    driver: local
EOF

# Create monitoring configuration
echo "📊 Setting up monitoring configuration..."
mkdir -p /opt/smartcloudops/monitoring

# Prometheus configuration
cat > /opt/smartcloudops/monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - localhost:9093

scrape_configs:
  - job_name: 'smartcloudops-app'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
    scrape_interval: 15s

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']
EOF

# Create alert rules
cat > /opt/smartcloudops/monitoring/alert_rules.yml << EOF
groups:
  - name: smartcloudops_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 10% for the last 5 minutes"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is above 1 second"

      - alert: MLPipelineFailure
        expr: rate(ml_predictions_total[5m]) == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "ML pipeline failure"
          description: "No ML predictions in the last 5 minutes"
EOF

# Create systemd service for the application
echo "🔧 Creating systemd service..."
cat > /etc/systemd/system/smartcloudops.service << EOF
[Unit]
Description=SmartCloudOps AI Application
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/smartcloudops
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
echo "🚀 Starting SmartCloudOps AI service..."
systemctl daemon-reload
systemctl enable smartcloudops.service
systemctl start smartcloudops.service

# Create health check script
echo "🏥 Creating health check script..."
cat > /opt/smartcloudops/health_check.sh << 'EOF'
#!/bin/bash

# Health check script for SmartCloudOps AI

APP_URL="http://localhost:5000/health"
PROMETHEUS_URL="http://localhost:9090/-/healthy"
GRAFANA_URL="http://localhost:3000/api/health"

# Check application health
if curl -f -s "$APP_URL" > /dev/null; then
    echo "✅ Application is healthy"
    APP_STATUS=0
else
    echo "❌ Application is unhealthy"
    APP_STATUS=1
fi

# Check Prometheus health
if curl -f -s "$PROMETHEUS_URL" > /dev/null; then
    echo "✅ Prometheus is healthy"
    PROM_STATUS=0
else
    echo "❌ Prometheus is unhealthy"
    PROM_STATUS=1
fi

# Check Grafana health
if curl -f -s "$GRAFANA_URL" > /dev/null; then
    echo "✅ Grafana is healthy"
    GRAFANA_STATUS=0
else
    echo "❌ Grafana is unhealthy"
    GRAFANA_STATUS=1
fi

# Overall status
if [ $APP_STATUS -eq 0 ] && [ $PROM_STATUS -eq 0 ] && [ $GRAFANA_STATUS -eq 0 ]; then
    echo "🎉 All services are healthy"
    exit 0
else
    echo "⚠️ Some services are unhealthy"
    exit 1
fi
EOF

chmod +x /opt/smartcloudops/health_check.sh

# Create log rotation configuration
echo "📝 Setting up log rotation..."
cat > /etc/logrotate.d/smartcloudops << EOF
/opt/smartcloudops/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        systemctl reload smartcloudops.service
    endscript
}
EOF

# Install CloudWatch agent for monitoring
echo "📊 Installing CloudWatch agent..."
yum install -y amazon-cloudwatch-agent

# Configure CloudWatch agent
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << EOF
{
    "agent": {
        "metrics_collection_interval": 60,
        "run_as_user": "root"
    },
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/opt/smartcloudops/logs/*.log",
                        "log_group_name": "/aws/ec2/smartcloudops/app",
                        "log_stream_name": "{instance_id}",
                        "timezone": "UTC"
                    },
                    {
                        "file_path": "/var/log/user-data.log",
                        "log_group_name": "/aws/ec2/smartcloudops/user-data",
                        "log_stream_name": "{instance_id}",
                        "timezone": "UTC"
                    }
                ]
            }
        }
    },
    "metrics": {
        "metrics_collected": {
            "disk": {
                "measurement": [
                    "used_percent"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "mem": {
                "measurement": [
                    "mem_used_percent"
                ],
                "metrics_collection_interval": 60
            }
        }
    }
}
EOF

# Start CloudWatch agent
systemctl enable amazon-cloudwatch-agent
systemctl start amazon-cloudwatch-agent

# Create a simple status page
echo "📄 Creating status page..."
cat > /opt/smartcloudops/status.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>SmartCloudOps AI - Status</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .healthy { background-color: #d4edda; color: #155724; }
        .unhealthy { background-color: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <h1>SmartCloudOps AI - System Status</h1>
    <div id="status"></div>
    <script>
        function checkStatus() {
            fetch('/health')
                .then(response => response.json())
                .then(data => {
                    const statusDiv = document.getElementById('status');
                    const className = data.status === 'healthy' ? 'healthy' : 'unhealthy';
                    statusDiv.innerHTML = `<div class="status ${className}">Status: ${data.status}</div>`;
                })
                .catch(error => {
                    document.getElementById('status').innerHTML = 
                        '<div class="status unhealthy">Status: Error checking health</div>';
                });
        }
        checkStatus();
        setInterval(checkStatus, 30000);
    </script>
</body>
</html>
EOF

# Set up cron job for health checks
echo "⏰ Setting up health check cron job..."
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/smartcloudops/health_check.sh >> /var/log/health-check.log 2>&1") | crontab -

# Final status check
echo "🔍 Performing final status check..."
sleep 30  # Wait for services to start

if /opt/smartcloudops/health_check.sh; then
    echo "🎉 SmartCloudOps AI production server setup completed successfully!"
    echo "📊 Monitoring available at:"
    echo "   - Application: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):5000"
    echo "   - Prometheus: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):9090"
    echo "   - Grafana: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):3000"
    echo "   - Status: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):5000/status"
else
    echo "⚠️ Setup completed but some services may need attention"
    echo "Check logs: journalctl -u smartcloudops.service"
fi

echo "✅ Production server setup completed!"
