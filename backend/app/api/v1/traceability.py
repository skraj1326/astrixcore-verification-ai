"""Traceability API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.engines.traceability import TraceabilityEngine

router = APIRouter(prefix="/traceability", tags=["Traceability"])


class TraceabilityRequest(BaseModel):
    requirement_id: str
    artifact_type: str  # verification_plan, assertion, test, simulation, failure, coverage
    artifact_id: str


@router.post("/link")
async def create_traceability_link(request: TraceabilityRequest):
    """Create a traceability link between requirement and artifact."""
    engine = TraceabilityEngine()
    engine.add_link(request.requirement_id, request.artifact_type, request.artifact_id)
    return {"status": "linked"}


@router.get("/{requirement_id}")
async def get_traceability(requirement_id: str):
    """Get traceability for a requirement."""
    engine = TraceabilityEngine()
    link = engine.get_traceability(requirement_id)
    if not link:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return {
        "requirement_id": link.requirement_id,
        "verification_plans": link.verification_plan_ids,
        "assertions": link.assertion_ids,
        "tests": link.test_ids,
        "simulations": link.simulation_ids,
        "failures": link.failure_ids,
        "coverage": link.coverage_ids,
    }


@router.get("/")
async def get_all_traceability():
    """Get full traceability matrix."""
    engine = TraceabilityEngine()
    return engine.generate_traceability_matrix()


@router.get("/unverified")
async def get_unverified_requirements():
    """Get requirements with missing verification artifacts."""
    engine = TraceabilityEngine()
    return {"unverified": engine.get_unverified_requirements()}