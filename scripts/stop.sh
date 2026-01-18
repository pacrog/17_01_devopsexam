#!/bin/bash
# Stop all services script

set -e

# Change to project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "==================================="
echo "Stopping ML Prediction Service"
echo "==================================="

# Stop all services
docker-compose --profile testing down

echo "All services stopped."
echo ""
echo "To remove volumes (data will be lost):"
echo "  docker-compose down -v"
