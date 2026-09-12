"""Verification Planning & Generation API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from app.engines.rtl import RTLAnalyzer
from app.engines.verification_planner import VerificationPlanGenerator
from app.engines.assertion_generator import AssertionGenerator
from app.engines.test_generator import TestGenerator

router = APIRouter(prefix="/verification", tags=["Verification"])


class VerificationPlanRequest(BaseModel):
    rtl_content: str
    specification: Optional[str] = ""


class AssertionGenRequest(BaseModel):
    rtl_content: str


class TestGenRequest(BaseModel):
    rtl_content: str
    coverage_gaps: Optional[List[dict]] = None
    test_types: List[str] = ["directed", "constrained_random"]


@router.post("/plan")
async def generate_verification_plan(request: VerificationPlanRequest):
    """Generate a verification plan from RTL analysis."""
    analyzer = RTLAnalyzer()
    modules = analyzer.analyze(request.rtl_content)

    if not modules:
        raise HTTPException(status_code=400, detail="No modules found in RTL")

    planner = VerificationPlanGenerator()
    plan = planner.generate(modules, request.specification)

    return {
        "plan": plan,
        "summary": plan["summary"],
        "traceability": plan["traceability"],
        "modules_analyzed": [m.name for m in modules],
    }


@router.post("/assertions")
async def generate_assertions(request: AssertionGenRequest):
    """Generate SystemVerilog assertions from RTL."""
    analyzer = RTLAnalyzer()
    modules = analyzer.analyze(request.rtl_content)

    if not modules:
        raise HTTPException(status_code=400, detail="No modules found in RTL")

    generator = AssertionGenerator()
    assertions = generator.generate(modules)

    return {
        "assertions": assertions,
        "total_generated": len(assertions),
        "modules_analyzed": [m.name for m in modules],
    }


@router.post("/tests")
async def generate_tests(request: TestGenRequest):
    """Generate tests from RTL."""
    analyzer = RTLAnalyzer()
    modules = analyzer.analyze(request.rtl_content)

    if not modules:
        raise HTTPException(status_code=400, detail="No modules found in RTL")

    generator = TestGenerator()
    tests = generator.generate(modules, request.coverage_gaps)

    if request.test_types:
        tests = [t for t in tests if t["test_type"] in request.test_types]

    return {
        "tests": tests,
        "total_generated": len(tests),
        "test_types": {
            tt: len([t for t in tests if t["test_type"] == tt])
            for tt in set(t["test_type"] for t in tests)
        },
        "modules_analyzed": [m.name for m in modules],
    }


@router.post("/uvm")
async def generate_uvm(request: AssertionGenRequest):
    """Generate UVM testbench components from RTL."""
    analyzer = RTLAnalyzer()
    modules = analyzer.analyze(request.rtl_content)

    if not modules:
        raise HTTPException(status_code=400, detail="No modules found in RTL")

    generator = TestGenerator()
    uvm_components = []

    for module in modules:
        uvm_components.extend(generator._gen_uvm_tests(module))

    return {
        "uvm_components": uvm_components,
        "total_generated": len(uvm_components),
        "modules_analyzed": [m.name for m in modules],
    }


@router.post("/full-flow")
async def full_verification_flow(request: VerificationPlanRequest):
    """Run the complete verification flow: plan → assertions → tests → UVM."""
    analyzer = RTLAnalyzer()
    modules = analyzer.analyze(request.rtl_content)

    if not modules:
        raise HTTPException(status_code=400, detail="No modules found in RTL")

    # Step 1: Verification Plan
    planner = VerificationPlanGenerator()
    plan = planner.generate(modules, request.specification)

    # Step 2: Assertions
    assertion_gen = AssertionGenerator()
    assertions = assertion_gen.generate(modules)

    # Step 3: Tests
    test_gen = TestGenerator()
    tests = test_gen.generate(modules)

    # Step 4: UVM
    uvm_components = []
    for module in modules:
        uvm_components.extend(test_gen._gen_uvm_tests(module))

    # Step 5: Summary
    summary = analyzer.get_summary()

    return {
        "summary": summary,
        "verification_plan": {
            "total_items": plan["summary"]["total_items"],
            "categories": plan["summary"]["categories"],
            "items": plan["items"][:20],
        },
        "assertions": {
            "total_generated": len(assertions),
            "assertions": assertions[:20],
        },
        "tests": {
            "total_generated": len(tests),
            "test_types": {
                tt: len([t for t in tests if t["test_type"] == tt])
                for tt in set(t["test_type"] for t in tests)
            },
            "tests": [
                {
                    "name": t["name"],
                    "type": t["test_type"],
                    "objective": t["verification_objective"],
                    "code_length": len(t["code"]),
                }
                for t in tests
            ],
        },
        "uvm": {
            "total_generated": len(uvm_components),
            "component_types": {
                c["test_type"]: len([c for c in uvm_components if c["test_type"] == c["test_type"]])
                for c in uvm_components
            },
        },
    }