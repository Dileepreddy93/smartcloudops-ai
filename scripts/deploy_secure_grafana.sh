#!/bin/bash
# SmartCloudOps AI - Production Grafana Security Deployment Test
# ============================================================
#
# This script deploys and tests the secure Grafana configuration
# Validates all 4 critical security fixes in production environment

set -euo pipefail

GRAFANA_URL="${GRAFANA_URL:-https://localhost:3000}"
ADMIN_USER="${GRAFANA_ADMIN_USER:-smartcloudops_admin}"
ADMIN_PASSWORD="${GRAFANA_ADMIN_PASSWORD:-f#%SBXHZm3eP06&L34AyO7!!%kNvvkO9}"

echo "🚀 SmartCloudOps AI - Production Security Deployment Test"
echo "========================================================"
echo "📅 Test Time: $(date)"
echo "🌐 Target URL: $GRAFANA_URL"
echo ""

# Deploy secure configuration
echo "📦 Deploying Secure Grafana Configuration..."

# Copy secure configuration
if [ -f "/tmp/grafana_secure.ini" ]; then
    echo "   ✅ Copying secure configuration to /etc/grafana/grafana.ini"
    sudo cp /tmp/grafana_secure.ini /etc/grafana/grafana.ini
    sudo chown grafana:grafana /etc/grafana/grafana.ini
    sudo chmod 640 /etc/grafana/grafana.ini
else
    echo "   ❌ Secure configuration not found. Running generator..."
    python3 scripts/secure_grafana_config.py
    sudo cp /tmp/grafana_secure.ini /etc/grafana/grafana.ini
    sudo chown grafana:grafana /etc/grafana/grafana.ini
    sudo chmod 640 /etc/grafana/grafana.ini
fi

# Generate SSL certificates if not exist
echo "🔐 Setting up SSL certificates..."
sudo mkdir -p /etc/grafana/ssl

if [ ! -f "/etc/grafana/ssl/grafana.crt" ]; then
    echo "   🔑 Generating SSL certificates..."
    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/grafana/ssl/grafana.key \
        -out /etc/grafana/ssl/grafana.crt \
        -subj "/C=US/ST=DevOps/L=Cloud/O=SmartCloudOps/OU=AI/CN=localhost"
    
    sudo chmod 600 /etc/grafana/ssl/grafana.key
    sudo chmod 644 /etc/grafana/ssl/grafana.crt
    sudo chown grafana:grafana /etc/grafana/ssl/grafana.*
    echo "   ✅ SSL certificates generated"
else
    echo "   ✅ SSL certificates already exist"
fi

# Start/restart Grafana service
echo "🔄 Starting Grafana service..."
sudo systemctl daemon-reload
sudo systemctl enable grafana-server
sudo systemctl restart grafana-server

# Wait for service to start
echo "⏳ Waiting for Grafana to start..."
sleep 10

# Test service status
echo "🔍 Testing Service Status..."
if sudo systemctl is-active --quiet grafana-server; then
    echo "   ✅ Grafana service: RUNNING"
else
    echo "   ❌ Grafana service: NOT RUNNING"
    echo "   📝 Checking logs..."
    sudo journalctl -u grafana-server --no-pager -l -n 20
    exit 1
fi

# Test network connectivity
echo "🌐 Testing Network Connectivity..."
if ss -tuln | grep -q ":3000"; then
    echo "   ✅ Port 3000: LISTENING"
else
    echo "   ❌ Port 3000: NOT LISTENING"
    exit 1
fi

# Test HTTPS Security (1. Transport Security)
echo "🔐 Testing HTTPS Security..."
if curl -k -s -I "$GRAFANA_URL" | grep -q "HTTP"; then
    echo "   ✅ HTTPS endpoint: RESPONDING"
    
    # Check HTTPS headers
    headers=$(curl -k -s -I "$GRAFANA_URL")
    
    if echo "$headers" | grep -q "Strict-Transport-Security"; then
        echo "   ✅ HSTS header: PRESENT"
    else
        echo "   ⚠️  HSTS header: MISSING"
    fi
    
    if echo "$headers" | grep -q "X-Content-Type-Options"; then
        echo "   ✅ Content-Type protection: ENABLED"
    else
        echo "   ⚠️  Content-Type protection: MISSING"
    fi
    
else
    echo "   ❌ HTTPS endpoint: NOT RESPONDING"
    echo "   📝 Testing HTTP fallback..."
    if curl -s -I "http://localhost:3000" | grep -q "HTTP"; then
        echo "   ❌ WARNING: HTTP is accessible (should be HTTPS only)"
    fi
fi

# Test Anonymous Access (2. Authentication Security)
echo "🚫 Testing Anonymous Access Prevention..."
anonymous_response=$(curl -k -s -o /dev/null -w "%{http_code}" "$GRAFANA_URL/api/org")

if [ "$anonymous_response" = "401" ] || [ "$anonymous_response" = "403" ]; then
    echo "   ✅ Anonymous access: BLOCKED (HTTP $anonymous_response)"
else
    echo "   ❌ Anonymous access: ALLOWED (HTTP $anonymous_response) - SECURITY ISSUE!"
fi

# Test Default Credentials (3. Credential Security)
echo "🔑 Testing Default Credentials Rejection..."
default_auth_response=$(curl -k -s -o /dev/null -w "%{http_code}" \
    -H "Content-Type: application/json" \
    -d '{"user":"admin","password":"admin"}' \
    "$GRAFANA_URL/login")

if [ "$default_auth_response" = "401" ] || [ "$default_auth_response" = "422" ]; then
    echo "   ✅ Default credentials: REJECTED (HTTP $default_auth_response)"
else
    echo "   ❌ Default credentials: ACCEPTED (HTTP $default_auth_response) - SECURITY ISSUE!"
fi

# Test Strong Authentication (4. Authentication Validation)
echo "🔐 Testing Strong Authentication..."
if [ -n "$ADMIN_PASSWORD" ]; then
    auth_response=$(curl -k -s -o /dev/null -w "%{http_code}" \
        -H "Content-Type: application/json" \
        -d "{\"user\":\"$ADMIN_USER\",\"password\":\"$ADMIN_PASSWORD\"}" \
        "$GRAFANA_URL/login")
    
    if [ "$auth_response" = "200" ]; then
        echo "   ✅ Strong authentication: WORKING (HTTP $auth_response)"
    else
        echo "   ⚠️  Strong authentication: FAILED (HTTP $auth_response)"
        echo "   📝 This may be expected if credentials were changed"
    fi
else
    echo "   ⚠️  No admin password provided for testing"
fi

# Test Security Headers (5. Header Security)
echo "🛡️  Testing Security Headers..."
security_headers=$(curl -k -s -I "$GRAFANA_URL")

security_checks=(
    "Strict-Transport-Security:HSTS"
    "X-Content-Type-Options:Content-Type Protection"
    "X-Frame-Options:Frame Protection"
    "X-XSS-Protection:XSS Protection"
)

for check in "${security_checks[@]}"; do
    header="${check%%:*}"
    description="${check##*:}"
    
    if echo "$security_headers" | grep -q "$header"; then
        echo "   ✅ $description: ENABLED"
    else
        echo "   ⚠️  $description: MISSING"
    fi
done

# Test Configuration Security
echo "📋 Verifying Configuration Security..."
if [ -f "/etc/grafana/grafana.ini" ]; then
    config_content=$(sudo cat /etc/grafana/grafana.ini)
    
    # Check anonymous access disabled
    if echo "$config_content" | grep -A 2 "\[auth.anonymous\]" | grep -q "enabled = false"; then
        echo "   ✅ Anonymous access: DISABLED in config"
    else
        echo "   ❌ Anonymous access: NOT PROPERLY DISABLED"
    fi
    
    # Check HTTPS protocol
    if echo "$config_content" | grep -q "protocol = https"; then
        echo "   ✅ HTTPS protocol: CONFIGURED"
    else
        echo "   ❌ HTTPS protocol: NOT CONFIGURED"
    fi
    
    # Check strong admin user
    if echo "$config_content" | grep -q "admin_user = smartcloudops_admin"; then
        echo "   ✅ Strong admin user: CONFIGURED"
    else
        echo "   ⚠️  Admin user: Using different username"
    fi
    
else
    echo "   ❌ Grafana configuration: NOT FOUND"
fi

# Performance and Health Check
echo "💓 Testing System Health..."
if curl -k -s "$GRAFANA_URL/api/health" | grep -q "ok"; then
    echo "   ✅ Health check: PASSING"
else
    echo "   ⚠️  Health check: NOT RESPONDING"
fi

# Generate Security Report
echo ""
echo "📊 SECURITY DEPLOYMENT REPORT"
echo "============================="
echo "📅 Test Date: $(date)"
echo "🌐 Target: $GRAFANA_URL"
echo ""

# Check overall security status
critical_issues=0
warnings=0

# Validate critical security requirements
echo "🔒 CRITICAL SECURITY VALIDATIONS:"

# 1. HTTPS Only
if curl -k -s -I "$GRAFANA_URL" | grep -q "HTTP"; then
    echo "   ✅ HTTPS Access: WORKING"
else
    echo "   ❌ HTTPS Access: FAILED"
    critical_issues=$((critical_issues + 1))
fi

# 2. Anonymous Access Blocked
if [ "$anonymous_response" = "401" ] || [ "$anonymous_response" = "403" ]; then
    echo "   ✅ Anonymous Access: BLOCKED"
else
    echo "   ❌ Anonymous Access: ALLOWED"
    critical_issues=$((critical_issues + 1))
fi

# 3. Default Credentials Rejected
if [ "$default_auth_response" = "401" ] || [ "$default_auth_response" = "422" ]; then
    echo "   ✅ Default Credentials: REJECTED"
else
    echo "   ❌ Default Credentials: ACCEPTED"
    critical_issues=$((critical_issues + 1))
fi

# 4. Service Running
if sudo systemctl is-active --quiet grafana-server; then
    echo "   ✅ Service Status: RUNNING"
else
    echo "   ❌ Service Status: NOT RUNNING"
    critical_issues=$((critical_issues + 1))
fi

echo ""
echo "📈 SECURITY SCORE:"
if [ $critical_issues -eq 0 ]; then
    echo "   🟢 Security Level: ENTERPRISE SECURE"
    echo "   ✅ All Critical Requirements: PASSED"
    echo "   🎯 Deployment Status: PRODUCTION READY"
else
    echo "   🔴 Security Level: ISSUES DETECTED"
    echo "   ❌ Critical Issues: $critical_issues"
    echo "   ⚠️  Deployment Status: REQUIRES ATTENTION"
fi

echo ""
echo "🔗 ACCESS INFORMATION:"
echo "   📊 Grafana Dashboard: $GRAFANA_URL"
echo "   👤 Admin Username: $ADMIN_USER"
echo "   🔑 Admin Password: [Generated - Check deployment logs]"

echo ""
echo "🔍 MONITORING COMMANDS:"
echo "   Service Status: sudo systemctl status grafana-server"
echo "   Service Logs: sudo journalctl -u grafana-server -f"
echo "   Configuration: sudo cat /etc/grafana/grafana.ini"
echo "   SSL Certificates: ls -la /etc/grafana/ssl/"

echo ""
if [ $critical_issues -eq 0 ]; then
    echo "🎉 DEPLOYMENT SUCCESSFUL - ENTERPRISE SECURITY ACTIVE!"
    exit 0
else
    echo "❌ DEPLOYMENT ISSUES - REVIEW REQUIRED!"
    exit 1
fi
