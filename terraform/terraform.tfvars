# Example Terraform variables file for SmartCloudOps AI
# Copy this file to terraform.tfvars and customize the values

# Basic Configuration
aws_region   = "us-east-1"
environment  = "dev"
project_name = "smartcloudops-ai"

# Network Configuration
vpc_cidr             = "10.0.0.0/16"
public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs = ["10.0.10.0/24", "10.0.20.0/24"]

# Database Configuration
db_instance_class = "db.t3.micro" # Use db.t3.small or larger for production
db_username       = "admin"
# SECURITY: Password must be set via environment variable or secure method
# db_password       = "change-this-password-123!" # REMOVED - UNSAFE
db_password       = var.db_password # Must be set securely

# ECS Configuration
ecs_cpu           = "256" # Use "512" or higher for production
ecs_memory        = "512" # Use "1024" or higher for production
ecs_desired_count = 2     # Number of running tasks

# Container Registry
ecr_repository_url = "123456789012.dkr.ecr.us-east-1.amazonaws.com/smartcloudops-ai"

# Monitoring and Backup
enable_monitoring     = true
enable_backup         = true
log_retention_days    = 30
backup_retention_days = 7

# Auto Scaling
auto_scaling_min_capacity = 1
auto_scaling_max_capacity = 10
auto_scaling_target_cpu   = 70

# Optional: SSL and Domain (for production)
# ssl_certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/your-cert-id"
# domain_name = "smartcloudops.yourdomain.com"

# Optional: WAF (for additional security)
# enable_waf = true

# Lambda Configuration (disabled by default)
enable_lambda      = false # Set to true to enable Lambda function for ML processing
lambda_timeout     = 300
lambda_memory_size = 128

# Storage
ml_model_storage_class = "STANDARD"

# Load Balancer
enable_cross_zone_lb = true

# Container Insights
enable_container_insights = true
