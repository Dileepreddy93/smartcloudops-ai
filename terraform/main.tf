# SmartCloudOps AI - FREE TIER Infrastructure
# Based on Phase 1: EC2 instances + basic monitoring
# Estimated cost: $0/month (AWS Free Tier)

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# VPC Configuration (Phase 1.1.2)
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

# Public Subnets (Phase 1.1.2 - 2 public subnets)
resource "aws_subnet" "public_1" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-1"
  }
}

resource "aws_subnet" "public_2" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = data.aws_availability_zones.available.names[1]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-2"
  }
}

# Route Table for Public Subnets
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

resource "aws_route_table_association" "public_1" {
  subnet_id      = aws_subnet.public_1.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_2" {
  subnet_id      = aws_subnet.public_2.id
  route_table_id = aws_route_table.public.id
}

# Security Groups (Phase 1.1.3) - 🔒 SECURITY HARDENED
resource "aws_security_group" "monitoring" {
  name_prefix = "${var.project_name}-monitoring-"
  vpc_id      = aws_vpc.main.id

  # 🔒 SSH access - RESTRICTED to specified CIDRs only
  dynamic "ingress" {
    for_each = length(var.allowed_ssh_cidrs) > 0 ? [1] : []
    content {
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = var.allowed_ssh_cidrs
      description = "SSH access from authorized networks only"
    }
  }

  # 🔒 Admin emergency SSH access
  dynamic "ingress" {
    for_each = var.admin_ip_cidr != "" ? [1] : []
    content {
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = [var.admin_ip_cidr]
      description = "Emergency admin SSH access"
    }
  }

  # 🔒 HTTP access - RESTRICTED to monitoring networks
  dynamic "ingress" {
    for_each = length(var.allowed_monitoring_cidrs) > 0 ? [1] : []
    content {
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      cidr_blocks = var.allowed_monitoring_cidrs
      description = "HTTP access from authorized monitoring networks"
    }
  }

  # 🔒 Grafana access - RESTRICTED to monitoring networks
  dynamic "ingress" {
    for_each = length(var.allowed_monitoring_cidrs) > 0 ? [1] : []
    content {
      from_port   = 3000
      to_port     = 3000
      protocol    = "tcp"
      cidr_blocks = var.allowed_monitoring_cidrs
      description = "Grafana access from authorized monitoring networks"
    }
  }

  # 🔒 Prometheus access - RESTRICTED to monitoring networks
  dynamic "ingress" {
    for_each = length(var.allowed_monitoring_cidrs) > 0 ? [1] : []
    content {
      from_port   = 9090
      to_port     = 9090
      protocol    = "tcp"
      cidr_blocks = var.allowed_monitoring_cidrs
      description = "Prometheus access from authorized monitoring networks"
    }
  }

  # Node Exporter - VPC internal only
  ingress {
    from_port   = 9100
    to_port     = 9100
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
    description = "Node Exporter - VPC internal communication"
  }

  # All outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = {
    Name        = "${var.project_name}-monitoring-sg"
    Environment = var.environment
    Security    = "hardened"
  }
}

resource "aws_security_group" "application" {
  name_prefix = "${var.project_name}-app-"
  vpc_id      = aws_vpc.main.id

  # 🔒 SSH access - RESTRICTED to specified CIDRs only
  dynamic "ingress" {
    for_each = length(var.allowed_ssh_cidrs) > 0 ? [1] : []
    content {
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = var.allowed_ssh_cidrs
      description = "SSH access from authorized networks only"
    }
  }

  # 🔒 Admin emergency SSH access
  dynamic "ingress" {
    for_each = var.admin_ip_cidr != "" ? [1] : []
    content {
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = [var.admin_ip_cidr]
      description = "Emergency admin SSH access"
    }
  }

  # 🔒 HTTP access - RESTRICTED to application networks
  dynamic "ingress" {
    for_each = length(var.allowed_app_cidrs) > 0 ? [1] : []
    content {
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      cidr_blocks = var.allowed_app_cidrs
      description = "HTTP access from authorized application networks"
    }
  }

  # 🔒 Flask app access - RESTRICTED to application networks
  dynamic "ingress" {
    for_each = length(var.allowed_app_cidrs) > 0 ? [1] : []
    content {
      from_port   = 5000
      to_port     = 5000
      protocol    = "tcp"
      cidr_blocks = var.allowed_app_cidrs
      description = "Flask application access from authorized networks"
    }
  }

  # Node Exporter - VPC internal only
  ingress {
    from_port   = 9100
    to_port     = 9100
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
    description = "Node Exporter - VPC internal communication"
  }

  # All outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = {
    Name        = "${var.project_name}-app-sg"
    Environment = var.environment
    Security    = "hardened"
  }
}

# Key Pair for EC2 access
resource "aws_key_pair" "main" {
  key_name   = "${var.project_name}-keypair"
  public_key = var.ssh_public_key

  tags = {
    Name = "${var.project_name}-keypair"
  }
}

# EC2 Instance for Monitoring (Phase 1.1.4 - ec2_monitoring)
resource "aws_instance" "monitoring" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = "t2.micro" # FREE TIER
  key_name               = aws_key_pair.main.key_name
  vpc_security_group_ids = [aws_security_group.monitoring.id]
  subnet_id              = aws_subnet.public_1.id
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  user_data = base64encode(templatefile("${path.module}/user_data/monitoring.sh", {
    project_name           = var.project_name,
    application_private_ip = "10.0.2.100", # Use static IP to avoid cycle
    grafana_admin_password = random_password.grafana_admin.result,
    prometheus_port        = var.prometheus_port,
    node_exporter_port     = "9100",
    grafana_port           = "3000"
  }))
  user_data_replace_on_change = true

  tags = {
    Name = "${var.project_name}-monitoring"
    Type = "monitoring"
  }
}

# Secure password for Grafana admin
resource "random_password" "grafana_admin" {
  length  = 20
  special = true
}

# EC2 Instance for Application (Phase 1.1.4 - ec2_application)
resource "aws_instance" "application" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = "t2.micro" # FREE TIER
  key_name               = aws_key_pair.main.key_name
  vpc_security_group_ids = [aws_security_group.application.id]
  subnet_id              = aws_subnet.public_2.id
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  user_data = base64encode(templatefile("${path.module}/user_data/application.sh", {
    project_name     = var.project_name,
    ml_models_bucket = aws_s3_bucket.ml_models.bucket,
    prometheus_host  = "10.0.1.100", # Use static IP to avoid cycle
    prometheus_port  = var.prometheus_port
  }))
  user_data_replace_on_change = true

  tags = {
    Name = "${var.project_name}-application"
    Type = "application"
  }
}

# Target Group Attachment for Application Instance
resource "aws_lb_target_group_attachment" "app" {
  count            = var.enable_https ? 1 : 0
  target_group_arn = aws_lb_target_group.app[0].arn
  target_id        = aws_instance.application.id
  port             = 5000
}

# S3 Bucket for ML Models (FREE TIER - 5GB)
resource "aws_s3_bucket" "ml_models" {
  bucket = "${var.project_name}-ml-models-${random_id.bucket_suffix.hex}"

  tags = {
    Name = "${var.project_name}-ml-models"
  }
}

resource "aws_s3_bucket_versioning" "ml_models" {
  bucket = aws_s3_bucket.ml_models.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ml_models" {
  bucket = aws_s3_bucket.ml_models.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 Bucket for Application Logs (FREE TIER - 5GB)
resource "aws_s3_bucket" "logs" {
  bucket = "${var.project_name}-logs-${random_id.bucket_suffix.hex}"

  tags = {
    Name = "${var.project_name}-logs"
  }
}

resource "aws_s3_bucket_versioning" "logs" {
  bucket = aws_s3_bucket.logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Random ID for unique bucket names
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# CloudWatch Log Groups (FREE TIER - 5GB)
resource "aws_cloudwatch_log_group" "application" {
  name              = "/aws/ec2/${var.project_name}-application"
  retention_in_days = 7 # Minimal retention for free tier

  tags = {
    Name = "${var.project_name}-application-logs"
  }
}

resource "aws_cloudwatch_log_group" "monitoring" {
  name              = "/aws/ec2/${var.project_name}-monitoring"
  retention_in_days = 7 # Minimal retention for free tier

  tags = {
    Name = "${var.project_name}-monitoring-logs"
  }
}

# IAM Role for EC2 instances
resource "aws_iam_role" "ec2_role" {
  name = "${var.project_name}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for S3 and CloudWatch access
resource "aws_iam_policy" "ec2_policy" {
  name = "${var.project_name}-ec2-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.ml_models.arn,
          "${aws_s3_bucket.ml_models.arn}/*",
          aws_s3_bucket.logs.arn,
          "${aws_s3_bucket.logs.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ec2_policy" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = aws_iam_policy.ec2_policy.arn
}

# Instance Profile for EC2
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.project_name}-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

# ===== PHASE 3: HTTPS/TLS IMPLEMENTATION =====

# SSL Certificate from AWS Certificate Manager
resource "aws_acm_certificate" "main" {
  count             = var.enable_https && var.domain_name != "" && var.certificate_arn == "" ? 1 : 0
  domain_name       = var.domain_name
  validation_method = "DNS"

  subject_alternative_names = [
    "*.${var.domain_name}"
  ]

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name        = "${var.project_name}-ssl-cert"
    Environment = var.environment
    Purpose     = "HTTPS termination"
  }
}

# Application Load Balancer for HTTPS termination
resource "aws_lb" "main" {
  count              = var.enable_https ? 1 : 0
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb[0].id]
  subnets            = [aws_subnet.public_1.id, aws_subnet.public_2.id]

  enable_deletion_protection = false

  # 🔒 SECURITY: Enhanced ALB logging
  access_logs {
    bucket  = aws_s3_bucket.alb_logs[0].bucket
    prefix  = "alb-logs"
    enabled = true
  }

  tags = {
    Name        = "${var.project_name}-alb"
    Environment = var.environment
    Purpose     = "HTTPS load balancing"
  }
}

# ALB Security Group - HTTPS focused
resource "aws_security_group" "alb" {
  count       = var.enable_https ? 1 : 0
  name_prefix = "${var.project_name}-alb-"
  vpc_id      = aws_vpc.main.id

  # 🔒 HTTP (redirect to HTTPS)
  dynamic "ingress" {
    for_each = var.enable_http_redirect ? [1] : []
    content {
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      cidr_blocks = length(var.allowed_app_cidrs) > 0 ? var.allowed_app_cidrs : ["0.0.0.0/0"]
      description = "HTTP traffic (will redirect to HTTPS)"
    }
  }

  # 🔒 HTTPS traffic
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = length(var.allowed_app_cidrs) > 0 ? var.allowed_app_cidrs : ["0.0.0.0/0"]
    description = "HTTPS traffic"
  }

  # Outbound to application servers
  egress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
    description = "Backend application traffic"
  }

  egress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
    description = "Backend HTTP traffic"
  }

  tags = {
    Name        = "${var.project_name}-alb-sg"
    Environment = var.environment
    Security    = "https-hardened"
  }
}

# Target Group for application servers
resource "aws_lb_target_group" "app" {
  count    = var.enable_https ? 1 : 0
  name     = "${var.project_name}-app-tg"
  port     = 5000
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  # 🔒 Enhanced health checks
  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    path                = "/status"
    matcher             = "200"
    port                = "traffic-port"
    protocol            = "HTTP"
  }

  # 🔒 Connection draining
  deregistration_delay = 30

  tags = {
    Name        = "${var.project_name}-app-tg"
    Environment = var.environment
  }
}

# HTTPS Listener (Primary)
resource "aws_lb_listener" "https" {
  count             = var.enable_https ? 1 : 0
  load_balancer_arn = aws_lb.main[0].arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01" # TLS 1.2 minimum
  certificate_arn   = var.certificate_arn != "" ? var.certificate_arn : aws_acm_certificate.main[0].arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app[0].arn
  }

  depends_on = [aws_acm_certificate.main]

  tags = {
    Name        = "${var.project_name}-https-listener"
    Environment = var.environment
  }
}

# HTTP Listener (Redirect to HTTPS)
resource "aws_lb_listener" "http_redirect" {
  count             = var.enable_https && var.enable_http_redirect ? 1 : 0
  load_balancer_arn = aws_lb.main[0].arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }

  tags = {
    Name        = "${var.project_name}-http-redirect"
    Environment = var.environment
  }
}

# S3 Bucket for ALB Access Logs
resource "aws_s3_bucket" "alb_logs" {
  count  = var.enable_https ? 1 : 0
  bucket = "${var.project_name}-alb-logs-${random_string.bucket_suffix[0].result}"

  tags = {
    Name        = "${var.project_name}-alb-logs"
    Environment = var.environment
    Purpose     = "Load balancer access logs"
  }
}

resource "aws_s3_bucket_versioning" "alb_logs" {
  count  = var.enable_https ? 1 : 0
  bucket = aws_s3_bucket.alb_logs[0].id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "alb_logs" {
  count  = var.enable_https ? 1 : 0
  bucket = aws_s3_bucket.alb_logs[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "alb_logs" {
  count  = var.enable_https ? 1 : 0
  bucket = aws_s3_bucket.alb_logs[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Random string for unique bucket naming
resource "random_string" "bucket_suffix" {
  count   = var.enable_https ? 1 : 0
  length  = 8
  special = false
  upper   = false
}

# ALB Log Policy
resource "aws_s3_bucket_policy" "alb_logs" {
  count  = var.enable_https ? 1 : 0
  bucket = aws_s3_bucket.alb_logs[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::127311923021:root" # ELB service account for us-east-1
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.alb_logs[0].arn}/alb-logs/AWSLogs/${data.aws_caller_identity.current.account_id}/*"
      },
      {
        Effect = "Allow"
        Principal = {
          Service = "delivery.logs.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.alb_logs[0].arn}/alb-logs/AWSLogs/${data.aws_caller_identity.current.account_id}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      },
      {
        Effect = "Allow"
        Principal = {
          Service = "delivery.logs.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.alb_logs[0].arn
      }
    ]
  })
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}

# ===== PHASE 3: AWS SECRETS MANAGER IMPLEMENTATION =====

# Secret for OpenAI API Key
resource "aws_secretsmanager_secret" "openai_api_key" {
  count                   = var.enable_secrets_manager ? 1 : 0
  name                    = "${var.project_name}/openai/api-key"
  description             = "OpenAI API key for SmartCloudOps AI"
  recovery_window_in_days = 7

  tags = {
    Name        = "${var.project_name}-openai-secret"
    Environment = var.environment
    Purpose     = "OpenAI API authentication"
  }
}

resource "aws_secretsmanager_secret_version" "openai_api_key" {
  count     = var.enable_secrets_manager && var.openai_api_key != "" ? 1 : 0
  secret_id = aws_secretsmanager_secret.openai_api_key[0].id
  secret_string = jsonencode({
    api_key = var.openai_api_key
  })
}

# Secret for Gemini API Key
resource "aws_secretsmanager_secret" "gemini_api_key" {
  count                   = var.enable_secrets_manager ? 1 : 0
  name                    = "${var.project_name}/gemini/api-key"
  description             = "Google Gemini API key for SmartCloudOps AI"
  recovery_window_in_days = 7

  tags = {
    Name        = "${var.project_name}-gemini-secret"
    Environment = var.environment
    Purpose     = "Gemini API authentication"
  }
}

resource "aws_secretsmanager_secret_version" "gemini_api_key" {
  count     = var.enable_secrets_manager && var.gemini_api_key != "" ? 1 : 0
  secret_id = aws_secretsmanager_secret.gemini_api_key[0].id
  secret_string = jsonencode({
    api_key = var.gemini_api_key
  })
}

# Secret for Application API Keys Database
resource "aws_secretsmanager_secret" "app_api_keys" {
  count                   = var.enable_secrets_manager ? 1 : 0
  name                    = "${var.project_name}/app/api-keys-db"
  description             = "Application API keys database"
  recovery_window_in_days = 7

  tags = {
    Name        = "${var.project_name}-app-keys-secret"
    Environment = var.environment
    Purpose     = "Application authentication database"
  }
}

# Secret for Database Credentials (if applicable)
resource "aws_secretsmanager_secret" "database_credentials" {
  count                   = var.enable_secrets_manager ? 1 : 0
  name                    = "${var.project_name}/database/credentials"
  description             = "Database connection credentials"
  recovery_window_in_days = 7

  tags = {
    Name        = "${var.project_name}-db-secret"
    Environment = var.environment
    Purpose     = "Database authentication"
  }
}

# IAM Role for Secrets Access
resource "aws_iam_role" "secrets_access_role" {
  count = var.enable_secrets_manager ? 1 : 0
  name  = "${var.project_name}-secrets-access-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-secrets-role"
    Environment = var.environment
  }
}

# IAM Policy for Secrets Manager Access
resource "aws_iam_policy" "secrets_access_policy" {
  count       = var.enable_secrets_manager ? 1 : 0
  name        = "${var.project_name}-secrets-access-policy"
  description = "Policy for accessing SmartCloudOps AI secrets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          aws_secretsmanager_secret.openai_api_key[0].arn,
          aws_secretsmanager_secret.gemini_api_key[0].arn,
          aws_secretsmanager_secret.app_api_keys[0].arn,
          aws_secretsmanager_secret.database_credentials[0].arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:ListSecrets"
        ]
        Resource = "*"
        Condition = {
          StringLike = {
            "secretsmanager:Name" = "${var.project_name}/*"
          }
        }
      }
    ]
  })
}

# Attach Secrets Policy to EC2 Role
resource "aws_iam_role_policy_attachment" "secrets_policy_attachment" {
  count      = var.enable_secrets_manager ? 1 : 0
  role       = aws_iam_role.ec2_role.name
  policy_arn = aws_iam_policy.secrets_access_policy[0].arn
}

# ===== PHASE 3: ADVANCED SECURITY MONITORING =====

# CloudTrail for API call logging
resource "aws_cloudtrail" "main" {
  count                         = var.enable_advanced_monitoring ? 1 : 0
  name                          = "${var.project_name}-cloudtrail"
  s3_bucket_name                = aws_s3_bucket.cloudtrail_logs[0].bucket
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_logging                = true

  event_selector {
    read_write_type                  = "All"
    include_management_events        = true
    exclude_management_event_sources = []

    data_resource {
      type   = "AWS::S3::Object"
      values = ["${aws_s3_bucket.ml_models.arn}/*"]
    }
  }

  tags = {
    Name        = "${var.project_name}-cloudtrail"
    Environment = var.environment
    Purpose     = "Security audit logging"
  }
}

# S3 Bucket for CloudTrail Logs
resource "aws_s3_bucket" "cloudtrail_logs" {
  count  = var.enable_advanced_monitoring ? 1 : 0
  bucket = "${var.project_name}-cloudtrail-logs-${random_string.cloudtrail_suffix[0].result}"

  tags = {
    Name        = "${var.project_name}-cloudtrail-logs"
    Environment = var.environment
    Purpose     = "CloudTrail audit logs"
  }
}

resource "aws_s3_bucket_versioning" "cloudtrail_logs" {
  count  = var.enable_advanced_monitoring ? 1 : 0
  bucket = aws_s3_bucket.cloudtrail_logs[0].id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "cloudtrail_logs" {
  count  = var.enable_advanced_monitoring ? 1 : 0
  bucket = aws_s3_bucket.cloudtrail_logs[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "cloudtrail_logs" {
  count  = var.enable_advanced_monitoring ? 1 : 0
  bucket = aws_s3_bucket.cloudtrail_logs[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "random_string" "cloudtrail_suffix" {
  count   = var.enable_advanced_monitoring ? 1 : 0
  length  = 8
  special = false
  upper   = false
}

# CloudTrail S3 Bucket Policy
resource "aws_s3_bucket_policy" "cloudtrail_logs" {
  count  = var.enable_advanced_monitoring ? 1 : 0
  bucket = aws_s3_bucket.cloudtrail_logs[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AWSCloudTrailAclCheck"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.cloudtrail_logs[0].arn
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = "arn:aws:cloudtrail:${var.aws_region}:${data.aws_caller_identity.current.account_id}:trail/${var.project_name}-cloudtrail"
          }
        }
      },
      {
        Sid    = "AWSCloudTrailWrite"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.cloudtrail_logs[0].arn}/AWSLogs/${data.aws_caller_identity.current.account_id}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl"  = "bucket-owner-full-control"
            "AWS:SourceArn" = "arn:aws:cloudtrail:${var.aws_region}:${data.aws_caller_identity.current.account_id}:trail/${var.project_name}-cloudtrail"
          }
        }
      }
    ]
  })
}

# GuardDuty for threat detection
resource "aws_guardduty_detector" "main" {
  count  = var.enable_advanced_monitoring ? 1 : 0
  enable = true

  datasources {
    s3_logs {
      enable = true
    }
    kubernetes {
      audit_logs {
        enable = false # Not using EKS
      }
    }
    malware_protection {
      scan_ec2_instance_with_findings {
        ebs_volumes {
          enable = true
        }
      }
    }
  }

  tags = {
    Name        = "${var.project_name}-guardduty"
    Environment = var.environment
    Purpose     = "Threat detection"
  }
}

# VPC Flow Logs for network monitoring
resource "aws_flow_log" "vpc_flow_logs" {
  count           = var.enable_advanced_monitoring ? 1 : 0
  iam_role_arn    = aws_iam_role.flow_log_role[0].arn
  log_destination = aws_cloudwatch_log_group.vpc_flow_logs[0].arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.main.id

  tags = {
    Name        = "${var.project_name}-vpc-flow-logs"
    Environment = var.environment
    Purpose     = "Network traffic monitoring"
  }
}

# CloudWatch Log Group for VPC Flow Logs
resource "aws_cloudwatch_log_group" "vpc_flow_logs" {
  count             = var.enable_advanced_monitoring ? 1 : 0
  name              = "/aws/vpc/flowlogs/${var.project_name}"
  retention_in_days = 30

  tags = {
    Name        = "${var.project_name}-vpc-flow-logs"
    Environment = var.environment
  }
}

# IAM Role for VPC Flow Logs
resource "aws_iam_role" "flow_log_role" {
  count = var.enable_advanced_monitoring ? 1 : 0
  name  = "${var.project_name}-flow-log-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for VPC Flow Logs
resource "aws_iam_role_policy" "flow_log_policy" {
  count = var.enable_advanced_monitoring ? 1 : 0
  name  = "${var.project_name}-flow-log-policy"
  role  = aws_iam_role.flow_log_role[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}
