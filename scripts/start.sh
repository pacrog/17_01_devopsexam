#!/bin/bash
# Start all services script

set -e

# Change to project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "==================================="
echo "Starting ML Prediction Service"
echo "==================================="
echo "Working directory: $PROJECT_DIR"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Copy .env if not exists
if [ ! -f .env ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
fi

# Start services
echo "Starting services with docker-compose..."
docker-compose up -d

# Wait for services to be healthy
echo "Waiting for services to be ready..."
sleep 10

# Health check
echo "Checking API health..."
for i in {1..30}; do
    if curl -s http://localhost:8001/healthcheck > /dev/null 2>&1; then
        echo "API is healthy!"
        break
    fi
    echo "Waiting for API... ($i/30)"
    sleep 2
done

# Display status
echo ""
echo "==================================="
echo "Services Status:"
echo "==================================="
docker-compose ps

echo ""
echo "==================================="
echo "Access URLs:"
echo "==================================="
echo "API Swagger UI:  http://localhost:8001/docs"
echo "API ReDoc:       http://localhost:8001/redoc"
echo "MLflow UI:       http://localhost:5000"
echo "MinIO Console:   http://localhost:9001 (minioadmin/minioadmin)"
echo ""
echo "To start Locust for load testing:"
echo "  docker-compose --profile testing up -d locust"
echo "  Then open: http://localhost:8089"
echo "==================================="
