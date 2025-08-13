# 🚀 SmartCloudOps AI - Production Deployment Guide

## 📋 Prerequisites

- AWS EC2 instance running (already deployed: `44.200.14.5`)
- Docker installed on EC2 instance
- SSH access to EC2 instance
- Security groups configured for port 5000

## 🎯 Quick Deployment

### 1. Upload Files to EC2

```bash
# Upload deployment files
scp -i your-key.pem smartcloudops-ai-production.tar.gz ec2-user@44.200.14.5:/home/ec2-user/
scp -i your-key.pem deploy-production.sh ec2-user@44.200.14.5:/home/ec2-user/
```

### 2. Execute Deployment

```bash
# SSH to EC2 instance
ssh -i your-key.pem ec2-user@44.200.14.5

# Run deployment script
chmod +x deploy-production.sh
./deploy-production.sh
```

## 🔧 Manual Deployment Steps

If you prefer manual deployment:

```bash
# 1. Load Docker image
gunzip -c smartcloudops-ai-production.tar.gz | docker load

# 2. Stop existing container
docker stop smartcloudops-ai-production 2>/dev/null || true
docker rm smartcloudops-ai-production 2>/dev/null || true

# 3. Run production container
docker run -d \
    --name smartcloudops-ai-production \
    --restart unless-stopped \
    -p 5000:5000 \
    -e ENVIRONMENT=production \
    -e DEBUG=false \
    -e PROMETHEUS_URL=http://3.89.229.102:9090 \
    -e AI_PROVIDER=fallback \
    -e LOG_LEVEL=INFO \
    --memory=512m \
    --cpus=0.5 \
    --security-opt no-new-privileges \
    --read-only \
    --tmpfs /tmp \
    smartcloudops-ai:production

# 4. Verify deployment
curl http://localhost:5000/status
```

## 🌐 Production URLs

Once deployed, the application will be available at:

- **Main Application**: http://44.200.14.5:5000
- **Health Status**: http://44.200.14.5:5000/status
- **Chat Interface**: http://44.200.14.5:5000/chat (POST)
- **ML Health**: http://44.200.14.5:5000/ml/health
- **ML Prediction**: http://44.200.14.5:5000/ml/predict (POST)
- **ML Metrics**: http://44.200.14.5:5000/ml/metrics

## 🧪 Testing Endpoints

```bash
# Health check
curl http://44.200.14.5:5000/status

# Chat test
curl -X POST -H "Content-Type: application/json" \
     -d '{"message":"hello"}' \
     http://44.200.14.5:5000/chat

# ML health
curl http://44.200.14.5:5000/ml/health
```

## 📊 Monitoring

```bash
# View container logs
docker logs -f smartcloudops-ai-production

# Check container status
docker ps | grep smartcloudops

# Resource usage
docker stats smartcloudops-ai-production
```

## 🛡️ Security Features

- ✅ Non-root container execution
- ✅ Read-only filesystem
- ✅ Resource limits (512MB RAM, 0.5 CPU)
- ✅ No new privileges
- ✅ Secure environment variables
- ✅ Health checks every 30 seconds

## 🔄 Updates

To update the application:

1. Build new Docker image
2. Create new deployment package
3. Upload to EC2
4. Run deployment script (handles zero-downtime updates)

## 🚨 Troubleshooting

### Container won't start
```bash
docker logs smartcloudops-ai-production
```

### Application not responding
```bash
# Check if container is running
docker ps

# Check health
curl http://localhost:5000/status
```

### Resource issues
```bash
# Check resource usage
docker stats

# Free up space
docker system prune -f
```

## 📈 Performance Monitoring

The application includes:
- Comprehensive logging
- Health check endpoints
- Performance metrics
- Error handling and recovery

## 🎉 Success Criteria

Deployment is successful when:
- ✅ Container starts without errors
- ✅ Health endpoint returns 200
- ✅ Chat endpoint responds correctly
- ✅ ML components are accessible
- ✅ Application serves on port 5000
