"""Verification Planner - Automatically generates verification plans from RTL analysis."""

from typing import List, Dict, Any
from .rtl import DesignModule, SignalDirection


class VerificationPlanGenerator:
    """Generates comprehensive verification plans from RTL analysis.

    Each generated item is traceable back to RTL behavior or explicit requirements.
    Items are labeled as [RTL-derived], [Specification-derived], or [AI-inferred].
    """

    def generate(self, modules: List[DesignModule],
                 specification: str = "") -> Dict[str, Any]:
        """Generate a verification plan from parsed RTL modules."""
        items = []

        for module in modules:
            items.extend(self._plan_module_functionality(module))
            items.extend(self._plan_port_behavior(module))
            items.extend(self._plan_fsm_verification(module))
            items.extend(self._plan_clock_reset(module))
            items.extend(self._plan_protocol(module))
            items.extend(self._plan_corner_cases(module))
            items.extend(self._plan_assertions(module))
            items.extend(self._plan_coverage(module))

        if specification:
            items.extend(self._plan_from_specification(specification, modules))

        items = self._prioritize_items(items)

        return {
            "items": items,
            "summary": self._generate_summary(items, modules),
            "traceability": self._build_traceability(items),
        }

    def _plan_module_functionality(self, module: DesignModule) -> List[Dict[str, Any]]:
        items = []

        items.append({
            "id": f"VP-{module.name}-001",
            "feature": "Basic Functionality",
            "requirement": f"Module {module.name} operates correctly under normal conditions",
            "stimulus": "Apply valid input combinations, observe outputs",
            "expected_behavior": "All outputs produce correct values for given inputs",
            "assertion_candidate": "Output validity assertions",
            "coverage_goal": "100% line coverage",
            "priority": 10,
            "confidence": "high",
            "evidence": f"Module {module.name} lines {module.start_line}-{module.end_line}",
            "source_type": "rtl-derived",
        })

        if module.parameters:
            items.append({
                "id": f"VP-{module.name}-002",
                "feature": "Parameter Variation",
                "requirement": f"Module works with all parameter combinations",
                "stimulus": f"Test with parameters: {[p.name for p in module.parameters]} at min/max/default",
                "expected_behavior": "Correct behavior for all parameter values",
                "assertion_candidate": "Parameter-dependent assertions",
                "coverage_goal": "All parameter combinations covered",
                "priority": 8,
                "confidence": "high",
                "evidence": f"Module has parameters: {[p.name for p in module.parameters]}",
                "source_type": "rtl-derived",
            })

        return items

    def _plan_port_behavior(self, module: DesignModule) -> List[Dict[str, Any]]:
        items = []
        port_idx = 1

        for port in module.ports:
            if port.direction in [SignalDirection.INPUT, SignalDirection.INOUT]:
                items.append({
                    "id": f"VP-{module.name}-PORT-{port_idx:03d}",
                    "feature": f"Input Port {port.name}",
                    "requirement": f"Input port {port.name} handles boundary values correctly",
                    "stimulus": f"Apply 0, max, alternating patterns to {port.name} ({port.width or '1-bit'})",
                    "expected_behavior": "Module responds correctly to all input values",
                    "assertion_candidate": f"Input range check on {port.name}",
                    "coverage_goal": "Boundary values covered",
                    "priority": 7,
                    "confidence": "high",
                    "evidence": f"Port {port.name} at line {port.line}",
                    "source_type": "rtl-derived",
                })
                port_idx += 1

            if port.direction == SignalDirection.OUTPUT:
                items.append({
                    "id": f"VP-{module.name}-OUT-{port_idx:03d}",
                    "feature": f"Output Port {port.name}",
                    "requirement": f"Output port {port.name} produces correct values",
                    "stimulus": "Apply known input patterns",
                    "expected_behavior": "Output matches expected values for each input combination",
                    "assertion_candidate": f"Output correctness check on {port.name}",
                    "coverage_goal": "All output transitions covered",
                    "priority": 6,
                    "confidence": "medium",
                    "evidence": f"Output port {port.name} at line {port.line}",
                    "source_type": "rtl-derived",
                })
                port_idx += 1

        return items

    def _plan_fsm_verification(self, module: DesignModule) -> List[Dict[str, Any]]:
        items = []

        for fsm in module.fsm_info:
            states = fsm.states
            num_transitions = len(fsm.transitions)

            items.append({
                "id": f"VP-{module.name}-FSM-001",
                "feature": f"FSM {fsm.name} State Reachability",
                "requirement": f"All {len(states)} states in FSM '{fsm.name}' are reachable",
                "stimulus": f"Drive inputs to traverse states: {states}",
                "expected_behavior": f"FSM visits each state: {states}",
                "assertion_candidate": f"FSM state validity: {fsm.state_variable} inside {{{', '.join(states)}}}",
                "coverage_goal": "100% state coverage",
                "priority": 10,
                "confidence": "high",
                "evidence": f"FSM '{fsm.name}' with states: {states}",
                "source_type": "rtl-derived",
            })

            if fsm.transitions:
                items.append({
                    "id": f"VP-{module.name}-FSM-002",
                    "feature": f"FSM {fsm.name} Transition Coverage",
                    "requirement": f"All {num_transitions} transitions in FSM '{fsm.name}' are exercised",
                    "stimulus": "Sequence inputs to trigger each transition",
                    "expected_behavior": "Each transition executes correctly",
                    "assertion_candidate": "Legal transition assertion",
                    "coverage_goal": "100% transition coverage",
                    "priority": 10,
                    "confidence": "high",
                    "evidence": "Transitions: " + ", ".join([f"{t['from']}->{t['to']}" for t in fsm.transitions]),
                    "source_type": "rtl-derived",
                })

            items.append({
                "id": f"VP-{module.name}-FSM-003",
                "feature": f"FSM {fsm.name} Reset Recovery",
                "requirement": f"FSM returns to initial state from any state on reset",
                "stimulus": "Drive to each state, then assert reset",
                "expected_behavior": "FSM returns to initial state after reset",
                "assertion_candidate": "Reset implication: reset |-> ##1 (state == INIT)",
                "coverage_goal": "Reset from all states",
                "priority": 9,
                "confidence": "high",
                "evidence": f"FSM '{fsm.name}' has reset signal: {module.reset_signals}",
                "source_type": "rtl-derived",
            })

            items.append({
                "id": f"VP-{module.name}-FSM-004",
                "feature": f"FSM {fsm.name} Invalid State Recovery",
                "requirement": "FSM recovers from invalid state encoding",
                "stimulus": "Force invalid state value, then reset",
                "expected_behavior": "FSM recovers via reset to known state",
                "assertion_candidate": "Invalid state detection",
                "coverage_goal": "Invalid state recovery",
                "priority": 8,
                "confidence": "medium",
                "evidence": f"FSM '{fsm.name}' state register width may allow invalid encodings",
                "source_type": "ai-inferred",
            })

        return items

    def _plan_clock_reset(self, module: DesignModule) -> List[Dict[str, Any]]:
        items = []

        if module.clock_signals:
            items.append({
                "id": f"VP-{module.name}-CLK-001",
                "feature": "Clock Behavior",
                "requirement": f"Module operates correctly at target frequency. Clocks: {module.clock_signals}",
                "stimulus": "Apply clock with varying frequency, duty cycle",
                "expected_behavior": "No timing violations, correct synchronous behavior",
                "assertion_candidate": "Clock period constraints",
                "coverage_goal": "Clock domain crossing checks",
                "priority": 9,
                "confidence": "high",
                "evidence": f"Clock signals detected: {module.clock_signals}",
                "source_type": "rtl-derived",
            })

        if module.reset_signals:
            items.append({
                "id": f"VP-{module.name}-RST-001",
                "feature": "Reset Behavior",
                "requirement": f"All reset scenarios work correctly. Resets: {module.reset_signals}",
                "stimulus": "Assert/de-assert reset at various times, during operation",
                "expected_behavior": "All registers clear, FSM returns to initial state",
                "assertion_candidate": "Register clear on reset, FSM reset implication",
                "coverage_goal": "Reset assertion/de-assertion, async/sync behavior",
                "priority": 10,
                "confidence": "high",
                "evidence": f"Reset signals: {module.reset_signals} with types from always blocks",
                "source_type": "rtl-derived",
            })

        return items

    def _plan_protocol(self, module: DesignModule) -> List[Dict[str, Any]]:
        items = []
        protocol = module.metadata.get("protocol", "")

        if protocol == "valid_ready_handshake":
            items.append({
                "id": f"VP-{module.name}-PROTO-001",
                "feature": "Valid/Ready Handshake",
                "requirement": "Correct valid/ready protocol operation including backpressure",
                "stimulus": "Test valid=1/ready=1, valid=1/ready=0, valid=0, multiple transfers",
                "expected_behavior": "Data transfers only when both valid and ready high; data held during backpressure",
                "assertion_candidate": "Data stability during backpressure, handshake completion",
                "coverage_goal": "All handshake scenarios covered",
                "priority": 10,
                "confidence": "very_high",
                "evidence": f"Valid/ready signals detected in module {module.name}",
                "source_type": "rtl-derived",
            })

        if module.metadata.get("is_fifo"):
            items.append({
                "id": f"VP-{module.name}-FIFO-001",
                "feature": "FIFO Behavior",
                "requirement": "FIFO full, empty, overflow, underflow, simultaneous R/W",
                "stimulus": "Fill to full, drain to empty, simultaneous read/write, write when full, read when empty",
                "expected_behavior": "Full/empty flags correct; no data loss/corruption; pointers track correctly",
                "assertion_candidate": "No write when full, no read when empty, pointer progress, count tracking",
                "coverage_goal": "All FIFO boundary conditions",
                "priority": 10,
                "confidence": "very_high",
                "evidence": f"FIFO signals detected: full/empty/pointers in module {module.name}",
                "source_type": "rtl-derived",
            })

        if protocol in ["axi_like", "simple_bus"]:
            items.append({
                "id": f"VP-{module.name}-BUS-001",
                "feature": f"Bus Protocol ({protocol})",
                "requirement": "Bus protocol compliance",
                "stimulus": "Single beat, burst transfers, address decoding, error responses",
                "expected_behavior": "Protocol-compliant responses for all transactions",
                "assertion_candidate": "Protocol-specific assertions",
                "coverage_goal": "Protocol compliance coverage",
                "priority": 9,
                "confidence": "high",
                "evidence": f"Bus interface signals detected: {protocol}",
                "source_type": "rtl-derived",
            })

        return items

    def _plan_corner_cases(self, module: DesignModule) -> List[Dict[str, Any]]:
        items = []
        corner_cases = module.metadata.get("corner_cases", [])

        for cc in corner_cases:
            items.append({
                "id": f"VP-{module.name}-CORNER-{cc['type'].upper()}",
                "feature": f"Corner Case: {cc['description']}",
                "requirement": f"Handle corner cases for {module.name}",
                "stimulus": "; ".join(cc["cases"]),
                "expected_behavior": "Correct behavior under all corner conditions",
                "assertion_candidate": f"Corner case assertions for {cc['type']}",
                "coverage_goal": "All corner cases exercised",
                "priority": 8,
                "confidence": "medium",
                "evidence": f"Detected {cc['type']} patterns in module {module.name}",
                "source_type": "ai-inferred",
            })

        return items

    def _plan_assertions(self, module: DesignModule) -> List[Dict[str, Any]]:
        items = []

        if not module.has_assertions:
            items.append({
                "id": f"VP-{module.name}-ASSERTS-001",
                "feature": "Assertion Generation",
                "requirement": f"Module {module.name} lacks assertions; generate SVA for key properties",
                "stimulus": "N/A - static generation",
                "expected_behavior": "Generated assertions cover reset, protocol, FSM, data integrity",
                "assertion_candidate": "Reset, handshake, FSM, FIFO, counter assertions",
                "coverage_goal": "Assertion coverage on generated properties",
                "priority": 8,
                "confidence": "high",
                "evidence": f"Module has no assertions, has {len(module.always_blocks)} always blocks, {len(module.ports)} ports",
                "source_type": "ai-inferred",
            })
        else:
            items.append({
                "id": f"VP-{module.name}-ASSERTS-002",
                "feature": "Existing Assertion Verification",
                "requirement": f"Verify {len(module.assertions)} existing assertions are correct",
                "stimulus": "Run simulation with assertions enabled",
                "expected_behavior": "All existing assertions pass",
                "assertion_candidate": "Existing assertion validation",
                "coverage_goal": "100% assertion coverage",
                "priority": 7,
                "confidence": "high",
                "evidence": f"Module has {len(module.assertions)} assertions",
                "source_type": "rtl-derived",
            })

        return items

    def _plan_coverage(self, module: DesignModule) -> List[Dict[str, Any]]:
        items = []

        items.append({
            "id": f"VP-{module.name}-COV-001",
            "feature": f"Line Coverage for {module.name}",
            "requirement": f"Achieve 95%+ line coverage",
            "stimulus": "Comprehensive test suite exercising all code paths",
            "expected_behavior": "Line coverage >= 95%",
            "assertion_candidate": "N/A",
            "coverage_goal": "Line coverage >= 95%",
            "priority": 9,
            "confidence": "high",
            "evidence": f"Module {module.name} lines {module.start_line}-{module.end_line}",
            "source_type": "rtl-derived",
        })

        items.append({
            "id": f"VP-{module.name}-COV-002",
            "feature": f"Branch Coverage for {module.name}",
            "requirement": f"Achieve 90%+ branch coverage",
            "stimulus": "Tests covering all if/else/case branches",
            "expected_behavior": "Branch coverage >= 90%",
            "assertion_candidate": "N/A",
            "coverage_goal": "Branch coverage >= 90%",
            "priority": 8,
            "confidence": "high",
            "evidence": f"Module has conditional statements",
            "source_type": "rtl-derived",
        })

        if module.has_fsm:
            items.append({
                "id": f"VP-{module.name}-COV-003",
                "feature": f"FSM Coverage for {module.name}",
                "requirement": f"100% FSM state and transition coverage",
                "stimulus": "Tests reaching all states and transitions",
                "expected_behavior": "All states reached, all transitions covered",
                "assertion_candidate": "FSM coverage assertions",
                "coverage_goal": "FSM arc coverage >= 100%",
                "priority": 10,
                "confidence": "high",
                "evidence": f"Module has {len(module.fsm_info)} FSM(s)",
                "source_type": "rtl-derived",
            })

        return items

    def _plan_from_specification(self, spec: str,
                                  modules: List[DesignModule]) -> List[Dict[str, Any]]:
        items = []
        spec_lower = spec.lower()
        keywords = {
            "reset": ("reset", "Verify reset behavior as specified"),
            "overflow": ("overflow", "Verify overflow handling as specified"),
            "underflow": ("underflow", "Verify underflow handling as specified"),
            "timeout": ("timeout", "Verify timeout behavior as specified"),
            "error": ("error", "Verify error handling as specified"),
            "interrupt": ("interrupt", "Verify interrupt behavior as specified"),
            "dma": ("dma", "Verify DMA transfer as specified"),
            "pipeline": ("pipeline", "Verify pipeline behavior as specified"),
        }

        for keyword, (category, desc) in keywords.items():
            if keyword in spec_lower:
                items.append({
                    "id": f"VP-SPEC-{category.upper()}",
                    "feature": desc,
                    "requirement": f"Specification mentions {keyword}. Verify behavior matches specification.",
                    "stimulus": f"Per specification requirements for {keyword}",
                    "expected_behavior": "Behavior matches specification",
                    "assertion_candidate": f"Specification-derived assertions for {keyword}",
                    "coverage_goal": f"Spec requirement for {keyword} verified",
                    "priority": 9,
                    "confidence": "high",
                    "evidence": f"Keyword '{keyword}' found in specification",
                    "source_type": "spec-derived",
                })

        return items

    def _prioritize_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        items.sort(key=lambda x: (-x.get("priority", 5), x.get("category", "")))
        return items

    def _generate_summary(self, items: List[Dict[str, Any]],
                          modules: List[DesignModule]) -> Dict[str, Any]:
        categories = {}
        source_counts = {"rtl-derived": 0, "spec-derived": 0, "ai-inferred": 0}

        for item in items:
            cat = item.get("feature", "unknown").split()[0]
            categories[cat] = categories.get(cat, 0) + 1
            src = item.get("source_type", "unknown")
            if src in source_counts:
                source_counts[src] += 1

        return {
            "total_items": len(items),
            "categories": categories,
            "source_breakdown": source_counts,
            "modules_analyzed": len(modules),
            "total_fsm": sum(len(m.fsm_info) for m in modules),
            "total_assertions": sum(len(m.assertions) for m in modules),
            "estimated_test_count": len(items) * 2,
        }

    def _build_traceability(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        traceability = {
            "module_to_items": {},
            "category_to_items": {},
            "source_to_items": {},
        }

        for item in items:
            module = item.get("evidence", "").split(" ")[-1] if "evidence" in item else "unknown"
            if module not in traceability["module_to_items"]:
                traceability["module_to_items"][module] = []
            traceability["module_to_items"][module].append(item["id"])

            cat = item.get("feature", "unknown").split()[0]
            if cat not in traceability["category_to_items"]:
                traceability["category_to_items"][cat] = []
            traceability["category_to_items"][cat].append(item["id"])

            src = item.get("source_type", "unknown")
            if src not in traceability["source_to_items"]:
                traceability["source_to_items"][src] = []
            traceability["source_to_items"][src].append(item["id"])

        return traceability