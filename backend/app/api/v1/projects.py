"""Project management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Project, ProjectStatus, RTLFile, VerificationPlan, Assertion, GeneratedTest, SimulationRun, Failure, CoverageReport, TraceabilityLink, AIAnalysis, RegressionRun
from app.core.database import get_db

router = APIRouter(prefix="/projects", tags=["Projects"])


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    status: str
    created_at: str
    updated_at: Optional[str] = None


class ProjectDetailResponse(ProjectResponse):
    rtl_files: int = 0
    verification_plans: int = 0
    assertions: int = 0
    tests: int = 0
    simulations: int = 0
    failures: int = 0
    coverage_reports: int = 0


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(project: ProjectCreate, db: AsyncSession = Depends(get_db)):
    """Create a new verification project."""
    import uuid

    new_project = Project(
        id=uuid.uuid4(),
        name=project.name,
        description=project.description,
        status=ProjectStatus.ACTIVE,
    )
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)

    return ProjectResponse(
        id=str(new_project.id),
        name=new_project.name,
        description=new_project.description,
        status=new_project.status.value,
        created_at=new_project.created_at.isoformat(),
        updated_at=new_project.updated_at.isoformat() if new_project.updated_at else None,
    )


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)):
    """List all projects."""
    result = await db.execute(
        select(Project).order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()

    return [
        ProjectResponse(
            id=str(p.id),
            name=p.name,
            description=p.description,
            status=p.status.value,
            created_at=p.created_at.isoformat(),
            updated_at=p.updated_at.isoformat() if p.updated_at else None,
        )
        for p in projects
    ]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        status=project.status.value,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat() if project.updated_at else None,
    )


@router.get("/{project_id}/detail", response_model=ProjectDetailResponse)
async def get_project_detail(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get project with counts of all artifacts."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Count related entities
    rtl_count = (await db.execute(select(RTLFile).where(RTLFile.project_id == project.id))).scalars().all()
    vp_count = (await db.execute(select(VerificationPlan).where(VerificationPlan.project_id == project.id))).scalars().all()
    ass_count = (await db.execute(select(Assertion).where(Assertion.project_id == project.id))).scalars().all()
    test_count = (await db.execute(select(GeneratedTest).where(GeneratedTest.project_id == project.id))).scalars().all()
    sim_count = (await db.execute(select(SimulationRun).where(SimulationRun.project_id == project.id))).scalars().all()
    fail_count = (await db.execute(select(Failure).where(Failure.project_id == project.id))).scalars().all()
    cov_count = (await db.execute(select(CoverageReport).where(CoverageReport.project_id == project.id))).scalars().all()

    return ProjectDetailResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        status=project.status.value,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat() if project.updated_at else None,
        rtl_files=len(rtl_count),
        verification_plans=len(vp_count),
        assertions=len(ass_count),
        tests=len(test_count),
        simulations=len(sim_count),
        failures=len(fail_count),
        coverage_reports=len(cov_count),
    )


@router.delete("/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await db.delete(project)
    await db.commit()
    return {"status": "deleted"}


@router.post("/{project_id}/rtl")
async def upload_rtl(project_id: str, rtl_data: dict, db: AsyncSession = Depends(get_db)):
    """Upload RTL file to project."""
    import uuid
    from app.utils.storage import save_uploaded_file

    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    content = rtl_data.get("content", "")
    filename = rtl_data.get("filename", "design.sv")

    # Save to storage
    file_path = save_uploaded_file(content.encode(), "rtl", filename)

    rtl_file = RTLFile(
        id=uuid.uuid4(),
        project_id=project.id,
        filename=filename,
        content=content,
        language="SystemVerilog",
    )
    db.add(rtl_file)
    await db.commit()
    await db.refresh(rtl_file)

    return {"id": str(rtl_file.id), "filename": rtl_file.filename, "path": file_path}