"""
Locust Load Testing for ML Prediction Service.

Declarative test scenarios for:
- Health check endpoints
- Prediction endpoints
- Batch prediction endpoints
- Data drift analysis

Usage:
    locust -f locustfile.py --host http://localhost:8000
    locust -f locustfile.py --host http://localhost:8000 --users 10 --spawn-rate 1 --run-time 60s
"""
import random
from locust import HttpUser, task, between, tag


class LoadTestingUser(HttpUser):
    """
    Simulates user behavior for load testing the ML service.

    Endpoints tested:
    - GET /healthcheck - Basic health probe
    - GET /readiness - Readiness check
    - POST /predict - Single prediction
    - POST /predict/batch - Batch predictions
    - POST /data/drift - Drift analysis
    """

    # Wait between 1-3 seconds between tasks
    wait_time = between(1, 3)

    # Sample Iris data for predictions
    SAMPLE_DATA = [
        {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2},  # setosa
        {"sepal_length": 7.0, "sepal_width": 3.2, "petal_length": 4.7, "petal_width": 1.4},  # versicolor
        {"sepal_length": 6.3, "sepal_width": 3.3, "petal_length": 6.0, "petal_width": 2.5},  # virginica
        {"sepal_length": 5.0, "sepal_width": 3.4, "petal_length": 1.5, "petal_width": 0.2},  # setosa
        {"sepal_length": 6.4, "sepal_width": 2.9, "petal_length": 4.3, "petal_width": 1.3},  # versicolor
        {"sepal_length": 6.7, "sepal_width": 3.0, "petal_length": 5.2, "petal_width": 2.3},  # virginica
        {"sepal_length": 4.9, "sepal_width": 3.1, "petal_length": 1.5, "petal_width": 0.1},  # setosa
        {"sepal_length": 5.7, "sepal_width": 2.8, "petal_length": 4.1, "petal_width": 1.3},  # versicolor
    ]

    def on_start(self):
        """Called when a user starts - verify service is ready."""
        response = self.client.get("/healthcheck")
        if response.status_code != 200:
            raise Exception("Service not healthy on start")

    @tag("health")
    @task(3)
    def healthcheck(self):
        """
        Test health check endpoint.
        Higher weight (3) - frequently called in production.
        """
        self.client.get("/healthcheck")

    @tag("health")
    @task(1)
    def readiness(self):
        """Test readiness probe endpoint."""
        self.client.get("/readiness")

    @tag("prediction")
    @task(5)
    def predict_single(self):
        """
        Test single prediction endpoint.
        Highest weight (5) - main use case.
        """
        sample = random.choice(self.SAMPLE_DATA)
        self.client.post(
            "/predict",
            json={"features": sample},
            headers={"Content-Type": "application/json"}
        )

    @tag("prediction")
    @task(2)
    def predict_batch(self):
        """
        Test batch prediction endpoint.
        Moderate weight (2) - used for bulk processing.
        """
        # Random batch size between 3 and 8
        batch_size = random.randint(3, 8)
        samples = random.choices(self.SAMPLE_DATA, k=batch_size)
        self.client.post(
            "/predict/batch",
            json={"samples": samples},
            headers={"Content-Type": "application/json"}
        )

    @tag("drift")
    @task(1)
    def check_drift(self):
        """
        Test drift analysis endpoint.
        Lower weight (1) - typically called less frequently.
        """
        # Generate slightly varied data for drift testing
        current_data = []
        for _ in range(20):
            sample = dict(random.choice(self.SAMPLE_DATA))
            # Add small random variations
            for key in sample:
                sample[key] += random.uniform(-0.2, 0.2)
            current_data.append(sample)

        self.client.post(
            "/data/drift",
            json={"current_data": current_data},
            headers={"Content-Type": "application/json"}
        )

    @tag("mlflow")
    @task(1)
    def list_experiments(self):
        """Test MLflow experiments listing."""
        self.client.get("/mlflow/experiments")


class HealthCheckUser(HttpUser):
    """
    Lightweight user for monitoring - only health checks.
    Useful for separate health monitoring scenarios.
    """

    wait_time = between(5, 10)

    @task
    def healthcheck(self):
        """Periodic health check."""
        self.client.get("/healthcheck")


class HeavyLoadUser(HttpUser):
    """
    Heavy load user - simulates intensive prediction workloads.
    Use with --tags heavy for stress testing.
    """

    wait_time = between(0.1, 0.5)

    SAMPLE_DATA = [
        {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2},
        {"sepal_length": 7.0, "sepal_width": 3.2, "petal_length": 4.7, "petal_width": 1.4},
        {"sepal_length": 6.3, "sepal_width": 3.3, "petal_length": 6.0, "petal_width": 2.5},
    ]

    @tag("heavy")
    @task(10)
    def rapid_predictions(self):
        """Rapid-fire predictions for stress testing."""
        sample = random.choice(self.SAMPLE_DATA)
        self.client.post(
            "/predict",
            json={"features": sample},
            headers={"Content-Type": "application/json"}
        )

    @tag("heavy")
    @task(3)
    def large_batch_predictions(self):
        """Large batch predictions for stress testing."""
        samples = random.choices(self.SAMPLE_DATA, k=50)
        self.client.post(
            "/predict/batch",
            json={"samples": samples},
            headers={"Content-Type": "application/json"}
        )
