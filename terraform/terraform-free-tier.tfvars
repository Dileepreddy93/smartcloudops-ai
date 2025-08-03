# SmartCloudOps AI - FREE TIER Configuration
# Estimated Cost: $0/month (AWS Free Tier)

# Project Configuration
project_name = "smartcloudops-ai"
environment  = "development"

# AWS Configuration
aws_region = "us-east-1"  # FREE TIER available

# IMPORTANT: Add your SSH public key here
# Generate with: ssh-keygen -t rsa -b 2048 -f ~/.ssh/smartcloudops-ai
# Then copy the contents of ~/.ssh/smartcloudops-ai.pub
ssh_public_key = ""  # MUST BE PROVIDED

# Network Configuration
vpc_cidr               = "10.0.0.0/16"
public_subnet_1_cidr   = "10.0.1.0/24"
public_subnet_2_cidr   = "10.0.2.0/24"

# EC2 Configuration (FREE TIER)
ec2_instance_type = "t2.micro"  # 750 hours/month free

# Monitoring Configuration
enable_monitoring   = true
log_retention_days  = 7  # Minimal for free tier

# Application Ports
flask_app_port      = 5000
prometheus_port     = 9090
grafana_port        = 3000
node_exporter_port  = 9100

# Tags
tags = {
  Project     = "SmartCloudOps-AI"
  Environment = "development"
  CostCenter  = "free-tier"
  Purpose     = "learning-and-development"
}
