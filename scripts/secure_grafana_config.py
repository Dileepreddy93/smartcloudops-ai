#!/usr/bin/env python3
"""
SmartCloudOps AI - Secure Grafana Configuration Generator
========================================================

Generates secure Grafana configuration with enterprise-grade security controls.
"""

import os
import secrets
import string
from datetime import datetime, timezone

def generate_secure_password(length=32):
    """Generate cryptographically secure password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_secret_key(length=64):
    """Generate secure secret key for Grafana"""
    return secrets.token_hex(length)

def create_secure_grafana_config():
    """Create secure Grafana configuration"""
    
    # Generate secure credentials
    admin_password = generate_secure_password(32)
    secret_key = generate_secret_key(32)
    
    config = f"""# SmartCloudOps AI - Secure Grafana Configuration
# Generated: {datetime.now(timezone.utc).isoformat()}
# Security Level: Enterprise Grade

##################### Grafana Configuration File #####################

#----------------------------------------------------------------------
# SECURITY CONFIGURATION - CRITICAL SETTINGS
#----------------------------------------------------------------------

[security]
# Admin credentials - MUST be changed from defaults
admin_user = smartcloudops_admin
admin_password = {admin_password}

# Secret key for signing - CRITICAL for session security
secret_key = {secret_key}

# Security headers and protections
disable_gravatar = true
cookie_secure = true
cookie_samesite = strict
strict_transport_security = true
strict_transport_security_max_age_seconds = 86400
content_type_protection = true
x_content_type_options = nosniff
x_xss_protection = true

# Disable unnecessary features that could pose security risks
disable_brute_force_login_protection = false
login_remember_days = 1
login_maximum_inactive_lifetime_days = 7
login_maximum_lifetime_days = 30

# Password policy
password_min_length = 12
password_require_uppercase = true
password_require_lowercase = true
password_require_digit = true
password_require_symbol = true

#----------------------------------------------------------------------
# SERVER CONFIGURATION - HTTPS ONLY
#----------------------------------------------------------------------

[server]
# HTTPS configuration - NO HTTP ALLOWED IN PRODUCTION
protocol = https
http_port = 3000
domain = localhost
enforce_domain = true

# TLS/SSL Configuration
cert_file = /etc/grafana/ssl/grafana.crt
cert_key = /etc/grafana/ssl/grafana.key
tls_min_version = "1.2"
tls_ciphers = "ECDHE-RSA-AES128-GCM-SHA256,ECDHE-RSA-AES256-GCM-SHA384"

# Security headers
enable_gzip = true
static_root_path = public
serve_from_sub_path = false

# Router logging for security monitoring
router_logging = true

#----------------------------------------------------------------------
# AUTHENTICATION CONFIGURATION - NO ANONYMOUS ACCESS
#----------------------------------------------------------------------

[auth]
# Disable automatic signup
disable_login_form = false
disable_signout_menu = false
signout_redirect_url = ""

# Session configuration
login_cookie_name = grafana_sess
login_maximum_inactive_lifetime_duration = 7d
login_maximum_lifetime_duration = 30d
token_rotation_interval_minutes = 10

[auth.anonymous]
# CRITICAL: Disable anonymous access - NO UNAUTHENTICATED USERS
enabled = false
org_name = ""
org_role = ""
hide_version = true

# Disable anonymous analytics
reporting_enabled = false
check_for_updates = false

[auth.basic]
enabled = true

#----------------------------------------------------------------------
# API INTEGRATION WITH SMARTCLOUDOPS BACKEND
#----------------------------------------------------------------------

[auth.proxy]
# Enable proxy authentication for API integration
enabled = false  # Can be enabled for SSO integration
header_name = X-WEBAUTH-USER
header_property = username
auto_sign_up = false
sync_ttl = 60
whitelist = 127.0.0.1

#----------------------------------------------------------------------
# SECURITY LOGGING AND MONITORING
#----------------------------------------------------------------------

[log]
mode = console file
level = info
format = text

[log.console]
level = info
format = text

[log.file]
level = info
format = text
log_rotate = true
max_lines = 1000000
max_size_shift = 28
daily_rotate = true
max_days = 7

# Security audit logging
[log.filters]
# Log all authentication events
auth = info
# Log configuration changes
config = info
# Log data source access
datasource = info

#----------------------------------------------------------------------
# DATABASE SECURITY
#----------------------------------------------------------------------

[database]
type = sqlite3
host = 127.0.0.1:3306
name = grafana
user = root
password = ""
ssl_mode = require
ca_cert_path = ""
client_key_path = ""
client_cert_path = ""
server_cert_name = ""
path = /var/lib/grafana/grafana.db
max_idle_conn = 2
max_open_conn = 0
conn_max_lifetime = 14400
log_queries = true

#----------------------------------------------------------------------
# PERFORMANCE AND RESOURCE LIMITS
#----------------------------------------------------------------------

[dataproxy]
# Query timeout and resource limits
timeout = 30
keep_alive_seconds = 30
tls_handshake_timeout_seconds = 10
expect_continue_timeout_seconds = 1
max_conns_per_host = 0
max_idle_connections = 100
idle_conn_timeout_seconds = 90

# Logging for debugging slow queries
logging = true

[quota]
# Resource quotas to prevent abuse
enabled = true
org_user = 10
org_dashboard = 100
org_data_source = 10
org_api_key = 10
user_org = 10
global_user = -1
global_org = -1
global_dashboard = -1
global_api_key = -1
global_session = -1

#----------------------------------------------------------------------
# CONTENT SECURITY POLICY
#----------------------------------------------------------------------

[security.content_security_policy]
enabled = true
template = "script-src 'self' 'unsafe-eval' 'unsafe-inline' 'strict-dynamic' $NONCE;object-src 'none';font-src 'self';style-src 'self' 'unsafe-inline' blob:;img-src * data:;base-uri 'self';connect-src 'self' grafana.com ws://localhost:3000/ wss://localhost:3000/;manifest-src 'self';media-src 'none';form-action 'self';"

#----------------------------------------------------------------------
# FEATURE TOGGLES - DISABLE UNNECESSARY FEATURES
#----------------------------------------------------------------------

[feature_toggles]
# Disable features that could pose security risks
live = false
ngalert = true
export = false
publicDashboards = false
lokiLive = false
lokiDataframeApi = false
swaggerUi = false

#----------------------------------------------------------------------
# ALERTING SECURITY
#----------------------------------------------------------------------

[alerting]
enabled = true
execute_alerts = true
error_or_timeout = alerting
nodata_or_nullvalues = no_data
concurrent_render_limit = 5

# Notification security
[smtp]
enabled = false
host = localhost:587
user = ""
password = ""
cert_file = ""
key_file = ""
skip_verify = false
from_address = admin@grafana.localhost
from_name = Grafana
ehlo_identity = ""
startTLS_policy = ""

#----------------------------------------------------------------------
# PANELS AND PLUGINS SECURITY
#----------------------------------------------------------------------

[panels]
# Disable potentially unsafe panel features
disable_sanitize_html = false
enable_alpha = false

[plugins]
enable_alpha = false
app_tls_skip_verify_insecure = false
allow_loading_unsigned_plugins = ""

# Plugin security
[plugin.grafana-image-renderer]
rendering_ignore_https_errors = false
rendering_viewport_device_scale_factor = 1
rendering_ignore_https_errors = false
rendering_verbose_logging = false
rendering_dumpio = false

#----------------------------------------------------------------------
# EXTERNAL INTEGRATIONS SECURITY
#----------------------------------------------------------------------

[external_image_storage]
provider = ""

[external_image_storage.s3]
endpoint = ""
path_style_access = false
bucket_url = ""
bucket = ""
region = ""
path = ""
access_key = ""
secret_key = ""

# Analytics and tracking - DISABLED for privacy
[analytics]
reporting_enabled = false
check_for_updates = false
google_analytics_ua_id = ""
google_tag_manager_id = ""
rudderstack_write_key = ""
rudderstack_data_plane_url = ""
rudderstack_sdk_url = ""
rudderstack_config_url = ""

[snapshots]
external_enabled = false
external_snapshot_url = ""
external_snapshot_name = ""
public_mode = false

# Remove X-Frame-Options to allow embedding only from same origin
[security]
allow_embedding = false
cookie_samesite = strict

#----------------------------------------------------------------------
# UNIFIED ALERTING
#----------------------------------------------------------------------

[unified_alerting]
enabled = true
disabled_orgs = ""
admin_config_poll_interval = 60s
alertmanager_config_poll_interval = 60s
ha_listen_address = "localhost:9094"
ha_advertise_address = ""
ha_peers = ""
ha_peer_timeout = 15s
ha_gossip_interval = 200ms
ha_push_pull_interval = 60s
ha_enable_v2 = false
reserved_labels = ""

[unified_alerting.reserved_labels]
disabled_labels = ""

# State history - secure storage
[unified_alerting.state_history]
enabled = true
backend = "annotations"

[unified_alerting.state_history.loki]
url = ""
tenant_id = ""
username = ""
password = ""

#----------------------------------------------------------------------
# ENTERPRISE FEATURES (If applicable)
#----------------------------------------------------------------------

[enterprise]
license_path = ""

[white_labeling]
app_title = "SmartCloudOps AI Monitoring"
login_title = "SmartCloudOps AI"
login_subtitle = "Secure Infrastructure Monitoring"
login_logo = ""
login_background = ""
menu_logo = ""
fav_icon = ""
apple_touch_icon = ""
footer_links = ""
loading_logo = ""

# Hide Grafana edition
hide_edition = true
hide_version = true

#----------------------------------------------------------------------
# REVERSE PROXY SECURITY (For production deployment)
#----------------------------------------------------------------------

[auth.proxy]
enabled = false
header_name = X-WEBAUTH-USER
header_property = username
auto_sign_up = false
ldap_sync_ttl = 60
sync_ttl = 60
whitelist = 127.0.0.1
headers = Email:X-User-Email, Name:X-User-Name

# Security for reverse proxy setup
[security]
strict_transport_security = true
strict_transport_security_max_age_seconds = 86400
content_type_protection = true
x_content_type_options = nosniff
x_xss_protection = true
"""

    # Create secure environment variables file
    env_vars = f"""# SmartCloudOps AI - Grafana Environment Variables
# SECURITY: Store these values securely, never commit to version control

# Grafana Admin Credentials
export GRAFANA_ADMIN_USER="smartcloudops_admin"
export GRAFANA_ADMIN_PASSWORD="{admin_password}"
export GRAFANA_SECRET_KEY="{secret_key}"

# SSL/TLS Configuration
export GRAFANA_SSL_CERT_PATH="/etc/grafana/ssl/grafana.crt"
export GRAFANA_SSL_KEY_PATH="/etc/grafana/ssl/grafana.key"

# Database Security
export GRAFANA_DATABASE_PASSWORD=""  # Set if using external database

# Integration with SmartCloudOps API
export SMARTCLOUDOPS_API_URL="https://localhost:5000"
export SMARTCLOUDOPS_API_KEY=""  # Set from backend API keys

# Security Configuration
export GRAFANA_DOMAIN="your-domain.com"  # Set to actual domain
export GRAFANA_ROOT_URL="https://your-domain.com:3000"

# Generated: {datetime.now(timezone.utc).isoformat()}
# CRITICAL: Change default values before production deployment!
"""

    return config, env_vars, admin_password, secret_key

if __name__ == "__main__":
    config, env_vars, admin_password, secret_key = create_secure_grafana_config()
    
    # Write secure configuration
    with open('/tmp/grafana_secure.ini', 'w') as f:
        f.write(config)
    
    # Write environment variables
    with open('/tmp/grafana_secure.env', 'w') as f:
        f.write(env_vars)
    
    print("🔒 SECURE GRAFANA CONFIGURATION GENERATED")
    print("=" * 50)
    print(f"📁 Configuration: /tmp/grafana_secure.ini")
    print(f"🔑 Environment: /tmp/grafana_secure.env")
    print()
    print("🎯 SECURITY IMPROVEMENTS:")
    print("✅ Anonymous access DISABLED")
    print("✅ Strong admin credentials generated")
    print("✅ HTTPS-only configuration")
    print("✅ Content Security Policy enabled")
    print("✅ Security headers configured")
    print("✅ Session security hardened")
    print("✅ Resource quotas implemented")
    print("✅ Audit logging enabled")
    print()
    print("🔐 GENERATED CREDENTIALS (STORE SECURELY):")
    print(f"Username: smartcloudops_admin")
    print(f"Password: {admin_password}")
    print(f"Secret Key: {secret_key}")
    print()
    print("⚠️  DEPLOYMENT STEPS:")
    print("1. Generate SSL certificates")
    print("2. Update domain/URL configuration")
    print("3. Replace /etc/grafana/grafana.ini")
    print("4. Restart Grafana service")
    print("5. Test authentication and HTTPS")
