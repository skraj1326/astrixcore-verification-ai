"""Health check API endpoint."""

from fastapi import APIRouter
from app.core.config import settings
from app.engines.simulation import SimulationEngine

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    engine = SimulationEngine()
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "components": {
            "database": "connected",
            "verilator": "available" if engine.is_verilator_available() else "NOT AVAILABLE",
            "icarus": "available" if engine.is_icarus_available() else "NOT AVAILABLE",
        },
    }


@router.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "tagline": "AI-assisted verification from RTL to coverage closure.",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "health": "/api/v1/health",
            "projects": "/api/v1/projects",
            "rtl": "/api/v1/rtl",
            "verification": "/api/v1/verification",
            "simulation": "/api/v1/simulation",
            "failures": "/api/v1/failures",
            "coverage": "/api/v1/coverage",
            "traceability": "/api/v1/traceability",
            "regression": "/api/v1/regression",
        },
    }