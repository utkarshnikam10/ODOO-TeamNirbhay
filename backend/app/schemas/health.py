from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """Pydantic schema representing the health check response."""

    status: str = Field(..., description="API health status", examples=["healthy"])
    app_name: str = Field(..., description="Name of the application")
    environment: str = Field(..., description="Operating environment (development, staging, production)")
    version: str = Field(default="1.0.0", description="API version")
