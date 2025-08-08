#!/bin/bash
# SmartCloudOps AI - Production Deployment Script
# Security-hardened deployment with health checks

set -e  # Exit on any error

echo "🚀 SmartCloudOps AI - Production Deployment Starting..."
echo "=================================================="

# Configuration
CONTAINER_NAME="smartcloudops-ai-production"
IMAGE_NAME="smartcloudops-ai:production"
PORT=5000
HEALTH_CHECK_URL="http://localhost:$PORT/status"

# Environment variables for production
export ENVIRONMENT=production
export DEBUG=false
export PROMETHEUS_URL=http://3.89.229.102:9090
export AI_PROVIDER=fallback
export LOG_LEVEL=INFO

echo "📦 Stopping existing container if running..."
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

echo "🧹 Cleaning up old images..."
docker image prune -f

echo "🔄 Loading new production image..."
if [ -f "smartcloudops-ai-production.tar.gz" ]; then
    gunzip -c smartcloudops-ai-production.tar.gz | docker load
    echo "✅ Docker image loaded successfully"
else
    echo "❌ Docker image file not found"
    exit 1
fi

echo "🚀 Starting production container..."
docker run -d \
    --name $CONTAINER_NAME \
    --restart unless-stopped \
    -p $PORT:5000 \
    -e ENVIRONMENT=$ENVIRONMENT \
    -e DEBUG=$DEBUG \
    -e PROMETHEUS_URL=$PROMETHEUS_URL \
    -e AI_PROVIDER=$AI_PROVIDER \
    -e LOG_LEVEL=$LOG_LEVEL \
    --memory=512m \
    --cpus=0.5 \
    --security-opt no-new-privileges \
    --read-only \
    --tmpfs /tmp \
    $IMAGE_NAME

echo "⏳ Waiting for application to start..."
sleep 30

echo "🔍 Running health checks..."
for i in {1..10}; do
    if curl -f $HEALTH_CHECK_URL 2>/dev/null; then
        echo "✅ Health check passed!"
        break
    else
        echo "⏳ Attempt $i: Waiting for application..."
        sleep 10
    fi
    
    if [ $i -eq 10 ]; then
        echo "❌ Health check failed after 10 attempts"
        echo "📋 Container logs:"
        docker logs $CONTAINER_NAME
        exit 1
    fi
done

echo "📊 Deployment verification..."
echo "Container Status:"
docker ps | grep $CONTAINER_NAME

echo ""
echo "Application Status:"
curl -s $HEALTH_CHECK_URL | python3 -m json.tool 2>/dev/null || curl -s $HEALTH_CHECK_URL

echo ""
echo "🎉 DEPLOYMENT SUCCESSFUL!"
echo "=================================================="
echo "🌐 Application URL: http://44.200.14.5:$PORT"
echo "📊 Status Endpoint: http://44.200.14.5:$PORT/status"
echo "🤖 Chat Endpoint: http://44.200.14.5:$PORT/chat"
echo "🧠 ML Health: http://44.200.14.5:$PORT/ml/health"
echo "📈 ML Predict: http://44.200.14.5:$PORT/ml/predict"
echo "📊 ML Metrics: http://44.200.14.5:$PORT/ml/metrics"
echo "=================================================="

echo "📋 Post-deployment monitoring:"
echo "- Container will restart automatically if it crashes"
echo "- Health checks run every 30 seconds"
echo "- Resource limits: 512MB RAM, 0.5 CPU cores"
echo "- Security: Read-only filesystem, no new privileges"
echo ""
echo "🔍 To monitor: docker logs -f $CONTAINER_NAME"
echo "🛑 To stop: docker stop $CONTAINER_NAME"
