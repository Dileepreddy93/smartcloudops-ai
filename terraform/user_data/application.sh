#!/bin/bash
# User Data Script for Application Instance (Phase 2)
# Installs: Python, Flask, Docker, Node Exporter

set -e

# Update system
yum update -y
yum install -y wget curl unzip git

# Install Python (prefer 3.8+) and pip
if command -v amazon-linux-extras >/dev/null 2>&1; then
  amazon-linux-extras enable python3.8 >/dev/null 2>&1 || true
  yum clean metadata -y || true
  yum install -y python3.8 python3.8-devel || true
fi
yum install -y python3 python3-pip python3-devel || true
PY3=$(command -v python3.8 || command -v python3)
"$PY3" -m pip install --upgrade pip

# Install Docker (Phase 2.3)
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Node.js for potential frontend needs
curl -sL https://rpm.nodesource.com/setup_18.x | bash -
yum install -y nodejs

# Create application user
useradd --create-home --shell /bin/bash appuser
useradd --no-create-home --shell /bin/false node_exporter

# Install Node Exporter for monitoring (Phase 1.2.2)
cd /tmp
wget https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
tar xvfz node_exporter-1.7.0.linux-amd64.tar.gz
cp node_exporter-1.7.0.linux-amd64/node_exporter /usr/local/bin/
chown node_exporter:node_exporter /usr/local/bin/node_exporter

# Create systemd service for Node Exporter
cat > /etc/systemd/system/node_exporter.service << 'EOF'
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF

# Create application directory structure
mkdir -p /opt/smartcloudops-ai
mkdir -p /opt/smartcloudops-ai/app
mkdir -p /opt/smartcloudops-ai/logs
mkdir -p /opt/smartcloudops-ai/data
mkdir -p /opt/smartcloudops-ai/scripts
mkdir -p /opt/smartcloudops-ai/ml_models/optimized
chown -R appuser:appuser /opt/smartcloudops-ai

# Create Python virtual environment
cd /opt/smartcloudops-ai
"$PY3" -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Install Python dependencies for Flask app (Phase 2.1)
pip install --no-cache-dir -r https://raw.githubusercontent.com/Dileepreddy93/smartcloudops-ai/main/app/requirements.txt || true
# Fallback explicit runtime deps (ensures ML imports work even if the above fails)
pip install --no-cache-dir flask gunicorn requests boto3 prometheus-client psutil pandas numpy scikit-learn joblib google-generativeai openai || true

# Deploy application code from GitHub (latest main)
cd /opt/smartcloudops-ai
git init
git remote add origin https://github.com/Dileepreddy93/smartcloudops-ai.git || true
git fetch --depth=1 origin main || true
git checkout -f FETCH_HEAD || true

# Fallback minimal Flask app if git fetch fails
if [ ! -f /opt/smartcloudops-ai/app/main.py ]; then
cat > /opt/smartcloudops-ai/app/main.py << 'EOF'
from flask import Flask, request, jsonify
import os
import logging
import boto3
from datetime import datetime
import psutil

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

# Status endpoint (Phase 2.1)
@app.route('/status', methods=['GET'])
def status():
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return jsonify({
            'status': 'running',
            'timestamp': datetime.now().isoformat(),
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': (disk.used / disk.total) * 100,
                'uptime': datetime.now().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Query endpoint for ChatOps (Phase 2.1)
@app.route('/query', methods=['POST'])
def query():
    try:
        data = request.get_json()
        query_text = data.get('query', '')
        
        # Basic response - will be enhanced with GPT integration (Phase 2.2)
        response = {
            'query': query_text,
            'response': f"Echo: {query_text}",
            'timestamp': datetime.now().isoformat(),
            'status': 'processed'
        }
        
        logger.info(f"Processed query: {query_text}")
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Query processing failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Logs endpoint (Phase 2.1)
@app.route('/logs', methods=['GET'])
def logs():
    try:
        # Return recent log entries
        log_lines = []
        log_file = '/opt/smartcloudops-ai/logs/app.log'
        
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                log_lines = f.readlines()[-50:]  # Last 50 lines
        
        return jsonify({
            'logs': log_lines,
            'count': len(log_lines),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Log retrieval failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
EOF
fi

# Install application requirements from repository
cd /opt/smartcloudops-ai
source venv/bin/activate
if [ -f app/requirements.txt ]; then
  pip install --no-cache-dir -r app/requirements.txt || true
fi

# Remove legacy inline requirements.txt creation (repo requirements is used)

# Create systemd service for Flask app
cat > /etc/systemd/system/smartcloudops-ai.service << 'EOF'
[Unit]
Description=SmartCloudOps AI Flask Application
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/opt/smartcloudops-ai
Environment=PATH=/opt/smartcloudops-ai/venv/bin
EnvironmentFile=-/etc/profile.d/smartcloudops-ai.sh
ExecStartPre=/bin/bash -lc 'test -x /opt/smartcloudops-ai/venv/bin/gunicorn'
ExecStartPre=/bin/bash -lc 'test -f /opt/smartcloudops-ai/app/main.py'
ExecStart=/opt/smartcloudops-ai/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 app.main:app
Restart=always
RestartSec=3
StandardOutput=append:/opt/smartcloudops-ai/logs/app.log
StandardError=append:/opt/smartcloudops-ai/logs/app.err

[Install]
WantedBy=multi-user.target
EOF

# Configure environment for ML S3 bucket and Prometheus
cat > /etc/profile.d/smartcloudops-ai.sh << 'EOF'
# Injected by Terraform template
export S3_ML_MODELS_BUCKET="${ml_models_bucket}"
export ML_MODELS_BUCKET="$S3_ML_MODELS_BUCKET"
export PROMETHEUS_URL="http://${prometheus_host}:${prometheus_port}"
EOF

# Create systemd service and timer for periodic training (daily)
cat > /etc/systemd/system/smartcloudops-train.service << 'EOF'
[Unit]
Description=SmartCloudOps AI - Real Data Training
After=network.target

[Service]
Type=oneshot
User=appuser
WorkingDirectory=/opt/smartcloudops-ai
Environment=PATH=/opt/smartcloudops-ai/venv/bin
EnvironmentFile=-/etc/profile.d/smartcloudops-ai.sh
ExecStart=/opt/smartcloudops-ai/venv/bin/python /opt/smartcloudops-ai/scripts/train_model.py
EOF

cat > /etc/systemd/system/smartcloudops-train.timer << 'EOF'
[Unit]
Description=Run SmartCloudOps AI Training daily

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Create Dockerfile (Phase 2.3)
cat > /opt/smartcloudops-ai/Dockerfile << 'EOF'
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app.main:app"]
EOF

# Install CloudWatch agent for log shipping
yum install -y amazon-cloudwatch-agent

# Configure CloudWatch agent
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << EOF
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/opt/smartcloudops-ai/logs/app.log",
            "log_group_name": "/aws/ec2/${project_name}-application",
            "log_stream_name": "app-logs"
          },
          {
            "file_path": "/var/log/messages",
            "log_group_name": "/aws/ec2/${project_name}-application",
            "log_stream_name": "system-logs"
          }
        ]
      }
    }
  }
}
EOF

# Set permissions
chown -R appuser:appuser /opt/smartcloudops-ai

# Start services
systemctl daemon-reload
systemctl start node_exporter
systemctl enable node_exporter
systemctl start smartcloudops-ai
systemctl enable smartcloudops-ai
systemctl enable smartcloudops-train.timer
systemctl start smartcloudops-train.timer

# Start CloudWatch agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json

# Create management scripts
cat > /home/ec2-user/app-status.sh << 'EOF'
#!/bin/bash
echo "=== SmartCloudOps AI Application Status ==="
echo "Date: $(date)"
echo ""
echo "Services Status:"
systemctl is-active smartcloudops-ai && echo "✓ Flask App: Running" || echo "✗ Flask App: Stopped"
systemctl is-active node_exporter && echo "✓ Node Exporter: Running" || echo "✗ Node Exporter: Stopped"
systemctl is-active docker && echo "✓ Docker: Running" || echo "✗ Docker: Stopped"
echo ""
echo "Application URL:"
echo "- Flask App: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):5000"
echo ""
echo "Test endpoints:"
echo "curl http://localhost:5000/health"
echo "curl http://localhost:5000/status"
echo ""
echo "View logs: journalctl -u smartcloudops-ai -f"
EOF

cat > /home/ec2-user/deploy-app.sh << 'EOF'
#!/bin/bash
echo "Deploying SmartCloudOps AI application..."
cd /opt/smartcloudops-ai

# Pull latest code (if git repo is set up)
# git pull origin main

# Rebuild virtual environment if needed
source venv/bin/activate
pip install -r requirements.txt

# Restart application
sudo systemctl restart smartcloudops-ai

echo "Application deployed and restarted!"
echo "Check status with: ./app-status.sh"
EOF

chmod +x /home/ec2-user/app-status.sh
chmod +x /home/ec2-user/deploy-app.sh
chown ec2-user:ec2-user /home/ec2-user/app-status.sh
chown ec2-user:ec2-user /home/ec2-user/deploy-app.sh

# Create welcome message
cat > /etc/motd << 'EOF'
   ____                      _    ____ _                 _  ___            
  / ___| _ __ ___   __ _ _ __| |_ / ___| | ___  _   _  __| |/ _ \ _ __  ___  
  \___ \| '_ ` _ \ / _` | '__| __| |   | |/ _ \| | | |/ _` | | | | '_ \/ __| 
   ___) | | | | | | (_| | |  | |_| |___| | (_) | |_| | (_| | |_| | |_) \__ \ 
  |____/|_| |_| |_|\__,_|_|   \__|\____|_|\___/ \__,_|\__,_|\___/| .__/|___/ 
                                                                |_|        
  
  🚀 APPLICATION INSTANCE - Phase 2 Setup Complete
  
  Flask Application: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):5000
  
  Management Commands:
  - ./app-status.sh    - Check application status
  - ./deploy-app.sh    - Deploy/restart application
  
  Endpoints:
  - GET  /health       - Health check
  - GET  /status       - System status
  - POST /query        - ChatOps queries
  - GET  /logs         - Application logs
  
EOF

echo "Application instance setup completed successfully!" > /var/log/user-data.log
