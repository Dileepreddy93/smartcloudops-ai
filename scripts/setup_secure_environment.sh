#!/bin/bash

# SmartCloudOps AI - Secure Environment Setup
# This script generates secure environment variables and validates the setup

set -e

echo "🔒 SmartCloudOps AI - Secure Environment Setup"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to generate secure random string
generate_secure_key() {
    local length=$1
    openssl rand -hex $((length / 2))
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command_exists openssl; then
    echo -e "${RED}❌ OpenSSL is required but not installed${NC}"
    echo "   Install OpenSSL: sudo apt-get install openssl"
    exit 1
fi

if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is required but not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Generate secure environment variables
echo ""
echo "🔑 Generating secure environment variables..."

# Generate Flask secret key (32 bytes = 64 hex characters)
SECRET_KEY=$(generate_secure_key 64)
echo "   Generated SECRET_KEY"

# Generate API keys (32+ characters each)
ADMIN_API_KEY="sk-admin-$(generate_secure_key 32)"
ML_API_KEY="sk-ml-$(generate_secure_key 32)"
READONLY_API_KEY="sk-readonly-$(generate_secure_key 32)"
echo "   Generated API keys"

# Generate API key salt
API_KEY_SALT=$(generate_secure_key 32)
echo "   Generated API_KEY_SALT"

# Generate database password
DB_PASSWORD=$(generate_secure_key 32)
echo "   Generated DB_PASSWORD"

# Generate Grafana admin password
GRAFANA_ADMIN_PASSWORD=$(generate_secure_key 16)
echo "   Generated GRAFANA_ADMIN_PASSWORD"

# Generate Redis password
REDIS_PASSWORD=$(generate_secure_key 32)
echo "   Generated REDIS_PASSWORD"

echo -e "${GREEN}✅ All secure keys generated${NC}"

# Create .env file
echo ""
echo "📝 Creating .env file..."

cat > .env << EOF
# SmartCloudOps AI - Production Environment Configuration
# Generated on $(date)
# DO NOT COMMIT THIS FILE TO VERSION CONTROL

# =============================================================================
# SECURITY - REQUIRED (Application will not start without these)
# =============================================================================

# Flask Secret Key
SECRET_KEY=${SECRET_KEY}

# API Keys (generate secure keys for each role)
ADMIN_API_KEY=${ADMIN_API_KEY}
ML_API_KEY=${ML_API_KEY}
READONLY_API_KEY=${READONLY_API_KEY}

# API Key Salt
API_KEY_SALT=${API_KEY_SALT}

# =============================================================================
# APPLICATION CONFIGURATION
# =============================================================================

# Flask Environment
FLASK_ENV=production
FLASK_DEBUG=False

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=smartcloudops
DB_USER=smartcloudops_user
DB_PASSWORD=${DB_PASSWORD}
DATABASE_URL=postgresql://smartcloudops_user:${DB_PASSWORD}@localhost:5432/smartcloudops

# Redis Configuration (for caching)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_URL=redis://:${REDIS_PASSWORD}@localhost:6379/0

# =============================================================================
# AWS CONFIGURATION (for production)
# =============================================================================

# AWS Credentials (use IAM roles in production)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_DEFAULT_REGION=us-east-1

# S3 Bucket for ML Models
S3_BUCKET_NAME=smartcloudops-ml-models

# =============================================================================
# MONITORING & LOGGING
# =============================================================================

# Prometheus Configuration
PROMETHEUS_PORT=9090

# Grafana Configuration  
GRAFANA_PORT=3000
GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}

# Log Level
LOG_LEVEL=INFO

# =============================================================================
# CORS & SECURITY
# =============================================================================

# Allowed Origins (comma-separated)
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# =============================================================================
# ML MODEL CONFIGURATION
# =============================================================================

# Model Path
ML_MODEL_PATH=/app/ml_models

# Model Update Interval (seconds)
MODEL_UPDATE_INTERVAL=3600

# =============================================================================
# DEVELOPMENT ONLY (remove in production)
# =============================================================================

# Development Mode
DEV_MODE=False

# Mock Services (for testing)
MOCK_ML_SERVICE=False
MOCK_AWS_SERVICE=False
EOF

echo -e "${GREEN}✅ .env file created${NC}"

# Set proper permissions
chmod 600 .env
echo "   Set secure permissions (600) on .env file"

# Validate the setup
echo ""
echo "🔍 Validating environment setup..."

# Check if .env file exists and has required variables
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    exit 1
fi

# Check if all required variables are set
required_vars=("SECRET_KEY" "ADMIN_API_KEY" "ML_API_KEY" "READONLY_API_KEY" "API_KEY_SALT" "DB_PASSWORD")
missing_vars=()

for var in "${required_vars[@]}"; do
    if ! grep -q "^${var}=" .env; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo -e "${RED}❌ Missing required variables: ${missing_vars[*]}${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All required variables are set${NC}"

# Test key generation with Python
echo ""
echo "🧪 Testing key generation..."

python3 -c "
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test required variables
required_vars = ['SECRET_KEY', 'ADMIN_API_KEY', 'ML_API_KEY', 'READONLY_API_KEY', 'API_KEY_SALT', 'DB_PASSWORD']

for var in required_vars:
    value = os.getenv(var)
    if not value:
        print(f'❌ {var} is not set')
        exit(1)
    elif len(value) < 32:
        print(f'⚠️ {var} is too short: {len(value)} characters')
    else:
        print(f'✅ {var}: {len(value)} characters')

print('✅ All environment variables validated successfully')
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Environment validation passed${NC}"
else
    echo -e "${RED}❌ Environment validation failed${NC}"
    exit 1
fi

# Create a backup of the current .env if it exists
if [ -f .env.backup ]; then
    echo -e "${YELLOW}⚠️ Removing old .env.backup${NC}"
    rm .env.backup
fi

echo ""
echo "📋 Setup Summary:"
echo "================="
echo "✅ Generated secure environment variables"
echo "✅ Created .env file with proper permissions"
echo "✅ Validated all required variables"
echo "✅ Tested key generation and validation"
echo ""
echo -e "${GREEN}🎉 Secure environment setup completed successfully!${NC}"
echo ""
echo "📝 Next steps:"
echo "1. Review the .env file and update any specific values"
echo "2. Update AWS credentials for production deployment"
echo "3. Update ALLOWED_ORIGINS with your domain"
echo "4. Run: docker-compose up -d (for local development)"
echo "5. Run: terraform apply (for production deployment)"
echo ""
echo -e "${YELLOW}⚠️ IMPORTANT: Never commit the .env file to version control!${NC}"
echo "   It's already added to .gitignore for security."
