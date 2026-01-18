# Terraform/OpenTofu Configuration for ML Prediction Service
# Programmatic Infrastructure Creation
#
# Resources:
# - S3 Bucket for MLflow artifacts
# - PostgreSQL Database for MLflow metadata
# - VPC and networking (optional)
#
# Compatible with: Terraform >= 1.0, OpenTofu >= 1.6

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  # Backend configuration for state storage
  # Uncomment for production use
  # backend "s3" {
  #   bucket         = "terraform-state-bucket"
  #   key            = "ml-service/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-locks"
  # }
}

# Provider configuration
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Random suffix for unique resource names
resource "random_id" "suffix" {
  byte_length = 4
}

# Local values
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# ============================================
# S3 Bucket for MLflow Artifacts
# ============================================
module "s3_bucket" {
  source = "./modules/s3"

  bucket_name = "${local.name_prefix}-mlflow-artifacts-${random_id.suffix.hex}"
  environment = var.environment

  enable_versioning = var.environment == "production"
  enable_encryption = true

  lifecycle_rules = [
    {
      id      = "cleanup-old-artifacts"
      enabled = true
      prefix  = "artifacts/"

      expiration = {
        days = var.artifact_retention_days
      }

      noncurrent_version_expiration = {
        days = 30
      }
    }
  ]

  tags = local.common_tags
}

# ============================================
# PostgreSQL Database for MLflow
# ============================================
module "database" {
  source = "./modules/database"

  identifier     = "${local.name_prefix}-mlflow-db"
  engine         = "postgres"
  engine_version = "15.4"

  instance_class    = var.db_instance_class
  allocated_storage = var.db_storage_gb

  database_name = "mlflow"
  username      = var.db_username
  password      = var.db_password

  # Networking
  vpc_id             = var.vpc_id
  subnet_ids         = var.subnet_ids
  security_group_ids = var.security_group_ids

  # Backup configuration
  backup_retention_period = var.environment == "production" ? 7 : 1
  skip_final_snapshot     = var.environment != "production"

  # Performance
  multi_az = var.environment == "production"

  tags = local.common_tags
}

# ============================================
# IAM Role for EC2/ECS to access S3
# ============================================
resource "aws_iam_role" "mlflow_role" {
  name = "${local.name_prefix}-mlflow-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = ["ec2.amazonaws.com", "ecs-tasks.amazonaws.com"]
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "mlflow_s3_policy" {
  name = "${local.name_prefix}-mlflow-s3-policy"
  role = aws_iam_role.mlflow_role.id

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
          module.s3_bucket.bucket_arn,
          "${module.s3_bucket.bucket_arn}/*"
        ]
      }
    ]
  })
}

# Instance profile for EC2
resource "aws_iam_instance_profile" "mlflow_profile" {
  name = "${local.name_prefix}-mlflow-profile"
  role = aws_iam_role.mlflow_role.name
}

# ============================================
# Security Group for MLflow services
# ============================================
resource "aws_security_group" "mlflow_sg" {
  count = var.create_security_group ? 1 : 0

  name        = "${local.name_prefix}-mlflow-sg"
  description = "Security group for MLflow services"
  vpc_id      = var.vpc_id

  # MLflow Tracking Server
  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
    description = "MLflow Tracking Server"
  }

  # API Service
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
    description = "ML API Service"
  }

  # PostgreSQL (internal only)
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    self        = true
    description = "PostgreSQL internal"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound"
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-mlflow-sg"
  })
}

# ============================================
# CloudWatch Log Group
# ============================================
resource "aws_cloudwatch_log_group" "mlflow_logs" {
  name              = "/aws/${local.name_prefix}/mlflow"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

# ============================================
# SSM Parameters for secrets
# ============================================
resource "aws_ssm_parameter" "db_password" {
  name        = "/${local.name_prefix}/database/password"
  description = "MLflow database password"
  type        = "SecureString"
  value       = var.db_password

  tags = local.common_tags
}

resource "aws_ssm_parameter" "s3_bucket_name" {
  name        = "/${local.name_prefix}/mlflow/artifact-bucket"
  description = "MLflow artifact S3 bucket name"
  type        = "String"
  value       = module.s3_bucket.bucket_name

  tags = local.common_tags
}
