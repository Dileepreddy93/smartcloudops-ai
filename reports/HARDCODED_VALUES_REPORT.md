# Hardcoded Values Report - SmartCloudOps.AI

## Executive Summary
This report identifies all hardcoded values found in the SmartCloudOps.AI application that should be externalized to configuration files or environment variables for better security, maintainability, and deployment flexibility.

## Critical Security Issues

### 1. Database Credentials
**File:** `app/database_pool.py:417`
```python
"postgresql://postgres:password@localhost:5432/smartcloudops"
```
**Risk:** HIGH - Hardcoded database password
**Recommendation:** Use environment variable `DATABASE_URL`

### 2. API Keys and Secrets
**File:** `app/auth_secure.py:166`
```python
salt = self.app.config.get("API_KEY_SALT", "smartcloudops_secure_salt_2024")
```
**Risk:** HIGH - Hardcoded salt value
**Recommendation:** Use environment variable `API_KEY_SALT`

### 3. AWS Region Hardcoding
**Files:** 
- `app/services/remediation_service.py:70-71`
- `app/services/aws_integration_service.py:29`
- `app/services/nlp_chatops_service.py:154-156`
```python
region_name="us-east-1"
```
**Risk:** MEDIUM - Limits deployment flexibility
**Recommendation:** Use environment variable `AWS_DEFAULT_REGION`

## Network Configuration Issues

### 4. Hardcoded IP Addresses and Hosts
**Files:**
- `app/main.py:405` - `host="0.0.0.0"`
- `app/main_secure.py:789` - `host="0.0.0.0"`
- `app/main_production.py:485` - `host="0.0.0.0"`
- `scripts/phase3_anomaly_detection.py:68` - `"http://3.89.229.102:9090"`
- `app/core/ml_engine/production_inference.py:134` - `"http://3.89.229.102:9090"`

**Risk:** MEDIUM - Security and deployment flexibility
**Recommendation:** Use environment variables for all network configurations

### 5. Port Numbers
**Common hardcoded ports:**
- Port 5000 (Flask app) - Found in 15+ files
- Port 3000 (Grafana) - Found in 10+ files  
- Port 5432 (PostgreSQL) - Found in 8+ files
- Port 6379 (Redis) - Found in 6+ files
- Port 9090 (Prometheus) - Found in 8+ files

**Recommendation:** Use environment variables for all port configurations

## File System Paths

### 6. Hardcoded Log Paths
**Files:**
- `app/main_secure.py:81` - `"/tmp/smartcloudops_api.log"`
- `app/api/v1/logs.py:12` - `"/tmp/smartcloudops_api.log"`
- `scripts/production_monitor.py:54` - `"/var/log/smartcloudops/monitoring.log"`
- `scripts/production_monitor.py:323` - `"/var/log/smartcloudops/metrics.jsonl"`

**Risk:** MEDIUM - Deployment flexibility
**Recommendation:** Use environment variables for log paths

### 7. Hardcoded User Paths
**File:** `scripts/production_monitor.py:356-360`
```python
WorkingDirectory=/home/ec2-user/smartcloudops-ai/scripts
ExecStart=/home/ec2-user/smartcloudops-ai/venv/bin/python3
Environment=PYTHONPATH=/home/ec2-user/smartcloudops-ai
```
**Risk:** MEDIUM - Deployment flexibility
**Recommendation:** Use environment variables for user paths

## Application Configuration

### 8. Database Names
**Files:**
- `app/config_manager.py:24` - `name: str = "smartcloudops"`
- `app/config_manager.py:88` - `"smartcloudops"`
- `app/config_manager.py:245` - `"smartcloudops_prod"`
- `app/config_manager.py:276` - `"smartcloudops_staging"`

**Recommendation:** Use environment variables for database names

### 9. Application Names and URLs
**Files:**
- `app/config_manager.py:124-125` - `"https://prometheus.smartcloudops.ai"`
- `app/config_manager.py:129-131` - `"https://prometheus-staging.smartcloudops.ai"`
- `app/config_manager.py:243` - `"prod-db.smartcloudops.ai"`
- `app/config_manager.py:274` - `"staging-db.smartcloudops.ai"`

**Recommendation:** Use environment variables for domain names

## Performance and Threshold Values

### 10. Hardcoded Thresholds
**Files:**
- `app/config_manager.py:251` - `"rate_limit_per_hour": 5000`
- `app/services/remediation_service.py:106` - `"threshold": 5000`
- `app/services/ml_service.py:177` - `np.random.normal(5000, 1000, anomaly_samples)`

**Recommendation:** Use configuration files for threshold values

## Temporary File Paths

### 11. Hardcoded Temp Paths
**Files:**
- `scripts/phase3_anomaly_detection.py:487` - `"/tmp/anomaly_model.pkl"`
- `scripts/production_inference.py:68` - `f"/tmp/model_{int(time.time())}.pkl"`
- `app/core/ml_engine/production_inference.py:64` - `f"/tmp/model_{int(time.time())}.pkl"`

**Recommendation:** Use environment variable `TEMP_DIR` or system temp directory

## Recommendations

### Immediate Actions (High Priority)
1. **Remove hardcoded database password** - Use `DATABASE_URL` environment variable
2. **Externalize API salt** - Use `API_KEY_SALT` environment variable
3. **Remove hardcoded IP addresses** - Use environment variables for all network configs

### Short-term Actions (Medium Priority)
1. **Create configuration management system** - Centralize all configs
2. **Add environment variable validation** - Ensure required vars are set
3. **Update deployment scripts** - Use environment-specific configs

### Long-term Actions (Low Priority)
1. **Implement configuration validation** - Validate all config values
2. **Add configuration documentation** - Document all environment variables
3. **Create configuration templates** - Provide example config files

## Files Requiring Immediate Attention

### Critical Security Files:
- `app/database_pool.py` - Database credentials
- `app/auth_secure.py` - API salt
- `app/services/remediation_service.py` - AWS region
- `app/services/aws_integration_service.py` - AWS region
- `app/services/nlp_chatops_service.py` - AWS region

### Configuration Files:
- `app/config_manager.py` - Multiple hardcoded values
- `app/config.py` - Database and Redis URLs
- `scripts/security_audit.py` - AWS region

### Main Application Files:
- `app/main.py` - Host configuration
- `app/main_secure.py` - Host and log paths
- `app/main_production.py` - Host configuration

## Environment Variables Needed

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@host:port/dbname
DB_HOST=localhost
DB_PORT=5432
DB_NAME=smartcloudops
DB_USER=postgres
DB_PASSWORD=secure_password

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379

# Application Configuration
PORT=5000
HOST=0.0.0.0
SECRET_KEY=your-secret-key
API_KEY_SALT=your-api-salt

# AWS Configuration
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# Monitoring Configuration
PROMETHEUS_ENDPOINT=http://localhost:9090
GRAFANA_ENDPOINT=http://localhost:3000

# Logging Configuration
LOG_PATH=/var/log/smartcloudops
TEMP_DIR=/tmp

# Domain Configuration
PROMETHEUS_DOMAIN=prometheus.smartcloudops.ai
GRAFANA_DOMAIN=grafana.smartcloudops.ai
DB_DOMAIN=db.smartcloudops.ai
```

## Conclusion

The application has **15+ critical hardcoded values** that need immediate attention, particularly around database credentials, API keys, and network configurations. Implementing the recommended changes will significantly improve security, maintainability, and deployment flexibility.

## ✅ HIGH PRIORITY ISSUES - RESOLVED

### Fixed Issues:

1. **✅ Database Password Hardcoding** - `app/database_pool.py:417`
   - **FIXED:** Removed hardcoded password, now requires `DATABASE_URL` environment variable
   - **Status:** RESOLVED

2. **✅ API Salt Hardcoding** - `app/auth_secure.py:166`
   - **FIXED:** Removed hardcoded salt, now requires `API_KEY_SALT` environment variable
   - **Status:** RESOLVED

3. **✅ AWS Region Hardcoding** - Multiple files
   - **FIXED:** All AWS region hardcoding replaced with `AWS_DEFAULT_REGION` environment variable
   - **Files Fixed:** 
     - `app/services/remediation_service.py:70-71`
     - `app/services/aws_integration_service.py:29`
     - `app/services/nlp_chatops_service.py:154-156`
   - **Status:** RESOLVED

4. **✅ Hardcoded IP Addresses** - Multiple files
   - **FIXED:** Removed hardcoded IP addresses, now use environment variables
   - **Files Fixed:**
     - `scripts/phase3_anomaly_detection.py:68` - Now uses `PROMETHEUS_URL`
     - `app/core/ml_engine/production_inference.py:134` - Now uses `PROMETHEUS_URL`
   - **Status:** RESOLVED

5. **✅ Host Configuration Hardcoding** - Multiple files
   - **FIXED:** All hardcoded host configurations now use `HOST` environment variable
   - **Files Fixed:**
     - `app/main.py:405`
     - `app/main_secure.py:789`
     - `app/main_production.py:485`
   - **Status:** RESOLVED

### Additional Improvements Made:

6. **✅ Environment Variables Template** - `env.example`
   - **CREATED:** Comprehensive environment variables template with all required configurations
   - **Status:** COMPLETED

7. **✅ Environment Validation Script** - `scripts/validate_environment.py`
   - **CREATED:** Automated script to validate environment configuration
   - **Features:**
     - Validates required environment variables
     - Checks secret strength
     - Validates URL formats
     - AWS configuration validation
     - Port number validation
   - **Status:** COMPLETED

## 🔄 REMAINING MEDIUM PRIORITY ISSUES

### Still Need Attention:

8. **🟡 Port Numbers** - Found in 15+ files
   - **Status:** PENDING - Should be externalized to environment variables

9. **🟡 Log Paths** - Multiple files
   - **Status:** PENDING - Should use `LOG_PATH` environment variable

10. **🟡 Database Names** - Multiple files
    - **Status:** PENDING - Should use environment variables

11. **🟡 Application URLs** - Multiple files
    - **Status:** PENDING - Should use environment variables

**Priority:** MEDIUM - High priority security issues have been resolved. Medium priority issues remain for deployment flexibility.
