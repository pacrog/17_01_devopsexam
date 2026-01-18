# Terraform Outputs for ML Prediction Service Infrastructure

# ============================================
# S3 Bucket Outputs
# ============================================
output "s3_bucket_name" {
  description = "Name of the S3 bucket for MLflow artifacts"
  value       = module.s3_bucket.bucket_name
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = module.s3_bucket.bucket_arn
}

output "s3_bucket_domain_name" {
  description = "Domain name of the S3 bucket"
  value       = module.s3_bucket.bucket_domain_name
}

# ============================================
# Database Outputs
# ============================================
output "database_endpoint" {
  description = "Database connection endpoint"
  value       = module.database.endpoint
}

output "database_port" {
  description = "Database port"
  value       = module.database.port
}

output "database_name" {
  description = "Database name"
  value       = module.database.database_name
}

# ============================================
# IAM Outputs
# ============================================
output "mlflow_role_arn" {
  description = "ARN of the MLflow IAM role"
  value       = aws_iam_role.mlflow_role.arn
}

output "mlflow_instance_profile_name" {
  description = "Name of the MLflow instance profile"
  value       = aws_iam_instance_profile.mlflow_profile.name
}

# ============================================
# Security Group Outputs
# ============================================
output "security_group_id" {
  description = "ID of the MLflow security group"
  value       = var.create_security_group ? aws_security_group.mlflow_sg[0].id : null
}

# ============================================
# SSM Parameter Outputs
# ============================================
output "db_password_ssm_parameter" {
  description = "SSM parameter name for database password"
  value       = aws_ssm_parameter.db_password.name
}

output "s3_bucket_ssm_parameter" {
  description = "SSM parameter name for S3 bucket"
  value       = aws_ssm_parameter.s3_bucket_name.name
}

# ============================================
# CloudWatch Outputs
# ============================================
output "cloudwatch_log_group_name" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.mlflow_logs.name
}

# ============================================
# Connection Strings (for application config)
# ============================================
output "mlflow_backend_store_uri" {
  description = "MLflow backend store URI for PostgreSQL"
  value       = "postgresql://${var.db_username}:****@${module.database.endpoint}/${module.database.database_name}"
  sensitive   = true
}

output "mlflow_artifact_root" {
  description = "MLflow artifact root URI for S3"
  value       = "s3://${module.s3_bucket.bucket_name}/artifacts"
}
