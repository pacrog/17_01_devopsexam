# Terraform Variables for ML Prediction Service Infrastructure

# ============================================
# General Settings
# ============================================
variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "ml-prediction-service"
}

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  default     = "development"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

# ============================================
# Networking
# ============================================
variable "vpc_id" {
  description = "VPC ID for resources"
  type        = string
  default     = null
}

variable "subnet_ids" {
  description = "List of subnet IDs for database"
  type        = list(string)
  default     = []
}

variable "security_group_ids" {
  description = "List of security group IDs"
  type        = list(string)
  default     = []
}

variable "create_security_group" {
  description = "Whether to create a new security group"
  type        = bool
  default     = true
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access services"
  type        = list(string)
  default     = ["10.0.0.0/8"]
}

# ============================================
# Database Settings
# ============================================
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_storage_gb" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "mlflow"
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

# ============================================
# S3/Storage Settings
# ============================================
variable "artifact_retention_days" {
  description = "Days to retain MLflow artifacts"
  type        = number
  default     = 90
}

# ============================================
# Logging
# ============================================
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

# ============================================
# Tags
# ============================================
variable "additional_tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}
