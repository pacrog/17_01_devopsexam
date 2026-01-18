#!/bin/bash
# Run Locust load testing script

set -e

# Change to project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Default parameters
USERS=${1:-10}
SPAWN_RATE=${2:-1}
RUN_TIME=${3:-60s}
HOST=${4:-http://localhost:8001}

echo "==================================="
echo "Running Load Test with Locust"
echo "==================================="
echo "Users: $USERS"
echo "Spawn rate: $SPAWN_RATE per second"
echo "Run time: $RUN_TIME"
echo "Target host: $HOST"
echo "==================================="

# Check if service is running
echo "Checking if API is available..."
if ! curl -s "$HOST/healthcheck" > /dev/null 2>&1; then
    echo "Error: API is not available at $HOST"
    echo "Please start the services first: ./scripts/start.sh"
    exit 1
fi
echo "API is healthy!"

# Create reports directory
mkdir -p reports

# Generate timestamp for report filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="reports/loadtest_report_${TIMESTAMP}.html"

echo ""
echo "Running headless load test..."
echo ""

# Run Locust
docker-compose run --rm \
    -v "$(pwd)/reports:/mnt/reports" \
    locust \
    -f /mnt/locust/locustfile.py \
    --host "$HOST" \
    --users "$USERS" \
    --spawn-rate "$SPAWN_RATE" \
    --run-time "$RUN_TIME" \
    --headless \
    --html "/mnt/reports/loadtest_report_${TIMESTAMP}.html" \
    --csv "/mnt/reports/loadtest_${TIMESTAMP}"

echo ""
echo "==================================="
echo "Load Test Complete!"
echo "==================================="
echo "HTML Report: $REPORT_FILE"
echo "CSV Reports: reports/loadtest_${TIMESTAMP}_*.csv"
echo "==================================="
