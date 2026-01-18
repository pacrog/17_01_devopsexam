#!/usr/bin/env python3
"""
Script to log ML experiments to MLflow for demonstration purposes.
Creates multiple runs with different hyperparameters for visualization.
"""
import os
import sys

# Set MLflow tracking URI
os.environ["MLFLOW_TRACKING_URI"] = "http://localhost:5001"
os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://localhost:9000"
os.environ["AWS_ACCESS_KEY_ID"] = "minioadmin"
os.environ["AWS_SECRET_ACCESS_KEY"] = "minioadmin"

import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import pandas as pd
import numpy as np

def main():
    print("=" * 50)
    print("Logging experiments to MLflow")
    print("=" * 50)

    # Setup MLflow
    mlflow.set_tracking_uri("http://localhost:5001")
    client = MlflowClient()

    # Test connection
    try:
        experiments = client.search_experiments()
        print(f"Connected to MLflow. Found {len(experiments)} existing experiments.")
    except Exception as e:
        print(f"ERROR: Cannot connect to MLflow: {e}")
        print("Make sure MLflow is running: docker-compose up -d mlflow")
        sys.exit(1)

    # Create experiment
    experiment_name = "iris_classification"
    try:
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment is None:
            experiment_id = mlflow.create_experiment(
                experiment_name,
                artifact_location="s3://mlflow/artifacts"
            )
            print(f"Created experiment: {experiment_name}")
        else:
            experiment_id = experiment.experiment_id
            print(f"Using existing experiment: {experiment_name}")
    except Exception as e:
        print(f"Warning: Could not set artifact location: {e}")
        experiment_id = mlflow.create_experiment(experiment_name)

    mlflow.set_experiment(experiment_name)

    # Load data
    print("\nLoading Iris dataset...")
    iris = load_iris()
    feature_names = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
    X = pd.DataFrame(iris.data, columns=feature_names)
    y = iris.target

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

    # Define experiments to run
    experiments_config = [
        {
            "name": "RandomForest_baseline",
            "model_class": RandomForestClassifier,
            "params": {"n_estimators": 50, "max_depth": 3, "random_state": 42}
        },
        {
            "name": "RandomForest_medium",
            "model_class": RandomForestClassifier,
            "params": {"n_estimators": 100, "max_depth": 5, "random_state": 42}
        },
        {
            "name": "RandomForest_deep",
            "model_class": RandomForestClassifier,
            "params": {"n_estimators": 200, "max_depth": 10, "random_state": 42}
        },
        {
            "name": "GradientBoosting_baseline",
            "model_class": GradientBoostingClassifier,
            "params": {"n_estimators": 50, "max_depth": 3, "random_state": 42}
        },
        {
            "name": "GradientBoosting_tuned",
            "model_class": GradientBoostingClassifier,
            "params": {"n_estimators": 100, "max_depth": 5, "learning_rate": 0.1, "random_state": 42}
        },
        {
            "name": "LogisticRegression",
            "model_class": LogisticRegression,
            "params": {"max_iter": 200, "random_state": 42}
        },
    ]

    best_model = None
    best_accuracy = 0
    best_run_id = None

    print(f"\nRunning {len(experiments_config)} experiments...")
    print("-" * 50)

    for config in experiments_config:
        run_name = config["name"]
        model_class = config["model_class"]
        params = config["params"]

        with mlflow.start_run(run_name=run_name) as run:
            print(f"\nRun: {run_name}")

            # Log parameters
            mlflow.log_params(params)
            mlflow.log_param("model_type", model_class.__name__)

            # Train model
            model = model_class(**params)
            model.fit(X_train, y_train)

            # Predict
            y_pred_train = model.predict(X_train)
            y_pred_test = model.predict(X_test)

            # Calculate metrics
            metrics = {
                "train_accuracy": accuracy_score(y_train, y_pred_train),
                "test_accuracy": accuracy_score(y_test, y_pred_test),
                "precision_macro": precision_score(y_test, y_pred_test, average='macro'),
                "recall_macro": recall_score(y_test, y_pred_test, average='macro'),
                "f1_macro": f1_score(y_test, y_pred_test, average='macro'),
            }

            # Log metrics
            mlflow.log_metrics(metrics)

            print(f"  Train Accuracy: {metrics['train_accuracy']:.4f}")
            print(f"  Test Accuracy:  {metrics['test_accuracy']:.4f}")
            print(f"  F1 Score:       {metrics['f1_macro']:.4f}")

            # Log model
            mlflow.sklearn.log_model(model, "model")

            # Track best model
            if metrics['test_accuracy'] > best_accuracy:
                best_accuracy = metrics['test_accuracy']
                best_model = model
                best_run_id = run.info.run_id

    print("-" * 50)
    print(f"\nBest model: Test Accuracy = {best_accuracy:.4f}")

    # Register best model
    print("\nRegistering best model...")
    model_name = "iris_classifier"

    try:
        model_uri = f"runs:/{best_run_id}/model"
        model_version = mlflow.register_model(model_uri, model_name)
        print(f"Registered model: {model_name} version {model_version.version}")

        # Transition to Production
        client.transition_model_version_stage(
            name=model_name,
            version=model_version.version,
            stage="Production"
        )
        print(f"Transitioned to Production stage")
    except Exception as e:
        print(f"Warning: Could not register model: {e}")

    print("\n" + "=" * 50)
    print("DONE! Open MLflow UI: http://localhost:5001")
    print("=" * 50)

if __name__ == "__main__":
    main()
