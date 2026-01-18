"""
Data Drift Detection using EvidentlyAI.
Monitors data quality and detects distribution shifts.
Compatible with evidently==0.6.7
"""
import os
import logging
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np
from sklearn.datasets import load_iris

# Evidently imports for version 0.6.7
from evidently import ColumnMapping
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, DataQualityPreset

logger = logging.getLogger(__name__)


class DriftDetector:
    """Detects data drift using EvidentlyAI."""

    def __init__(self, reference_data: pd.DataFrame = None):
        self.feature_columns = [
            "sepal_length", "sepal_width",
            "petal_length", "petal_width"
        ]
        self.reference_data = reference_data
        self.last_report = None
        self.report_path = "/tmp/drift_report.html"

        # Initialize with Iris data if no reference provided
        if self.reference_data is None:
            self._init_reference_from_iris()

    def _init_reference_from_iris(self):
        """Initialize reference data from Iris dataset."""
        iris = load_iris()
        self.reference_data = pd.DataFrame(
            iris.data,
            columns=self.feature_columns
        )
        logger.info(f"Initialized reference data with {len(self.reference_data)} samples")

    def set_reference_data(self, data: List[Dict[str, Any]]) -> None:
        """Set reference data from list of dictionaries."""
        self.reference_data = pd.DataFrame(data)
        if len(self.reference_data.columns) == 4:
            self.reference_data.columns = self.feature_columns
        logger.info(f"Updated reference data with {len(self.reference_data)} samples")

    def analyze_drift(
        self,
        current_data: List[Dict[str, Any]],
        reference_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Analyze data drift between reference and current data.

        Args:
            current_data: Current dataset as list of dictionaries
            reference_data: Optional reference dataset (uses stored if not provided)

        Returns:
            Dictionary with drift analysis results
        """
        # Prepare current data
        current_df = pd.DataFrame(current_data)

        # Ensure column names match
        if list(current_df.columns) != self.feature_columns:
            if len(current_df.columns) == 4:
                current_df.columns = self.feature_columns
            else:
                current_df = current_df[self.feature_columns]

        # Use provided reference or stored reference
        if reference_data is not None:
            ref_df = pd.DataFrame(reference_data)
            if len(ref_df.columns) == 4:
                ref_df.columns = self.feature_columns
        else:
            ref_df = self.reference_data

        # Column mapping for Evidently
        column_mapping = ColumnMapping(
            numerical_features=self.feature_columns
        )

        # Create drift report
        report = Report(metrics=[
            DataDriftPreset()
        ])

        # Run report: reference_data first, then current_data
        report.run(
            reference_data=ref_df,
            current_data=current_df,
            column_mapping=column_mapping
        )

        # Extract results
        report_dict = report.as_dict()

        # Parse drift results
        drift_detected = False
        drift_share = 0.0
        feature_drift = {}

        try:
            metrics = report_dict.get("metrics", [])
            for metric in metrics:
                result = metric.get("result", {})

                # Dataset drift info
                if "dataset_drift" in result:
                    drift_detected = result.get("dataset_drift", False)
                    drift_share = result.get("drift_share", 0.0)

                # Per-column drift info
                drift_by_columns = result.get("drift_by_columns", {})
                if drift_by_columns:
                    for feature in self.feature_columns:
                        if feature in drift_by_columns:
                            col_info = drift_by_columns[feature]
                            feature_drift[feature] = {
                                "drift_detected": col_info.get("drift_detected", False),
                                "drift_score": col_info.get("drift_score", 0.0)
                            }
        except Exception as e:
            logger.warning(f"Error parsing drift results: {e}")

        # Fill missing features
        for feature in self.feature_columns:
            if feature not in feature_drift:
                feature_drift[feature] = {"drift_detected": False, "drift_score": 0.0}

        # Save HTML report
        try:
            report.save_html(self.report_path)
            self.last_report = report
            logger.info(f"Saved drift report to {self.report_path}")
        except Exception as e:
            logger.warning(f"Could not save HTML report: {e}")

        return {
            "drift_detected": drift_detected,
            "drift_score": drift_share,
            "feature_drift": feature_drift,
            "report_url": "/data/drift/report"
        }

    def get_report_html(self) -> Optional[str]:
        """Get the last generated HTML report."""
        try:
            if os.path.exists(self.report_path):
                with open(self.report_path, "r") as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Could not read report: {e}")
        return None

    def generate_drifted_data(
        self,
        n_samples: int = 50,
        drift_magnitude: float = 0.5
    ) -> List[Dict[str, float]]:
        """Generate synthetic data with drift for testing."""
        ref_means = self.reference_data[self.feature_columns].mean()
        ref_stds = self.reference_data[self.feature_columns].std()

        drifted_data = []
        for _ in range(n_samples):
            sample = {}
            for feature in self.feature_columns:
                shifted_mean = ref_means[feature] * (1 + drift_magnitude * np.random.choice([-1, 1]))
                value = np.random.normal(shifted_mean, ref_stds[feature])
                sample[feature] = max(0, value)
            drifted_data.append(sample)

        return drifted_data

    def create_data_quality_report(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a data quality report."""
        df = pd.DataFrame(data)

        column_mapping = ColumnMapping(
            numerical_features=self.feature_columns
        )

        report = Report(metrics=[
            DataQualityPreset()
        ])

        report.run(
            current_data=df,
            reference_data=self.reference_data,
            column_mapping=column_mapping
        )

        return report.as_dict()
