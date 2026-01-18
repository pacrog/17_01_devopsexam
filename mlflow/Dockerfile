# MLflow Server with PostgreSQL and S3 support
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    mlflow>=2.10.0 \
    psycopg2-binary \
    boto3

# Expose MLflow port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=5 \
    CMD curl -f http://localhost:5000/health || exit 1

# Default command
CMD ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000"]
