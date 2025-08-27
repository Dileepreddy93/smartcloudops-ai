# SmartCloudOps AI - Auto Scaling Configuration
# ============================================

# Application Load Balancer Target Group
resource "aws_lb_target_group" "smartcloudops" {
  name        = "smartcloudops-tg"
  port        = 5000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 3
  }

  tags = {
    Name = "SmartCloudOps-TargetGroup"
    Environment = var.environment
  }
}

# Application Load Balancer
resource "aws_lb" "smartcloudops" {
  name               = "smartcloudops-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = var.environment == "production"

  access_logs {
    bucket  = aws_s3_bucket.logs.bucket
    prefix  = "alb-logs"
    enabled = true
  }

  tags = {
    Name = "SmartCloudOps-ALB"
    Environment = var.environment
  }
}

# ALB Listener
resource "aws_lb_listener" "smartcloudops" {
  load_balancer_arn = aws_lb.smartcloudops.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.smartcloudops.arn
  }
}

# HTTPS Listener (if SSL certificate is available)
resource "aws_lb_listener" "smartcloudops_https" {
  count             = var.enable_ssl ? 1 : 0
  load_balancer_arn = aws_lb.smartcloudops.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = var.ssl_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.smartcloudops.arn
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "smartcloudops" {
  name = "smartcloudops-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "SmartCloudOps-ECS-Cluster"
    Environment = var.environment
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "smartcloudops" {
  family                   = "smartcloudops"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "smartcloudops-app"
      image = "${var.ecr_repository_url}:latest"

      portMappings = [
        {
          containerPort = 5000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "FLASK_ENV"
          value = var.environment
        },
        {
          name  = "DATABASE_URL"
          value = var.database_url
        },
        {
          name  = "REDIS_URL"
          value = var.redis_url
        }
      ]

      secrets = [
        {
          name      = "JWT_SECRET_KEY"
          valueFrom = aws_secretsmanager_secret.jwt_secret.arn
        },
        {
          name      = "ADMIN_API_KEY"
          valueFrom = aws_secretsmanager_secret.admin_api_key.arn
        },
        {
          name      = "ML_API_KEY"
          valueFrom = aws_secretsmanager_secret.ml_api_key.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.smartcloudops.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:5000/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = {
    Name = "SmartCloudOps-TaskDefinition"
    Environment = var.environment
  }
}

# ECS Service
resource "aws_ecs_service" "smartcloudops" {
  name            = "smartcloudops-service"
  cluster         = aws_ecs_cluster.smartcloudops.id
  task_definition = aws_ecs_task_definition.smartcloudops.arn
  desired_count   = var.service_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.smartcloudops.arn
    container_name   = "smartcloudops-app"
    container_port   = 5000
  }

  depends_on = [aws_lb_listener.smartcloudops]

  # Enable service discovery
  service_registries {
    registry_arn = aws_service_discovery_service.smartcloudops.arn
  }

  tags = {
    Name = "SmartCloudOps-ECS-Service"
    Environment = var.environment
  }
}

# Auto Scaling Target
resource "aws_appautoscaling_target" "smartcloudops" {
  max_capacity       = var.max_capacity
  min_capacity       = var.min_capacity
  resource_id        = "service/${aws_ecs_cluster.smartcloudops.name}/${aws_ecs_service.smartcloudops.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# CPU-based Auto Scaling Policy
resource "aws_appautoscaling_policy" "smartcloudops_cpu" {
  name               = "smartcloudops-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.smartcloudops.resource_id
  scalable_dimension = aws_appautoscaling_target.smartcloudops.scalable_dimension
  service_namespace  = aws_appautoscaling_target.smartcloudops.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = var.cpu_target_value
    scale_in_cooldown  = var.scale_in_cooldown
    scale_out_cooldown = var.scale_out_cooldown
  }
}

# Memory-based Auto Scaling Policy
resource "aws_appautoscaling_policy" "smartcloudops_memory" {
  name               = "smartcloudops-memory-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.smartcloudops.resource_id
  scalable_dimension = aws_appautoscaling_target.smartcloudops.scalable_dimension
  service_namespace  = aws_appautoscaling_target.smartcloudops.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value       = var.memory_target_value
    scale_in_cooldown  = var.scale_in_cooldown
    scale_out_cooldown = var.scale_out_cooldown
  }
}

# Custom Metric-based Auto Scaling Policy (Request Count)
resource "aws_appautoscaling_policy" "smartcloudops_requests" {
  name               = "smartcloudops-requests-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.smartcloudops.resource_id
  scalable_dimension = aws_appautoscaling_target.smartcloudops.scalable_dimension
  service_namespace  = aws_appautoscaling_target.smartcloudops.service_namespace

  target_tracking_scaling_policy_configuration {
    customized_metric_specification {
      metric_name = "RequestCount"
      namespace   = "AWS/ApplicationELB"
      statistic   = "Sum"
      unit        = "Count"

      dimensions {
        name  = "TargetGroup"
        value = aws_lb_target_group.smartcloudops.arn_suffix
      }

      dimensions {
        name  = "LoadBalancer"
        value = aws_lb.smartcloudops.arn_suffix
      }
    }
    target_value       = var.requests_per_target
    scale_in_cooldown  = var.scale_in_cooldown
    scale_out_cooldown = var.scale_out_cooldown
  }
}

# Scheduled Scaling (for predictable traffic patterns)
resource "aws_appautoscaling_scheduled_action" "smartcloudops_scale_up" {
  count              = var.enable_scheduled_scaling ? 1 : 0
  name               = "smartcloudops-scale-up"
  service_namespace  = aws_appautoscaling_target.smartcloudops.service_namespace
  resource_id        = aws_appautoscaling_target.smartcloudops.resource_id
  scalable_dimension = aws_appautoscaling_target.smartcloudops.scalable_dimension

  scalable_target_action {
    min_capacity = var.scheduled_scale_up_min
    max_capacity = var.scheduled_scale_up_max
  }

  schedule = "cron(0 8 * * ? *)" # 8 AM UTC daily
}

resource "aws_appautoscaling_scheduled_action" "smartcloudops_scale_down" {
  count              = var.enable_scheduled_scaling ? 1 : 0
  name               = "smartcloudops-scale-down"
  service_namespace  = aws_appautoscaling_target.smartcloudops.service_namespace
  resource_id        = aws_appautoscaling_target.smartcloudops.resource_id
  scalable_dimension = aws_appautoscaling_target.smartcloudops.scalable_dimension

  scalable_target_action {
    min_capacity = var.scheduled_scale_down_min
    max_capacity = var.scheduled_scale_down_max
  }

  schedule = "cron(0 22 * * ? *)" # 10 PM UTC daily
}

# CloudWatch Alarms for Auto Scaling
resource "aws_cloudwatch_metric_alarm" "smartcloudops_high_cpu" {
  alarm_name          = "smartcloudops-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors ECS CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ClusterName = aws_ecs_cluster.smartcloudops.name
    ServiceName = aws_ecs_service.smartcloudops.name
  }
}

resource "aws_cloudwatch_metric_alarm" "smartcloudops_high_memory" {
  alarm_name          = "smartcloudops-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "85"
  alarm_description   = "This metric monitors ECS memory utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ClusterName = aws_ecs_cluster.smartcloudops.name
    ServiceName = aws_ecs_service.smartcloudops.name
  }
}

resource "aws_cloudwatch_metric_alarm" "smartcloudops_high_response_time" {
  alarm_name          = "smartcloudops-high-response-time"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Average"
  threshold           = "2"
  alarm_description   = "This metric monitors ALB target response time"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    TargetGroup  = aws_lb_target_group.smartcloudops.arn_suffix
    LoadBalancer = aws_lb.smartcloudops.arn_suffix
  }
}

# Service Discovery
resource "aws_service_discovery_private_dns_namespace" "smartcloudops" {
  name        = "smartcloudops.local"
  description = "SmartCloudOps service discovery namespace"
  vpc         = aws_vpc.main.id
}

resource "aws_service_discovery_service" "smartcloudops" {
  name = "smartcloudops"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.smartcloudops.id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  health_check_custom_config {
    failure_threshold = 1
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "smartcloudops" {
  name              = "/ecs/smartcloudops"
  retention_in_days = 30

  tags = {
    Name = "SmartCloudOps-LogGroup"
    Environment = var.environment
  }
}

# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  name = "smartcloudops-alerts"

  tags = {
    Name = "SmartCloudOps-Alerts"
    Environment = var.environment
  }
}

# SNS Topic Subscription (email)
resource "aws_sns_topic_subscription" "alerts_email" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# SNS Topic Subscription (Slack webhook)
resource "aws_sns_topic_subscription" "alerts_slack" {
  count     = var.slack_webhook_url != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "https"
  endpoint  = var.slack_webhook_url
}

# IAM Role for ECS Execution
resource "aws_iam_role" "ecs_execution_role" {
  name = "smartcloudops-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# IAM Role for ECS Tasks
resource "aws_iam_role" "ecs_task_role" {
  name = "smartcloudops-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for ECS Tasks
resource "aws_iam_role_policy" "ecs_task_policy" {
  name = "smartcloudops-ecs-task-policy"
  role = aws_iam_role.ecs_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "kms:Decrypt"
        ]
        Resource = [
          aws_secretsmanager_secret.jwt_secret.arn,
          aws_secretsmanager_secret.admin_api_key.arn,
          aws_secretsmanager_secret.ml_api_key.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          "${aws_s3_bucket.ml_models.arn}/*",
          "${aws_s3_bucket.backups.arn}/*"
        ]
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

# Secrets Manager Secrets
resource "aws_secretsmanager_secret" "jwt_secret" {
  name        = "smartcloudops/jwt-secret"
  description = "JWT secret key for SmartCloudOps"
}

resource "aws_secretsmanager_secret" "admin_api_key" {
  name        = "smartcloudops/admin-api-key"
  description = "Admin API key for SmartCloudOps"
}

resource "aws_secretsmanager_secret" "ml_api_key" {
  name        = "smartcloudops/ml-api-key"
  description = "ML API key for SmartCloudOps"
}

# S3 Bucket for ML Models
resource "aws_s3_bucket" "ml_models" {
  bucket = "smartcloudops-ml-models-${random_string.bucket_suffix.result}"

  tags = {
    Name = "SmartCloudOps-ML-Models"
    Environment = var.environment
  }
}

# S3 Bucket for Backups
resource "aws_s3_bucket" "backups" {
  bucket = "smartcloudops-backups-${random_string.bucket_suffix.result}"

  tags = {
    Name = "SmartCloudOps-Backups"
    Environment = var.environment
  }
}

# S3 Bucket for Logs
resource "aws_s3_bucket" "logs" {
  bucket = "smartcloudops-logs-${random_string.bucket_suffix.result}"

  tags = {
    Name = "SmartCloudOps-Logs"
    Environment = var.environment
  }
}

# Random string for bucket names
resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# Outputs
output "alb_dns_name" {
  description = "The DNS name of the load balancer"
  value       = aws_lb.smartcloudops.dns_name
}

output "ecs_cluster_name" {
  description = "The name of the ECS cluster"
  value       = aws_ecs_cluster.smartcloudops.name
}

output "ecs_service_name" {
  description = "The name of the ECS service"
  value       = aws_ecs_service.smartcloudops.name
}

output "target_group_arn" {
  description = "The ARN of the target group"
  value       = aws_lb_target_group.smartcloudops.arn
}

output "sns_topic_arn" {
  description = "The ARN of the SNS topic for alerts"
  value       = aws_sns_topic.alerts.arn
}
