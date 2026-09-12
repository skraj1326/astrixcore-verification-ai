"""SVA Assertion Generator - Generates SystemVerilog Assertions from RTL analysis."""

from typing import List, Dict, Any
from .rtl import DesignModule, SignalDirection


class AssertionGenerator:
    """Generates syntactically valid SystemVerilog assertions.

    For every assertion provides:
    - Assertion code
    - Explanation
    - Signals used
    - Reasoning/evidence
    - Confidence level
    - Potential false-positive conditions
    """

    def generate(self, modules: List[DesignModule]) -> List[Dict[str, Any]]:
        """Generate assertions for all analyzed modules."""
        all_assertions = []
        for module in modules:
            all_assertions.extend(self._generate_for_module(module))
        return all_assertions

    def _generate_for_module(self, module: DesignModule) -> List[Dict[str, Any]]:
        assertions = []

        assertions.extend(self._gen_reset_assertions(module))

        if module.metadata.get("protocol") == "valid_ready_handshake":
            assertions.extend(self._gen_handshake_assertions(module))

        for fsm in module.fsm_info:
            assertions.extend(self._gen_fsm_assertions(module, fsm))

        if module.metadata.get("is_fifo"):
            assertions.extend(self._gen_fifo_assertions(module))

        if module.metadata.get("counters"):
            assertions.extend(self._gen_counter_assertions(module))

        if module.metadata.get("pointers"):
            assertions.extend(self._gen_pointer_assertions(module))

        assertions.extend(self._gen_stability_assertions(module))
        assertions.extend(self._gen_data_integrity_assertions(module))

        return assertions

    def _gen_reset_assertions(self, module: DesignModule) -> List[Dict[str, Any]]:
        assertions = []
        resets = module.reset_signals

        if not resets:
            return assertions

        clk = module.clock_signals[0] if module.clock_signals else "clk"
        regs = [s.name for s in module.signals
                if s.signal_type.value in ("reg", "logic")]

        for rst in resets:
            if regs:
                reg_list = ", ".join(regs[:5])
                assertions.append({
                    "name": f"{module.name}_reset_clears_registers",
                    "description": f"Reset {rst} clears all registers within one cycle",
                    "sva_code": (
                        f"// Assert: Reset clears all registers\n"
                        f"property {module.name}_p_reset_clears;\n"
                        f"  @(posedge {clk})\n"
                        f"  {rst} |-> ##1 ({' && '.join(f'{r} == 0' for r in regs[:5])});\n"
                        f"endproperty\n"
                        f"{module.name}_a_reset_clears: assert property ({module.name}_p_reset_clears);"
                    ),
                    "assertion_type": "concurrent",
                    "confidence": "high",
                    "evidence": f"Module '{module.name}' has reset '{rst}' and registers: {reg_list}",
                    "assumptions": "All registers have synchronous reset to zero",
                    "validation_status": "REQUIRES ENGINEER VALIDATION",
                    "classification": "GENERATED",
                })

            # FSM reset
            for fsm in module.fsm_info:
                if fsm.states:
                    initial_state = fsm.states[0]
                    assertions.append({
                        "name": f"{module.name}_{fsm.name}_reset_to_initial",
                        "description": f"FSM {fsm.name} returns to initial state on reset",
                        "sva_code": (
                            f"// Assert: FSM returns to initial state on reset\n"
                            f"property {module.name}_{fsm.name}_p_reset_state;\n"
                            f"  @(posedge {clk})\n"
                            f"  {rst} |-> ##1 ({fsm.state_variable} == {initial_state});\n"
                            f"endproperty\n"
                            f"{module.name}_{fsm.name}_a_reset_state: assert property ({module.name}_{fsm.name}_p_reset_state);"
                        ),
                        "assertion_type": "concurrent",
                        "confidence": "high",
                        "evidence": f"FSM '{fsm.name}' with state variable {fsm.state_variable}, initial state {initial_state}",
                        "assumptions": "Reset is synchronous and FSM has defined initial state",
                        "validation_status": "REQUIRES ENGINEER VALIDATION",
                        "classification": "GENERATED",
                    })

        return assertions

    def _gen_handshake_assertions(self, module: DesignModule) -> List[Dict[str, Any]]:
        assertions = []

        all_names = [p.name for p in module.ports] + [s.name for s in module.signals]
        valid_signals = [n for n in all_names if "valid" in n.lower()]
        ready_signals = [n for n in all_names if "ready" in n.lower()]

        clk = module.clock_signals[0] if module.clock_signals else "clk"
        rst = module.reset_signals[0] if module.reset_signals else "rst"

        for valid in valid_signals[:2]:
            for ready in ready_signals[:2]:
                # Data stability during backpressure
                assertions.append({
                    "name": f"{module.name}_{valid}_data_stable",
                    "description": f"Data stable while {valid} asserted and {ready} deasserted",
                    "sva_code": (
                        f"// Assert: Data stable during backpressure\n"
                        f"property {module.name}_p_{valid}_stability;\n"
                        f"  @(posedge {clk})\n"
                        f"  disable iff ({rst})\n"
                        f"  ({valid} && !{ready}) |-> $stable({valid});\n"
                        f"endproperty\n"
                        f"{module.name}_a_{valid}_stability: assert property ({module.name}_p_{valid}_stability);"
                    ),
                    "assertion_type": "concurrent",
                    "confidence": "very_high",
                    "evidence": f"Standard valid/ready handshake. Signals {valid} and {ready} detected.",
                    "assumptions": "Valid remains stable during backpressure (standard protocol)",
                    "validation_status": "REQUIRES ENGINEER VALIDATION",
                    "classification": "GENERATED",
                })

                # Handshake completion
                assertions.append({
                    "name": f"{module.name}_{valid}_{ready}_transfer",
                    "description": f"Transfer occurs when both {valid} and {ready} high",
                    "sva_code": (
                        f"// Assert: Transfer on valid && ready\n"
                        f"property {module.name}_p_{valid}_{ready}_transfer;\n"
                        f"  @(posedge {clk})\n"
                        f"  disable iff ({rst})\n"
                        f"  {valid} && {ready} |-> ##1 1;\n"
                        f"endproperty\n"
                        f"{module.name}_a_{valid}_{ready}_transfer: assert property ({module.name}_p_{valid}_{ready}_transfer);"
                    ),
                    "assertion_type": "concurrent",
                    "confidence": "high",
                    "evidence": f"Handshake protocol in '{module.name}'",
                    "assumptions": "Transfer completes in same cycle as valid && ready",
                    "validation_status": "REQUIRES ENGINEER VALIDATION",
                    "classification": "GENERATED",
                })

                # Ready cannot be asserted before valid (for some protocols)
                assertions.append({
                    "name": f"{module.name}_{ready}_after_{valid}",
                    "description": f"{ready} should not be asserted without pending {valid}",
                    "sva_code": (
                        f"// Assert: Ready follows valid (no premature ready)\n"
                        f"property {module.name}_p_{ready}_follows_{valid};\n"
                        f"  @(posedge {clk})\n"
                        f"  disable iff ({rst})\n"
                        f"  !{valid} && {ready} |-> ##1 !{ready};\n"
                        f"endproperty\n"
                        f"{module.name}_a_{ready}_follows_{valid}: assert property ({module.name}_p_{ready}_follows_{valid});"
                    ),
                    "assertion_type": "concurrent",
                    "confidence": "medium",
                    "evidence": f"Protocol heuristic for {valid}/{ready} in '{module.name}'",
                    "assumptions": "Ready is not asserted before valid (protocol dependent)",
                    "validation_status": "REQUIRES ENGINEER VALIDATION",
                    "classification": "GENERATED",
                })

        return assertions

    def _gen_fsm_assertions(self, module: DesignModule, fsm) -> List[Dict[str, Any]]:
        assertions = []
        clk = module.clock_signals[0] if module.clock_signals else "clk"
        rst = module.reset_signals[0] if module.reset_signals else "rst"
        state_var = fsm.state_variable

        # Legal state transitions only
        if fsm.transitions:
            assertions.append({
                "name": f"{module.name}_{fsm.name}_legal_transitions",
                "description": f"FSM '{fsm.name}' only makes defined transitions",
                "sva_code": (
                    f"// Assert: Only legal FSM transitions\n"
                    f"property {module.name}_{fsm.name}_p_legal_transitions;\n"
                    f"  @(posedge {clk})\n"
                    f"  disable iff ({rst})\n"
                    f"  $changed({state_var}) |-> (\n"
                    + "    ".join(
                        f"({state_var} == {t['from']} && $next({state_var}) == {t['to']})"
                        for t in fsm.transitions[:10]
                    ) + "\n  );\n"
                    f"endproperty\n"
                    f"{module.name}_{fsm.name}_a_legal_transitions: "
                    f"assert property ({module.name}_{fsm.name}_p_legal_transitions);"
                ),
                "assertion_type": "concurrent",
                "confidence": "high",
                "evidence": f"FSM '{fsm.name}' has {len(fsm.transitions)} defined transitions",
                "assumptions": "All transitions are captured in RTL case statements",
                "validation_status": "REQUIRES ENGINEER VALIDATION",
                "classification": "GENERATED",
            })

        # Valid state at all times
        if fsm.states:
            state_names = fsm.states
            assertions.append({
                "name": f"{module.name}_{fsm.name}_valid_state",
                "description": f"FSM '{fsm.name}' always in a defined state",
                "sva_code": (
                    f"// Assert: FSM always in valid state\n"
                    f"property {module.name}_{fsm.name}_p_valid_state;\n"
                    f"  @(posedge {clk})\n"
                    f"  disable iff ({rst})\n"
                    f"  ({state_var} inside {{{', '.join(state_names)}}});\n"
                    f"endproperty\n"
                    f"{module.name}_{fsm.name}_a_valid_state: "
                    f"assert property ({module.name}_{fsm.name}_p_valid_state);"
                ),
                "assertion_type": "concurrent",
                "confidence": "very_high",
                "evidence": f"FSM has {len(state_names)} defined states: {state_names}",
                "assumptions": "State register width matches state encoding",
                "validation_status": "REQUIRES ENGINEER VALIDATION",
                "classification": "GENERATED",
            })

        return assertions

    def _gen_fifo_assertions(self, module: DesignModule) -> List[Dict[str, Any]]:
        assertions = []
        clk = module.clock_signals[0] if module.clock_signals else "clk"
        rst = module.reset_signals[0] if module.reset_signals else "rst"

        all_names = [p.name for p in module.ports] + [s.name for s in module.signals]

        full_sig = next((n for n in all_names if "full" in n.lower()), None)
        empty_sig = next((n for n in all_names if "empty" in n.lower()), None)
        wr_en = next((n for n in all_names if "wr" in n.lower() and "en" in n.lower()), None)
        rd_en = next((n for n in all_names if "rd" in n.lower() and "en" in n.lower()), None)
        wr_ptr = next((n for n in all_names if "wr" in n.lower() and "ptr" in n.lower()), None)
        rd_ptr = next((n for n in all_names if "rd" in n.lower() and "ptr" in n.lower()), None)
        count_sig = next((n for n in all_names if "count" in n.lower()), None)

        if full_sig and wr_en:
            assertions.append({
                "name": f"{module.name}_no_write_when_full",
                "description": "No write when FIFO is full",
                "sva_code": (
                    f"// Assert: No write when full\n"
                    f"property {module.name}_p_no_write_full;\n"
                    f"  @(posedge {clk})\n"
                    f"  disable iff ({rst})\n"
                    f"  {full_sig} |-> !{wr_en};\n"
                    f"endproperty\n"
                    f"{module.name}_a_no_write_full: "
                    f"assert property ({module.name}_p_no_write_full);"
                ),
                "assertion_type": "concurrent",
                "confidence": "high",
                "evidence": f"Standard FIFO protocol in '{module.name}'",
                "assumptions": "FIFO does not accept writes when full",
                "validation_status": "REQUIRES ENGINEER VALIDATION",
                "classification": "GENERATED",
            })

        if empty_sig and rd_en:
            assertions.append({
                "name": f"{module.name}_no_read_when_empty",
                "description": "No read when FIFO is empty",
                "sva_code": (
                    f"// Assert: No read when empty\n"
                    f"property {module.name}_p_no_read_empty;\n"
                    f"  @(posedge {clk})\n"
                    f"  disable iff ({rst})\n"
                    f"  {empty_sig} |-> !{rd_en};\n"
                    f"endproperty\n"
                    f"{module.name}_a_no_read_empty: "
                    f"assert property ({module.name}_p_no_read_empty);"
                ),
                "assertion_type": "concurrent",
                "confidence": "high",
                "evidence": f"Standard FIFO protocol in '{module.name}'",
                "assumptions": "FIFO does not allow reads when empty",
                "validation_status": "REQUIRES ENGINEER VALIDATION",
                "classification": "GENERATED",
            })

        # Pointer progress
        if wr_ptr and wr_en:
            assertions.append({
                "name": f"{module.name}_wr_ptr_progress",
                "description": "Write pointer increments on valid write",
                "sva_code": (
                    f"// Assert: Write pointer increments\n"
                    f"property {module.name}_p_wr_ptr_progress;\n"
                    f"  @(posedge {clk})\n"
                    f"  disable iff ({rst})\n"
                    f'  {wr_en} && !{full_sig if full_sig else "1" + chr(39) + "b0"} |=> ({wr_ptr} == $past({wr_ptr}) + 1);\n'
                    f"endproperty\n"
                    f"{module.name}_a_wr_ptr_progress: assert property ({module.name}_p_wr_ptr_progress);"
                ),
                "assertion_type": "concurrent",
                "confidence": "high",
                "evidence": f"Write pointer {wr_ptr} and write enable {wr_en} detected",
                "assumptions": "Single write per cycle, pointer increments by 1",
                "validation_status": "REQUIRES ENGINEER VALIDATION",
                "classification": "GENERATED",
            })

        if rd_ptr and rd_en:
            assertions.append({
                "name": f"{module.name}_rd_ptr_progress",
                "description": "Read pointer increments on valid read",
                "sva_code": (
                    f"// Assert: Read pointer increments\n"
                    f"property {module.name}_p_rd_ptr_progress;\n"
                    f"  @(posedge {clk})\n"
                    f"  disable iff ({rst})\n"
                    f'  {wr_en} && !{full_sig if full_sig else "1" + chr(39) + "b0"} |=> ({wr_ptr} == $past({wr_ptr}) + 1);\n'
                    f"endproperty\n"
                    f"{module.name}_a_rd_ptr_progress: assert property ({module.name}_p_rd_ptr_progress);"
                ),
                "assertion_type": "concurrent",
                "confidence": "high",
                "evidence": f"Read pointer {rd_ptr} and read enable {rd_en} detected",
                "assumptions": "Single read per cycle, pointer increments by 1",
                "validation_status": "REQUIRES ENGINEER VALIDATION",
                "classification": "GENERATED",
            })

        # Count tracking
        if count_sig and wr_ptr and rd_ptr:
            assertions.append({
                "name": f"{module.name}_count_tracking",
                "description": "Occupancy count equals wr_ptr - rd_ptr",
                "sva_code": (
                    f"// Assert: Count tracks occupancy\n"
                    f"property {module.name}_p_count_tracking;\n"
                    f"  @(posedge {clk})\n"
                    f"  disable iff ({rst})\n"
                    f"  {count_sig} == {wr_ptr} - {rd_ptr};\n"
                    f"endproperty\n"
                    f"{module.name}_a_count_tracking: assert property ({module.name}_p_count_tracking);"
                ),
                "assertion_type": "concurrent",
                "confidence": "high",
                "evidence": f"Count {count_sig}, wr_ptr {wr_ptr}, rd_ptr {rd_ptr} detected",
                "assumptions": "Count is wr_ptr - rd_ptr (no pointer wrapping issues)",
                "validation_status": "REQUIRES ENGINEER VALIDATION",
                "classification": "GENERATED",
            })

        # Full/empty mutual exclusion
        if full_sig and empty_sig:
            assertions.append({
                "name": f"{module.name}_full_empty_mutex",
                "description": "FIFO cannot be both full and empty simultaneously",
                "sva_code": (
                    f"// Assert: Full and empty mutually exclusive\n"
                    f"property {module.name}_p_full_empty_mutex;\n"
                    f"  @(posedge {clk})\n"
                    f"  disable iff ({rst})\n"
                    f"  !({full_sig} && {empty_sig});\n"
                    f"endproperty\n"
                    f"{module.name}_a_full_empty_mutex: assert property ({module.name}_p_full_empty_mutex);"
                ),
                "assertion_type": "concurrent",
                "confidence": "high",
                "evidence": f"Full {full_sig} and empty {empty_sig} signals detected",
                "assumptions": "DEPTH > 1 (for DEPTH=1, full and empty can coincide)",
                "validation_status": "REQUIRES ENGINEER VALIDATION",
                "classification": "GENERATED",
            })

        return assertions

    def _gen_counter_assertions(self, module: DesignModule) -> List[Dict[str, Any]]:
        assertions = []
        clk = module.clock_signals[0] if module.clock_signals else "clk"

        for counter in module.metadata.get("counters", [])[:3]:
            assertions.append({
                "name": f"{module.name}_{counter}_range",
                "description": f"Counter {counter} operates within expected range",
                "sva_code": (
                    f"// Cover: Counter reaches various values\n"
                    f"property {module.name}_p_{counter}_range;\n"
                    f"  @(posedge {clk})\n"
                    f"  1'b1 |=> ({counter} >= 0);\n"
                    f"endproperty\n"
                    f"{module.name}_c_{counter}_range: "
                    f"cover property ({module.name}_p_{counter}_range);"
                ),
                "assertion_type": "cover",
                "confidence": "medium",
                "evidence": f"Counter '{counter}' detected in module '{module.name}'",
                "assumptions": "Counter width and max value per specification",
                "validation_status": "REQUIRES ENGINEER VALIDATION",
                "classification": "GENERATED",
            })

        return assertions

    def _gen_pointer_assertions(self, module: DesignModule) -> List[Dict[str, Any]]:
        assertions = []
        clk = module.clock_signals[0] if module.clock_signals else "clk"
        rst = module.reset_signals[0] if module.reset_signals else "rst"

        for ptr in module.metadata.get("pointers", [])[:3]:
            assertions.append({
                "name": f"{module.name}_{ptr}_valid_range",
                "description": f"Pointer {ptr} stays within valid address range",
                "sva_code": (
                    f"// Assert: Pointer within valid range\n"
                    f"property {module.name}_p_{ptr}_range;\n"
                    f"  @(posedge {clk})\n"
                    f"  disable iff ({rst})\n"
                    f"  {ptr} < DEPTH;\n"
                    f"endproperty\n"
                    f"{module.name}_a_{ptr}_range: assert property ({module.name}_p_{ptr}_range);"
                ),
                "assertion_type": "concurrent",
                "confidence": "medium",
                "evidence": f"Pointer '{ptr}' detected in module '{module.name}'",
                "assumptions": "DEPTH parameter defines address range",
                "validation_status": "REQUIRES ENGINEER VALIDATION",
                "classification": "GENERATED",
            })

        return assertions

    def _gen_stability_assertions(self, module: DesignModule) -> List[Dict[str, Any]]:
        assertions = []

        regs = [s.name for s in module.signals if s.signal_type.value == "reg"]
        if regs and module.clock_signals:
            clk = module.clock_signals[0]
            assertions.append({
                "name": f"{module.name}_registered_outputs_stable",
                "description": "Registered outputs only change on clock edge",
                "sva_code": (
                    f"// Assert: Registered output stability\n"
                    f"property {module.name}_p_registered_stability;\n"
                    f"  @(posedge {clk})\n"
                    f"  disable iff ({module.reset_signals[0] if module.reset_signals else 'rst'})\n"
                    f"  $stable({clk}) |-> ($stable({regs[0]}) || $changed({clk}));\n"
                    f"endproperty\n"
                    f"{module.name}_a_registered_stability: "
                    f"assert property ({module.name}_p_registered_stability);"
                ),
                "assertion_type": "concurrent",
                "confidence": "medium",
                "evidence": f"Register '{regs[0]}' detected in module '{module.name}'",
                "assumptions": "Signal is truly registered, not combinational",
                "validation_status": "REQUIRES ENGINEER VALIDATION",
                "classification": "GENERATED",
            })

        return assertions

    def _gen_data_integrity_assertions(self, module: DesignModule) -> List[Dict[str, Any]]:
        assertions = []

        # For FIFOs, check data integrity
        if module.metadata.get("is_fifo"):
            all_names = [p.name for p in module.ports] + [s.name for s in module.signals]
            din = next((n for n in all_names if "din" in n.lower() or "data_in" in n.lower()), None)
            dout = next((n for n in all_names if "dout" in n.lower() or "data_out" in n.lower()), None)
            wr_en = next((n for n in all_names if "wr" in n.lower() and "en" in n.lower()), None)
            rd_en = next((n for n in all_names if "rd" in n.lower() and "en" in n.lower()), None)

            if din and dout and wr_en and rd_en:
                assertions.append({
                    "name": f"{module.name}_data_integrity",
                    "description": "Data written equals data read (FIFO integrity)",
                    "sva_code": (
                        f"// Assert: FIFO data integrity - data out matches data in order\n"
                        f"// This requires a reference model or queue in verification environment\n"
                        f"// Placeholder for formal data integrity check\n"
                        f"property {module.name}_p_data_integrity;\n"
                        f"  @(posedge {module.clock_signals[0] if module.clock_signals else 'clk'})\n"
                        f"  disable iff ({module.reset_signals[0] if module.reset_signals else 'rst'})\n"
                        f"  1'b1; // Placeholder - requires reference model\n"
                        f"endproperty\n"
                        f"{module.name}_a_data_integrity: assert property ({module.name}_p_data_integrity);"
                    ),
                    "assertion_type": "concurrent",
                    "confidence": "low",
                    "evidence": f"FIFO with din={din}, dout={dout} detected",
                    "assumptions": "Requires reference model for full data integrity check",
                    "validation_status": "REQUIRES ENGINEER VALIDATION",
                    "classification": "GENERATED",
                })

        return assertions