#!/bin/bash
# Production Server Setup - Replace Flask Dev Server
# Implements Gunicorn + Nginx for production-grade serving

set -euo pipefail

echo "🚀 Setting up Production Server Infrastructure..."

# Install production dependencies
sudo yum update -y
sudo yum install -y nginx
pip3 install gunicorn gevent

# Create Gunicorn configuration
cat > /home/ec2-user/smartcloudops-ai/gunicorn.conf.py << 'EOF'
import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "/var/log/smartcloudops/gunicorn-access.log"
errorlog = "/var/log/smartcloudops/gunicorn-error.log"
loglevel = "info"

# Process naming
proc_name = "smartcloudops-ai"

# Security
user = "ec2-user"
group = "ec2-user"
EOF

# Create Nginx configuration
sudo tee /etc/nginx/conf.d/smartcloudops-ai.conf << 'EOF'
upstream smartcloudops_app {
    server 127.0.0.1:8000 fail_timeout=0;
}

server {
    listen 80;
    server_name _;
    
    # Security headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    # Application
    location / {
        proxy_pass http://smartcloudops_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://smartcloudops_app;
    }
}
EOF

# Create systemd service for Gunicorn
sudo tee /etc/systemd/system/smartcloudops-ai.service << 'EOF'
[Unit]
Description=SmartCloudOps AI Gunicorn Application
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=/home/ec2-user/smartcloudops-ai/app
Environment="PATH=/home/ec2-user/smartcloudops-ai/venv/bin"
ExecStart=/home/ec2-user/smartcloudops-ai/venv/bin/gunicorn -c /home/ec2-user/smartcloudops-ai/gunicorn.conf.py main:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Create log directory
sudo mkdir -p /var/log/smartcloudops
sudo chown ec2-user:ec2-user /var/log/smartcloudops

# Enable services
sudo systemctl daemon-reload
sudo systemctl enable nginx
sudo systemctl enable smartcloudops-ai
sudo systemctl start nginx
sudo systemctl start smartcloudops-ai

echo "✅ Production server setup complete!"
