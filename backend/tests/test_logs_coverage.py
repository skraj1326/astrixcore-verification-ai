"""Tests for Log Analyzer and Coverage Engine."""

import pytest
from app.engines.logs import LogAnalyzer
from app.engines.coverage import CoverageAnalyzer, CoverageData


class TestLogAnalyzer:
    """Test Log Analyzer."""

    def setup_method(self):
        self.analyzer = LogAnalyzer()

    def test_parse_simulation_log(self):
        """Test parsing a simulation log."""
        log_content = """
        [INFO] Starting simulation...
        [INFO] Test basic started
        [ERROR] Assertion failed in fifo_sync.a_no_write_when_full at fifo.sv:45
        [INFO] Test basic completed
        """
        
        result = self.analyzer.parse_log(log_content)
        
        assert result["total_lines"] > 0
        assert result["total_errors"] >= 1
        assert result["assertion_failures"] >= 1

    def test_parse_compilation_errors(self):
        """Test parsing compilation errors."""
        log_content = """
        Error: fifo.sv:45: syntax error near "endmodule"
        Error: fifo.sv:50: undefined variable "count"
        """
        
        result = self.analyzer.parse_log(log_content)
        
        assert result["total_errors"] >= 2
        assert result["errors"][0]["category"] == "compile"

    def test_parse_uvm_log(self):
        """Test parsing UVM log."""
        log_content = """
        UVM_INFO @ 0: reporter [RNTST] Running test basic_test...
        UVM_ERROR @ 100: driver [DRVERR] Transaction failed
        UVM_FATAL @ 200: scoreboard [SCBDFATAL] Comparison failed
        """
        
        result = self.analyzer.parse_log(log_content)
        
        assert result["uvm_errors"] >= 2

    def test_first_failure_detection(self):
        """Test first failure detection."""
        log_content = """
        [INFO] Starting...
        [WARNING] Minor issue
        [ERROR] First real error
        [ERROR] Second error
        """
        
        result = self.analyzer.parse_log(log_content)
        
        first_failure = result["first_failure"]
        assert "First real error" in first_failure.get("message", "")
        # The error doesn't contain compilation-specific keywords, so it's categorized as general
        assert first_failure.get("category") == "general"

    def test_failure_clustering(self):
        """Test failure clustering."""
        log_content = """
        [ERROR] Assertion failed in module_a.assert_1
        [ERROR] Assertion failed in module_a.assert_1
        [ERROR] Assertion failed in module_b.assert_2
        """
        
        result = self.analyzer.parse_log(log_content)
        
        clusters = result["failure_clusters"]
        assert len(clusters) >= 1
        # Should cluster similar errors
        assert any(c["count"] >= 2 for c in clusters)

    def test_root_cause_analysis(self):
        """Test root cause analysis."""
        log_content = """
        [ERROR] Assertion failed in fifo_sync.a_no_write_when_full at fifo.sv:45
        """
        
        result = self.analyzer.parse_log(log_content)
        
        root_cause = result["root_cause_analysis"]
        assert "likely_cause" in root_cause
        assert "affected_module" in root_cause
        assert "suggested_investigation" in root_cause
        assert root_cause["confidence"] in ["low", "medium", "high"]

    def test_severity_detection(self):
        """Test severity level detection."""
        test_cases = [
            ("FATAL: Simulation crashed", "FATAL"),
            ("Error: Compilation failed", "ERROR"),
            ("Assertion failed at line 10", "ERROR"),
            ("Warning: Unused signal", "WARNING"),
            ("Note: Compilation successful", "INFO"),
        ]
        
        for message, expected_severity in test_cases:
            severity = self.analyzer._detect_severity(message)
            assert severity == expected_severity, f"Failed for: {message}"

    def test_empty_log(self):
        """Test parsing empty log."""
        result = self.analyzer.parse_log("")
        
        assert result["total_lines"] == 1  # empty string splits to [""]
        assert result["total_errors"] == 0
        assert result["total_warnings"] == 0

    def test_compilation_error_parsing(self):
        """Test specific compilation error parsing."""
        log_content = """
        Error: fifo.sv:45: syntax error near "endmodule"
        Syntax error at line 50
        Undefined variable "count"
        """
        
        errors = self.analyzer.parse_compilation_errors(log_content)
        
        assert len(errors) >= 2
        assert any(e["type"] == "sv" for e in errors)
        assert any(e["type"] == "syntax" for e in errors)
        assert any(e["type"] == "undefined" for e in errors)


class TestCoverageAnalyzer:
    """Test Coverage Analyzer."""

    def setup_method(self):
        self.analyzer = CoverageAnalyzer()

    def test_parse_verilator_coverage(self):
        """Test parsing Verilator coverage output."""
        coverage_report = """
        Lines     150/200 (75.00%)
        Branches  80/100 (80.00%)
        Toggles   200/300 (66.67%)
        """
        
        coverage = self.analyzer.parse_verilator_coverage(coverage_report)
        
        assert coverage["line"].overall == 75.0
        assert coverage["line"].covered == 150
        assert coverage["line"].total == 200
        
        assert coverage["branch"].overall == 80.0
        assert coverage["branch"].covered == 80
        assert coverage["branch"].total == 100
        
        assert coverage["toggle"].overall == 66.67
        assert coverage["toggle"].covered == 200
        assert coverage["toggle"].total == 300

    def test_parse_ucov_report(self):
        """Test parsing generic coverage report."""
        coverage_report = """
        Overall coverage = 85.5%
        Line coverage: 90.0%
        Branch coverage: 75.0%
        """
        
        coverage = self.analyzer.parse_ucov_report(coverage_report)
        
        assert coverage["line"].overall == 90.0
        assert coverage["branch"].overall == 75.0

    def test_identify_gaps(self):
        """Test gap identification."""
        coverage = {
            "line": CoverageData(report_type="line", overall=75.0, covered=150, total=200),
            "branch": CoverageData(report_type="branch", overall=80.0, covered=80, total=100),
        }
        
        gaps = self.analyzer.identify_gaps(coverage, "", "test_module")
        
        assert len(gaps) >= 2
        
        gap_types = [g["gap_type"] for g in gaps]
        assert "reachable_untested" in gap_types or "potentially_unreachable" in gap_types

    def test_classify_gap(self):
        """Test gap classification."""
        # Test error-related gap -> potentially_unreachable
        error_gap = {"description": "Uncovered error handling path", "conditions": []}
        gap_type = self.analyzer._classify_gap(error_gap, "")
        assert gap_type == "potentially_unreachable"

        # Test complex conditions -> potentially_unreachable
        complex_gap = {"description": "Some branch", "conditions": ["a", "b", "c", "d", "e"]}
        gap_type = self.analyzer._classify_gap(complex_gap, "")
        assert gap_type == "potentially_unreachable"

        # Test normal gap -> reachable_untested
        normal_gap = {"description": "Normal branch", "conditions": ["a", "b"]}
        gap_type = self.analyzer._classify_gap(normal_gap, "")
        assert gap_type == "reachable_untested"

    def test_compare_coverage(self):
        """Test coverage comparison."""
        before = {
            "line": CoverageData(report_type="line", overall=70.0, covered=70, total=100),
            "branch": CoverageData(report_type="branch", overall=60.0, covered=60, total=100),
        }
        
        after = {
            "line": CoverageData(report_type="line", overall=80.0, covered=80, total=100),
            "branch": CoverageData(report_type="branch", overall=65.0, covered=65, total=100),
        }
        
        comparison = self.analyzer.compare_coverage(before, after)
        
        assert comparison["line"]["delta"] == 10.0
        assert comparison["line"]["improved"] is True
        assert comparison["branch"]["delta"] == 5.0
        assert comparison["branch"]["improved"] is True

    def test_generate_coverage_report(self):
        """Test coverage report generation."""
        coverage = {
            "line": CoverageData(report_type="line", overall=75.0, covered=150, total=200),
            "branch": CoverageData(report_type="branch", overall=80.0, covered=80, total=100),
        }
        
        gaps = [
            {"gap_type": "reachable_untested", "coverage_type": "line"},
            {"gap_type": "potentially_unreachable", "coverage_type": "branch"},
        ]
        
        report = self.analyzer.generate_coverage_report(coverage, gaps, "test_module")
        
        assert report["module"] == "test_module"
        assert report["overall_coverage"] > 0
        assert report["total_gaps"] == 2
        assert report["gap_summary"]["reachable_untested"] == 1
        assert report["gap_summary"]["potentially_unreachable"] == 1
        assert "closure_estimate" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])