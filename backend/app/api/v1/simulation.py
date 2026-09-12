"""Simulation API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from app.engines.simulation import SimulationEngine, SimulationConfig
from app.engines.logs import LogAnalyzer

router = APIRouter(prefix="/simulation", tags=["Simulation"])


class CompileRequest(BaseModel):
    rtl_files: List[str]
    testbench: str
    top_module: str
    simulator: str = "verilator"
    timeout: int = 300


class SimulateRequest(BaseModel):
    rtl_content: str
    test_code: str
    top_module: str
    simulator: str = "verilator"
    timeout: int = 300


class LogAnalysisRequest(BaseModel):
    log_content: str
    log_type: str = "simulation"


@router.post("/compile")
async def compile_rtl(request: CompileRequest):
    """Compile RTL with a simulator."""
    engine = SimulationEngine()
    config = SimulationConfig(
        simulator=request.simulator,
        top_module=request.top_module,
        timeout=request.timeout,
    )

    result = engine.compile(request.rtl_files, config)

    return {
        "success": result.success,
        "exit_code": result.exit_code,
        "compilation_log": result.compilation_log,
        "error_message": result.error_message,
        "runtime_seconds": result.runtime_seconds,
        "command": result.command,
        "artifacts": result.artifacts,
        "status": "UNAVAILABLE" if not engine.is_verilator_available() else ("SUCCESS" if result.success else "FAILED"),
    }


@router.post("/run")
async def run_simulation(request: SimulateRequest):
    """Run a complete simulation (compile + execute)."""
    engine = SimulationEngine()

    # Save RTL content to temp file
    import tempfile
    import os
    with tempfile.TemporaryDirectory() as tmpdir:
        rtl_path = os.path.join(tmpdir, "design.sv")
        with open(rtl_path, "w") as f:
            f.write(request.rtl_content)

        config = SimulationConfig(
            simulator=request.simulator,
            top_module=request.top_module,
            timeout=request.timeout,
        )

        result = engine.run_test([rtl_path], request.test_code, config)

    return {
        "success": result.success,
        "exit_code": result.exit_code,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "compilation_log": result.compilation_log,
        "simulation_log": result.simulation_log,
        "duration_seconds": result.runtime_seconds,
        "error_message": result.error_message,
        "command": result.command,
        "artifacts": result.artifacts,
        "status": "UNAVAILABLE" if not engine.is_verilator_available() else ("PASSED" if result.success else "FAILED"),
    }


@router.post("/analyze-log")
async def analyze_simulation_log(request: LogAnalysisRequest):
    """Analyze a simulation log file."""
    analyzer = LogAnalyzer()

    if request.log_type == "compilation":
        errors = analyzer.parse_compilation_errors(request.log_content)
        return {
            "log_type": "compilation",
            "errors": errors,
            "total_errors": len(errors),
        }
    elif request.log_type == "uvm":
        uvm_info = analyzer.parse_uvm_log(request.log_content)
        return {
            "log_type": "uvm",
            **uvm_info,
        }
    else:
        analysis = analyzer.parse_log(request.log_content)
        return {
            "log_type": "simulation",
            **analysis,
        }