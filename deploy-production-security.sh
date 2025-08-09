#!/bin/bash
# Production security fix deployment - Simplified for direct execution

set -e
echo "🚨 Deploying security fixes to production..."

# Stop any running Flask development servers
sudo pkill -f "python.*main.py" || true
echo "✅ Stopped insecure Flask processes"

# Load new secure image
docker load < /tmp/smartcloudops-ai-security-fixed.tar.gz
echo "✅ Loaded secure Docker image"

# Stop existing container if running
docker stop smartcloudops-ai-production || true
docker rm smartcloudops-ai-production || true
echo "✅ Cleaned up old containers"

# Create secure systemd service
sudo tee /etc/systemd/system/smartcloudops-ai.service > /dev/null << 'SERVICE_EOF'
[Unit]
Description=SmartCloudOps AI Production Application
Wants=network-online.target
After=network-online.target docker.service

[Service]
Type=simple
User=ec2-user
Environment=ENVIRONMENT=production
Environment=DEBUG=false
ExecStartPre=/usr/bin/docker pull smartcloudops-ai:security-fixed || true
ExecStart=/usr/bin/docker run --name smartcloudops-ai-production \
  --rm \
  -p 5000:5000 \
  -e ENVIRONMENT=production \
  -e DEBUG=false \
  --user 1000:1000 \
  --read-only \
  --tmpfs /tmp \
  --memory=512m \
  --cpus="0.5" \
  --security-opt=no-new-privileges:true \
  smartcloudops-ai:security-fixed
ExecStop=/usr/bin/docker stop smartcloudops-ai-production
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# Enable and start secure service
sudo systemctl daemon-reload
sudo systemctl enable smartcloudops-ai
sudo systemctl start smartcloudops-ai

echo "✅ Secure systemd service deployed"

# Wait for service to start
sleep 15

# Verify secure deployment
if systemctl is-active --quiet smartcloudops-ai; then
    echo "✅ Secure service is running"
    curl -s http://localhost:5000/status | python3 -m json.tool
else
    echo "❌ Service failed to start"
    sudo systemctl status smartcloudops-ai
    exit 1
fi

echo "🎉 Security fix deployment complete!"
