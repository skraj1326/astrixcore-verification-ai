"""Coverage Analysis API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from app.engines.coverage import CoverageAnalyzer
from app.engines.test_generator import TestGenerator
from app.engines.rtl import RTLAnalyzer

router = APIRouter(prefix="/coverage", tags=["Coverage"])


class CoverageAnalysisRequest(BaseModel):
    coverage_report: str
    rtl_content: Optional[str] = ""
    module_name: Optional[str] = ""


class CoverageGapRequest(BaseModel):
    coverage_report: str
    rtl_content: str
    module_name: str


class CoverageComparisonRequest(BaseModel):
    coverage_before: Dict[str, Any]
    coverage_after: Dict[str, Any]


@router.post("/analyze")
async def analyze_coverage(request: CoverageAnalysisRequest):
    """Analyze a coverage report and identify gaps."""
    analyzer = CoverageAnalyzer()

    coverage = analyzer.parse_verilator_coverage(request.coverage_report)
    if not any(d.overall > 0 for d in coverage.values()):
        coverage = analyzer.parse_ucov_report(request.coverage_report)

    gaps = analyzer.identify_gaps(coverage, request.rtl_content, request.module_name)
    report = analyzer.generate_coverage_report(coverage, gaps, request.module_name)

    return {
        "report": report,
        "coverage": {
            ct: {"overall": d.overall, "covered": d.covered, "total": d.total}
            for ct, d in coverage.items()
        },
        "gaps": gaps,
    }


@router.post("/gaps")
async def identify_coverage_gaps(request: CoverageGapRequest):
    """Identify specific coverage gaps from RTL and coverage data."""
    analyzer = CoverageAnalyzer()

    coverage = analyzer.parse_verilator_coverage(request.coverage_report)
    if not any(d.overall > 0 for d in coverage.values()):
        coverage = analyzer.parse_ucov_report(request.coverage_report)

    gaps = analyzer.identify_gaps(coverage, request.rtl_content, request.module_name)

    return {
        "total_gaps": len(gaps),
        "gaps": gaps,
        "gap_types": {
            "reachable_untested": len([g for g in gaps if g["gap_type"] == "reachable_untested"]),
            "potentially_unreachable": len([g for g in gaps if g["gap_type"] == "potentially_unreachable"]),
            "unreachable": len([g for g in gaps if g["gap_type"] == "unreachable"]),
        },
    }


@router.post("/generate-targeted-tests")
async def generate_targeted_tests(request: CoverageGapRequest):
    """Generate tests specifically targeting coverage gaps."""
    analyzer = CoverageAnalyzer()
    parser = RTLAnalyzer()
    test_gen = TestGenerator()

    modules = parser.parse(request.rtl_content)
    if not modules:
        raise HTTPException(status_code=400, detail="No modules found in RTL")

    coverage = analyzer.parse_verilator_coverage(request.coverage_report)
    if not any(d.overall > 0 for d in coverage.values()):
        coverage = analyzer.parse_ucov_report(request.coverage_report)

    gaps = analyzer.identify_gaps(coverage, request.rtl_content, request.module_name)
    tests = test_gen.generate(modules, gaps)

    return {
        "total_tests_generated": len(tests),
        "tests": [
            {
                "name": t["name"],
                "type": t["test_type"],
                "objective": t["verification_objective"],
                "target_coverage": t["target_coverage"],
                "code": t["code"],
            }
            for t in tests
        ],
        "gaps_addressed": len(gaps),
    }


@router.post("/compare")
async def compare_coverage(request: CoverageComparisonRequest):
    """Compare before/after coverage reports."""
    analyzer = CoverageAnalyzer()

    from app.engines.coverage import CoverageData

    before = {}
    for ct, data in request.coverage_before.items():
        before[ct] = CoverageData(
            report_type=ct,
            overall=data.get("overall", 0),
            covered=data.get("covered", 0),
            total=data.get("total", 0),
        )

    after = {}
    for ct, data in request.coverage_after.items():
        after[ct] = CoverageData(
            report_type=ct,
            overall=data.get("overall", 0),
            covered=data.get("covered", 0),
            total=data.get("total", 0),
        )

    comparison = analyzer.compare_coverage(before, after)

    return {
        "comparison": comparison,
        "overall_improved": any(c["improved"] for c in comparison.values()),
        "total_delta": sum(c["delta"] for c in comparison.values()),
    }