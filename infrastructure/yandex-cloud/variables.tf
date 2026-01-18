# Yandex Cloud Variables

# ============================================
# YC Provider Configuration
# ============================================
variable "yc_token" {
  description = "Yandex Cloud OAuth token or IAM token"
  type        = string
  sensitive   = true
}

variable "yc_cloud_id" {
  description = "Yandex Cloud ID"
  type        = string
}

variable "yc_folder_id" {
  description = "Yandex Cloud Folder ID"
  type        = string
}

variable "yc_zone" {
  description = "Yandex Cloud availability zone"
  type        = string
  default     = "ru-central1-a"
}

# ============================================
# Project Configuration
# ============================================
variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "mlservice"
}

variable "environment" {
  description = "Environment (dev, staging, production)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }
}

# ============================================
# Database Configuration
# ============================================
variable "db_username" {
  description = "PostgreSQL username"
  type        = string
  default     = "mlflow"
}

variable "db_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
}

variable "db_resource_preset" {
  description = "PostgreSQL resource preset (s2.micro, s2.small, etc.)"
  type        = string
  default     = "s2.micro"
}

variable "db_disk_size" {
  description = "PostgreSQL disk size in GB"
  type        = number
  default     = 10
}

# ============================================
# Serverless Container Configuration
# ============================================
variable "api_memory_mb" {
  description = "API container memory in MB"
  type        = number
  default     = 512
}

variable "api_cores" {
  description = "API container CPU cores"
  type        = number
  default     = 1
}

variable "mlflow_memory_mb" {
  description = "MLflow container memory in MB"
  type        = number
  default     = 1024
}

variable "mlflow_cores" {
  description = "MLflow container CPU cores"
  type        = number
  default     = 1
}

# ============================================
# Storage Configuration
# ============================================
variable "artifact_retention_days" {
  description = "Number of days to retain MLflow artifacts"
  type        = number
  default     = 90
}
