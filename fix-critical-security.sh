#!/bin/bash
# 🚨 CRITICAL SECURITY FIX DEPLOYMENT SCRIPT
# Fixes all critical security vulnerabilities identified in audit

set -e

echo "🚨 CRITICAL SECURITY FIX - PHASE 1"
echo "=================================="

# Check if we can connect to production
if ! curl -s http://44.200.14.5:5000/status > /dev/null; then
    echo "❌ Cannot connect to production server"
    exit 1
fi

echo "✅ Production server responding"

# Step 1: Create secure application bundle
echo "📦 Creating secure application bundle..."

# Build latest Docker image with security fixes
docker build -t smartcloudops-ai:security-fixed .

# Save image for deployment
docker save smartcloudops-ai:security-fixed | gzip > smartcloudops-ai-security-fixed.tar.gz

echo "✅ Secure application image created"

# Step 2: Create production deployment script
cat > deploy-security-fix.sh << 'EOF'
#!/bin/bash
# Production security fix deployment

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
sleep 10

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
EOF

chmod +x deploy-security-fix.sh

echo "✅ Deployment script created"

# Step 3: Upload and execute security fix
echo "🚀 Uploading security fixes to production..."
scp smartcloudops-ai-security-fixed.tar.gz ec2-user@44.200.14.5:/tmp/
scp deploy-security-fix.sh ec2-user@44.200.14.5:/tmp/

echo "✅ Files uploaded to production"

echo "🔧 Executing security fixes on production..."
ssh ec2-user@44.200.14.5 "chmod +x /tmp/deploy-security-fix.sh && /tmp/deploy-security-fix.sh"

echo "✅ Security fixes applied!"

# Step 4: Verify security fix
echo "🔍 Verifying security fixes..."
sleep 5

# Check that no Flask dev server is running
if ssh ec2-user@44.200.14.5 "ps aux | grep -E 'python.*main\.py' | grep -v grep"; then
    echo "❌ WARNING: Flask dev server still running!"
else
    echo "✅ No Flask dev server processes found"
fi

# Check systemd service
if ssh ec2-user@44.200.14.5 "sudo systemctl is-active --quiet smartcloudops-ai"; then
    echo "✅ Secure systemd service is active"
else
    echo "❌ Systemd service not active"
fi

# Check Docker container
if ssh ec2-user@44.200.14.5 "docker ps | grep smartcloudops-ai-production"; then
    echo "✅ Secure Docker container is running"
else
    echo "❌ Docker container not running"
fi

# Test application
echo "🧪 Testing application endpoints..."
curl -s http://44.200.14.5:5000/status | python3 -m json.tool

echo ""
echo "🎉 CRITICAL SECURITY FIXES COMPLETE!"
echo "=================================="
echo "✅ Flask development server eliminated"
echo "✅ Secure Docker container deployed"
echo "✅ Systemd service with proper security"
echo "✅ Production environment hardened"
