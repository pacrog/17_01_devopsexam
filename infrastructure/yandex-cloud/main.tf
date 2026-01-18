# Yandex Cloud Serverless Containers Configuration
# ML Prediction Service Deployment
#
# Resources:
# - Serverless Container for API
# - Serverless Container for MLflow
# - Managed PostgreSQL
# - Object Storage (S3-compatible)
# - Container Registry

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.100"
    }
  }
}

# Provider configuration
provider "yandex" {
  token     = var.yc_token
  cloud_id  = var.yc_cloud_id
  folder_id = var.yc_folder_id
  zone      = var.yc_zone
}

# Local values
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  labels = {
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
  }
}

# ============================================
# Service Account for Serverless Containers
# ============================================
resource "yandex_iam_service_account" "serverless_sa" {
  name        = "${local.name_prefix}-serverless-sa"
  description = "Service account for serverless containers"
}

# Roles for service account
resource "yandex_resourcemanager_folder_iam_member" "sa_invoker" {
  folder_id = var.yc_folder_id
  role      = "serverless-containers.containerInvoker"
  member    = "serviceAccount:${yandex_iam_service_account.serverless_sa.id}"
}

resource "yandex_resourcemanager_folder_iam_member" "sa_puller" {
  folder_id = var.yc_folder_id
  role      = "container-registry.images.puller"
  member    = "serviceAccount:${yandex_iam_service_account.serverless_sa.id}"
}

resource "yandex_resourcemanager_folder_iam_member" "sa_storage" {
  folder_id = var.yc_folder_id
  role      = "storage.editor"
  member    = "serviceAccount:${yandex_iam_service_account.serverless_sa.id}"
}

# ============================================
# Container Registry
# ============================================
resource "yandex_container_registry" "registry" {
  name      = "${local.name_prefix}-registry"
  folder_id = var.yc_folder_id
  labels    = local.labels
}

# ============================================
# Object Storage (S3-compatible) for MLflow
# ============================================
resource "yandex_storage_bucket" "mlflow_artifacts" {
  bucket     = "${local.name_prefix}-mlflow-artifacts"
  access_key = yandex_iam_service_account_static_access_key.sa_static_key.access_key
  secret_key = yandex_iam_service_account_static_access_key.sa_static_key.secret_key

  anonymous_access_flags {
    read        = false
    list        = false
    config_read = false
  }

  versioning {
    enabled = var.environment == "production"
  }

  lifecycle_rule {
    id      = "cleanup-old-artifacts"
    enabled = true
    prefix  = "artifacts/"

    expiration {
      days = var.artifact_retention_days
    }
  }
}

# Static access key for S3
resource "yandex_iam_service_account_static_access_key" "sa_static_key" {
  service_account_id = yandex_iam_service_account.serverless_sa.id
  description        = "Static access key for Object Storage"
}

# ============================================
# Managed PostgreSQL for MLflow
# ============================================
resource "yandex_mdb_postgresql_cluster" "mlflow_db" {
  name        = "${local.name_prefix}-mlflow-db"
  environment = var.environment == "production" ? "PRODUCTION" : "PRESTABLE"
  network_id  = yandex_vpc_network.network.id
  folder_id   = var.yc_folder_id

  config {
    version = "15"
    resources {
      resource_preset_id = var.db_resource_preset
      disk_type_id       = "network-ssd"
      disk_size          = var.db_disk_size
    }

    postgresql_config = {
      max_connections = 100
    }
  }

  host {
    zone             = var.yc_zone
    subnet_id        = yandex_vpc_subnet.subnet.id
    assign_public_ip = true
  }

  labels = local.labels
}

resource "yandex_mdb_postgresql_database" "mlflow" {
  cluster_id = yandex_mdb_postgresql_cluster.mlflow_db.id
  name       = "mlflow"
  owner      = yandex_mdb_postgresql_user.mlflow_user.name
}

resource "yandex_mdb_postgresql_user" "mlflow_user" {
  cluster_id = yandex_mdb_postgresql_cluster.mlflow_db.id
  name       = var.db_username
  password   = var.db_password
}

# ============================================
# VPC Network
# ============================================
resource "yandex_vpc_network" "network" {
  name      = "${local.name_prefix}-network"
  folder_id = var.yc_folder_id
  labels    = local.labels
}

resource "yandex_vpc_subnet" "subnet" {
  name           = "${local.name_prefix}-subnet"
  zone           = var.yc_zone
  network_id     = yandex_vpc_network.network.id
  v4_cidr_blocks = ["10.0.0.0/24"]
  folder_id      = var.yc_folder_id
  labels         = local.labels
}

# ============================================
# Serverless Container - API
# ============================================
resource "yandex_serverless_container" "api" {
  name               = "${local.name_prefix}-api"
  folder_id          = var.yc_folder_id
  memory             = var.api_memory_mb
  execution_timeout  = "30s"
  cores              = var.api_cores
  core_fraction      = 100
  service_account_id = yandex_iam_service_account.serverless_sa.id

  image {
    url = "${yandex_container_registry.registry.id}/api:latest"
  }

  secrets {
    id                   = yandex_lockbox_secret.db_credentials.id
    version_id           = yandex_lockbox_secret_version.db_credentials_v1.id
    key                  = "password"
    environment_variable = "DB_PASSWORD"
  }

  connectivity {
    network_id = yandex_vpc_network.network.id
  }
}

# ============================================
# Serverless Container - MLflow
# ============================================
resource "yandex_serverless_container" "mlflow" {
  name               = "${local.name_prefix}-mlflow"
  folder_id          = var.yc_folder_id
  memory             = var.mlflow_memory_mb
  execution_timeout  = "60s"
  cores              = var.mlflow_cores
  core_fraction      = 100
  service_account_id = yandex_iam_service_account.serverless_sa.id

  image {
    url = "${yandex_container_registry.registry.id}/mlflow:latest"
    environment = {
      MLFLOW_BACKEND_STORE_URI    = "postgresql://${var.db_username}:${var.db_password}@${yandex_mdb_postgresql_cluster.mlflow_db.host[0].fqdn}:6432/mlflow"
      MLFLOW_DEFAULT_ARTIFACT_ROOT = "s3://${yandex_storage_bucket.mlflow_artifacts.bucket}/artifacts"
      AWS_ACCESS_KEY_ID           = yandex_iam_service_account_static_access_key.sa_static_key.access_key
      AWS_SECRET_ACCESS_KEY       = yandex_iam_service_account_static_access_key.sa_static_key.secret_key
      MLFLOW_S3_ENDPOINT_URL      = "https://storage.yandexcloud.net"
    }
  }

  connectivity {
    network_id = yandex_vpc_network.network.id
  }
}

# ============================================
# Lockbox Secret for DB credentials
# ============================================
resource "yandex_lockbox_secret" "db_credentials" {
  name      = "${local.name_prefix}-db-credentials"
  folder_id = var.yc_folder_id
  labels    = local.labels
}

resource "yandex_lockbox_secret_version" "db_credentials_v1" {
  secret_id = yandex_lockbox_secret.db_credentials.id
  entries {
    key        = "password"
    text_value = var.db_password
  }
  entries {
    key        = "username"
    text_value = var.db_username
  }
}

# ============================================
# API Gateway for public access
# ============================================
resource "yandex_api_gateway" "gateway" {
  name      = "${local.name_prefix}-gateway"
  folder_id = var.yc_folder_id
  labels    = local.labels

  spec = <<-EOT
openapi: 3.0.0
info:
  title: ML API Gateway
  version: 1.0.0

paths:
  /api/{path+}:
    x-yc-apigateway-any-method:
      x-yc-apigateway-integration:
        type: serverless_containers
        container_id: ${yandex_serverless_container.api.id}
        service_account_id: ${yandex_iam_service_account.serverless_sa.id}
      parameters:
        - name: path
          in: path
          required: true
          schema:
            type: string

  /mlflow/{path+}:
    x-yc-apigateway-any-method:
      x-yc-apigateway-integration:
        type: serverless_containers
        container_id: ${yandex_serverless_container.mlflow.id}
        service_account_id: ${yandex_iam_service_account.serverless_sa.id}
      parameters:
        - name: path
          in: path
          required: true
          schema:
            type: string
EOT
}
