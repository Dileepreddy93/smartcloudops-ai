#!/bin/bash
# SmartCloudOps AI - Secure Production Deployment Script
# This script implements emergency security fixes

set -euo pipefail  # Exit on error, undefined vars, pipe failures

echo "🚨 EMERGENCY SECURITY FIX DEPLOYMENT"
echo "====================================="

# Check if we're in the right directory
if [[ ! -f "app/main.py" ]]; then
    echo "❌ Error: Not in SmartCloudOps AI root directory"
    exit 1
fi

# Check environment
ENVIRONMENT=${ENVIRONMENT:-production}
echo "📋 Environment: $ENVIRONMENT"

# Security validations
echo "🔒 Running security validations..."

# 1. Check for sensitive files in git
echo "   Checking for sensitive files in git..."
if git ls-files | grep -E "\.(env|key|pem|p12)$" | grep -v ".env.example"; then
    echo "❌ ERROR: Sensitive files found in git! Remove them before deployment."
    echo "   Run: git rm <sensitive-file> && git commit -m 'Remove sensitive file'"
    exit 1
fi

# 2. Check for hardcoded secrets
echo "   Scanning for hardcoded secrets..."
if grep -r -i "secret.*=" app/ --include="*.py" | grep -v "SECRET_KEY.*get_secret\|SECRET_KEY.*config\|# secret"; then
    echo "❌ ERROR: Potential hardcoded secrets found!"
    echo "   Review the files above and ensure secrets are properly externalized."
    exit 1
fi

# 3. Validate required environment variables for production
if [[ "$ENVIRONMENT" == "production" ]]; then
    echo "   Validating production requirements..."
    
    required_vars=(
        "SECRET_KEY"
        "PROMETHEUS_URL" 
        "AWS_REGION"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            echo "❌ ERROR: Required environment variable $var is not set"
            exit 1
        fi
    done
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &>/dev/null; then
        echo "❌ ERROR: AWS credentials not configured or invalid"
        exit 1
    fi
    
    # Validate Prometheus URL is HTTPS
    if [[ ! "$PROMETHEUS_URL" =~ ^https:// ]]; then
        echo "❌ ERROR: Production Prometheus URL must use HTTPS"
        exit 1
    fi
fi

# 4. Test configuration loading
echo "   Testing secure configuration..."
if ! python3 -c "
import sys
sys.path.append('app')
try:
    from config import config
    print(f'✅ Configuration loaded for {config.environment}')
    if config.environment == 'production':
        assert not config.debug, 'Debug mode must be disabled in production'
        assert config.prometheus.url.startswith('https://'), 'Production must use HTTPS'
    print('✅ All configuration validations passed')
except Exception as e:
    print(f'❌ Configuration error: {e}')
    sys.exit(1)
"; then
    echo "❌ ERROR: Configuration validation failed"
    exit 1
fi

echo "✅ All security validations passed"

# Install/update dependencies
echo "📦 Installing secure dependencies..."
pip install --upgrade pip
pip install -r app/requirements.txt
pip install python-dotenv boto3 requests prometheus-client

# Run tests if available
if [[ -d "tests" ]]; then
    echo "🧪 Running security tests..."
    python -m pytest tests/ -v
fi

# Create secure directories
echo "📁 Setting up secure directories..."
mkdir -p logs
mkdir -p ml_models
mkdir -p data
chmod 750 logs ml_models data

# Set file permissions
echo "🔐 Setting secure file permissions..."
find app/ -name "*.py" -exec chmod 644 {} \;
chmod 600 .env* 2>/dev/null || true
chmod 700 scripts/*.py 2>/dev/null || true

# Health check
echo "🏥 Running health check..."
if python3 -c "
import sys
sys.path.append('app')
from main import app
with app.test_client() as client:
    response = client.get('/health')
    if response.status_code == 200:
        print('✅ Health check passed')
    else:
        print(f'❌ Health check failed: {response.status_code}')
        sys.exit(1)
"; then
    echo "✅ Application health check passed"
else
    echo "❌ Health check failed"
    exit 1
fi

# Generate deployment report
echo "📊 Generating deployment report..."
cat > deployment-report-$(date +%Y%m%d-%H%M%S).txt << EOF
SmartCloudOps AI - Secure Deployment Report
==========================================
Date: $(date)
Environment: $ENVIRONMENT
Deployed by: $(whoami)
Git commit: $(git rev-parse HEAD)
Git branch: $(git branch --show-current)

Security Validations:
✅ No sensitive files in git
✅ No hardcoded secrets detected
✅ Configuration validation passed
✅ Dependencies updated
✅ File permissions secured
✅ Health check passed

Configuration Summary:
$(python3 -c "
import sys
sys.path.append('app')
from config import config
import json
print(json.dumps(config.to_dict(), indent=2))
")
EOF

echo ""
echo "🎉 SECURE DEPLOYMENT COMPLETED SUCCESSFULLY!"
echo "============================================="
echo "📋 Environment: $ENVIRONMENT"
echo "🔐 Security: All validations passed"
echo "📊 Report: deployment-report-$(date +%Y%m%d-%H%M%S).txt"
echo ""
echo "🚀 Application is ready to start with:"
echo "   python3 app/main.py"
echo ""
echo "🔍 Monitor logs in: logs/"
echo "📈 Metrics available at: /metrics"
echo "🏥 Health check at: /health"
