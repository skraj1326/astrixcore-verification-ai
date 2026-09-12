"""Regression API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.engines.simulation import SimulationEngine, SimulationConfig

router = APIRouter(prefix="/regression", tags=["Regression"])


class RegressionRequest(BaseModel):
    rtl_files: List[str]
    test_files: List[str]
    top_module: str
    simulator: str = "verilator"
    timeout: int = 300


@router.post("/run")
async def run_regression(request: RegressionRequest):
    """Run a full regression suite."""
    engine = SimulationEngine()
    config = SimulationConfig(
        simulator=request.simulator,
        top_module=request.top_module,
        timeout=request.timeout,
    )

    results = {}
    for test_file in request.test_files:
        test_name = test_file.split("/")[-1].replace(".sv", "")
        with open(test_file, "r") as f:
            test_code = f.read()
        results[test_name] = engine.run_test(request.rtl_files, test_code, config)

    total = len(results)
    passed = sum(1 for r in results.values() if r.success)
    failed = total - passed

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": 0,
        "duration_seconds": sum(r.runtime_seconds for r in results.values()),
        "results": {
            name: {
                "success": r.success,
                "exit_code": r.exit_code,
                "duration": r.runtime_seconds,
                "error": r.error_message,
            }
            for name, r in results.items()
        },
        "failure_distribution": {},
        "top_causes": [],
        "coverage_delta": {},
    }


@router.get("/{project_id}")
async def get_regression_history(project_id: str):
    """Get regression history for a project."""
    return {
        "runs": [],
        "total": 0,
    }