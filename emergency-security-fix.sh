#!/bin/bash
# 🚨 EMERGENCY PRODUCTION SECURITY FIX
# Fix critical Flask development server vulnerability

set -e
echo "🚨 EMERGENCY: Fixing critical security vulnerability..."

# 1. Stop insecure Flask development server
echo "Stopping insecure Flask server..."
ssh ec2-user@44.200.14.5 "sudo pkill -f 'python main.py' || true"

# 2. Create proper systemd service
echo "Creating secure systemd service..."
ssh ec2-user@44.200.14.5 "sudo bash -c 'cat > /etc/systemd/system/smartcloudops-ai.service << EOF
[Unit]
Description=SmartCloudOps AI Flask Application
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/smartcloudops-ai
Environment=PATH=/opt/smartcloudops-ai/venv/bin
Environment=ENVIRONMENT=production
Environment=DEBUG=false
ExecStartPre=/bin/bash -lc \"test -f /opt/smartcloudops-ai/app/main.py\"
ExecStart=/opt/smartcloudops-ai/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 --worker-class sync app.main:app
Restart=always
RestartSec=3
StandardOutput=append:/opt/smartcloudops-ai/logs/app.log
StandardError=append:/opt/smartcloudops-ai/logs/app.err

[Install]
WantedBy=multi-user.target
EOF'"

# 3. Ensure gunicorn is installed
echo "Installing gunicorn..."
ssh ec2-user@44.200.14.5 "cd /opt/smartcloudops-ai && source venv/bin/activate && pip install gunicorn"

# 4. Start secure service
echo "Starting secure Gunicorn service..."
ssh ec2-user@44.200.14.5 "sudo systemctl daemon-reload && sudo systemctl enable smartcloudops-ai && sudo systemctl start smartcloudops-ai"

# 5. Verify secure deployment
echo "Verifying secure deployment..."
sleep 5
ssh ec2-user@44.200.14.5 "sudo systemctl status smartcloudops-ai && ps aux | grep gunicorn | grep -v grep"

echo "✅ Emergency fix complete! Production now running on secure Gunicorn server."
