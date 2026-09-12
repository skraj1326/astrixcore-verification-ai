"""RTL Analysis API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.engines.rtl import RTLAnalyzer

router = APIRouter(prefix="/rtl", tags=["RTL Analysis"])


class RTLAnalysisRequest(BaseModel):
    content: str
    filename: str = "design.sv"


class RTLAnalysisResponse(BaseModel):
    filename: str
    modules: list
    summary: dict


@router.post("/analyze", response_model=RTLAnalysisResponse)
async def analyze_rtl(request: RTLAnalysisRequest):
    """Parse and analyze SystemVerilog RTL code."""
    analyzer = RTLAnalyzer()

    try:
        modules = analyzer.analyze(request.content, request.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {str(e)}")

    if not modules:
        raise HTTPException(
            status_code=400,
            detail="No modules found in the provided RTL code"
        )

    return RTLAnalysisResponse(
        filename=request.filename,
        modules=analyzer.to_dict()["modules"],
        summary=analyzer.get_summary(),
    )


@router.get("/examples/fifo")
async def get_fifo_example():
    """Get the FIFO example RTL."""
    import os
    example_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "examples", "fifo", "fifo.sv")
    if os.path.exists(example_path):
        with open(example_path, "r") as f:
            content = f.read()
        return {
            "filename": "fifo.sv",
            "content": content,
            "description": "Parameterized synchronous FIFO with assertions"
        }
    raise HTTPException(status_code=404, detail="FIFO example not found")