# SmartCloudOps AI - Phase 3 Production Configuration
# 🚀 HTTPS/TLS + Secrets Management + Advanced Monitoring

# Project configuration
project_name = "smartcloudops-ai"
environment  = "production"

# ===== PHASE 3: HTTPS/TLS CONFIGURATION =====
# 🔒 Disable HTTPS for initial deployment (can be enabled later with domain)
enable_https = false

# 🔒 Domain configuration (disabled for now)
# domain_name = ""  # Leave empty to use ALB DNS name for testing

# 🔒 HTTP to HTTPS redirect (disabled when HTTPS is off)
enable_http_redirect = false

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
# 🔒 Configured with your current IP and common networks

# SSH Access - Admin/operations team IPs
allowed_ssh_cidrs = [
  "0.0.0.0/0",           # Allow SSH from anywhere (can be restricted later)
]

# Application Access - Authorized client networks
allowed_app_cidrs = [
  "0.0.0.0/0",           # Allow application access from anywhere (can be restricted later)
]

# Monitoring Access - Monitoring systems
allowed_monitoring_cidrs = [
  "157.50.81.168/32",    # Your current IP for monitoring
]

# Emergency Admin Access
admin_ip_cidr = "157.50.81.168/32"  # Your current IP for emergency access

# ===== BASIC CONFIGURATION =====
# EC2 Configuration
ec2_instance_type = "t2.micro"  # Free tier eligible

# SSH Key - Generated for SmartCloudOps AI
ssh_public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDKxBAiQLVq+M1pKlWW0HIcOItBUfSRjhyLPioR+xU0ndvwqmMIG0A5HO2/lBWr/ICIECm+46eRDsvxC3cz49Vw7J82a1lFquBtr1xhFJYBg5N/nLjGlw73c2HFzlOVmhNZXU/rT5s5EJgokkgKHgw/9/PiRRuuMizrsYMWturjLpa5d9elvr+xeHlGIqH+VEZbxG6+fsN2Yt1a9n5X/l+VznZcoA05Ml6luD6BRiLWmjhj5oClvO/cKhRttSspOqW9e3rHJzh23fsMqPmd2Ykl/kI4tXExBIt/DTu2f0bd4V3A6ydTFsGXJ8p0zfV9USwoeBekgzsPdOGqeu6+b7kKNsiVFMSsnc6TU7i1F76VGYGYFR85uXptw/hCJ//KKUkRexmxkwTF36IzGN/WYNJrBaDDqQSxTCiEQB4eFaAgAcsNc6TxAquhZVBHWwQA3W8DpBkSgXeTxCmCJ8icZ4hIgg0VqUzNUvHZwkQF6BjPl8e8jl//Dx5DxYS/uSMMefq0SM0egcNNFtOSBrAyDEkhscZyGBwlCmzcfDgVi9bGsEjAlLqQF3GCX1JGm5Z9PbYipEe1br/4Mv5qvDqqA1MpkQpVxFsOupFPIQReY+iB6KvvdrJz/02q0A6JIS31YWJ6qVfMcqtQfT0tzJwyphOullNy9VBrHOlkePtWLOzGSQ== smartcloudops-ai-20250808"

# Storage (Free tier)
ebs_volume_size = 8  # GB - Free tier includes 30GB EBS storage

# API Configuration (will migrate to Secrets Manager)
openai_api_key = ""  # Will be migrated to Secrets Manager
gemini_api_key = ""  # Will be migrated to Secrets Manager
