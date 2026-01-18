"""
ML Model Manager for loading and inference.
Integrates with MLflow for model versioning and serving.
"""
import os
import time
import logging
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages ML model lifecycle: loading, inference, and MLflow integration."""

    def __init__(
        self,
        mlflow_tracking_uri: str = None,
        model_name: str = "iris_classifier",
        model_stage: str = "Production"
    ):
        self.mlflow_tracking_uri = mlflow_tracking_uri or os.getenv(
            "MLFLOW_TRACKING_URI", "http://mlflow:5000"
        )
        self.model_name = model_name
        self.model_stage = model_stage
        self.model = None
        self.model_version = None
        self.feature_names = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
        self.target_names = ["setosa", "versicolor", "virginica"]
        self._client = None

    @property
    def client(self) -> MlflowClient:
        if self._client is None:
            mlflow.set_tracking_uri(self.mlflow_tracking_uri)
            self._client = MlflowClient()
        return self._client

    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self.model is not None

    def load_model(self) -> bool:
        """
        Load model from MLflow registry.
        Falls back to training a new model if none exists.
        """
        try:
            mlflow.set_tracking_uri(self.mlflow_tracking_uri)
            # Try to load from registry
            model_uri = f"models:/{self.model_name}/{self.model_stage}"
            self.model = mlflow.sklearn.load_model(model_uri)
            # Get version info
            versions = self.client.get_latest_versions(self.model_name, stages=[self.model_stage])
            if versions:
                self.model_version = versions[0].version
            logger.info(f"Loaded model {self.model_name} version {self.model_version}")
            return True
        except Exception as e:
            logger.warning(f"Could not load model from registry: {e}")
            # Train and register a default model
            return self._train_and_register_default_model()

    def _train_and_register_default_model(self) -> bool:
        """Train and register a default Iris classifier."""
        try:
            mlflow.set_tracking_uri(self.mlflow_tracking_uri)

            # Create or get experiment
            experiment_name = "iris_classification"
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if experiment is None:
                experiment_id = mlflow.create_experiment(experiment_name)
            else:
                experiment_id = experiment.experiment_id

            mlflow.set_experiment(experiment_name)

            # Load Iris dataset
            iris = load_iris()
            X = pd.DataFrame(iris.data, columns=self.feature_names)
            y = iris.target

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # Train model with MLflow tracking
            with mlflow.start_run(run_name="default_model") as run:
                # Log parameters
                params = {
                    "n_estimators": 100,
                    "max_depth": 5,
                    "random_state": 42
                }
                mlflow.log_params(params)

                # Train
                model = RandomForestClassifier(**params)
                model.fit(X_train, y_train)

                # Evaluate
                train_score = model.score(X_train, y_train)
                test_score = model.score(X_test, y_test)

                mlflow.log_metrics({
                    "train_accuracy": train_score,
                    "test_accuracy": test_score
                })

                # Log model
                mlflow.sklearn.log_model(
                    model,
                    "model",
                    registered_model_name=self.model_name
                )

                self.model = model
                logger.info(f"Trained default model. Train acc: {train_score:.4f}, Test acc: {test_score:.4f}")

            # Transition to Production
            try:
                versions = self.client.get_latest_versions(self.model_name, stages=["None"])
                if versions:
                    self.client.transition_model_version_stage(
                        name=self.model_name,
                        version=versions[0].version,
                        stage="Production"
                    )
                    self.model_version = versions[0].version
            except Exception as e:
                logger.warning(f"Could not transition model to Production: {e}")
                self.model_version = "1"

            return True
        except Exception as e:
            logger.error(f"Failed to train default model: {e}")
            # Create a simple in-memory model as fallback
            iris = load_iris()
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.model.fit(iris.data, iris.target)
            self.model_version = "local"
            logger.info("Created local fallback model")
            return True

    def predict(self, features: Dict[str, float]) -> Tuple[str, List[float], float]:
        """
        Make a prediction for given features.

        Args:
            features: Dictionary with feature names and values

        Returns:
            Tuple of (predicted_class, probabilities, latency_ms)
        """
        if not self.is_loaded():
            raise RuntimeError("Model not loaded")

        start_time = time.time()

        # Prepare input
        X = np.array([[
            features.get("sepal_length", 0),
            features.get("sepal_width", 0),
            features.get("petal_length", 0),
            features.get("petal_width", 0)
        ]])

        # Predict
        prediction_idx = self.model.predict(X)[0]
        probabilities = self.model.predict_proba(X)[0].tolist()

        latency_ms = (time.time() - start_time) * 1000

        return self.target_names[prediction_idx], probabilities, latency_ms

    def predict_batch(
        self,
        samples: List[Dict[str, float]]
    ) -> List[Tuple[str, List[float], float]]:
        """Make predictions for multiple samples."""
        if not self.is_loaded():
            raise RuntimeError("Model not loaded")

        start_time = time.time()

        # Prepare batch input
        X = np.array([
            [
                s.get("sepal_length", 0),
                s.get("sepal_width", 0),
                s.get("petal_length", 0),
                s.get("petal_width", 0)
            ]
            for s in samples
        ])

        # Batch predict
        predictions = self.model.predict(X)
        probabilities = self.model.predict_proba(X)

        total_latency = (time.time() - start_time) * 1000
        per_sample_latency = total_latency / len(samples)

        return [
            (self.target_names[pred], prob.tolist(), per_sample_latency)
            for pred, prob in zip(predictions, probabilities)
        ]

    def get_experiments(self) -> List[Dict[str, Any]]:
        """Get list of MLflow experiments."""
        try:
            experiments = self.client.search_experiments()
            return [
                {
                    "experiment_id": exp.experiment_id,
                    "name": exp.name,
                    "artifact_location": exp.artifact_location
                }
                for exp in experiments
            ]
        except Exception as e:
            logger.error(f"Failed to get experiments: {e}")
            return []

    def get_models(self) -> List[Dict[str, Any]]:
        """Get list of registered models."""
        try:
            models = self.client.search_registered_models()
            result = []
            for model in models:
                latest_version = None
                if model.latest_versions:
                    latest_version = model.latest_versions[0].version
                result.append({
                    "name": model.name,
                    "latest_version": latest_version,
                    "description": model.description
                })
            return result
        except Exception as e:
            logger.error(f"Failed to get models: {e}")
            return []

    def check_mlflow_connection(self) -> bool:
        """Check if MLflow is accessible."""
        try:
            self.client.search_experiments(max_results=1)
            return True
        except Exception:
            return False
