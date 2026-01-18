"""
Pydantic models for API request/response validation.
Matches OpenAPI specification in docs/api_spec.yaml
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


# Health check models
class HealthResponse(BaseModel):
    status: str = Field(..., description="Service health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"


class ReadinessChecks(BaseModel):
    model_loaded: bool = False
    database_connected: bool = False
    mlflow_connected: bool = False


class ReadinessResponse(BaseModel):
    ready: bool
    checks: ReadinessChecks


# Prediction models
class PredictionRequest(BaseModel):
    features: Dict[str, float] = Field(
        ...,
        description="Feature values for prediction",
        example={
            "sepal_length": 5.1,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2
        }
    )


class PredictionResponse(BaseModel):
    prediction: Union[str, int] = Field(..., description="Predicted class")
    probability: List[float] = Field(..., description="Class probabilities")
    model_version: Optional[str] = None
    latency_ms: Optional[float] = None


class BatchPredictionRequest(BaseModel):
    samples: List[Dict[str, float]] = Field(
        ...,
        description="List of feature dictionaries for batch prediction"
    )


class BatchPredictionResponse(BaseModel):
    predictions: List[PredictionResponse]
    total_latency_ms: Optional[float] = None


# Data drift models
class DriftAnalysisRequest(BaseModel):
    reference_data: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Reference dataset (baseline). If not provided, uses stored reference."
    )
    current_data: List[Dict[str, Any]] = Field(
        ...,
        description="Current dataset to compare against reference"
    )


class FeatureDrift(BaseModel):
    drift_detected: bool
    drift_score: float


class DriftAnalysisResponse(BaseModel):
    drift_detected: bool
    drift_score: float = Field(..., ge=0, le=1)
    feature_drift: Dict[str, FeatureDrift]
    report_url: Optional[str] = None


# MLflow models
class ExperimentInfo(BaseModel):
    experiment_id: str
    name: str
    artifact_location: Optional[str] = None


class ExperimentsResponse(BaseModel):
    experiments: List[ExperimentInfo]


class ModelInfo(BaseModel):
    name: str
    latest_version: Optional[str] = None
    description: Optional[str] = None


class ModelsResponse(BaseModel):
    models: List[ModelInfo]


# Error models
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
