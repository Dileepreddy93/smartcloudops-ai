#!/bin/bash

# SmartCloudOps AI - Production Monitoring Setup Script
# ====================================================

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

# Configuration
PROJECT_ROOT="/home/dileep-reddy/smartcloudops-ai"
MONITORING_DIR="$PROJECT_ROOT/monitoring"
LOGS_DIR="$PROJECT_ROOT/logs"

# Create directories
log "Creating monitoring directories..."
mkdir -p "$MONITORING_DIR" "$LOGS_DIR"

# Setup Python environment
log "Setting up Python environment..."
cd "$PROJECT_ROOT"
source .venv/bin/activate

# Create health check script
log "Creating health check script..."
cat > "$MONITORING_DIR/health-check.sh" << 'EOF'
#!/bin/bash

# SmartCloudOps AI Health Check
BASE_URL="http://localhost:5000"
ENDPOINTS=("/status" "/ml/health" "/api/v1/remediation/status" "/api/v1/chatops/health")

echo "🔍 SmartCloudOps AI Health Check - $(date)"
echo "=========================================="

for endpoint in "${ENDPOINTS[@]}"; do
    response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint")
    if [ "$response" = "200" ]; then
        echo "✅ $endpoint: OK"
    else
        echo "❌ $endpoint: FAILED (HTTP $response)"
    fi
done

# Check system resources
echo ""
echo "📊 System Resources:"
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "Memory: $(free | grep Mem | awk '{printf("%.1f%%", $3/$2 * 100.0)}')"
echo "Disk: $(df / | tail -1 | awk '{print $5}')"
EOF

chmod +x "$MONITORING_DIR/health-check.sh"

# Create performance monitor
log "Creating performance monitor..."
cat > "$MONITORING_DIR/performance-monitor.py" << 'EOF'
#!/usr/bin/env python3

import psutil
import time
import json
from datetime import datetime
from pathlib import Path

def collect_metrics():
    return {
        "timestamp": datetime.now().isoformat(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    }

def main():
    log_file = Path("/home/dileep-reddy/smartcloudops-ai/logs/performance.log")
    log_file.parent.mkdir(exist_ok=True)
    
    print("📊 Starting performance monitoring...")
    
    while True:
        try:
            metrics = collect_metrics()
            print(f"CPU: {metrics['cpu_percent']:.1f}% | "
                  f"Memory: {metrics['memory_percent']:.1f}% | "
                  f"Disk: {metrics['disk_percent']:.1f}%")
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(metrics) + '\n')
            
            time.sleep(30)
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped")
            break

if __name__ == "__main__":
    main()
EOF

chmod +x "$MONITORING_DIR/performance-monitor.py"

# Create monitoring startup script
log "Creating monitoring startup script..."
cat > "$MONITORING_DIR/start-monitoring.sh" << 'EOF'
#!/bin/bash

echo "🚀 Starting SmartCloudOps AI Production Monitoring..."

# Start performance monitoring
nohup /home/dileep-reddy/smartcloudops-ai/monitoring/performance-monitor.py > /dev/null 2>&1 &

# Schedule health checks
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/dileep-reddy/smartcloudops-ai/monitoring/health-check.sh >> /home/dileep-reddy/smartcloudops-ai/logs/health.log 2>&1") | crontab -

echo "✅ Monitoring started"
echo "📊 Health Check: /home/dileep-reddy/smartcloudops-ai/monitoring/health-check.sh"
echo "📈 Performance: /home/dileep-reddy/smartcloudops-ai/monitoring/performance-monitor.py"
EOF

chmod +x "$MONITORING_DIR/start-monitoring.sh"

log "🎉 Production monitoring setup complete!"
log ""
log "📋 Usage:"
log "1. Start monitoring: $MONITORING_DIR/start-monitoring.sh"
log "2. Check health: $MONITORING_DIR/health-check.sh"
log "3. View logs: tail -f $LOGS_DIR/*.log"
