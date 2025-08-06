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
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "development"
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
