# SmartCloudOps AI - API Key Setup Guide

## Overview
The SmartCloudOps AI application now implements secure API key authentication for all endpoints. This guide explains how to set up and manage API keys.

## 🔐 Authentication System Features

- **SHA256 Hashed Keys**: All API keys are securely hashed for storage
- **Rate Limiting**: 100 requests per hour per API key (configurable)
- **Permission Levels**: Read, Write, and Admin access levels
- **User Tracking**: All requests are logged with authenticated user information

## 📝 Permission Levels

### Read Access (`require_read()`)
- **Endpoints**: `/status`, `/ml/health`
- **Purpose**: View system status and health information
- **Use Case**: Monitoring systems, dashboards

### Write Access (`require_write()`)
- **Endpoints**: `/chat`, `/ml/predict`
- **Purpose**: Interact with AI and ML prediction services
- **Use Case**: ChatOps operations, anomaly detection

### Admin Access (`require_admin()`)
- **Endpoints**: `/ml/metrics`, `/metrics`
- **Purpose**: Access sensitive metrics and administrative data
- **Use Case**: System administrators, monitoring infrastructure

## 🚀 Quick Setup

### 1. Create API Keys
```python
from app.auth import APIKeyAuth

# Initialize auth system
auth = APIKeyAuth()

# Create keys for different access levels
read_key = auth.create_key("monitoring-system", "read")
write_key = auth.create_key("chatops-user", "write") 
admin_key = auth.create_key("system-admin", "admin")

print(f"Read Key: {read_key}")
print(f"Write Key: {write_key}")
print(f"Admin Key: {admin_key}")
```

### 2. Using API Keys
Include the API key in the `X-API-Key` header:

```bash
# Read access example
curl -H "X-API-Key: your-read-key-here" \
     http://44.200.14.5:5000/status

# Write access example
curl -H "X-API-Key: your-write-key-here" \
     -H "Content-Type: application/json" \
     -d '{"message": "What is the system status?"}' \
     http://44.200.14.5:5000/chat

# Admin access example
curl -H "X-API-Key: your-admin-key-here" \
     http://44.200.14.5:5000/metrics
```

## 🔧 Configuration

### Environment Variables
```bash
# Optional: Custom rate limiting
export API_RATE_LIMIT="200"  # Requests per hour (default: 100)

# Optional: API key length
export API_KEY_LENGTH="32"   # Key length in bytes (default: 32)
```

### Persistent Storage
API keys are stored in `/tmp/api_keys.json` by default. For production:

1. **Secure Location**: Move to protected directory
2. **Backup**: Regular backups of key database
3. **Rotation**: Implement key rotation policy

## 🛡️ Security Features

### Rate Limiting
- **Default**: 100 requests per hour per API key
- **Configurable**: Set via environment variable
- **Per-Key**: Each key has independent rate limit
- **Reset**: Limits reset every hour

### Request Tracking
- **User Identification**: All requests logged with user name
- **Access Patterns**: Monitor usage patterns per key
- **Security Auditing**: Full audit trail of API access

### Key Security
- **SHA256 Hashing**: Keys stored as secure hashes
- **No Plaintext**: Original keys never stored
- **Secure Generation**: Cryptographically secure random generation

## 📊 Monitoring Integration

### Prometheus Metrics
- **Request Counts**: Track requests per endpoint
- **Rate Limit Hits**: Monitor rate limiting effectiveness
- **Authentication Failures**: Security monitoring

### Logging
- **Structured Logs**: JSON formatted for parsing
- **User Context**: All operations include user information
- **Security Events**: Authentication failures logged

## 🚨 Error Responses

### 401 Unauthorized
```json
{
  "error": "Invalid API key",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 403 Forbidden
```json
{
  "error": "Insufficient permissions",
  "required": "admin",
  "provided": "read",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 429 Too Many Requests
```json
{
  "error": "Rate limit exceeded",
  "limit": 100,
  "window": "1 hour",
  "retry_after": 1800,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🔄 Migration from Unauthenticated

### Step 1: Deploy New Version
The authentication system is backward compatible during transition:
- Deploy updated application
- Test with API keys
- Monitor logs for unauthenticated requests

### Step 2: Create API Keys
Generate keys for all systems and users:
```python
# Run this script to create initial keys
python scripts/create_initial_keys.py
```

### Step 3: Update Clients
Update all client systems to include API keys:
```bash
# Example client update
# OLD: curl http://44.200.14.5:5000/status
# NEW: curl -H "X-API-Key: key" http://44.200.14.5:5000/status
```

### Step 4: Enforce Authentication
Once all clients updated, remove fallback authentication.

## 🧪 Testing

### Test Authentication
```bash
# Test read access
curl -H "X-API-Key: $(cat read_key.txt)" \
     http://44.200.14.5:5000/status

# Test write access
curl -H "X-API-Key: $(cat write_key.txt)" \
     -H "Content-Type: application/json" \
     -d '{"message": "test"}' \
     http://44.200.14.5:5000/chat

# Test admin access
curl -H "X-API-Key: $(cat admin_key.txt)" \
     http://44.200.14.5:5000/metrics
```

### Test Rate Limiting
```bash
# Rapid requests to test rate limiting
for i in {1..105}; do
  curl -H "X-API-Key: test-key" \
       http://44.200.14.5:5000/status
  echo "Request $i"
done
```

## 📞 Support

For issues with API key setup:
1. Check application logs: `tail -f /var/log/smartcloudops-ai/app.log`
2. Verify key format and headers
3. Test with different permission levels
4. Review rate limit status

## 🔐 Security Best Practices

1. **Key Rotation**: Regularly rotate API keys
2. **Least Privilege**: Assign minimum required permissions
3. **Monitoring**: Monitor for unusual access patterns
4. **Secure Storage**: Store keys securely in client applications
5. **Network Security**: Use HTTPS in production (next phase)

---
**Status**: ✅ API Authentication Implemented
**Next Phase**: Network Security Restrictions
