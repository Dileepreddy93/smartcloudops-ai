# SmartCloudOps AI - FREE TIER Configuration
# Estimated Cost: $0/month (AWS Free Tier)

# Project Configuration
project_name = "smartcloudops-ai"
environment  = "development"

# AWS Configuration
aws_region = "us-east-1" # FREE TIER available

# IMPORTANT: Add your SSH public key here
# Generate with: ssh-keygen -t rsa -b 2048 -f ~/.ssh/smartcloudops-ai
# Then copy the contents of ~/.ssh/smartcloudops-ai.pub
ssh_public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDU9xkRxchF9RAwBtObNjzzotJl+mlQ99PRiDn1gr7HibMqnnx4rNYFfcUPhBP0IYte87vWwjPONyYSADl8uaQkOm4nWwqS7dTWYRwwlDIggHhAzGAJI8Ufs8YGLkqQmMdjhc8jGbXJ7eQZ+8QNce7RCH7T4WJnHgv/CKsEnxJ1GuWtQ9CYIKauVMy4ePoq19Iz8WQfX1VCwclGKH2lRVcB3zPll8pr26jAB93899PVj2vuag0d/HSq78T+fMiDQ88aW9Z8tf1BIOQuCAMRZfX8liNiv8Ts7aYe+uXPV7Mnr0Rv/S1g7XgJVfR6qHqcecml2zZES4awBz2/ab/UE6lv smartcloudops-ai-project"

# Network Configuration
vpc_cidr             = "10.0.0.0/16"
public_subnet_1_cidr = "10.0.1.0/24"
public_subnet_2_cidr = "10.0.2.0/24"

# EC2 Configuration (FREE TIER)
ec2_instance_type = "t2.micro" # 750 hours/month free

# Monitoring Configuration
enable_monitoring  = true
log_retention_days = 7 # Minimal for free tier

# Application Ports
flask_app_port     = 5000
prometheus_port    = 9090
grafana_port       = 3000
node_exporter_port = 9100

# Tags
tags = {
  Project     = "SmartCloudOps-AI"
  Environment = "development"
  CostCenter  = "free-tier"
  Purpose     = "learning-and-development"
}
