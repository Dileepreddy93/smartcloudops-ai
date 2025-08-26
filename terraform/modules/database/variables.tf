# SmartCloudOps AI - Database Module Variables
# ===========================================

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment (development, staging, production)"
  type        = string
  
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production."
  }
}

variable "vpc_id" {
  description = "VPC ID where the database will be created"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for the database subnet group"
  type        = list(string)
  
  validation {
    condition     = length(var.subnet_ids) >= 2
    error_message = "At least 2 subnets are required for high availability."
  }
}

variable "app_security_group_id" {
  description = "Security group ID of the application servers"
  type        = string
}

variable "instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
  
  validation {
    condition     = can(regex("^db\\.[a-z0-9]+\\.[a-z0-9]+$", var.instance_class))
    error_message = "Instance class must be a valid RDS instance class."
  }
}

variable "allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
  
  validation {
    condition     = var.allocated_storage >= 20
    error_message = "Allocated storage must be at least 20 GB."
  }
}

variable "max_allocated_storage" {
  description = "Maximum allocated storage in GB for auto-scaling"
  type        = number
  default     = 100
  
  validation {
    condition     = var.max_allocated_storage >= var.allocated_storage
    error_message = "Maximum allocated storage must be greater than or equal to allocated storage."
  }
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "admin"
  
  validation {
    condition     = length(var.db_username) >= 3
    error_message = "Database username must be at least 3 characters long."
  }
}

variable "db_password" {
  description = "Database master password - MUST be set securely"
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

variable "backup_retention_period" {
  description = "Backup retention period in days"
  type        = number
  default     = 7
  
  validation {
    condition     = var.backup_retention_period >= 1 && var.backup_retention_period <= 35
    error_message = "Backup retention period must be between 1 and 35 days."
  }
}

variable "monitoring_role_arn" {
  description = "IAM role ARN for RDS monitoring"
  type        = string
  default     = ""
}

variable "alarm_actions" {
  description = "List of ARNs for CloudWatch alarm actions (SNS topics, etc.)"
  type        = list(string)
  default     = []
}
