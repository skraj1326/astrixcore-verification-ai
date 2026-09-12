"""Traceability Engine - Links requirements to verification artifacts."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import uuid


@dataclass
class TraceabilityLink:
    requirement_id: str
    verification_plan_ids: List[str] = field(default_factory=list)
    assertion_ids: List[str] = field(default_factory=list)
    test_ids: List[str] = field(default_factory=list)
    simulation_ids: List[str] = field(default_factory=list)
    failure_ids: List[str] = field(default_factory=list)
    coverage_ids: List[str] = field(default_factory=list)


class TraceabilityEngine:
    """Manages traceability from requirements to verification closure."""

    def __init__(self):
        self.links: Dict[str, TraceabilityLink] = {}

    def add_link(self, requirement_id: str, artifact_type: str, artifact_id: str) -> None:
        """Add a traceability link."""
        if requirement_id not in self.links:
            self.links[requirement_id] = TraceabilityLink(requirement_id=requirement_id)

        link = self.links[requirement_id]
        attr_map = {
            "verification_plan": "verification_plan_ids",
            "assertion": "assertion_ids",
            "test": "test_ids",
            "simulation": "simulation_ids",
            "failure": "failure_ids",
            "coverage": "coverage_ids",
        }
        attr = attr_map.get(artifact_type)
        if attr and artifact_id not in getattr(link, attr):
            getattr(link, attr).append(artifact_id)

    def get_traceability(self, requirement_id: str) -> Optional[TraceabilityLink]:
        """Get traceability for a requirement."""
        return self.links.get(requirement_id)

    def get_all_traceability(self) -> Dict[str, TraceabilityLink]:
        """Get all traceability links."""
        return self.links

    def get_coverage_for_requirement(self, requirement_id: str) -> Dict[str, Any]:
        """Get coverage status for a requirement."""
        link = self.links.get(requirement_id)
        if not link:
            return {"status": "NOT_LINKED"}

        return {
            "requirement_id": requirement_id,
            "has_verification_plan": len(link.verification_plan_ids) > 0,
            "has_assertions": len(link.assertion_ids) > 0,
            "has_tests": len(link.test_ids) > 0,
            "has_simulations": len(link.simulation_ids) > 0,
            "has_failures": len(link.failure_ids) > 0,
            "has_coverage": len(link.coverage_ids) > 0,
            "verification_plan_count": len(link.verification_plan_ids),
            "assertion_count": len(link.assertion_ids),
            "test_count": len(link.test_ids),
            "simulation_count": len(link.simulation_ids),
            "failure_count": len(link.failure_ids),
            "coverage_count": len(link.coverage_ids),
        }

    def get_unverified_requirements(self) -> List[str]:
        """Get requirements with missing verification artifacts."""
        unverified = []
        for req_id, link in self.links.items():
            if not link.verification_plan_ids:
                unverified.append(req_id)
            elif not link.assertion_ids and not link.test_ids:
                unverified.append(req_id)
        return unverified

    def generate_traceability_matrix(self) -> Dict[str, Any]:
        """Generate a traceability matrix."""
        matrix = {
            "requirements": [],
            "summary": {
                "total_requirements": len(self.links),
                "with_plan": 0,
                "with_assertions": 0,
                "with_tests": 0,
                "with_simulations": 0,
                "with_coverage": 0,
                "fully_verified": 0,
            }
        }

        for req_id, link in self.links.items():
            row = {
                "requirement_id": req_id,
                "verification_plans": link.verification_plan_ids,
                "assertions": link.assertion_ids,
                "tests": link.test_ids,
                "simulations": link.simulation_ids,
                "failures": link.failure_ids,
                "coverage": link.coverage_ids,
            }
            matrix["requirements"].append(row)

            if link.verification_plan_ids:
                matrix["summary"]["with_plan"] += 1
            if link.assertion_ids:
                matrix["summary"]["with_assertions"] += 1
            if link.test_ids:
                matrix["summary"]["with_tests"] += 1
            if link.simulation_ids:
                matrix["summary"]["with_simulations"] += 1
            if link.coverage_ids:
                matrix["summary"]["with_coverage"] += 1
            if (link.verification_plan_ids and link.assertion_ids and
                link.test_ids and link.simulation_ids and link.coverage_ids):
                matrix["summary"]["fully_verified"] += 1

        return matrix

    def export_traceability(self, format: str = "json") -> Any:
        """Export traceability data."""
        if format == "json":
            return {req_id: {
                "verification_plans": link.verification_plan_ids,
                "assertions": link.assertion_ids,
                "tests": link.test_ids,
                "simulations": link.simulation_ids,
                "failures": link.failure_ids,
                "coverage": link.coverage_ids,
            } for req_id, link in self.links.items()}
        return self.generate_traceability_matrix()