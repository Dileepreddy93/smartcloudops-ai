# Variables for SmartCloudOps AI - FREE TIER Version
# Cost: $0/month (AWS Free Tier eligible)

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "smartcloudops-ai"
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1" # FREE TIER available
}

variable "ssh_public_key" {
  description = "SSH public key for EC2 access"
  type        = string
  default     = "" # Must be provided
  validation {
    condition     = length(var.ssh_public_key) > 0
    error_message = "SSH public key must be provided for security."
  }
  
  validation {
    condition     = length(var.ssh_public_key) > 0
    error_message = "SSH public key must be provided for security."
  }
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "development"
}

# 🔒 SECURITY: Network Access Control
variable "allowed_ssh_cidrs" {
  description = "CIDR blocks allowed for SSH access (port 22)"
  type        = list(string)
  default     = [] # Must be explicitly set - no default SSH access
}

variable "allowed_app_cidrs" {
  description = "CIDR blocks allowed for application access (port 5000)"
  type        = list(string)
  default     = [] # Must be explicitly set - no default app access
}

variable "allowed_monitoring_cidrs" {
  description = "CIDR blocks allowed for monitoring access (ports 3000, 9090)"
  type        = list(string)
  default     = [] # Must be explicitly set - no default monitoring access
}

# ===== PHASE 3: HTTPS/TLS CONFIGURATION =====
variable "domain_name" {
  description = "Domain name for SSL certificate (e.g., smartcloudops.yourdomain.com)"
  type        = string
  default     = "" # Set to enable HTTPS
}

variable "enable_https" {
  description = "Enable HTTPS with Application Load Balancer and SSL certificate"
  type        = bool
  default     = false # Set to true to enable HTTPS
}

variable "certificate_arn" {
  description = "ARN of existing SSL certificate in ACM (optional)"
  type        = string
  default     = "" # Leave empty to create new certificate
}

variable "enable_http_redirect" {
  description = "Redirect HTTP traffic to HTTPS automatically"
  type        = bool
  default     = true
}

# ===== PHASE 3: SECRETS MANAGEMENT =====
variable "enable_secrets_manager" {
  description = "Enable AWS Secrets Manager for API keys and sensitive data"
  type        = bool
  default     = false
}

variable "secret_rotation_days" {
  description = "Number of days between automatic secret rotation"
  type        = number
  default     = 30
}

# ===== PHASE 3: ADVANCED MONITORING =====
variable "enable_advanced_monitoring" {
  description = "Enable advanced security monitoring (CloudTrail, GuardDuty, etc.)"
  type        = bool
  default     = false
}

variable "enable_waf" {
  description = "Enable Web Application Firewall for enhanced security"
  type        = bool
  default     = false
}

# EC2 Configuration (FREE TIER)
variable "ec2_instance_type" {
  description = "Instance type for EC2 instances"
  type        = string
  default     = "t2.micro" # FREE TIER: 750 hours/month
}

# Monitoring Configuration
variable "enable_monitoring" {
  description = "Enable CloudWatch monitoring"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7 # Minimal for free tier
}

# Network Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_1_cidr" {
  description = "CIDR block for public subnet 1"
  type        = string
  default     = "10.0.1.0/24"
}

variable "public_subnet_2_cidr" {
  description = "CIDR block for public subnet 2"
  type        = string
  default     = "10.0.2.0/24"
}

# Application Configuration
variable "flask_app_port" {
  description = "Port for Flask application"
  type        = number
  default     = 5000
}

variable "prometheus_port" {
  description = "Port for Prometheus"
  type        = number
  default     = 9090
}

variable "grafana_port" {
  description = "Port for Grafana"
  type        = number
  default     = 3000
}

variable "node_exporter_port" {
  description = "Port for Node Exporter"
  type        = number
  default     = 9100
}

# Tags
variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "SmartCloudOps-AI"
    Environment = "development"
    CostCenter  = "free-tier"
  }
}

# ===== MISSING VARIABLES FOR PHASE 3 =====

variable "admin_ip_cidr" {
  description = "CIDR block for emergency admin access"
  type        = string
  default     = ""
}

variable "openai_api_key" {
  description = "OpenAI API key for AI integration"
  type        = string
  default     = ""
  sensitive   = true
}

variable "gemini_api_key" {
  description = "Google Gemini API key for AI integration"
  type        = string
  default     = ""
  sensitive   = true
}
