"""Coverage Engine - Simulator-independent coverage abstraction."""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class CoverageData:
    report_type: str
    overall: float = 0.0
    covered: int = 0
    total: int = 0
    details: Dict[str, Any] = field(default_factory=dict)
    gaps: List[Dict[str, Any]] = field(default_factory=list)


class CoverageAnalyzer:
    """Analyzes coverage reports and identifies gaps."""

    def parse_verilator_coverage(self, content: str) -> Dict[str, CoverageData]:
        """Parse Verilator coverage output."""
        coverage = {
            "line": CoverageData(report_type="line"),
            "branch": CoverageData(report_type="branch"),
            "toggle": CoverageData(report_type="toggle"),
        }

        lines = content.split("\n")
        for line in lines:
            match = re.search(r"Lines\s+(\d+)/(\d+)\s+\((\d+\.?\d*)%\)", line)
            if match:
                coverage["line"].covered = int(match.group(1))
                coverage["line"].total = int(match.group(2))
                coverage["line"].overall = float(match.group(3))

            match = re.search(r"Branches\s+(\d+)/(\d+)\s+\((\d+\.?\d*)%\)", line)
            if match:
                coverage["branch"].covered = int(match.group(1))
                coverage["branch"].total = int(match.group(2))
                coverage["branch"].overall = float(match.group(3))

            match = re.search(r"Toggles\s+(\d+)/(\d+)\s+\((\d+\.?\d*)%\)", line)
            if match:
                coverage["toggle"].covered = int(match.group(1))
                coverage["toggle"].total = int(match.group(2))
                coverage["toggle"].overall = float(match.group(3))

        return coverage

    def parse_ucov_report(self, content: str) -> Dict[str, CoverageData]:
        """Parse generic coverage report format."""
        coverage = {"line": CoverageData(report_type="line")}

        patterns = [
            (r"coverage\s*=\s*(\d+\.?\d*)%", "line"),
            (r"line\s+coverage.*?(\d+\.?\d*)%", "line"),
            (r"branch\s+coverage.*?(\d+\.?\d*)%", "branch"),
        ]

        for pattern, cov_type in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                if cov_type not in coverage:
                    coverage[cov_type] = CoverageData(report_type=cov_type)
                coverage[cov_type].overall = float(match.group(1))

        return coverage

    def identify_gaps(self, coverage: Dict[str, CoverageData],
                      rtl_content: str = "", module_name: str = "") -> List[Dict[str, Any]]:
        """Identify coverage gaps and classify them."""
        gaps = []

        for cov_type, data in coverage.items():
            if data.overall < 100.0:
                uncovered = self._find_uncovered_items(data, rtl_content)

                for item in uncovered:
                    gap_type = self._classify_gap(item, rtl_content)
                    gaps.append({
                        "gap_type": gap_type,
                        "coverage_type": cov_type,
                        "description": item.get("description", ""),
                        "rtl_location": {
                            "module": module_name,
                            "line": item.get("line", 0),
                            "file": item.get("file", ""),
                        },
                        "conditions": item.get("conditions", []),
                        "coverage_before": data.overall,
                        "estimated_impact": self._estimate_impact(data, item),
                        "suggested_test": item.get("suggestion", ""),
                    })

        return gaps

    def _find_uncovered_items(self, data: CoverageData,
                              rtl_content: str) -> List[Dict[str, Any]]:
        items = []

        if data.details:
            for item_id, item_data in data.details.items():
                if not item_data.get("covered", False):
                    items.append({
                        "id": item_id,
                        "description": f"Uncovered {data.report_type}: {item_id}",
                        "line": item_data.get("line", 0),
                        "conditions": item_data.get("conditions", []),
                        "suggestion": self._suggest_test_for_item(item_data),
                    })

        if not items and data.overall < 100.0:
            uncovered_count = data.total - data.covered
            items.append({
                "id": f"{data.report_type}_gap",
                "description": f"{uncovered_count} uncovered {data.report_type} points ({data.overall:.1f}%)",
                "line": 0,
                "conditions": [],
                "suggestion": f"Generate additional tests targeting uncovered {data.report_type} points",
            })

        return items

    def _classify_gap(self, item: Dict[str, Any], rtl_content: str) -> str:
        description = item.get("description", "").lower()
        conditions = item.get("conditions", [])

        error_keywords = ["error", "overflow", "underflow", "exception", "fatal"]
        if any(kw in description for kw in error_keywords):
            return "potentially_unreachable"

        if "unreachable" in description:
            return "unreachable"

        if len(conditions) > 4:
            return "potentially_unreachable"

        return "reachable_untested"

    def _estimate_impact(self, data: CoverageData, item: Dict[str, Any]) -> float:
        uncovered = data.total - data.covered
        if uncovered == 0:
            return 0.0
        return (1.0 / uncovered) * 100.0

    def _suggest_test_for_item(self, item_data: Dict[str, Any]) -> str:
        item_type = item_data.get("type", "unknown")

        suggestions = {
            "branch": "Generate test that exercises both branch conditions",
            "line": "Generate test that executes the uncovered line",
            "toggle": "Generate test that toggles the uncovered signal",
            "fsm_transition": "Generate test that triggers the specific FSM transition",
            "condition": "Generate test that satisfies the uncovered condition combination",
        }

        return suggestions.get(item_type, "Review RTL and generate targeted stimulus")

    def compare_coverage(self, before: Dict[str, CoverageData],
                         after: Dict[str, CoverageData]) -> Dict[str, Any]:
        """Compare two coverage reports and compute delta."""
        comparison = {}

        all_types = set(list(before.keys()) + list(after.keys()))

        for cov_type in all_types:
            before_data = before.get(cov_type, CoverageData(report_type=cov_type))
            after_data = after.get(cov_type, CoverageData(report_type=cov_type))

            delta = after_data.overall - before_data.overall
            comparison[cov_type] = {
                "before": before_data.overall,
                "after": after_data.overall,
                "delta": delta,
                "improved": delta > 0,
                "before_covered": before_data.covered,
                "after_covered": after_data.covered,
                "total": after_data.total,
            }

        return comparison

    def generate_coverage_report(self, coverage: Dict[str, CoverageData],
                                 gaps: List[Dict[str, Any]],
                                 module_name: str) -> Dict[str, Any]:
        """Generate a comprehensive coverage analysis report."""
        total_points = sum(d.total for d in coverage.values())
        covered_points = sum(d.covered for d in coverage.values())
        overall = (covered_points / total_points * 100) if total_points > 0 else 0

        gap_summary = {
            "reachable_untested": len([g for g in gaps if g["gap_type"] == "reachable_untested"]),
            "potentially_unreachable": len([g for g in gaps if g["gap_type"] == "potentially_unreachable"]),
            "unreachable": len([g for g in gaps if g["gap_type"] == "unreachable"]),
        }

        return {
            "module": module_name,
            "overall_coverage": overall,
            "coverage_by_type": {
                ct: {"coverage": d.overall, "covered": d.covered, "total": d.total}
                for ct, d in coverage.items()
            },
            "total_gaps": len(gaps),
            "gap_summary": gap_summary,
            "high_priority_gaps": [
                g for g in gaps
                if g["gap_type"] == "reachable_untested"
            ][:10],
            "closure_estimate": {
                "achievable_coverage": min(100.0, overall + len([g for g in gaps if g["gap_type"] == "reachable_untested"]) * 2),
                "tests_needed": len([g for g in gaps if g["gap_type"] == "reachable_untested"]),
            },
        }