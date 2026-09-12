"""Tests for RTL Analyzer."""

import pytest
from app.engines.rtl import RTLAnalyzer, DesignModule, SignalDirection, SignalType


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

SIMPLE_FSM_RTL = """
module traffic_light (
    input  logic clk,
    input  logic reset,
    input  logic sensor,
    output logic [1:0] light
);

    typedef enum logic [1:0] {
        GREEN  = 2'b00,
        YELLOW = 2'b01,
        RED    = 2'b10
    } state_t;

    state_t current_state, next_state;

    always_ff @(posedge clk or posedge reset) begin
        if (reset) current_state <= GREEN;
        else current_state <= next_state;
    end

    always_comb begin
        case (current_state)
            GREEN:  next_state = sensor ? GREEN : YELLOW;
            YELLOW: next_state = RED;
            RED:    next_state = GREEN;
            default: next_state = GREEN;
        endcase
    end

    always_comb begin
        case (current_state)
            GREEN:  light = 2'b00;
            YELLOW: light = 2'b01;
            RED:    light = 2'b10;
            default: light = 2'b00;
        endcase
    end

endmodule
"""


class TestRTLAnalyzer:
    """Test RTL Analyzer functionality."""

    def test_parse_fifo_module(self):
        """Test parsing a FIFO module."""
        analyzer = RTLAnalyzer()
        modules = analyzer.analyze(FIFO_RTL, "fifo.sv")

        assert len(modules) == 1
        module = modules[0]
        assert module.name == "fifo_sync"
        assert module.module_type.value == "module"

    def test_extract_parameters(self):
        """Test parameter extraction."""
        analyzer = RTLAnalyzer()
        modules = analyzer.analyze(FIFO_RTL, "fifo.sv")
        module = modules[0]

        params = {p.name: p.default_value for p in module.parameters}
        assert "DEPTH" in params
        assert "DATA_WIDTH" in params
        assert params["DEPTH"] == "16"
        assert params["DATA_WIDTH"] == "32"

    def test_extract_ports(self):
        """Test port extraction."""
        analyzer = RTLAnalyzer()
        modules = analyzer.analyze(FIFO_RTL, "fifo.sv")
        module = modules[0]

        port_names = [p.name for p in module.ports]
        assert "clk" in port_names
        assert "reset" in port_names
        assert "wr_en" in port_names
        assert "rd_en" in port_names
        assert "din" in port_names
        assert "dout" in port_names
        assert "full" in port_names
        assert "empty" in port_names
        assert "count" in port_names

        # Check directions
        clk_port = next(p for p in module.ports if p.name == "clk")
        assert clk_port.direction == SignalDirection.INPUT

        dout_port = next(p for p in module.ports if p.name == "dout")
        assert dout_port.direction == SignalDirection.OUTPUT

    def test_detect_clocks(self):
        """Test clock signal detection."""
        analyzer = RTLAnalyzer()
        modules = analyzer.analyze(FIFO_RTL, "fifo.sv")
        module = modules[0]

        clocks = module.clock_signals
        assert "clk" in clocks

    def test_detect_resets(self):
        """Test reset signal detection."""
        analyzer = RTLAnalyzer()
        modules = analyzer.analyze(FIFO_RTL, "fifo.sv")
        module = modules[0]

        resets = module.reset_signals
        assert "reset" in resets

    def test_detect_fsm(self):
        """Test FSM detection."""
        analyzer = RTLAnalyzer()
        modules = analyzer.analyze(SIMPLE_FSM_RTL, "fsm.sv")
        module = modules[0]

        assert module.has_fsm
        assert len(module.fsm_info) >= 1
        fsm = module.fsm_info[0]
        assert len(fsm.states) >= 3  # GREEN, YELLOW, RED
        assert fsm.state_variable == "current_state"

    def test_detect_assertions(self):
        """Test assertion detection."""
        analyzer = RTLAnalyzer()
        modules = analyzer.analyze(FIFO_RTL, "fifo.sv")
        module = modules[0]

        assert module.has_assertions
        assert len(module.assertions) >= 2
        assertion_names = [a["name"] for a in module.assertions]
        assert "p_no_write_when_full" in " ".join(assertion_names) or "a_no_write_when_full" in " ".join(assertion_names)

    def test_summary_generation(self):
        """Test design summary generation."""
        analyzer = RTLAnalyzer()
        modules = analyzer.analyze(FIFO_RTL, "fifo.sv")
        summary = analyzer.get_summary()

        assert summary["num_modules"] == 1
        assert "fifo_sync" in summary["module_names"]
        assert summary["total_ports"] > 0
        assert "clk" in summary["clock_signals"]
        assert "reset" in summary["reset_signals"]

    def test_fifo_detection(self):
        """Test FIFO candidate detection."""
        analyzer = RTLAnalyzer()
        modules = analyzer.analyze(FIFO_RTL, "fifo.sv")
        module = modules[0]

        assert module.metadata.get("is_fifo") is True
        assert "fifo_candidates" in module.metadata

    def test_protocol_detection(self):
        """Test handshake protocol detection."""
        handshake_rtl = """
        module handshake_dut (
            input logic clk,
            input logic reset,
            input logic valid,
            input logic [7:0] data,
            output logic ready
        );
        endmodule
        """
        analyzer = RTLAnalyzer()
        modules = analyzer.analyze(handshake_rtl, "handshake.sv")
        module = modules[0]

        assert module.metadata.get("protocol") == "valid_ready_handshake"

    def test_empty_rtl(self):
        """Test handling of empty RTL."""
        analyzer = RTLAnalyzer()
        modules = analyzer.analyze("", "empty.sv")
        assert len(modules) == 0

    def test_invalid_rtl(self):
        """Test handling of invalid RTL."""
        analyzer = RTLAnalyzer()
        modules = analyzer.analyze("this is not valid rtl", "invalid.sv")
        # Should not crash, just return empty
        assert len(modules) == 0


class TestRTLAnalyzerEdgeCases:
    """Test edge cases for RTL Analyzer."""

    def test_parameterized_module(self):
        """Test module with complex parameters."""
        rtl = """
        module complex #(
            parameter int WIDTH = 32,
            parameter int DEPTH = 16,
            parameter string NAME = "default"
        ) (
            input logic clk,
            input logic [WIDTH-1:0] data_in,
            output logic [WIDTH-1:0] data_out
        );
        endmodule
        """
        analyzer = RTLAnalyzer()
        modules = analyzer.analyze(rtl, "complex.sv")
        assert len(modules) == 1
        params = {p.name: p.default_value for p in modules[0].parameters}
        assert params["WIDTH"] == "32"
        assert params["DEPTH"] == "16"

    def test_multiple_modules(self):
        """Test parsing multiple modules."""
        rtl = """
        module sub (input logic clk, output logic out); endmodule
        module top (input logic clk, output logic out); sub u_sub (.clk(clk), .out(out)); endmodule
        """
        analyzer = RTLAnalyzer()
        modules = analyzer.analyze(rtl, "multi.sv")
        assert len(modules) == 2
        names = [m.name for m in modules]
        assert "sub" in names
        assert "top" in names

    def test_interface_parsing(self):
        """Test interface parsing."""
        rtl = """
        interface simple_if (input logic clk);
            logic valid;
            logic ready;
        endinterface
        """
        analyzer = RTLAnalyzer()
        modules = analyzer.analyze(rtl, "interface.sv")
        assert len(modules) == 1
        assert modules[0].module_type.value == "interface"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])