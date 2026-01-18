# PostgreSQL Database Module for MLflow
# Creates an RDS PostgreSQL instance with proper configuration

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# DB Subnet Group
resource "aws_db_subnet_group" "this" {
  count = length(var.subnet_ids) > 0 ? 1 : 0

  name       = "${var.identifier}-subnet-group"
  subnet_ids = var.subnet_ids

  tags = merge(var.tags, {
    Name = "${var.identifier}-subnet-group"
  })
}

# Security Group for RDS
resource "aws_security_group" "this" {
  count = var.create_security_group ? 1 : 0

  name        = "${var.identifier}-sg"
  description = "Security group for ${var.identifier} RDS instance"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = var.security_group_ids
    description     = "PostgreSQL access"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound"
  }

  tags = merge(var.tags, {
    Name = "${var.identifier}-sg"
  })
}

# Parameter Group
resource "aws_db_parameter_group" "this" {
  name   = "${var.identifier}-params"
  family = "postgres15"

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
    value = "ddl"
  }

  tags = var.tags
}

# RDS PostgreSQL Instance
resource "aws_db_instance" "this" {
  identifier = var.identifier

  engine         = var.engine
  engine_version = var.engine_version
  instance_class = var.instance_class

  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type          = var.storage_type
  storage_encrypted     = var.storage_encrypted

  db_name  = var.database_name
  username = var.username
  password = var.password

  db_subnet_group_name   = length(var.subnet_ids) > 0 ? aws_db_subnet_group.this[0].name : null
  vpc_security_group_ids = var.create_security_group ? [aws_security_group.this[0].id] : var.security_group_ids
  parameter_group_name   = aws_db_parameter_group.this.name
  publicly_accessible    = var.publicly_accessible

  multi_az               = var.multi_az
  backup_retention_period = var.backup_retention_period
  backup_window          = var.backup_window
  maintenance_window     = var.maintenance_window

  skip_final_snapshot       = var.skip_final_snapshot
  final_snapshot_identifier = var.skip_final_snapshot ? null : "${var.identifier}-final-snapshot"
  deletion_protection       = var.deletion_protection

  performance_insights_enabled = var.performance_insights_enabled

  tags = merge(var.tags, {
    Name = var.identifier
  })
}
