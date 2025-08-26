# SmartCloudOps AI - Database Module Outputs
# ==========================================

output "db_instance_id" {
  description = "The RDS instance ID"
  value       = aws_db_instance.main.id
}

output "db_endpoint" {
  description = "The connection endpoint for the RDS instance"
  value       = aws_db_instance.main.endpoint
}

output "db_port" {
  description = "The database port"
  value       = aws_db_instance.main.port
}

output "db_name" {
  description = "The name of the database"
  value       = aws_db_instance.main.db_name
}

output "db_username" {
  description = "The master username for the database"
  value       = aws_db_instance.main.username
  sensitive   = true
}

output "db_connection_string" {
  description = "The database connection string (without password)"
  value       = "postgresql://${aws_db_instance.main.username}@${aws_db_instance.main.endpoint}:${aws_db_instance.main.port}/${aws_db_instance.main.db_name}"
  sensitive   = false
}

output "db_security_group_id" {
  description = "The security group ID for the database"
  value       = aws_security_group.database.id
}

output "db_subnet_group_name" {
  description = "The name of the database subnet group"
  value       = aws_db_subnet_group.main.name
}

output "db_parameter_group_name" {
  description = "The name of the database parameter group"
  value       = aws_db_parameter_group.main.name
}

output "db_option_group_name" {
  description = "The name of the database option group"
  value       = aws_db_option_group.main.name
}

output "db_arn" {
  description = "The ARN of the RDS instance"
  value       = aws_db_instance.main.arn
}

output "db_resource_id" {
  description = "The RDS Resource ID of the instance"
  value       = aws_db_instance.main.resource_id
}
