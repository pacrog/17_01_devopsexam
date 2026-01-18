"""API Routers."""
from .health import router as health_router
from .predict import router as predict_router
from .data import router as data_router

__all__ = ["health_router", "predict_router", "data_router"]
