"""API v1 router."""

from fastapi import APIRouter

from app.api.v1 import (
    health,
    projects,
    rtl,
    verification,
    simulation,
    failures,
    coverage,
    traceability,
    regression,
)

router = APIRouter(prefix="/api/v1")

router.include_router(health.router)
router.include_router(projects.router)
router.include_router(rtl.router)
router.include_router(verification.router)
router.include_router(simulation.router)
router.include_router(failures.router)
router.include_router(coverage.router)
router.include_router(traceability.router)
router.include_router(regression.router)