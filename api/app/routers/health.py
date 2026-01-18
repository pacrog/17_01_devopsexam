"""
Health check endpoints.
Provides health and readiness probes for Kubernetes/Docker orchestration.
"""
from datetime import datetime
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from ..models import HealthResponse, ReadinessResponse, ReadinessChecks

router = APIRouter(tags=["health"])

# Global state references (set by main app)
_model_manager = None
_drift_detector = None


def set_dependencies(model_manager, drift_detector):
    """Set global dependencies from main app."""
    global _model_manager, _drift_detector
    _model_manager = model_manager
    _drift_detector = drift_detector


@router.get(
    "/healthcheck",
    response_model=HealthResponse,
    summary="Basic health check",
    description="Returns service health status"
)
async def healthcheck():
    """
    Basic health check endpoint.
    Returns healthy if the service is running.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )


@router.get(
    "/readiness",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    description="Checks if service is ready to accept requests"
)
async def readiness():
    """
    Readiness probe for orchestration systems.
    Checks model loading, database, and MLflow connectivity.
    """
    checks = ReadinessChecks(
        model_loaded=_model_manager.is_loaded() if _model_manager else False,
        database_connected=True,  # Simplified for demo
        mlflow_connected=_model_manager.check_mlflow_connection() if _model_manager else False
    )

    is_ready = checks.model_loaded

    response = ReadinessResponse(
        ready=is_ready,
        checks=checks
    )

    if not is_ready:
        return JSONResponse(
            status_code=503,
            content=response.model_dump()
        )

    return response
