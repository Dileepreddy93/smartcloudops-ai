# SmartCloudOps AI - Secure Terraform Configuration
# 🔒 SECURITY HARDENED: Network access restricted to authorized IPs only

# Project configuration
project_name = "smartcloudops-ai"
environment  = "production"

# 🔒 SECURITY: Network Access Control
# IMPORTANT: Replace these with your actual authorized IP addresses/ranges

# SSH Access - Replace with your admin IP addresses
allowed_ssh_cidrs = [
  # "203.0.113.0/24",    # Example: Your office network
  # "198.51.100.5/32",   # Example: Your home IP
]

# Application Access - Replace with authorized application client IPs  
allowed_app_cidrs = [
  # "203.0.113.0/24",    # Example: Your office network
  # "10.0.0.0/8",        # Example: Internal corporate network
  # "172.16.0.0/12",     # Example: VPN network range
]

# Monitoring Access - Replace with monitoring system IPs
allowed_monitoring_cidrs = [
  # "203.0.113.10/32",   # Example: Monitoring server IP
  # "198.51.100.0/24",   # Example: Operations team network
]

# Emergency Admin Access - Replace with your current IP
admin_ip_cidr = ""  # "203.0.113.100/32"  # Your current IP for emergency access

# EC2 Configuration
ec2_instance_type = "t2.micro"  # Free tier eligible

# SSH Key - Provide your public key
ssh_public_key = ""  # Add your SSH public key here

# Storage (Free tier)
ebs_volume_size = 8  # GB - Free tier includes 30GB EBS storage

# OpenAI Configuration (if using)
openai_api_key = ""  # Set if using OpenAI integration

# Gemini Configuration  
gemini_api_key = ""  # Set if using Gemini integration

# ===== SECURITY NOTICE =====
# 
# This configuration implements network-level security by restricting access
# to specific IP addresses/ranges instead of allowing all internet traffic (0.0.0.0/0).
#
# Before applying this configuration:
# 1. Replace the example IP addresses with your actual authorized IPs
# 2. Use CIDR notation (e.g., 203.0.113.100/32 for single IP)
# 3. Test access after applying to ensure you're not locked out
# 4. Keep admin_ip_cidr updated with your current IP for emergency access
#
# Example IP sources to consider:
# - Your office/home IP addresses
# - VPN network ranges  
# - Monitoring system IPs
# - CI/CD pipeline IPs
# - Load balancer/proxy IPs
#
# Get your current IP: curl -s https://checkip.amazonaws.com/
# ===========================
