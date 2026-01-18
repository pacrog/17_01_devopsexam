"""
ML Prediction Service - Main Application

API-first designed service providing:
- ML predictions (Iris classification)
- Data drift detection via EvidentlyAI
- MLflow integration for experiment tracking
- Health and readiness probes
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from .ml import ModelManager, DriftDetector
from .routers import health_router, predict_router, data_router
from .routers.health import set_dependencies as set_health_deps
from .routers.predict import set_model_manager
from .routers.data import set_drift_detector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global instances
model_manager: ModelManager = None
drift_detector: DriftDetector = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    global model_manager, drift_detector

    logger.info("Starting ML Prediction Service...")

    # Initialize ML components
    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    logger.info(f"MLflow tracking URI: {mlflow_uri}")

    # Initialize model manager
    model_manager = ModelManager(mlflow_tracking_uri=mlflow_uri)

    # Try to load model (will train default if needed)
    try:
        model_manager.load_model()
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.warning(f"Model loading deferred: {e}")

    # Initialize drift detector
    drift_detector = DriftDetector()
    logger.info("Drift detector initialized")

    # Set dependencies for routers
    set_health_deps(model_manager, drift_detector)
    set_model_manager(model_manager)
    set_drift_detector(drift_detector)

    logger.info("ML Prediction Service started successfully")

    yield

    # Cleanup on shutdown
    logger.info("Shutting down ML Prediction Service...")


# Create FastAPI application
app = FastAPI(
    title="ML Prediction Service",
    description="""
    API-first designed ML service for predictions and monitoring.

    ## Features
    - **Predictions**: Single and batch ML predictions
    - **Drift Detection**: Data drift analysis via EvidentlyAI
    - **MLflow Integration**: Experiment tracking and model registry
    - **Health Monitoring**: Kubernetes-ready health probes

    ## Architecture
    This service is part of a microservices architecture:
    - API Service (this)
    - MLflow Tracking Server
    - PostgreSQL (metadata storage)
    - MinIO (artifact storage)
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(predict_router)
app.include_router(data_router)


# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="ML Prediction Service API",
        version="1.0.0",
        description=app.description,
        routes=app.routes,
    )

    # Add custom info
    openapi_schema["info"]["contact"] = {
        "name": "DevOps Exam Project"
    }
    openapi_schema["info"]["license"] = {
        "name": "MIT"
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - redirects to docs."""
    return {
        "message": "ML Prediction Service",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/healthcheck"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
