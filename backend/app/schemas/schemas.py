"""Pydantic schemas for API request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TestType(str, Enum):
    DIRECTED = "directed"
    CONSTRAINED_RANDOM = "constrained_random"
    UVM_SEQUENCE = "uvm_sequence"
    UVM_TEST = "uvm_test"
    COVERAGE_TARGETED = "coverage_targeted"


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class SeverityLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


class FactClassification(str, Enum):
    FACT = "FACT"
    INFERENCE = "INFERENCE"
    HYPOTHESIS = "HYPOTHESIS"
    GENERATED = "GENERATED"
    TOOL_RESULT = "TOOL_RESULT"


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = ""


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    status: str
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        orm_mode = True


class RTLFileUpload(BaseModel):
    filename: str
    content: str


class RTLAnalysisResponse(BaseModel):
    id: str
    project_id: str
    filename: str
    modules: List[Dict[str, Any]]
    ports: List[Dict[str, Any]]
    signals: List[Dict[str, Any]]
    parameters: List[Dict[str, Any]]
    clocks: List[Dict[str, Any]]
    resets: List[Dict[str, Any]]
    always_blocks: List[Dict[str, Any]]
    fsm_candidates: List[Dict[str, Any]]
    fifo_candidates: List[Dict[str, Any]]
    valid_ready_interfaces: List[Dict[str, Any]]
    counters: List[Dict[str, Any]]
    pointers: List[Dict[str, Any]]
    warnings: List[str]
    created_at: str
    completed_at: Optional[str] = None


class VerificationPlanItem(BaseModel):
    id: str
    feature: str
    requirement: str
    stimulus: str
    expected_behavior: str
    assertion_candidate: str
    coverage_goal: str
    priority: int
    confidence: ConfidenceLevel
    evidence: str
    source_type: str = "rtl-derived"


class VerificationPlanResponse(BaseModel):
    id: str
    project_id: str
    name: str
    items: List[VerificationPlanItem]
    status: str
    created_at: str


class AssertionResponse(BaseModel):
    id: str
    project_id: str
    name: str
    description: str
    sva_code: str
    assertion_type: str
    confidence: ConfidenceLevel
    evidence: str
    assumptions: str
    validation_status: str
    classification: str
    created_at: str


class GeneratedTestResponse(BaseModel):
    id: str
    project_id: str
    test_id: str
    objective: str
    stimulus: str
    expected_behavior: str
    coverage_target: List[str]
    source_requirement: str
    test_code: str
    test_type: str
    status: str
    created_at: str


class UVMComponentResponse(BaseModel):
    id: str
    project_id: str
    component_type: str
    name: str
    code: str
    validation_status: str
    created_at: str


class SimulationRequest(BaseModel):
    test_id: Optional[str] = None
    test_code: Optional[str] = None
    simulator: str = "verilator"
    timeout: int = 300


class SimulationRunResponse(BaseModel):
    id: str
    project_id: str
    test_id: Optional[str] = None
    simulator: str
    status: str
    command: str
    return_code: Optional[int] = None
    stdout: str
    stderr: str
    duration_seconds: Optional[float] = None
    artifacts: Dict[str, Any]
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class FailureResponse(BaseModel):
    id: str
    project_id: str
    failure_id: str
    severity: SeverityLevel
    error: str
    location: str
    observed_fact: str
    root_cause_hypothesis: str
    confidence: ConfidenceLevel
    evidence: List[str]
    recommended_action: str
    classification: str
    created_at: str


class CoverageReportResponse(BaseModel):
    id: str
    project_id: str
    simulation_run_id: Optional[str] = None
    report_type: str
    line_coverage: float
    branch_coverage: float
    toggle_coverage: float
    functional_coverage: float
    assertion_coverage: float
    overall_coverage: float
    details: Dict[str, Any]
    gaps: List[Dict[str, Any]]
    status: str
    created_at: str


class CoverageGapResponse(BaseModel):
    id: str
    project_id: str
    gap_id: str
    feature: str
    reason: str
    priority: int
    recommended_test: str
    related_requirement: str
    gap_type: str
    is_addressed: bool
    created_at: str


class TraceabilityResponse(BaseModel):
    requirement_id: str
    verification_plan_ids: List[str]
    assertion_ids: List[str]
    test_ids: List[str]
    simulation_ids: List[str]
    failure_ids: List[str]
    coverage_ids: List[str]


class RegressionRunResponse(BaseModel):
    id: str
    project_id: str
    name: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration_seconds: float
    failure_distribution: Dict[str, int]
    top_causes: List[Dict[str, Any]]
    coverage_delta: Dict[str, float]
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class FIFODemoResponse(BaseModel):
    rtl_code: str
    description: str
    features: List[str]
    parameters: Dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    version: str
    components: Dict[str, str]