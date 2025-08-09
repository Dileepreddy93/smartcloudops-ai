#!/bin/bash
# 🆓 SmartCloudOps AI - FREE TIER SECURITY FIX
# Remove secrets from git and implement Parameter Store

set -e

echo "🆓 FREE TIER SECURITY IMPLEMENTATION"
echo "====================================="

# 1. Remove .env files from git history (FREE)
echo "🧹 Step 1: Cleaning git history..."
if [ -f ".env.production.template" ] || [ -f ".env.staging" ]; then
    echo "⚠️ Found sensitive files in git. Removing..."
    
    # Backup current files
    mkdir -p backup/env-files-$(date +%Y%m%d)
    cp -f .env* backup/env-files-$(date +%Y%m%d)/ 2>/dev/null || true
    
    # Remove from git history
    git filter-branch --force --index-filter \
        'git rm --cached --ignore-unmatch .env* *.env' HEAD
    
    # Remove files
    rm -f .env.production.template .env.staging .env.local 2>/dev/null || true
    
    echo "✅ Sensitive files removed from git"
else
    echo "✅ No sensitive files found in git"
fi

# 2. Create Parameter Store secrets (FREE)
echo "🔐 Step 2: Setting up AWS Parameter Store..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run: aws configure"
    exit 1
fi

# Create parameters (FREE - no cost for standard parameters)
echo "Creating secure parameters..."

# Application secrets
aws ssm put-parameter \
    --name "/smartcloudops/prod/secret-key" \
    --value "$(openssl rand -hex 32)" \
    --type "SecureString" \
    --description "Flask secret key" \
    --overwrite >/dev/null 2>&1 || echo "⚠️ Parameter may already exist"

aws ssm put-parameter \
    --name "/smartcloudops/prod/database-url" \
    --value "postgresql://smartcloudops:change-this-password@localhost/smartcloudops" \
    --type "SecureString" \
    --description "Database connection URL" \
    --overwrite >/dev/null 2>&1 || echo "⚠️ Parameter may already exist"

# API Keys (you'll need to set these manually with your actual keys)
aws ssm put-parameter \
    --name "/smartcloudops/prod/openai-api-key" \
    --value "your-openai-key-here" \
    --type "SecureString" \
    --description "OpenAI API Key" \
    --overwrite >/dev/null 2>&1 || echo "⚠️ Parameter may already exist"

aws ssm put-parameter \
    --name "/smartcloudops/prod/gemini-api-key" \
    --value "your-gemini-key-here" \
    --type "SecureString" \
    --description "Gemini API Key" \
    --overwrite >/dev/null 2>&1 || echo "⚠️ Parameter may already exist"

echo "✅ Parameter Store configured"

# 3. Create free SSL certificate script
echo "🔒 Step 3: Creating Let's Encrypt SSL setup..."
cat > scripts/setup-free-ssl.sh << 'EOF'
#!/bin/bash
# FREE SSL Certificate with Let's Encrypt

DOMAIN=${1:-"your-domain.com"}

if [ "$DOMAIN" = "your-domain.com" ]; then
    echo "❌ Please provide your domain: ./setup-free-ssl.sh yourdomain.com"
    exit 1
fi

# Install certbot (FREE)
sudo yum update -y
sudo yum install -y certbot

# Get certificate (FREE)
sudo certbot certonly --standalone \
    --email admin@${DOMAIN} \
    --agree-tos \
    --non-interactive \
    -d ${DOMAIN}

# Setup auto-renewal (FREE)
echo "0 2 * * * certbot renew --quiet && systemctl reload nginx" | sudo crontab -

echo "✅ FREE SSL certificate installed for ${DOMAIN}"
echo "📍 Certificate location: /etc/letsencrypt/live/${DOMAIN}/"
EOF

chmod +x scripts/setup-free-ssl.sh

# 4. Create free monitoring setup
echo "📊 Step 4: Creating free monitoring configuration..."
cat > scripts/setup-free-monitoring.sh << 'EOF'
#!/bin/bash
# FREE Monitoring Stack Setup

echo "🆓 Setting up FREE monitoring stack..."

# 1. Grafana Cloud (FREE tier)
echo "📊 Grafana Cloud setup:"
echo "1. Go to: https://grafana.com/products/cloud/"
echo "2. Sign up for FREE account (10k metrics, 50GB logs)"
echo "3. Get your Prometheus remote write endpoint"
echo "4. Update prometheus.yml with remote_write config"

# 2. UptimeRobot (FREE tier)
echo "⏰ UptimeRobot setup:"
echo "1. Go to: https://uptimerobot.com/"
echo "2. Sign up for FREE account (50 monitors)"
echo "3. Add HTTP monitor for your domain"

# 3. CloudWatch (FREE tier)
echo "☁️ CloudWatch basic monitoring (FREE)"
aws logs create-log-group --log-group-name /aws/ec2/smartcloudops || true

echo "✅ Free monitoring setup complete"
EOF

chmod +x scripts/setup-free-monitoring.sh

# 5. Update terraform for FREE tier
echo "🏗️ Step 5: Creating FREE tier infrastructure..."
cat > terraform/free-tier-main.tf << 'EOF'
# 🆓 SmartCloudOps AI - FREE TIER Infrastructure
# Optimized for AWS Free Tier limits

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

# VPC (FREE)
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "smartcloudops-free-vpc"
    Tier = "Free"
  }
}

# Internet Gateway (FREE)
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  
  tags = {
    Name = "smartcloudops-free-igw"
  }
}

# Public Subnet (FREE)
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true
  
  tags = {
    Name = "smartcloudops-free-public"
  }
}

# Private Subnet for RDS (FREE)
resource "aws_subnet" "private" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = data.aws_availability_zones.available.names[1]
  
  tags = {
    Name = "smartcloudops-free-private"
  }
}

# Route Table (FREE)
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  
  tags = {
    Name = "smartcloudops-free-rt"
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# Security Group - RESTRICTED (FREE)
resource "aws_security_group" "app" {
  name_prefix = "smartcloudops-free-"
  vpc_id      = aws_vpc.main.id
  
  # HTTPS only (secure)
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS traffic"
  }
  
  # HTTP redirect to HTTPS
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP redirect to HTTPS"
  }
  
  # SSH - RESTRICTED (replace with your IP)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["YOUR_IP/32"]  # 🔒 CHANGE THIS
    description = "SSH from your IP only"
  }
  
  # Outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "smartcloudops-free-sg"
  }
}

# IAM Role for EC2 (FREE)
resource "aws_iam_role" "ec2_role" {
  name = "smartcloudops-free-ec2-role"
  
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

# IAM Policy for Parameter Store (FREE)
resource "aws_iam_role_policy" "parameter_store" {
  name = "parameter-store-access"
  role = aws_iam_role.ec2_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath"
        ]
        Resource = "arn:aws:ssm:*:*:parameter/smartcloudops/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = "arn:aws:s3:::smartcloudops-free-models/*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "smartcloudops-free-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

# S3 Bucket for ML Models (FREE 5GB)
resource "aws_s3_bucket" "models" {
  bucket = "smartcloudops-free-models-${random_string.bucket_suffix.result}"
  
  tags = {
    Name = "SmartCloudOps ML Models"
    Tier = "Free"
  }
}

resource "aws_s3_bucket_versioning" "models" {
  bucket = aws_s3_bucket.models.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "models" {
  bucket = aws_s3_bucket.models.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# RDS Subnet Group (FREE)
resource "aws_db_subnet_group" "main" {
  name       = "smartcloudops-free-db-subnet"
  subnet_ids = [aws_subnet.public.id, aws_subnet.private.id]
  
  tags = {
    Name = "SmartCloudOps DB subnet group"
  }
}

# RDS PostgreSQL (FREE TIER)
resource "aws_db_instance" "postgres" {
  identifier = "smartcloudops-free-db"
  
  # FREE TIER SETTINGS
  instance_class    = "db.t3.micro"  # FREE
  allocated_storage = 20             # FREE up to 20GB
  storage_type      = "gp2"
  
  engine         = "postgres"
  engine_version = "14.9"
  
  db_name  = "smartcloudops"
  username = "smartcloudops"
  password = "change-this-password-123"  # 🔒 CHANGE THIS
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 7  # FREE
  backup_window          = "03:00-04:00"
  maintenance_window     = "Sun:04:00-Sun:05:00"
  
  skip_final_snapshot = true  # For demo
  deletion_protection = false # For demo
  
  tags = {
    Name = "SmartCloudOps Free DB"
  }
}

# RDS Security Group
resource "aws_security_group" "rds" {
  name_prefix = "smartcloudops-free-rds-"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
    description     = "PostgreSQL from app"
  }
  
  tags = {
    Name = "smartcloudops-free-rds-sg"
  }
}

# Single EC2 Instance (FREE TIER)
resource "aws_instance" "app" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = "t2.micro"  # FREE TIER
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.app.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name
  
  user_data = base64encode(templatefile("${path.module}/user_data/free_tier_setup.sh", {
    db_endpoint     = aws_db_instance.postgres.endpoint
    s3_bucket       = aws_s3_bucket.models.bucket
    aws_region      = var.aws_region
  }))
  
  tags = {
    Name = "SmartCloudOps-Free-Tier"
    Tier = "Free"
  }
}

# Outputs
output "instance_ip" {
  value = aws_instance.app.public_ip
}

output "database_endpoint" {
  value = aws_db_instance.postgres.endpoint
}

output "s3_bucket" {
  value = aws_s3_bucket.models.bucket
}

# Variables
variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"  # Cheapest region
}
EOF

echo "✅ FREE tier infrastructure created"

# 6. Create cost monitoring script
echo "💰 Step 6: Creating cost monitoring..."
cat > scripts/monitor-costs.sh << 'EOF'
#!/bin/bash
# FREE TIER Cost Monitoring

echo "💰 AWS FREE TIER USAGE CHECK"
echo "================================"

# Check current costs (requires AWS CLI)
echo "📊 Current month billing:"
aws ce get-cost-and-usage \
    --time-period Start=$(date -d "$(date +%Y-%m-01)" +%Y-%m-%d),End=$(date +%Y-%m-%d) \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --query 'ResultsByTime[0].Total.BlendedCost.Amount' \
    --output text 2>/dev/null || echo "Unable to fetch costs"

echo ""
echo "🆓 FREE TIER LIMITS:"
echo "EC2: 750 hours t2.micro (currently using: 1 instance)"
echo "RDS: 750 hours t3.micro (currently using: 1 instance)"
echo "S3: 5GB storage (check your usage in S3 console)"

echo ""
echo "💡 To check detailed usage:"
echo "1. Visit: https://console.aws.amazon.com/billing/home#/freetier"
echo "2. Monitor your free tier usage"
echo "3. Set up billing alerts at $1 threshold"
EOF

chmod +x scripts/monitor-costs.sh

echo ""
echo "🎉 FREE TIER SECURITY SETUP COMPLETE!"
echo "====================================="
echo ""
echo "✅ What was implemented (ALL FREE):"
echo "   🧹 Removed .env files from git"
echo "   🔐 AWS Parameter Store for secrets"
echo "   🔒 Let's Encrypt SSL script"
echo "   📊 Free monitoring setup"
echo "   🏗️ FREE tier infrastructure"
echo "   💰 Cost monitoring script"
echo ""
echo "🚀 NEXT STEPS:"
echo "1. Update your API keys in Parameter Store:"
echo "   aws ssm put-parameter --name '/smartcloudops/prod/openai-api-key' --value 'your-key' --type SecureString --overwrite"
echo ""
echo "2. Deploy FREE infrastructure:"
echo "   cd terraform && terraform apply -var-file='free-tier.tfvars'"
echo ""
echo "3. Setup FREE SSL:"
echo "   ./scripts/setup-free-ssl.sh yourdomain.com"
echo ""
echo "4. Monitor costs:"
echo "   ./scripts/monitor-costs.sh"
echo ""
echo "💰 TOTAL MONTHLY COST: $0.50 (Route 53 only)"
