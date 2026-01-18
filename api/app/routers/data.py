"""
Data management and drift detection endpoints.
Uses EvidentlyAI for data quality monitoring.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from ..models import (
    DriftAnalysisRequest,
    DriftAnalysisResponse,
    FeatureDrift
)

router = APIRouter(prefix="/data", tags=["data"])

# Global drift detector (set by main app)
_drift_detector = None


def set_drift_detector(drift_detector):
    """Set global drift detector from main app."""
    global _drift_detector
    _drift_detector = drift_detector


@router.post(
    "/drift",
    response_model=DriftAnalysisResponse,
    summary="Analyze data drift",
    description="Analyzes data drift between reference and current datasets using EvidentlyAI"
)
async def analyze_drift(request: DriftAnalysisRequest):
    """
    Analyze data drift between reference and current datasets.

    Uses EvidentlyAI to detect distribution shifts in features.
    Returns overall drift score and per-feature drift metrics.

    If reference_data is not provided, uses the stored reference
    (initialized from Iris dataset by default).
    """
    if not _drift_detector:
        raise HTTPException(
            status_code=503,
            detail="Drift detector not initialized"
        )

    if not request.current_data:
        raise HTTPException(
            status_code=400,
            detail="current_data is required"
        )

    try:
        result = _drift_detector.analyze_drift(
            current_data=request.current_data,
            reference_data=request.reference_data
        )

        return DriftAnalysisResponse(
            drift_detected=result["drift_detected"],
            drift_score=result["drift_score"],
            feature_drift={
                k: FeatureDrift(**v)
                for k, v in result["feature_drift"].items()
            },
            report_url=result.get("report_url")
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Drift analysis failed: {str(e)}"
        )


@router.get(
    "/drift/report",
    response_class=HTMLResponse,
    summary="Get drift report",
    description="Returns the latest drift analysis report in HTML format"
)
async def get_drift_report():
    """
    Get the HTML drift report from the last analysis.

    The report contains visualizations of:
    - Overall dataset drift
    - Per-feature distribution comparisons
    - Statistical test results
    """
    if not _drift_detector:
        raise HTTPException(
            status_code=503,
            detail="Drift detector not initialized"
        )

    html = _drift_detector.get_report_html()

    if html is None:
        raise HTTPException(
            status_code=404,
            detail="No drift report available. Run /data/drift first."
        )

    return HTMLResponse(content=html)


@router.post(
    "/drift/generate-test-data",
    summary="Generate test data with drift",
    description="Generates synthetic drifted data for testing purposes"
)
async def generate_test_data(
    n_samples: int = 50,
    drift_magnitude: float = 0.5
):
    """
    Generate synthetic data with artificial drift for testing.

    Args:
        n_samples: Number of samples to generate (default: 50)
        drift_magnitude: How much drift to introduce (0-1, default: 0.5)

    Returns:
        List of data samples with drift
    """
    if not _drift_detector:
        raise HTTPException(
            status_code=503,
            detail="Drift detector not initialized"
        )

    if n_samples < 1 or n_samples > 1000:
        raise HTTPException(
            status_code=400,
            detail="n_samples must be between 1 and 1000"
        )

    if drift_magnitude < 0 or drift_magnitude > 1:
        raise HTTPException(
            status_code=400,
            detail="drift_magnitude must be between 0 and 1"
        )

    data = _drift_detector.generate_drifted_data(
        n_samples=n_samples,
        drift_magnitude=drift_magnitude
    )

    return {"data": data, "n_samples": len(data)}
