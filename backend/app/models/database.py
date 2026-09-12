"""Database models for AstrixCore Verification AI."""

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime,
    ForeignKey, JSON, Enum, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class ProjectStatus(str, PyEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class AnalysisStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SeverityLevel(str, PyEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


class ConfidenceLevel(str, PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class TestStatus(str, PyEnum):
    GENERATED = "generated"
    COMPILED = "compiled"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"


class RTLFile(Base):
    __tablename__ = "rtl_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    language = Column(String(50), default="SystemVerilog")
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="rtl_files")


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    status = Column(Enum(ProjectStatus), default=ProjectStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    settings = Column(JSONB, default=dict)

    rtl_files = relationship("RTLFile", back_populates="project", cascade="all, delete-orphan")
    verification_plans = relationship("VerificationPlan", back_populates="project", cascade="all, delete-orphan")
    assertions = relationship("Assertion", back_populates="project", cascade="all, delete-orphan")
    generated_tests = relationship("GeneratedTest", back_populates="project", cascade="all, delete-orphan")
    simulation_runs = relationship("SimulationRun", back_populates="project", cascade="all, delete-orphan")
    failures = relationship("Failure", back_populates="project", cascade="all, delete-orphan")
    coverage_reports = relationship("CoverageReport", back_populates="project", cascade="all, delete-orphan")
    traceability_links = relationship("TraceabilityLink", back_populates="project", cascade="all, delete-orphan")
    ai_analyses = relationship("AIAnalysis", back_populates="project", cascade="all, delete-orphan")
    regression_runs = relationship("RegressionRun", back_populates="project", cascade="all, delete-orphan")


class RTLAnalysis(Base):
    __tablename__ = "rtl_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    rtl_file_id = Column(UUID(as_uuid=True), ForeignKey("rtl_files.id"), nullable=False)
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.PENDING)
    modules = Column(JSONB, default=list)
    ports = Column(JSONB, default=list)
    signals = Column(JSONB, default=list)
    parameters = Column(JSONB, default=list)
    clocks = Column(JSONB, default=list)
    resets = Column(JSONB, default=list)
    always_blocks = Column(JSONB, default=list)
    fsm_candidates = Column(JSONB, default=list)
    fifo_candidates = Column(JSONB, default=list)
    valid_ready_interfaces = Column(JSONB, default=list)
    counters = Column(JSONB, default=list)
    pointers = Column(JSONB, default=list)
    warnings = Column(JSONB, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


class VerificationPlan(Base):
    __tablename__ = "verification_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), default="Auto-generated Plan")
    items = Column(JSONB, default=list)
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="verification_plans")


class Assertion(Base):
    __tablename__ = "assertions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    verification_plan_id = Column(UUID(as_uuid=True), ForeignKey("verification_plans.id"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    sva_code = Column(Text, nullable=False)
    assertion_type = Column(String(50), default="concurrent")
    confidence = Column(Enum(ConfidenceLevel), default=ConfidenceLevel.MEDIUM)
    evidence = Column(Text, default="")
    assumptions = Column(Text, default="")
    validation_status = Column(String(50), default="REQUIRES ENGINEER VALIDATION")
    classification = Column(String(50), default="GENERATED")
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="assertions")


class GeneratedTest(Base):
    __tablename__ = "generated_tests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    verification_plan_id = Column(UUID(as_uuid=True), ForeignKey("verification_plans.id"), nullable=True)
    test_id = Column(String(100), nullable=False)
    objective = Column(Text, default="")
    stimulus = Column(Text, default="")
    expected_behavior = Column(Text, default="")
    coverage_target = Column(JSONB, default=list)
    source_requirement = Column(String(100), default="")
    test_code = Column(Text, nullable=False)
    test_type = Column(String(50), default="directed")
    status = Column(Enum(TestStatus), default=TestStatus.GENERATED)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="generated_tests")


class UVMComponent(Base):
    __tablename__ = "uvm_components"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    component_type = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(Text, nullable=False)
    validation_status = Column(String(50), default="REQUIRES ENGINEER VALIDATION")
    created_at = Column(DateTime, default=datetime.utcnow)


class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    test_id = Column(UUID(as_uuid=True), ForeignKey("generated_tests.id"), nullable=True)
    simulator = Column(String(50), default="verilator")
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.PENDING)
    command = Column(Text, default="")
    return_code = Column(Integer)
    stdout = Column(Text, default="")
    stderr = Column(Text, default="")
    duration_seconds = Column(Float)
    artifacts = Column(JSONB, default=dict)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    project = relationship("Project", back_populates="simulation_runs")


class Failure(Base):
    __tablename__ = "failures"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    simulation_run_id = Column(UUID(as_uuid=True), ForeignKey("simulation_runs.id"), nullable=True)
    test_id = Column(UUID(as_uuid=True), ForeignKey("generated_tests.id"), nullable=True)
    failure_id = Column(String(100), nullable=False)
    severity = Column(Enum(SeverityLevel), default=SeverityLevel.ERROR)
    error = Column(Text, default="")
    location = Column(String(500), default="")
    observed_fact = Column(Text, default="")
    root_cause_hypothesis = Column(Text, default="")
    confidence = Column(Enum(ConfidenceLevel), default=ConfidenceLevel.LOW)
    evidence = Column(JSONB, default=list)
    recommended_action = Column(Text, default="")
    classification = Column(String(50), default="HYPOTHESIS")
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="failures")


class CoverageReport(Base):
    __tablename__ = "coverage_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    simulation_run_id = Column(UUID(as_uuid=True), ForeignKey("simulation_runs.id"), nullable=True)
    report_type = Column(String(50), default="verilator")
    line_coverage = Column(Float, default=0.0)
    branch_coverage = Column(Float, default=0.0)
    toggle_coverage = Column(Float, default=0.0)
    functional_coverage = Column(Float, default=0.0)
    assertion_coverage = Column(Float, default=0.0)
    overall_coverage = Column(Float, default=0.0)
    details = Column(JSONB, default=dict)
    gaps = Column(JSONB, default=list)
    status = Column(String(50), default="NOT AVAILABLE")
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="coverage_reports")


class CoverageGap(Base):
    __tablename__ = "coverage_gaps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    coverage_report_id = Column(UUID(as_uuid=True), ForeignKey("coverage_reports.id"), nullable=True)
    gap_id = Column(String(100), nullable=False)
    feature = Column(String(255), default="")
    reason = Column(Text, default="")
    priority = Column(Integer, default=5)
    recommended_test = Column(Text, default="")
    related_requirement = Column(String(100), default="")
    gap_type = Column(String(50), default="reachable_untested")
    is_addressed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class TraceabilityLink(Base):
    __tablename__ = "traceability_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    requirement_id = Column(String(100), nullable=False)
    verification_plan_id = Column(String(100), nullable=True)
    assertion_id = Column(UUID(as_uuid=True), ForeignKey("assertions.id"), nullable=True)
    test_id = Column(UUID(as_uuid=True), ForeignKey("generated_tests.id"), nullable=True)
    simulation_id = Column(UUID(as_uuid=True), ForeignKey("simulation_runs.id"), nullable=True)
    failure_id = Column(UUID(as_uuid=True), ForeignKey("failures.id"), nullable=True)
    coverage_id = Column(UUID(as_uuid=True), ForeignKey("coverage_reports.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="traceability_links")


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    analysis_type = Column(String(50), default="")
    input_data = Column(JSONB, default=dict)
    output_data = Column(JSONB, default=dict)
    model_used = Column(String(100), default="")
    confidence = Column(Enum(ConfidenceLevel), default=ConfidenceLevel.LOW)
    classification = Column(String(50), default="INFERENCE")
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="ai_analyses")


class RegressionRun(Base):
    __tablename__ = "regression_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), default="Regression Run")
    total_tests = Column(Integer, default=0)
    passed = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    skipped = Column(Integer, default=0)
    duration_seconds = Column(Float, default=0.0)
    failure_distribution = Column(JSONB, default=dict)
    top_causes = Column(JSONB, default=list)
    coverage_delta = Column(JSONB, default=dict)
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.PENDING)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="regression_runs")