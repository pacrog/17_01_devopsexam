"""
Prediction endpoints.
Handles single and batch ML predictions.
"""
import time
from typing import List
from fastapi import APIRouter, HTTPException

from ..models import (
    PredictionRequest,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
    ExperimentsResponse,
    ModelsResponse,
    ExperimentInfo,
    ModelInfo
)

router = APIRouter(tags=["predict"])

# Global model manager (set by main app)
_model_manager = None


def set_model_manager(model_manager):
    """Set global model manager from main app."""
    global _model_manager
    _model_manager = model_manager


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Make prediction",
    description="Submit features for ML model prediction"
)
async def predict(request: PredictionRequest):
    """
    Make a single prediction using the loaded model.

    Expects Iris flower features:
    - sepal_length
    - sepal_width
    - petal_length
    - petal_width

    Returns predicted class and probabilities.
    """
    if not _model_manager or not _model_manager.is_loaded():
        raise HTTPException(
            status_code=503,
            detail="Model not available. Please try again later."
        )

    try:
        prediction, probabilities, latency_ms = _model_manager.predict(
            request.features
        )

        return PredictionResponse(
            prediction=prediction,
            probability=probabilities,
            model_version=_model_manager.model_version,
            latency_ms=latency_ms
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


@router.post(
    "/predict/batch",
    response_model=BatchPredictionResponse,
    summary="Batch predictions",
    description="Submit multiple samples for batch prediction"
)
async def predict_batch(request: BatchPredictionRequest):
    """
    Make predictions for multiple samples in a single request.
    More efficient than multiple single predictions.
    """
    if not _model_manager or not _model_manager.is_loaded():
        raise HTTPException(
            status_code=503,
            detail="Model not available. Please try again later."
        )

    if not request.samples:
        raise HTTPException(
            status_code=400,
            detail="No samples provided"
        )

    try:
        start_time = time.time()
        results = _model_manager.predict_batch(request.samples)
        total_latency = (time.time() - start_time) * 1000

        predictions = [
            PredictionResponse(
                prediction=pred,
                probability=probs,
                model_version=_model_manager.model_version,
                latency_ms=latency
            )
            for pred, probs, latency in results
        ]

        return BatchPredictionResponse(
            predictions=predictions,
            total_latency_ms=total_latency
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch prediction failed: {str(e)}"
        )


@router.get(
    "/mlflow/experiments",
    response_model=ExperimentsResponse,
    summary="List experiments",
    description="Returns list of MLflow experiments",
    tags=["mlflow"]
)
async def list_experiments():
    """Get list of all MLflow experiments."""
    if not _model_manager:
        raise HTTPException(
            status_code=503,
            detail="MLflow not configured"
        )

    experiments = _model_manager.get_experiments()
    return ExperimentsResponse(
        experiments=[
            ExperimentInfo(**exp) for exp in experiments
        ]
    )


@router.get(
    "/mlflow/models",
    response_model=ModelsResponse,
    summary="List registered models",
    description="Returns list of registered models in MLflow registry",
    tags=["mlflow"]
)
async def list_models():
    """Get list of all registered models in MLflow."""
    if not _model_manager:
        raise HTTPException(
            status_code=503,
            detail="MLflow not configured"
        )

    models = _model_manager.get_models()
    return ModelsResponse(
        models=[
            ModelInfo(**model) for model in models
        ]
    )
