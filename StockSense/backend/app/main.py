from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, health
from app.routers.api import api_router

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle events."""
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="StockSense Inventory Management System API - High performance inventory tracking and analytics.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root-level health endpoint: GET /health
app.include_router(health.router)

# Direct root-level auth endpoints: /auth/register, /auth/login, etc.
app.include_router(auth.router, prefix="/auth")

# Versioned API router: /api/v1/... (includes /api/v1/auth, /api/v1/health)
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
def root() -> dict[str, str]:
    """Root entrypoint for StockSense API."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "docs": "/docs",
        "health": "/health",
        "version": "1.0.0",
    }
