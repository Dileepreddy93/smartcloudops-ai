# SmartCloudOps AI - Phase 3 Advanced Security Configuration
# 🚀 HTTPS/TLS + Secrets Management + Advanced Monitoring

# Project configuration
project_name = "smartcloudops-ai"
environment  = "production"

# ===== PHASE 3: HTTPS/TLS CONFIGURATION =====
# 🔒 Enable HTTPS with Application Load Balancer
enable_https = true

# 🔒 Domain configuration (REPLACE WITH YOUR DOMAIN)
# domain_name = "smartcloudops.yourdomain.com"  # Uncomment and set your domain

# 🔒 HTTP to HTTPS redirect
enable_http_redirect = true

# Optional: Use existing certificate ARN instead of creating new one
# certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012"

# ===== PHASE 3: SECRETS MANAGEMENT =====
# 🔐 Enable AWS Secrets Manager for API keys
enable_secrets_manager = true

# 🔐 Automatic secret rotation (30 days)
secret_rotation_days = 30

# ===== PHASE 3: ADVANCED MONITORING =====
# 📊 Enable comprehensive security monitoring
enable_advanced_monitoring = true

# 🛡️ Enable Web Application Firewall
enable_waf = true

# ===== NETWORK SECURITY (From Phase 2) =====
# 🔒 IMPORTANT: Replace with your actual authorized IP addresses

# SSH Access - Admin/operations team IPs
allowed_ssh_cidrs = [
  # "203.0.113.100/32",    # Your current IP
  # "198.51.100.0/24",     # Your office network
]

# Application Access - Authorized client networks
allowed_app_cidrs = [
  # "203.0.113.0/24",      # Your office network
  # "10.0.0.0/8",          # Internal corporate network
  # "172.16.0.0/12",       # VPN network range
]

# Monitoring Access - Monitoring systems
allowed_monitoring_cidrs = [
  # "203.0.113.100/32",    # Your monitoring workstation
  # "198.51.100.10/32",    # Dedicated monitoring server
]

# Emergency Admin Access
admin_ip_cidr = ""  # "203.0.113.100/32"  # Your current IP for emergency access

# ===== BASIC CONFIGURATION =====
# EC2 Configuration
ec2_instance_type = "t2.micro"  # Free tier eligible

# SSH Key - Provide your public key
ssh_public_key = ""  # Add your SSH public key here

# Storage (Free tier)
ebs_volume_size = 8  # GB - Free tier includes 30GB EBS storage

# API Configuration
openai_api_key = ""  # Set if using OpenAI integration
gemini_api_key = ""  # Set if using Gemini integration

# ===== PHASE 3 HTTPS SETUP INSTRUCTIONS =====
# 
# To enable HTTPS with your own domain:
# 
# 1. Domain Setup:
#    - Set domain_name = "smartcloudops.yourdomain.com"
#    - Ensure you have DNS control for domain validation
# 
# 2. Apply Infrastructure:
#    terraform apply -var-file="terraform-phase3.tfvars"
# 
# 3. Complete DNS Validation:
#    - Check output for domain_validation_options
#    - Create required DNS CNAME records for certificate validation
#    - Wait for certificate validation (up to 30 minutes)
# 
# 4. Update DNS to point to Load Balancer:
#    - Create A record: smartcloudops.yourdomain.com -> [ALB DNS Name]
#    - Or CNAME record: smartcloudops.yourdomain.com -> [ALB DNS Name]
# 
# 5. Test HTTPS:
#    curl https://smartcloudops.yourdomain.com/status
# 
# ===== TESTING WITHOUT DOMAIN =====
# 
# You can test HTTPS features without a custom domain:
# 1. Set enable_https = true but leave domain_name empty
# 2. Access via ALB DNS name (from terraform output)
# 3. Use --insecure flag for testing: curl -k https://[ALB-DNS]/status
# 
# ===== SECURITY WARNINGS =====
# 
# 🚨 BEFORE PRODUCTION DEPLOYMENT:
# 1. Set all allowed_*_cidrs with your actual IP ranges
# 2. Configure domain_name for proper SSL certificate
# 3. Set admin_ip_cidr to your current admin IP
# 4. Review all security settings for your specific requirements
# 5. Test thoroughly in staging environment first
# 
# 🔐 SECRETS MANAGEMENT:
# - API keys will be stored in AWS Secrets Manager
# - Original keys in files should be deleted after migration
# - Enable rotation for enhanced security
# 
# 📊 MONITORING:
# - Advanced monitoring will create CloudTrail, GuardDuty resources
# - May incur additional costs beyond free tier
# - Monitor AWS billing dashboard
# 
# ===========================
