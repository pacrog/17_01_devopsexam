# Database Module Outputs

output "endpoint" {
  description = "Database endpoint"
  value       = aws_db_instance.this.endpoint
}

output "address" {
  description = "Database address (hostname)"
  value       = aws_db_instance.this.address
}

output "port" {
  description = "Database port"
  value       = aws_db_instance.this.port
}

output "database_name" {
  description = "Database name"
  value       = aws_db_instance.this.db_name
}

output "identifier" {
  description = "Database identifier"
  value       = aws_db_instance.this.identifier
}

output "arn" {
  description = "Database ARN"
  value       = aws_db_instance.this.arn
}

output "security_group_id" {
  description = "Security group ID"
  value       = var.create_security_group ? aws_security_group.this[0].id : null
}
