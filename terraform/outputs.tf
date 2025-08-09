# Outputs for SmartCloudOps AI - FREE TIER Version

# Network Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_1_id" {
  description = "ID of public subnet 1"
  value       = aws_subnet.public_1.id
}

output "public_subnet_2_id" {
  description = "ID of public subnet 2"
  value       = aws_subnet.public_2.id
}

# EC2 Outputs
output "monitoring_instance_id" {
  description = "ID of the monitoring EC2 instance"
  value       = aws_instance.monitoring.id
}

output "monitoring_instance_public_ip" {
  description = "Public IP of the monitoring instance"
  value       = aws_instance.monitoring.public_ip
}

output "monitoring_instance_public_dns" {
  description = "Public DNS of the monitoring instance"
  value       = aws_instance.monitoring.public_dns
}

output "application_instance_id" {
  description = "ID of the application EC2 instance"
  value       = aws_instance.application.id
}

output "application_instance_public_ip" {
  description = "Public IP of the application instance"
  value       = aws_instance.application.public_ip
}

output "application_instance_public_dns" {
  description = "Public DNS of the application instance"
  value       = aws_instance.application.public_dns
}

# Application URLs
output "application_url" {
  description = "URL to access the SmartCloudOps AI application"
  value       = var.enable_https ? "https://${aws_lb.main[0].dns_name}" : "http://${aws_instance.application.public_ip}:5000"
}

output "application_status_url" {
  description = "URL to check application status"
  value       = var.enable_https ? "https://${aws_lb.main[0].dns_name}/status" : "http://${aws_instance.application.public_ip}:5000/status"
}

# ===== PHASE 3: HTTPS/TLS OUTPUTS =====
output "load_balancer_dns" {
  description = "DNS name of the Application Load Balancer"
  value       = var.enable_https ? aws_lb.main[0].dns_name : null
}

output "load_balancer_arn" {
  description = "ARN of the Application Load Balancer"
  value       = var.enable_https ? aws_lb.main[0].arn : null
}

output "ssl_certificate_arn" {
  description = "ARN of the SSL certificate"
  value       = var.enable_https && var.certificate_arn == "" ? aws_acm_certificate.main[0].arn : var.certificate_arn
}

output "ssl_certificate_domain_validation_options" {
  description = "Domain validation options for SSL certificate (for DNS validation)"
  value       = var.enable_https && var.certificate_arn == "" ? aws_acm_certificate.main[0].domain_validation_options : null
}

output "https_enabled" {
  description = "Whether HTTPS is enabled"
  value       = var.enable_https
}

output "alb_security_group_id" {
  description = "Security group ID for the Application Load Balancer"
  value       = var.enable_https ? aws_security_group.alb[0].id : null
}

# ===== PHASE 3: SECRETS MANAGER OUTPUTS =====
output "secrets_manager_enabled" {
  description = "Whether AWS Secrets Manager is enabled"
  value       = var.enable_secrets_manager
}

output "openai_secret_arn" {
  description = "ARN of the OpenAI API key secret"
  value       = var.enable_secrets_manager ? aws_secretsmanager_secret.openai_api_key[0].arn : null
}

output "gemini_secret_arn" {
  description = "ARN of the Gemini API key secret"
  value       = var.enable_secrets_manager ? aws_secretsmanager_secret.gemini_api_key[0].arn : null
}

output "app_api_keys_secret_arn" {
  description = "ARN of the application API keys database secret"
  value       = var.enable_secrets_manager ? aws_secretsmanager_secret.app_api_keys[0].arn : null
}

# ===== PHASE 3: ADVANCED MONITORING OUTPUTS =====
output "advanced_monitoring_enabled" {
  description = "Whether advanced monitoring is enabled"
  value       = var.enable_advanced_monitoring
}

output "cloudtrail_arn" {
  description = "ARN of the CloudTrail"
  value       = var.enable_advanced_monitoring ? aws_cloudtrail.main[0].arn : null
}

output "guardduty_detector_id" {
  description = "ID of the GuardDuty detector"
  value       = var.enable_advanced_monitoring ? aws_guardduty_detector.main[0].id : null
}

output "vpc_flow_logs_log_group" {
  description = "CloudWatch log group for VPC Flow Logs"
  value       = var.enable_advanced_monitoring ? aws_cloudwatch_log_group.vpc_flow_logs[0].name : null
}

output "cloudtrail_s3_bucket" {
  description = "S3 bucket for CloudTrail logs"
  value       = var.enable_advanced_monitoring ? aws_s3_bucket.cloudtrail_logs[0].bucket : null
}
output "flask_app_url" {
  description = "URL to access the Flask application"
  value       = "http://${aws_instance.application.public_ip}:5000"
}

output "grafana_url" {
  description = "URL to access Grafana dashboard"
  value       = "http://${aws_instance.monitoring.public_ip}:3000"
}

output "prometheus_url" {
  description = "URL to access Prometheus"
  value       = "http://${aws_instance.monitoring.public_ip}:9090"
}

# S3 Outputs
output "ml_models_bucket_name" {
  description = "Name of the S3 bucket for ML models"
  value       = aws_s3_bucket.ml_models.bucket
}

output "ml_models_bucket_arn" {
  description = "ARN of the S3 bucket for ML models"
  value       = aws_s3_bucket.ml_models.arn
}

output "logs_bucket_name" {
  description = "Name of the S3 bucket for logs"
  value       = aws_s3_bucket.logs.bucket
}

output "logs_bucket_arn" {
  description = "ARN of the S3 bucket for logs"
  value       = aws_s3_bucket.logs.arn
}

# Security Groups
output "monitoring_security_group_id" {
  description = "ID of the monitoring security group"
  value       = aws_security_group.monitoring.id
}

output "application_security_group_id" {
  description = "ID of the application security group"
  value       = aws_security_group.application.id
}

# IAM
output "ec2_role_arn" {
  description = "ARN of the EC2 IAM role"
  value       = aws_iam_role.ec2_role.arn
}

output "ec2_instance_profile_name" {
  description = "Name of the EC2 instance profile"
  value       = aws_iam_instance_profile.ec2_profile.name
}

# CloudWatch
output "application_log_group_name" {
  description = "Name of the application CloudWatch log group"
  value       = aws_cloudwatch_log_group.application.name
}

output "monitoring_log_group_name" {
  description = "Name of the monitoring CloudWatch log group"
  value       = aws_cloudwatch_log_group.monitoring.name
}

# SSH Connection Commands
output "ssh_monitoring_command" {
  description = "SSH command to connect to monitoring instance"
  value       = "ssh -i ~/.ssh/${var.project_name}.pem ec2-user@${aws_instance.monitoring.public_ip}"
}

output "ssh_application_command" {
  description = "SSH command to connect to application instance"
  value       = "ssh -i ~/.ssh/${var.project_name}.pem ec2-user@${aws_instance.application.public_ip}"
}

# Cost Summary
output "estimated_monthly_cost" {
  description = "Estimated monthly cost (FREE TIER)"
  value       = "$0/month (within AWS Free Tier limits)"
}

output "free_tier_resources" {
  description = "Free tier resources used"
  value = {
    ec2_instances   = "2 x t2.micro (750 hours/month each)"
    s3_storage      = "5GB standard storage per bucket"
    cloudwatch_logs = "5GB log ingestion"
    data_transfer   = "15GB outbound"
  }
}
