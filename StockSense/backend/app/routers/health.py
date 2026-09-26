from fastapi import APIRouter, status

from app.core.config import settings
from app.schemas.health import HealthCheckResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check the operational status of the StockSense API service.",
)
def health_check() -> HealthCheckResponse:
    """Return API health status and basic application details."""
    return HealthCheckResponse(
        status="healthy",
        app_name=settings.PROJECT_NAME,
        environment=settings.ENVIRONMENT,
        version="1.0.0",
    )
