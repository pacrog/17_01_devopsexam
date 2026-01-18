# Yandex Cloud Outputs

output "api_container_url" {
  description = "API Serverless Container URL"
  value       = yandex_serverless_container.api.url
}

output "mlflow_container_url" {
  description = "MLflow Serverless Container URL"
  value       = yandex_serverless_container.mlflow.url
}

output "api_gateway_url" {
  description = "API Gateway public URL"
  value       = "https://${yandex_api_gateway.gateway.domain}"
}

output "container_registry_id" {
  description = "Container Registry ID"
  value       = yandex_container_registry.registry.id
}

output "s3_bucket_name" {
  description = "S3 bucket name for MLflow artifacts"
  value       = yandex_storage_bucket.mlflow_artifacts.bucket
}

output "postgres_host" {
  description = "PostgreSQL host FQDN"
  value       = yandex_mdb_postgresql_cluster.mlflow_db.host[0].fqdn
}

output "s3_access_key" {
  description = "S3 access key ID"
  value       = yandex_iam_service_account_static_access_key.sa_static_key.access_key
  sensitive   = true
}

output "s3_secret_key" {
  description = "S3 secret access key"
  value       = yandex_iam_service_account_static_access_key.sa_static_key.secret_key
  sensitive   = true
}
