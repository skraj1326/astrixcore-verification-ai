"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestHealthEndpoints:
    """Test health and root endpoints."""

    def test_health_endpoint(self):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "AstrixCore Verification AI"
        assert "endpoints" in data

    def test_docs_endpoint(self):
        """Test docs endpoint exists."""
        response = client.get("/docs")
        assert response.status_code == 200


class TestProjectEndpoints:
    """Test project management endpoints."""

    def test_create_project(self):
        """Test project creation."""
        response = client.post("/api/v1/projects/", json={
            "name": "Test Project",
            "description": "A test project"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["description"] == "A test project"
        assert data["status"] == "active"
        assert "id" in data

    def test_list_projects(self):
        """Test listing projects."""
        response = client.get("/api/v1/projects/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_project(self):
        """Test getting a specific project."""
        # First create a project
        create_resp = client.post("/api/v1/projects/", json={"name": "Test Get"})
        project_id = create_resp.json()["id"]
        
        response = client.get(f"/api/v1/projects/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["name"] == "Test Get"

    def test_get_nonexistent_project(self):
        """Test getting non-existent project."""
        import uuid
        response = client.get(f"/api/v1/projects/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_delete_project(self):
        """Test deleting a project."""
        create_resp = client.post("/api/v1/projects/", json={"name": "Test Delete"})
        project_id = create_resp.json()["id"]
        
        response = client.delete(f"/api/v1/projects/{project_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"
        
        # Verify deleted
        get_resp = client.get(f"/api/v1/projects/{project_id}")
        assert get_resp.status_code == 404


class TestRTLEndpoints:
    """Test RTL analysis endpoints."""

    def test_analyze_rtl(self):
        """Test RTL analysis."""
        fifo_rtl = """
        module test_fifo (
            input logic clk,
            input logic reset,
            input logic wr_en,
            input logic [7:0] din,
            output logic [7:0] dout,
            output logic full
        );
        endmodule
        """
        
        response = client.post("/api/v1/rtl/analyze", json={
            "content": fifo_rtl,
            "filename": "test_fifo.sv"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test_fifo.sv"
        assert len(data["modules"]) == 1
        assert data["modules"][0]["name"] == "test_fifo"
        assert "summary" in data

    def test_analyze_invalid_rtl(self):
        """Test analysis of invalid RTL."""
        response = client.post("/api/v1/rtl/analyze", json={
            "content": "not valid rtl",
            "filename": "invalid.sv"
        })
        
        assert response.status_code == 400
        assert "No modules found" in response.json()["detail"]

    def test_get_fifo_example(self):
        """Test getting FIFO example."""
        response = client.get("/api/v1/rtl/examples/fifo")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "fifo_sync" in data["content"]


class TestVerificationEndpoints:
    """Test verification endpoints."""

    def test_generate_verification_plan(self):
        """Test verification plan generation."""
        fifo_rtl = """
        module test_fifo (
            input logic clk,
            input logic reset,
            input logic wr_en,
            input logic [7:0] din,
            output logic [7:0] dout,
            output logic full
        );
        endmodule
        """
        
        response = client.post("/api/v1/verification/plan", json={
            "rtl_content": fifo_rtl,
            "specification": ""
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "plan" in data
        assert "summary" in data
        assert "traceability" in data
        assert data["summary"]["total_items"] > 0

    def test_generate_assertions(self):
        """Test assertion generation."""
        fifo_rtl = """
        module test_fifo (
            input logic clk,
            input logic reset,
            input logic wr_en,
            input logic [7:0] din,
            output logic [7:0] dout,
            output logic full,
            output logic empty
        );
        endmodule
        """
        
        response = client.post("/api/v1/verification/assertions", json={
            "rtl_content": fifo_rtl
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "assertions" in data
        assert data["total_generated"] > 0
        assert len(data["assertions"]) > 0

    def test_generate_tests(self):
        """Test test generation."""
        fifo_rtl = """
        module test_fifo (
            input logic clk,
            input logic reset,
            input logic wr_en,
            input logic rd_en,
            input logic [7:0] din,
            output logic [7:0] dout,
            output logic full,
            output logic empty
        );
        endmodule
        """
        
        response = client.post("/api/v1/verification/tests", json={
            "rtl_content": fifo_rtl
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "tests" in data
        assert data["total_generated"] > 0
        assert len(data["tests"]) > 0

    def test_generate_uvm(self):
        """Test UVM generation."""
        fifo_rtl = """
        module test_fifo (
            input logic clk,
            input logic reset,
            input logic wr_en,
            input logic [7:0] din,
            output logic [7:0] dout
        );
        endmodule
        """
        
        response = client.post("/api/v1/verification/uvm", json={
            "rtl_content": fifo_rtl
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "uvm_components" in data
        assert data["total_generated"] > 0

    def test_full_verification_flow(self):
        """Test full verification flow."""
        fifo_rtl = """
        module test_fifo (
            input logic clk,
            input logic reset,
            input logic wr_en,
            input logic rd_en,
            input logic [7:0] din,
            output logic [7:0] dout,
            output logic full,
            output logic empty
        );
        endmodule
        """
        
        response = client.post("/api/v1/verification/full-flow", json={
            "rtl_content": fifo_rtl,
            "specification": ""
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "verification_plan" in data
        assert "assertions" in data
        assert "tests" in data
        assert "uvm" in data


class TestSimulationEndpoints:
    """Test simulation endpoints."""

    def test_compile_rtl(self):
        """Test RTL compilation."""
        fifo_rtl = """
        module test_fifo (
            input logic clk,
            input logic reset,
            input logic wr_en,
            input logic [7:0] din,
            output logic [7:0] dout,
            output logic full
        );
        endmodule
        
        module tb_test_fifo;
            logic clk, reset, wr_en;
            logic [7:0] din, dout;
            logic full;
            
            test_fifo uut (.clk(clk), .reset(reset), .wr_en(wr_en), .din(din), .dout(dout), .full(full));
            
            initial begin
                clk = 0;
                forever #5 clk = ~clk;
            end
            
            initial begin
                reset = 1; wr_en = 0; din = 0;
                #20 reset = 0;
                #20 wr_en = 1; din = 8'hAA;
                #20 wr_en = 0;
                #20 $finish;
            end
        endmodule
        """
        
        response = client.post("/api/v1/simulation/compile", json={
            "rtl_files": [fifo_rtl],
            "testbench": "",
            "top_module": "tb_test_fifo",
            "simulator": "verilator",
            "timeout": 60
        })
        
        # Should either succeed or return UNAVAILABLE if verilator not installed
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "status" in data

    def test_run_simulation(self):
        """Test running simulation."""
        fifo_rtl = """
        module test_fifo (
            input logic clk,
            input logic reset,
            input logic wr_en,
            input logic [7:0] din,
            output logic [7:0] dout,
            output logic full
        );
        endmodule
        """
        
        test_code = """
        module tb_test_fifo;
            logic clk, reset, wr_en;
            logic [7:0] din, dout;
            logic full;
            
            test_fifo uut (.clk(clk), .reset(reset), .wr_en(wr_en), .din(din), .dout(dout), .full(full));
            
            initial begin
                clk = 0;
                forever #5 clk = ~clk;
            end
            
            initial begin
                reset = 1; wr_en = 0; din = 0;
                #20 reset = 0;
                #20 wr_en = 1; din = 8'hAA;
                #20 wr_en = 0;
                #20 $finish;
            end
        endmodule
        """
        
        response = client.post("/api/v1/simulation/run", json={
            "rtl_content": fifo_rtl,
            "test_code": test_code,
            "top_module": "tb_test_fifo",
            "simulator": "verilator",
            "timeout": 60
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "status" in data

    def test_analyze_log(self):
        """Test log analysis."""
        log_content = """
        [INFO] Starting simulation
        [ERROR] Assertion failed in test_module.assert_1
        [INFO] Simulation completed
        """
        
        response = client.post("/api/v1/simulation/analyze-log", json={
            "log_content": log_content,
            "log_type": "simulation"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "log_type" in data
        assert data["total_errors"] >= 1


class TestCoverageEndpoints:
    """Test coverage endpoints."""

    def test_analyze_coverage(self):
        """Test coverage analysis."""
        coverage_report = """
        Lines     150/200 (75.00%)
        Branches  80/100 (80.00%)
        Toggles   200/300 (66.67%)
        """
        
        response = client.post("/api/v1/coverage/analyze", json={
            "coverage_report": coverage_report,
            "rtl_content": "",
            "module_name": "test_module"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "report" in data
        assert "coverage" in data
        assert "gaps" in data

    def test_identify_gaps(self):
        """Test gap identification."""
        coverage_report = """
        Lines     150/200 (75.00%)
        """
        
        response = client.post("/api/v1/coverage/gaps", json={
            "coverage_report": coverage_report,
            "rtl_content": "",
            "module_name": "test_module"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "total_gaps" in data
        assert "gaps" in data


class TestFailureEndpoints:
    """Test failure analysis endpoints."""

    def test_analyze_failure(self):
        """Test failure analysis."""
        response = client.post("/api/v1/failures/analyze", json={
            "failure_info": {
                "error": "Assertion failed",
                "location": "fifo.sv:45",
                "severity": "ERROR"
            },
            "rtl_content": "",
            "log_analysis": {}
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "failure_id" in data
        assert "severity" in data


class TestTraceabilityEndpoints:
    """Test traceability endpoints."""

    def test_create_traceability_link(self):
        """Test creating traceability link."""
        response = client.post("/api/v1/traceability/link", json={
            "requirement_id": "REQ-001",
            "artifact_type": "verification_plan",
            "artifact_id": "VP-001"
        })
        
        assert response.status_code == 200
        assert response.json()["status"] == "linked"

    def test_get_traceability(self):
        """Test getting traceability."""
        # First create a link
        client.post("/api/v1/traceability/link", json={
            "requirement_id": "REQ-002",
            "artifact_type": "test",
            "artifact_id": "TEST-001"
        })
        
        response = client.get("/api/v1/traceability/REQ-002")
        assert response.status_code == 200
        data = response.json()
        assert data["requirement_id"] == "REQ-002"
        assert "tests" in data

    def test_get_all_traceability(self):
        """Test getting all traceability."""
        response = client.get("/api/v1/traceability/")
        assert response.status_code == 200
        data = response.json()
        assert "requirements" in data
        assert "summary" in data


class TestRegressionEndpoints:
    """Test regression endpoints."""

    def test_run_regression(self):
        """Test regression run (will likely fail without verilator)."""
        fifo_rtl = """
        module test_fifo (
            input logic clk,
            input logic reset,
            output logic full
        );
        endmodule
        """
        
        response = client.post("/api/v1/regression/run", json={
            "rtl_files": [fifo_rtl],
            "test_files": [],
            "top_module": "tb_test_fifo",
            "simulator": "verilator"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "passed" in data
        assert "failed" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])