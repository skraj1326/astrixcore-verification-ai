"""Tests for Verification Planner, Assertion Generator, and Test Generator."""

import pytest
from app.engines.rtl import RTLAnalyzer
from app.engines.verification_planner import VerificationPlanGenerator
from app.engines.assertion_generator import AssertionGenerator
from app.engines.test_generator import TestGenerator


FIFO_RTL = """
module fifo_sync #(
    parameter int DEPTH = 16,
    parameter int DATA_WIDTH = 32
) (
    input  logic                  clk,
    input  logic                  reset,
    input  logic                  wr_en,
    input  logic                  rd_en,
    input  logic [DATA_WIDTH-1:0] din,
    output logic [DATA_WIDTH-1:0] dout,
    output logic                  full,
    output logic                  empty,
    output logic [$clog2(DEPTH):0] count
);

    logic [DATA_WIDTH-1:0] mem [0:DEPTH-1];
    logic [$clog2(DEPTH):0] wr_ptr, rd_ptr;

    always_ff @(posedge clk) begin
        if (reset) begin
            wr_ptr <= 0;
            rd_ptr <= 0;
        end else begin
            if (wr_en && !full) wr_ptr <= wr_ptr + 1;
            if (rd_en && !empty) rd_ptr <= rd_ptr + 1;
        end
    end

    property p_no_write_when_full;
        @(posedge clk) disable iff (reset) full |-> !wr_en;
    endproperty
    a_no_write_when_full: assert property (p_no_write_when_full);

    property p_no_read_when_empty;
        @(posedge clk) disable iff (reset) empty |-> !rd_en;
    endproperty
    a_no_read_when_empty: assert property (p_no_read_when_empty);

endmodule
"""


class TestVerificationPlanner:
    """Test Verification Plan Generator."""

    def setup_method(self):
        self.analyzer = RTLAnalyzer()
        self.modules = self.analyzer.analyze(FIFO_RTL, "fifo.sv")
        self.planner = VerificationPlanGenerator()

    def test_generate_plan(self):
        """Test basic plan generation."""
        plan = self.planner.generate(self.modules)
        
        assert "items" in plan
        assert "summary" in plan
        assert "traceability" in plan
        assert len(plan["items"]) > 0

    def test_plan_has_fifo_items(self):
        """Test that FIFO-specific items are generated."""
        plan = self.planner.generate(self.modules)
        
        # Check for FIFO-related items
        item_ids = [item["id"] for item in plan["items"]]
        fifo_items = [id for id in item_ids if "FIFO" in id or "fifo" in id.lower()]
        assert len(fifo_items) > 0

    def test_plan_has_reset_items(self):
        """Test that reset items are generated."""
        plan = self.planner.generate(self.modules)
        
        item_ids = [item["id"] for item in plan["items"]]
        reset_items = [id for id in item_ids if "RST" in id or "reset" in id.lower()]
        assert len(reset_items) > 0

    def test_plan_has_clock_items(self):
        """Test that clock items are generated."""
        plan = self.planner.generate(self.modules)
        
        item_ids = [item["id"] for item in plan["items"]]
        clock_items = [id for id in item_ids if "CLK" in id or "clock" in id.lower()]
        assert len(clock_items) > 0

    def test_plan_items_have_required_fields(self):
        """Test that all plan items have required fields."""
        plan = self.planner.generate(self.modules)
        
        required_fields = ["id", "feature", "requirement", "stimulus", 
                          "expected_behavior", "assertion_candidate", 
                          "coverage_goal", "priority", "confidence", "evidence", "source_type"]
        
        for item in plan["items"]:
            for field in required_fields:
                assert field in item, f"Missing field {field} in item {item.get('id', 'unknown')}"

    def test_plan_source_types(self):
        """Test that items have valid source types."""
        plan = self.planner.generate(self.modules)
        
        valid_sources = {"rtl-derived", "spec-derived", "ai-inferred"}
        for item in plan["items"]:
            assert item["source_type"] in valid_sources

    def test_plan_priorities(self):
        """Test that priorities are valid."""
        plan = self.planner.generate(self.modules)
        
        for item in plan["items"]:
            assert 1 <= item["priority"] <= 10

    def test_plan_summary(self):
        """Test plan summary generation."""
        plan = self.planner.generate(self.modules)
        summary = plan["summary"]
        
        assert "total_items" in summary
        assert "categories" in summary
        assert "source_breakdown" in summary
        assert summary["total_items"] == len(plan["items"])
        assert summary["modules_analyzed"] == 1

    def test_traceability_matrix(self):
        """Test traceability matrix generation."""
        plan = self.planner.generate(self.modules)
        traceability = plan["traceability"]
        
        assert "module_to_items" in traceability
        assert "category_to_items" in traceability
        assert "source_to_items" in traceability


class TestAssertionGenerator:
    """Test Assertion Generator."""

    def setup_method(self):
        self.analyzer = RTLAnalyzer()
        self.modules = self.analyzer.analyze(FIFO_RTL, "fifo.sv")
        self.generator = AssertionGenerator()

    def test_generate_assertions(self):
        """Test basic assertion generation."""
        assertions = self.generator.generate(self.modules)
        
        assert len(assertions) > 0

    def test_assertions_have_required_fields(self):
        """Test that all assertions have required fields."""
        assertions = self.generator.generate(self.modules)
        
        required_fields = ["name", "description", "sva_code", "assertion_type", 
                          "confidence", "evidence", "assumptions", 
                          "validation_status", "classification"]
        
        for assertion in assertions:
            for field in required_fields:
                assert field in assertion, f"Missing field {field} in assertion {assertion.get('name', 'unknown')}"

    def test_fifo_assertions_generated(self):
        """Test that FIFO-specific assertions are generated."""
        assertions = self.generator.generate(self.modules)
        
        assertion_names = [a["name"] for a in assertions]
        # Should have no_write_when_full, no_read_when_empty, pointer progress, count tracking, full_empty_mutex
        fifo_assertions = [n for n in assertion_names if "fifo" in n.lower() or "full" in n.lower() or "empty" in n.lower() or "ptr" in n.lower() or "count" in n.lower()]
        assert len(fifo_assertions) >= 4

    def test_reset_assertions_generated(self):
        """Test that reset assertions are generated."""
        assertions = self.generator.generate(self.modules)
        
        assertion_names = [a["name"] for a in assertions]
        reset_assertions = [n for n in assertion_names if "reset" in n.lower()]
        assert len(reset_assertions) >= 1

    def test_confidence_levels(self):
        """Test that confidence levels are valid."""
        assertions = self.generator.generate(self.modules)
        
        valid_confidences = {"low", "medium", "high", "very_high"}
        for assertion in assertions:
            assert assertion["confidence"] in valid_confidences

    def test_assertion_types(self):
        """Test that assertion types are valid."""
        assertions = self.generator.generate(self.modules)
        
        valid_types = {"concurrent", "immediate", "cover", "assume"}
        for assertion in assertions:
            # The generated assertions should be concurrent or cover
            assert assertion["assertion_type"] in valid_types

    def test_validation_status(self):
        """Test that validation status is set correctly."""
        assertions = self.generator.generate(self.modules)
        
        for assertion in assertions:
            assert assertion["validation_status"] == "REQUIRES ENGINEER VALIDATION"
            assert assertion["classification"] == "GENERATED"

    def test_sva_code_syntax(self):
        """Test that SVA code has basic SystemVerilog syntax."""
        assertions = self.generator.generate(self.modules)
        
        for assertion in assertions:
            code = assertion["sva_code"]
            assert "property" in code or "cover" in code
            assert "assert property" in code or "cover property" in code
            assert "endproperty" in code


class TestTestGenerator:
    """Test Test Generator."""

    def setup_method(self):
        self.analyzer = RTLAnalyzer()
        self.modules = self.analyzer.analyze(FIFO_RTL, "fifo.sv")
        self.generator = TestGenerator()

    def test_generate_tests(self):
        """Test basic test generation."""
        tests = self.generator.generate(self.modules)
        
        assert len(tests) > 0

    def test_tests_have_required_fields(self):
        """Test that all tests have required fields."""
        tests = self.generator.generate(self.modules)
        
        required_fields = ["name", "test_type", "code", "verification_objective", 
                          "target_coverage", "target_signals"]
        
        for test in tests:
            for field in required_fields:
                assert field in test, f"Missing field {field} in test {test.get('name', 'unknown')}"

    def test_directed_tests_generated(self):
        """Test that directed tests are generated."""
        tests = self.generator.generate(self.modules)
        
        directed_tests = [t for t in tests if t["test_type"] == "directed"]
        assert len(directed_tests) >= 4  # basic, reset, port_sweep, fifo

    def test_constrained_random_tests_generated(self):
        """Test that constrained random tests are generated."""
        tests = self.generator.generate(self.modules)
        
        random_tests = [t for t in tests if t["test_type"] == "constrained_random"]
        assert len(random_tests) >= 1

    def test_uvm_tests_generated(self):
        """Test that UVM components are generated."""
        tests = self.generator.generate(self.modules)
        
        uvm_tests = [t for t in tests if t["test_type"] in ["uvm_sequence_item", "uvm_sequence", "uvm_monitor"]]
        assert len(uvm_tests) >= 3

    def test_fifo_specific_tests(self):
        """Test that FIFO-specific tests are generated."""
        tests = self.generator.generate(self.modules)
        
        fifo_tests = [t for t in tests if "fifo" in t["name"].lower()]
        assert len(fifo_tests) >= 1

    def test_reset_test_generated(self):
        """Test that reset test is generated."""
        tests = self.generator.generate(self.modules)
        
        reset_tests = [t for t in tests if "reset" in t["name"].lower()]
        assert len(reset_tests) >= 1

    def test_test_code_has_module(self):
        """Test that test code contains module or class declaration."""
        tests = self.generator.generate(self.modules)
        
        for test in tests:
            code = test["code"]
            # UVM sequence items are classes, other tests are modules
            if test["test_type"] in {"uvm_sequence_item", "uvm_sequence", "uvm_monitor"}:
                assert "class " in code
                assert "endclass" in code
            else:
                assert "module " in code
                assert "endmodule" in code

    def test_test_types_valid(self):
        """Test that test types are valid."""
        tests = self.generator.generate(self.modules)
        
        valid_types = {"directed", "constrained_random", "uvm_sequence_item", "uvm_sequence", "uvm_monitor", "coverage_targeted"}
        for test in tests:
            assert test["test_type"] in valid_types

    def test_coverage_targeted_tests(self):
        """Test coverage-targeted test generation."""
        coverage_gaps = [{
            "gap_type": "reachable_untested",
            "description": "Uncovered branch in FIFO full logic",
            "rtl_location": {"module": "fifo_sync", "line": 45},
        }]
        
        tests = self.generator.generate(self.modules, coverage_gaps)
        
        targeted_tests = [t for t in tests if t["test_type"] == "coverage_targeted"]
        assert len(targeted_tests) >= 1


class TestGeneratorIntegration:
    """Integration tests for all generators together."""

    def setup_method(self):
        self.analyzer = RTLAnalyzer()
        self.modules = self.analyzer.analyze(FIFO_RTL, "fifo.sv")

    def test_full_flow_consistency(self):
        """Test that all generators produce consistent output for same RTL."""
        planner = VerificationPlanGenerator()
        assertion_gen = AssertionGenerator()
        test_gen = TestGenerator()

        plan = planner.generate(self.modules)
        assertions = assertion_gen.generate(self.modules)
        tests = test_gen.generate(self.modules)

        # All should have items
        assert len(plan["items"]) > 0
        assert len(assertions) > 0
        assert len(tests) > 0

        # Plan should cover reset, FIFO, clock
        plan_features = [item["feature"] for item in plan["items"]]
        assert any("FIFO" in f or "fifo" in f.lower() for f in plan_features)
        assert any("Reset" in f or "reset" in f.lower() for f in plan_features)

        # Assertions should cover FIFO properties
        assertion_names = [a["name"] for a in assertions]
        assert any("full" in n.lower() for n in assertion_names)
        assert any("empty" in n.lower() for n in assertion_names)

        # Tests should cover basic, reset, FIFO
        test_names = [t["name"] for t in tests]
        assert any("basic" in n.lower() for n in test_names)
        assert any("reset" in n.lower() for n in test_names)
        assert any("fifo" in n.lower() for n in test_names)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])