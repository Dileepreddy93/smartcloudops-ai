# SmartCloudOps AI - Production Configuration
# 🚀 PRODUCTION READY: High availability, security, and performance

# Project configuration
project_name = "smartcloudops-ai"
environment  = "production"

# AWS Configuration
aws_region = "us-east-1"

# SECURITY: Network Access Control (MUST BE SET)
# Replace with your actual authorized IP addresses/ranges
allowed_ssh_cidrs = [
  "YOUR_OFFICE_IP/32",        # Replace with your office IP
  "YOUR_HOME_IP/32",          # Replace with your home IP
  "YOUR_VPN_RANGE/24"         # Replace with your VPN range
]

allowed_app_cidrs = [
  "0.0.0.0/0"                 # Allow from anywhere for web app (use ALB in production)
]

allowed_monitoring_cidrs = [
  "YOUR_OFFICE_IP/32",        # Replace with your office IP
  "YOUR_HOME_IP/32"           # Replace with your home IP
]

admin_ip_cidr = "YOUR_EMERGENCY_IP/32"  # Replace with emergency access IP

# SSH Public Key (MUST BE SET)
ssh_public_key = "ssh-rsa YOUR_PUBLIC_KEY_HERE"  # Replace with your SSH public key

# Database Configuration (MUST BE SET SECURELY)
# Set via environment variable: export TF_VAR_db_password="YourSecurePassword123!"
db_password = "CHANGE_ME_TO_SECURE_PASSWORD"

# HTTPS/TLS Configuration
enable_https = true
domain_name = "smartcloudops.yourdomain.com"  # Replace with your domain
enable_http_redirect = true

# Secrets Management
enable_secrets_manager = true
# Set via environment variables:
# export TF_VAR_openai_api_key="your-openai-key"
# export TF_VAR_gemini_api_key="your-gemini-key"

# Advanced Monitoring
enable_advanced_monitoring = true

# Production Instance Types (Not Free Tier)
monitoring_instance_type = "t3.small"      # 2 vCPU, 2 GB RAM
application_instance_type = "t3.small"     # 2 vCPU, 2 GB RAM

# Database Configuration
db_username = "smartcloudops_admin"
db_password = "CHANGE_ME_TO_SECURE_PASSWORD"  # Must be set securely

# Monitoring Configuration
prometheus_port = "9090"
