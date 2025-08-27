# SmartCloudOps AI - Terraform Variables
# =====================================

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "smartcloudops-ai"
}

variable "environment" {
  description = "Environment (development, staging, production)"
  type        = string
  default     = "development"
  
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production."
  }
}

# SECURITY: Database password variable with validation
variable "db_password" {
  description = "Database password - MUST be set securely"
  type        = string
  sensitive   = true
  
  validation {
    condition     = length(var.db_password) >= 12
    error_message = "Database password must be at least 12 characters long."
  }
  
  validation {
    condition     = can(regex("^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[@$!%*?&])[A-Za-z\\d@$!%*?&]", var.db_password))
    error_message = "Database password must contain at least one uppercase letter, one lowercase letter, one number, and one special character."
  }
}

variable "ssh_public_key" {
  description = "SSH public key for EC2 access"
  type        = string
  default     = "" # Must be provided
  
  validation {
    condition     = length(var.ssh_public_key) > 0
    error_message = "SSH public key must be provided for security."
  }
}

# SECURITY: Network access control variables
variable "allowed_ssh_cidrs" {
  description = "List of CIDR blocks allowed SSH access"
  type        = list(string)
  default     = []
  
  validation {
    condition     = length(var.allowed_ssh_cidrs) == 0 || can(cidrhost(var.allowed_ssh_cidrs[0], 0))
    error_message = "All SSH CIDR blocks must be valid CIDR notation."
  }
}

variable "allowed_app_cidrs" {
  description = "List of CIDR blocks allowed application access"
  type        = list(string)
  default     = []
  
  validation {
    condition     = length(var.allowed_app_cidrs) == 0 || can(cidrhost(var.allowed_app_cidrs[0], 0))
    error_message = "All application CIDR blocks must be valid CIDR notation."
  }
}

variable "allowed_monitoring_cidrs" {
  description = "List of CIDR blocks allowed monitoring access"
  type        = list(string)
  default     = []
  
  validation {
    condition     = length(var.allowed_monitoring_cidrs) == 0 || can(cidrhost(var.allowed_monitoring_cidrs[0], 0))
    error_message = "All monitoring CIDR blocks must be valid CIDR notation."
  }
}

variable "admin_ip_cidr" {
  description = "Admin IP CIDR for emergency access"
  type        = string
  default     = ""
  
  validation {
    condition     = var.admin_ip_cidr == "" || can(cidrhost(var.admin_ip_cidr, 0))
    error_message = "Admin IP CIDR must be valid CIDR notation or empty."
  }
}

# HTTPS/TLS Configuration
variable "enable_https" {
  description = "Enable HTTPS with Application Load Balancer"
  type        = bool
  default     = false
}

variable "domain_name" {
  description = "Domain name for SSL certificate"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "ARN of existing SSL certificate"
  type        = string
  default     = ""
}

variable "enable_http_redirect" {
  description = "Enable HTTP to HTTPS redirect"
  type        = bool
  default     = true
}

# Secrets Management
variable "enable_secrets_manager" {
  description = "Enable AWS Secrets Manager integration"
  type        = bool
  default     = false
}

variable "openai_api_key" {
  description = "OpenAI API key for Secrets Manager"
  type        = string
  default     = ""
  sensitive   = true
}

variable "gemini_api_key" {
  description = "Gemini API key for Secrets Manager"
  type        = string
  default     = ""
  sensitive   = true
}

# Advanced Monitoring
variable "enable_advanced_monitoring" {
  description = "Enable advanced monitoring (CloudTrail, GuardDuty, VPC Flow Logs)"
  type        = bool
  default     = false
}

# Monitoring Configuration
variable "prometheus_port" {
  description = "Prometheus port"
  type        = string
  default     = "9090"
}

# Instance Types (Production Ready)
variable "monitoring_instance_type" {
  description = "EC2 instance type for monitoring server"
  type        = string
  default     = "t3.small" # Production ready, not free tier
}

variable "application_instance_type" {
  description = "EC2 instance type for application server"
  type        = string
  default     = "t3.small" # Production ready, not free tier
}
