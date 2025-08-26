# SmartCloudOps AI - Database Module
# =================================
# Production-ready PostgreSQL database with proper security and backup

resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet-group"
  subnet_ids = var.subnet_ids

  tags = {
    Name        = "${var.project_name}-db-subnet-group"
    Environment = var.environment
  }
}

resource "aws_security_group" "database" {
  name_prefix = "${var.project_name}-db-"
  vpc_id      = var.vpc_id

  # Database access from application servers only
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.app_security_group_id]
    description     = "PostgreSQL access from application servers"
  }

  # No outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = {
    Name        = "${var.project_name}-db-sg"
    Environment = var.environment
    Security    = "hardened"
  }
}

resource "aws_db_instance" "main" {
  identifier = "${var.project_name}-db"

  # Database configuration
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = var.instance_class

  # Storage configuration
  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true

  # Credentials
  username = var.db_username
  password = var.db_password

  # Network configuration
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.database.id]
  publicly_accessible    = false
  port                   = 5432

  # Backup and maintenance
  backup_retention_period = var.backup_retention_period
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  auto_minor_version_upgrade = true

  # Performance insights
  performance_insights_enabled = true
  performance_insights_retention_period = 7

  # Monitoring
  monitoring_interval = 60
  monitoring_role_arn = var.monitoring_role_arn

  # Deletion protection
  deletion_protection = var.environment == "production"

  # Tags
  tags = {
    Name        = "${var.project_name}-db"
    Environment = var.environment
    Purpose     = "Application database"
  }

  # Parameter group for security settings
  parameter_group_name = aws_db_parameter_group.main.name

  # Option group for additional features
  option_group_name = aws_db_option_group.main.name
}

resource "aws_db_parameter_group" "main" {
  family = "postgres15"
  name   = "${var.project_name}-db-params"

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

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  parameter {
    name  = "rds.force_ssl"
    value = "1"
  }

  tags = {
    Name        = "${var.project_name}-db-params"
    Environment = var.environment
  }
}

resource "aws_db_option_group" "main" {
  name                     = "${var.project_name}-db-options"
  engine_name              = "postgres"
  major_engine_version     = "15"

  tags = {
    Name        = "${var.project_name}-db-options"
    Environment = var.environment
  }
}

# CloudWatch alarms for database monitoring
resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "${var.project_name}-db-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "Database CPU utilization is high"
  alarm_actions       = var.alarm_actions

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }
}

resource "aws_cloudwatch_metric_alarm" "free_storage_low" {
  alarm_name          = "${var.project_name}-db-storage-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "1000000000" # 1GB
  alarm_description   = "Database free storage space is low"
  alarm_actions       = var.alarm_actions

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }
}

resource "aws_cloudwatch_metric_alarm" "connections_high" {
  alarm_name          = "${var.project_name}-db-connections-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "Database connection count is high"
  alarm_actions       = var.alarm_actions

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }
}
