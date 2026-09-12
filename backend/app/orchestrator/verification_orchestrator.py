"""Verification Orchestrator - Coordinates the complete verification flow."""

from typing import Dict, List, Any, Optional
import uuid
from datetime import datetime

from app.engines.rtl import RTLAnalyzer
from app.engines.verification_planner import VerificationPlanGenerator
from app.engines.assertion_generator import AssertionGenerator
from app.engines.test_generator import TestGenerator
from app.engines.simulation import SimulationEngine, SimulationConfig
from app.engines.logs import LogAnalyzer
from app.engines.coverage import CoverageAnalyzer
from app.engines.traceability import TraceabilityEngine
from app.ai.agents import (
    RTLAnalysisAgent,
    VerificationPlannerAgent,
    AssertionGeneratorAgent,
    TestGeneratorAgent,
    DebugAgent,
    CoverageAgent,
)
from app.ai.providers import get_ai_provider


class VerificationOrchestrator:
    """Main orchestrator for the verification flow."""

    def __init__(self, use_ai: bool = True, ai_provider: str = "mock"):
        self.rtl_analyzer = RTLAnalyzer()
        self.plan_generator = VerificationPlanGenerator()
        self.assertion_generator = AssertionGenerator()
        self.test_generator = TestGenerator()
        self.simulation_engine = SimulationEngine()
        self.log_analyzer = LogAnalyzer()
        self.coverage_analyzer = CoverageAnalyzer()
        self.traceability_engine = TraceabilityEngine()

        self.use_ai = use_ai
        if use_ai:
            self.ai_provider = get_ai_provider(ai_provider)
            self.rtl_agent = RTLAnalysisAgent(self.ai_provider)
            self.plan_agent = VerificationPlannerAgent(self.ai_provider)
            self.assertion_agent = AssertionGeneratorAgent(self.ai_provider)
            self.test_agent = TestGeneratorAgent(self.ai_provider)
            self.debug_agent = DebugAgent(self.ai_provider)
            self.coverage_agent = CoverageAgent(self.ai_provider)
        else:
            self.ai_provider = None

    def analyze_rtl(self, rtl_content: str, filename: str = "design.sv") -> Dict[str, Any]:
        """Step 1: Analyze RTL and extract design information."""
        modules = self.rtl_analyzer.analyze(rtl_content, filename)
        summary = self.rtl_analyzer.get_summary()

        result = {
            "modules": self.rtl_analyzer.to_dict()["modules"],
            "summary": summary,
        }

        if self.use_ai and self.ai_provider.is_available():
            ai_analysis = self.rtl_agent.analyze_rtl(rtl_content)
            result["ai_analysis"] = ai_analysis

        return result

    def generate_verification_plan(self, rtl_content: str,
                                   specification: str = "") -> Dict[str, Any]:
        """Step 2: Generate verification plan from RTL."""
        modules = self.rtl_analyzer.analyze(rtl_content)
        plan = self.plan_generator.generate(modules, specification)

        if self.use_ai and self.ai_provider.is_available():
            rtl_analysis = self.analyze_rtl(rtl_content)
            ai_plan = self.plan_agent.generate_plan(rtl_analysis, specification)
            plan["ai_generated"] = ai_plan

        return plan

    def generate_assertions(self, rtl_content: str) -> List[Dict[str, Any]]:
        """Step 3: Generate SVA assertions."""
        modules = self.rtl_analyzer.analyze(rtl_content)
        assertions = self.assertion_generator.generate(modules)

        if self.use_ai and self.ai_provider.is_available():
            ai_assertions = self.assertion_agent.generate_assertions(
                rtl_content, self.rtl_analyzer.to_dict()["modules"]
            )
            # Merge AI assertions (marked as AI-generated)
            for a in ai_assertions.get("ai_generated_assertions", []):
                if isinstance(a, dict):
                    a["classification"] = "GENERATED"
                    a["validation_status"] = "REQUIRES ENGINEER VALIDATION"
                    assertions.append(a)

        return assertions

    def generate_tests(self, rtl_content: str,
                       coverage_gaps: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Step 4: Generate tests."""
        modules = self.rtl_analyzer.analyze(rtl_content)
        tests = self.test_generator.generate(modules, coverage_gaps)

        if self.use_ai and self.ai_provider.is_available():
            ai_tests = self.test_agent.generate_tests(rtl_content, coverage_gaps)
            for t in ai_tests.get("ai_generated_tests", []):
                if isinstance(t, dict):
                    t["classification"] = "GENERATED"
                    tests.append(t)

        return tests

    def generate_uvm(self, rtl_content: str) -> List[Dict[str, Any]]:
        """Step 5: Generate UVM testbench components."""
        modules = self.rtl_analyzer.analyze(rtl_content)
        uvm_components = []

        for module in modules:
            uvm_components.extend(self.test_generator._gen_uvm_tests(module))

        return uvm_components

    def run_simulation(self, rtl_files: List[str], test_code: str,
                       top_module: str, simulator: str = "verilator",
                       timeout: int = 300) -> Dict[str, Any]:
        """Step 6: Run simulation."""
        config = SimulationConfig(
            simulator=simulator,
            top_module=top_module,
            timeout=timeout,
        )

        result = self.simulation_engine.run_test(rtl_files, test_code, config)

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
            "status": "UNAVAILABLE" if not self.simulation_engine.is_verilator_available() else
                     ("PASSED" if result.success else "FAILED"),
        }

    def analyze_logs(self, log_content: str) -> Dict[str, Any]:
        """Step 7: Analyze simulation logs."""
        analysis = self.log_analyzer.parse_log(log_content)

        if self.use_ai and self.ai_provider.is_available():
            # AI can enhance log analysis
            pass

        return analysis

    def analyze_failures(self, failure_info: Dict[str, Any],
                         rtl_content: str = "",
                         log_analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Step 8: Analyze failures."""
        failure = {
            "failure_id": f"FAIL-{uuid.uuid4().hex[:8]}",
            "severity": failure_info.get("severity", "ERROR"),
            "error": failure_info.get("error", ""),
            "location": failure_info.get("location", ""),
            "observed_fact": failure_info.get("observed_fact", ""),
            "root_cause_hypothesis": "",
            "confidence": "LOW",
            "evidence": [],
            "recommended_action": "",
            "classification": "HYPOTHESIS",
        }

        if self.use_ai and self.ai_provider.is_available():
            ai_analysis = self.debug_agent.analyze_failure(
                failure_info, rtl_content, log_analysis
            )
            failure["ai_analysis"] = ai_analysis

        return failure

    def analyze_coverage(self, coverage_report: str,
                         rtl_content: str = "",
                         module_name: str = "") -> Dict[str, Any]:
        """Step 9: Analyze coverage."""
        coverage = self.coverage_analyzer.parse_verilator_coverage(coverage_report)
        if not any(d.overall > 0 for d in coverage.values()):
            coverage = self.coverage_analyzer.parse_ucov_report(coverage_report)

        gaps = self.coverage_analyzer.identify_gaps(coverage, rtl_content, module_name)
        report = self.coverage_analyzer.generate_coverage_report(coverage, gaps, module_name)

        if self.use_ai and self.ai_provider.is_available():
            ai_coverage = self.coverage_agent.analyze_coverage(
                {ct: {"overall": d.overall, "covered": d.covered, "total": d.total}
                 for ct, d in coverage.items()}, rtl_content
            )
            report["ai_analysis"] = ai_coverage

        return {
            "report": report,
            "coverage": {
                ct: {"overall": d.overall, "covered": d.covered, "total": d.total}
                for ct, d in coverage.items()
            },
            "gaps": gaps,
        }

    def identify_coverage_gaps(self, coverage_report: str,
                               rtl_content: str,
                               module_name: str) -> List[Dict[str, Any]]:
        """Identify coverage gaps."""
        coverage = self.coverage_analyzer.parse_verilator_coverage(coverage_report)
        if not any(d.overall > 0 for d in coverage.values()):
            coverage = self.coverage_analyzer.parse_ucov_report(coverage_report)

        return self.coverage_analyzer.identify_gaps(coverage, rtl_content, module_name)

    def generate_targeted_tests(self, coverage_gaps: List[Dict[str, Any]],
                                rtl_content: str) -> List[Dict[str, Any]]:
        """Step 10: Generate targeted tests for coverage gaps."""
        modules = self.rtl_analyzer.analyze(rtl_content)
        return self.test_generator.generate(modules, coverage_gaps)

    def run_regression(self, rtl_files: List[str], test_files: List[str],
                       config: SimulationConfig) -> Dict[str, Any]:
        """Step 11: Run regression."""
        results = {}
        for test_file in test_files:
            test_name = test_file.split("/")[-1].replace(".sv", "")
            with open(test_file, "r") as f:
                test_code = f.read()
            results[test_name] = self.simulation_engine.run_test(rtl_files, test_code, config)

        # Compute summary
        total = len(results)
        passed = sum(1 for r in results.values() if r.success)
        failed = total - passed

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": 0,
            "results": {
                name: {
                    "success": r.success,
                    "exit_code": r.exit_code,
                    "duration": r.runtime_seconds,
                    "error": r.error_message,
                }
                for name, r in results.items()
            },
        }

    def full_verification_flow(self, rtl_content: str,
                               specification: str = "",
                               top_module: str = "",
                               run_simulation: bool = False) -> Dict[str, Any]:
        """Execute the complete verification flow."""
        results = {}

        # Step 1: RTL Analysis
        print("Step 1: RTL Analysis...")
        results["rtl_analysis"] = self.analyze_rtl(rtl_content)

        # Step 2: Verification Plan
        print("Step 2: Verification Plan...")
        results["verification_plan"] = self.generate_verification_plan(rtl_content, specification)

        # Step 3: Assertions
        print("Step 3: SVA Generation...")
        results["assertions"] = self.generate_assertions(rtl_content)

        # Step 4: Tests
        print("Step 4: Test Generation...")
        results["tests"] = self.generate_tests(rtl_content)

        # Step 5: UVM
        print("Step 5: UVM Generation...")
        results["uvm"] = self.generate_uvm(rtl_content)

        # Step 6: Simulation (if requested)
        if run_simulation and top_module:
            print("Step 6: Simulation...")
            # Save RTL to temp file for simulation
            import tempfile
            import os
            with tempfile.TemporaryDirectory() as tmpdir:
                rtl_path = os.path.join(tmpdir, "design.sv")
                with open(rtl_path, "w") as f:
                    f.write(rtl_content)

                for test in results["tests"][:3]:  # Run first 3 tests
                    sim_result = self.run_simulation(
                        [rtl_path], test["code"], top_module
                    )
                    test["simulation_result"] = sim_result

                    # Step 7: Log Analysis
                    if sim_result.get("simulation_log"):
                        log_analysis = self.analyze_logs(sim_result["simulation_log"])
                        test["log_analysis"] = log_analysis

                        # Step 8: Failure Analysis
                        if not sim_result["success"]:
                            failure = self.analyze_failures(
                                {"error": sim_result.get("error_message", "Simulation failed"),
                                 "location": top_module},
                                rtl_content,
                                log_analysis
                            )
                            test["failure_analysis"] = failure

        return results