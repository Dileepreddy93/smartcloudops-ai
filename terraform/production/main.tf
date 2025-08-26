# Production Infrastructure for SmartCloudOps AI
# High availability, security, and scalability

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket         = "smartcloudops-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = "production"
      Project     = "smartcloudops-ai"
      ManagedBy   = "terraform"
    }
  }
}

# =============================================================================
# VPC & NETWORKING
# =============================================================================

# VPC with CIDR 10.0.0.0/16
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "smartcloudops-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "smartcloudops-igw"
  }
}

# NAT Gateway for private subnets
resource "aws_eip" "nat" {
  domain = "vpc"
  
  tags = {
    Name = "smartcloudops-nat-eip"
  }
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public_1.id

  tags = {
    Name = "smartcloudops-nat"
  }

  depends_on = [aws_internet_gateway.main]
}

# Public Subnets (for ALB and NAT Gateway)
resource "aws_subnet" "public_1" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name = "smartcloudops-public-1"
  }
}

resource "aws_subnet" "public_2" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = data.aws_availability_zones.available.names[1]
  map_public_ip_on_launch = true

  tags = {
    Name = "smartcloudops-public-2"
  }
}

# Private Subnets (for application instances)
resource "aws_subnet" "private_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.10.0/24"
  availability_zone = data.aws_availability_zones.available.names[0]

  tags = {
    Name = "smartcloudops-private-1"
  }
}

resource "aws_subnet" "private_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.20.0/24"
  availability_zone = data.aws_availability_zones.available.names[1]

  tags = {
    Name = "smartcloudops-private-2"
  }
}

# Database Subnets (for RDS)
resource "aws_subnet" "database_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.30.0/24"
  availability_zone = data.aws_availability_zones.available.names[0]

  tags = {
    Name = "smartcloudops-database-1"
  }
}

resource "aws_subnet" "database_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.40.0/24"
  availability_zone = data.aws_availability_zones.available.names[1]

  tags = {
    Name = "smartcloudops-database-2"
  }
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "smartcloudops-public-rt"
  }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }

  tags = {
    Name = "smartcloudops-private-rt"
  }
}

# Route Table Associations
resource "aws_route_table_association" "public_1" {
  subnet_id      = aws_subnet.public_1.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_2" {
  subnet_id      = aws_subnet.public_2.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private_1" {
  subnet_id      = aws_subnet.private_1.id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "private_2" {
  subnet_id      = aws_subnet.private_2.id
  route_table_id = aws_route_table.private.id
}

# =============================================================================
# SECURITY GROUPS
# =============================================================================

# ALB Security Group
resource "aws_security_group" "alb" {
  name        = "smartcloudops-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP from Internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS from Internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "smartcloudops-alb-sg"
  }
}

# Application Security Group
resource "aws_security_group" "app" {
  name        = "smartcloudops-app-sg"
  description = "Security group for application instances"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "HTTP from ALB"
    from_port       = 5000
    to_port         = 5000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  ingress {
    description     = "Health checks from ALB"
    from_port       = 5000
    to_port         = 5000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "smartcloudops-app-sg"
  }
}

# Database Security Group
resource "aws_security_group" "database" {
  name        = "smartcloudops-database-sg"
  description = "Security group for RDS database"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "PostgreSQL from application"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "smartcloudops-database-sg"
  }
}

# Redis Security Group
resource "aws_security_group" "redis" {
  name        = "smartcloudops-redis-sg"
  description = "Security group for ElastiCache Redis"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Redis from application"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "smartcloudops-redis-sg"
  }
}

# =============================================================================
# DATABASE (RDS)
# =============================================================================

# RDS Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "smartcloudops-db-subnet-group"
  subnet_ids = [aws_subnet.database_1.id, aws_subnet.database_2.id]

  tags = {
    Name = "smartcloudops-db-subnet-group"
  }
}

# RDS Parameter Group
resource "aws_db_parameter_group" "main" {
  family = "postgres15"
  name   = "smartcloudops-db-params"

  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  parameter {
    name  = "log_statement"
    value = "all"
  }
}

# RDS Instance
resource "aws_db_instance" "main" {
  identifier = "smartcloudops-db"

  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.micro"

  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp2"
  storage_encrypted     = true

  db_name  = "smartcloudops"
  username = var.db_username
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.database.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  parameter_group_name   = aws_db_parameter_group.main.name

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  multi_az               = false  # Enable for production
  publicly_accessible    = false
  skip_final_snapshot    = false
  final_snapshot_identifier = "smartcloudops-final-snapshot"

  tags = {
    Name = "smartcloudops-db"
  }
}

# =============================================================================
# CACHE (ElastiCache Redis)
# =============================================================================

# Redis Subnet Group
resource "aws_elasticache_subnet_group" "main" {
  name       = "smartcloudops-redis-subnet-group"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]
}

# Redis Parameter Group
resource "aws_elasticache_parameter_group" "main" {
  family = "redis7"
  name   = "smartcloudops-redis-params"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }
}

# Redis Cluster
resource "aws_elasticache_cluster" "main" {
  cluster_id           = "smartcloudops-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = aws_elasticache_parameter_group.main.name
  port                 = 6379
  security_group_ids   = [aws_security_group.redis.id]
  subnet_group_name    = aws_elasticache_subnet_group.main.name

  tags = {
    Name = "smartcloudops-redis"
  }
}

# =============================================================================
# APPLICATION LOAD BALANCER
# =============================================================================

resource "aws_lb" "main" {
  name               = "smartcloudops-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = [aws_subnet.public_1.id, aws_subnet.public_2.id]

  enable_deletion_protection = true

  tags = {
    Name = "smartcloudops-alb"
  }
}

resource "aws_lb_target_group" "main" {
  name     = "smartcloudops-tg"
  port     = 5000
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name = "smartcloudops-tg"
  }
}

resource "aws_lb_listener" "main" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main.arn
  }
}

# =============================================================================
# AUTO SCALING GROUP
# =============================================================================

# Launch Template
resource "aws_launch_template" "main" {
  name_prefix   = "smartcloudops-lt"
  image_id      = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"

  network_interfaces {
    associate_public_ip_address = false
    security_groups             = [aws_security_group.app.id]
  }

  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    db_host     = aws_db_instance.main.endpoint
    db_name     = aws_db_instance.main.db_name
    db_username = aws_db_instance.main.username
    db_password = aws_db_instance.main.password
    redis_host  = aws_elasticache_cluster.main.cache_nodes[0].address
    redis_port  = aws_elasticache_cluster.main.port
  }))

  iam_instance_profile {
    name = aws_iam_instance_profile.ec2_profile.name
  }

  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "smartcloudops-app"
    }
  }
}

# Auto Scaling Group
resource "aws_autoscaling_group" "main" {
  name                = "smartcloudops-asg"
  desired_capacity    = 2
  max_size           = 4
  min_size           = 1
  target_group_arns  = [aws_lb_target_group.main.arn]
  vpc_zone_identifier = [aws_subnet.private_1.id, aws_subnet.private_2.id]

  launch_template {
    id      = aws_launch_template.main.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value              = "smartcloudops-app"
    propagate_at_launch = true
  }
}

# Auto Scaling Policy
resource "aws_autoscaling_policy" "cpu" {
  name                   = "smartcloudops-cpu-policy"
  scaling_adjustment     = 1
  adjustment_type        = "ChangeInCapacity"
  cooldown              = 300
  autoscaling_group_name = aws_autoscaling_group.main.name
}

resource "aws_autoscaling_policy" "cpu_down" {
  name                   = "smartcloudops-cpu-down-policy"
  scaling_adjustment     = -1
  adjustment_type        = "ChangeInCapacity"
  cooldown              = 300
  autoscaling_group_name = aws_autoscaling_group.main.name
}

# CloudWatch CPU Alarm
resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "smartcloudops-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "120"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "Scale up if CPU > 80% for 4 minutes"
  alarm_actions       = [aws_autoscaling_policy.cpu.arn]

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.main.name
  }
}

resource "aws_cloudwatch_metric_alarm" "cpu_low" {
  alarm_name          = "smartcloudops-cpu-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "120"
  statistic           = "Average"
  threshold           = "20"
  alarm_description   = "Scale down if CPU < 20% for 4 minutes"
  alarm_actions       = [aws_autoscaling_policy.cpu_down.arn]

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.main.name
  }
}

# =============================================================================
# IAM ROLES
# =============================================================================

resource "aws_iam_role" "ec2_role" {
  name = "smartcloudops-ec2-role"

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

resource "aws_iam_role_policy" "ec2_policy" {
  name = "smartcloudops-ec2-policy"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.ml_models.arn,
          "${aws_s3_bucket.ml_models.arn}/*"
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

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "smartcloudops-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

# =============================================================================
# S3 BUCKETS
# =============================================================================

resource "aws_s3_bucket" "ml_models" {
  bucket = "smartcloudops-ml-models-${random_string.bucket_suffix.result}"

  tags = {
    Name = "smartcloudops-ml-models"
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

resource "aws_s3_bucket_public_access_block" "ml_models" {
  bucket = aws_s3_bucket.ml_models.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# =============================================================================
# DATA SOURCES
# =============================================================================

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

# =============================================================================
# RANDOM RESOURCES
# =============================================================================

resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "database_endpoint" {
  description = "RDS database endpoint"
  value       = aws_db_instance.main.endpoint
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = aws_elasticache_cluster.main.cache_nodes[0].address
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}
