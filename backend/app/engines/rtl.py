"""RTL Analyzer - Deterministic SystemVerilog/Verilog parser."""

import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class SignalDirection(str, Enum):
    INPUT = "input"
    OUTPUT = "output"
    INOUT = "inout"
    INTERNAL = "internal"


class SignalType(str, Enum):
    WIRE = "wire"
    REG = "reg"
    LOGIC = "logic"
    INTEGER = "integer"
    REAL = "real"
    BIT = "bit"
    TRI = "tri"
    WAND = "wand"
    WOR = "wor"
    UNKNOWN = "unknown"


class ModuleType(str, Enum):
    MODULE = "module"
    INTERFACE = "interface"
    PACKAGE = "package"
    PROGRAM = "program"


@dataclass
class Parameter:
    name: str
    default_value: str = ""
    type: str = "integer"
    line: int = 0


@dataclass
class Port:
    name: str
    direction: SignalDirection = SignalDirection.INPUT
    width: str = ""
    type: str = "logic"
    line: int = 0


@dataclass
class Signal:
    name: str
    signal_type: SignalType = SignalType.WIRE
    width: str = ""
    line: int = 0


@dataclass
class FSMState:
    name: str
    encoding: str = ""
    line: int = 0


@dataclass
class FSMTransition:
    from_state: str
    to_state: str
    condition: str = ""
    line: int = 0


@dataclass
class FSMInfo:
    name: str
    current_signal: str = ""
    states: List[str] = field(default_factory=list)
    transitions: List[Dict[str, str]] = field(default_factory=list)
    state_variable: str = ""
    line: int = 0


@dataclass
class AlwaysBlock:
    sensitivity: str = ""
    clock: str = ""
    reset: str = ""
    reset_type: str = ""
    statements: List[str] = field(default_factory=list)
    line: int = 0


@dataclass
class DesignModule:
    name: str
    module_type: ModuleType = ModuleType.MODULE
    is_top: bool = False
    start_line: int = 0
    end_line: int = 0
    parameters: List[Parameter] = field(default_factory=list)
    ports: List[Port] = field(default_factory=list)
    signals: List[Signal] = field(default_factory=list)
    fsm_info: List[FSMInfo] = field(default_factory=list)
    instances: List[Dict[str, Any]] = field(default_factory=list)
    always_blocks: List[AlwaysBlock] = field(default_factory=list)
    assigns: List[Dict[str, Any]] = field(default_factory=list)
    assertions: List[Dict[str, Any]] = field(default_factory=list)
    functions: List[Dict[str, Any]] = field(default_factory=list)
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def clock_signals(self) -> List[str]:
        clocks = set()
        for ab in self.always_blocks:
            if ab.clock:
                clocks.add(ab.clock)
        return list(clocks)

    @property
    def reset_signals(self) -> List[str]:
        resets = set()
        for ab in self.always_blocks:
            if ab.reset:
                resets.add(ab.reset)
        return list(resets)

    @property
    def input_ports(self) -> List[Port]:
        return [p for p in self.ports if p.direction == SignalDirection.INPUT]

    @property
    def output_ports(self) -> List[Port]:
        return [p for p in self.ports if p.direction == SignalDirection.OUTPUT]

    @property
    def has_fsm(self) -> bool:
        return len(self.fsm_info) > 0

    @property
    def has_assertions(self) -> bool:
        return len(self.assertions) > 0


class RTLAnalyzer:
    """Comprehensive SystemVerilog/Verilog parser for design analysis."""

    def __init__(self):
        self.modules: List[DesignModule] = []
        self._current_module: Optional[DesignModule] = None
        self._content: str = ""
        self._lines: List[str] = []
        self._defines: Dict[str, str] = {}
        self._includes: List[str] = []

    def analyze(self, content: str, filename: str = "") -> List[DesignModule]:
        """Parse SystemVerilog/Verilog content and return extracted modules."""
        self._content = content
        self._lines = content.split("\n")
        self.modules = []
        self._parse_defines()
        self._parse_includes()
        self._parse_modules()
        self._analyze_fsms()
        self._analyze_protocols()
        self._identify_counters_and_pointers()
        return self.modules

    def _parse_defines(self) -> None:
        for i, line in enumerate(self._lines):
            match = re.match(r'\s*`define\s+(\w+)\s*(.*)', line)
            if match:
                self._defines[match.group(1)] = match.group(2).strip()

    def _parse_includes(self) -> None:
        for line in self._lines:
            match = re.match(r'\s*`include\s+["<](.+)[">]', line)
            if match:
                self._includes.append(match.group(1))

    def _parse_modules(self) -> None:
        i = 0
        while i < len(self._lines):
            line = self._lines[i]
            stripped = line.strip()

            # Check if this line starts a module declaration
            mod_type = None
            for mt in [ModuleType.MODULE, ModuleType.INTERFACE,
                       ModuleType.PACKAGE, ModuleType.PROGRAM]:
                keyword = mt.value
                if re.match(rf'\s*{keyword}\s+\w+', stripped):
                    mod_type = mt
                    break

            if mod_type:
                # Found a module declaration, now find the complete declaration
                # which may span multiple lines
                decl_lines = []
                j = i
                paren_depth = 0
                found_open_paren = False
                
                while j < len(self._lines):
                    decl_lines.append(self._lines[j])
                    current_line = self._lines[j]
                    paren_depth += current_line.count('(') - current_line.count(')')
                    if '(' in current_line:
                        found_open_paren = True
                    if found_open_paren and paren_depth <= 0:
                        break
                    j += 1
                    if j >= len(self._lines):
                        break
                
                # Combine declaration lines
                full_decl = ' '.join(l.strip() for l in decl_lines)
                
                # Extract module name, parameters, and ports manually
                keyword = mod_type.value
                name_match = re.match(rf'\s*{keyword}\s+(\w+)', full_decl)
                if not name_match:
                    i += 1
                    continue
                
                module_name = name_match.group(1)
                
                # Find parameter section
                param_str = ""
                param_start = full_decl.find('#(')
                if param_start != -1:
                    param_start += 2  # Skip '#('
                    param_depth = 1
                    k = param_start
                    while k < len(full_decl) and param_depth > 0:
                        if full_decl[k] == '(':
                            param_depth += 1
                        elif full_decl[k] == ')':
                            param_depth -= 1
                        k += 1
                    param_str = full_decl[param_start:k-1]
                
                # Find port section
                port_str = ""
                port_start = full_decl.find(') (')
                if port_start != -1:
                    port_start += 3  # Skip ') ('
                    port_depth = 1
                    k = port_start
                    while k < len(full_decl) and port_depth > 0:
                        if full_decl[k] == '(':
                            port_depth += 1
                        elif full_decl[k] == ')':
                            port_depth -= 1
                        k += 1
                    port_str = full_decl[port_start:k-1]
                
                self._parse_module_body_direct(i, mod_type, module_name, param_str, port_str)
                i = j + 1
                continue

            if self._current_module and i < self._current_module.end_line:
                i = self._current_module.end_line + 1
                self._current_module = None
            else:
                i += 1

    def _parse_module_body_direct(self, start_line: int, mod_type: ModuleType,
                                  module_name: str, param_str: str, port_str: str) -> None:
        module = DesignModule(
            name=module_name,
            module_type=mod_type,
            start_line=start_line + 1,
        )

        if param_str:
            module.parameters = self._parse_parameters(param_str, start_line)

        # Skip _parse_port_list as it doesn't correctly parse ANSI-style ports
        # The ANSI port parsing in _parse_module_content will handle this correctly

        depth = 0
        end_line = start_line
        for i in range(start_line, len(self._lines)):
            line = self._lines[i].strip()
            # Use word boundaries to avoid matching 'module' inside 'endmodule'
            depth += len(re.findall(r'\bmodule\b', line)) + len(re.findall(r'\binterface\b', line)) + \
                     len(re.findall(r'\bpackage\b', line)) + len(re.findall(r'\bprogram\b', line)) \
                     - len(re.findall(r'\bendmodule\b', line)) - len(re.findall(r'\bendinterface\b', line)) \
                     - len(re.findall(r'\bendpackage\b', line)) - len(re.findall(r'\bendprogram\b', line))
            if depth <= 0:
                end_line = i
                break

        module.end_line = end_line + 1

        body_lines = self._lines[start_line:end_line + 1]
        self._parse_module_content(module, body_lines, start_line)

        self.modules.append(module)
        self._current_module = module

    def _parse_module_body(self, start_line: int, mod_type: ModuleType,
                           match: re.Match) -> None:
        module_name = match.group(1)
        module = DesignModule(
            name=module_name,
            module_type=mod_type,
            start_line=start_line + 1,
        )

        param_str = match.group(3) or ""
        if param_str:
            module.parameters = self._parse_parameters(param_str, start_line)

        port_str = match.group(4) or ""
        if port_str:
            module.ports = self._parse_port_list(port_str, start_line)

        depth = 0
        end_line = start_line
        for i in range(start_line, len(self._lines)):
            line = self._lines[i].strip()
            # Use word boundaries to avoid matching 'module' inside 'endmodule'
            depth += len(re.findall(r'\bmodule\b', line)) + len(re.findall(r'\binterface\b', line)) + \
                     len(re.findall(r'\bpackage\b', line)) + len(re.findall(r'\bprogram\b', line)) \
                     - len(re.findall(r'\bendmodule\b', line)) - len(re.findall(r'\bendinterface\b', line)) \
                     - len(re.findall(r'\bendpackage\b', line)) - len(re.findall(r'\bendprogram\b', line))
            if depth <= 0:
                end_line = i
                break

        module.end_line = end_line + 1

        body_lines = self._lines[start_line:end_line + 1]
        self._parse_module_content(module, body_lines, start_line)

        self.modules.append(module)
        self._current_module = module

    def _parse_parameters(self, param_str: str, base_line: int) -> List[Parameter]:
        params = []
        for part in param_str.split(","):
            part = part.strip()
            if not part:
                continue
            # Handle SystemVerilog parameter declarations:
            # parameter int DEPTH = 16
            # parameter DEPTH = 16
            # int DEPTH = 16
            # DEPTH = 16
            match = re.match(r'(?:parameter\s+)?(?:int|bit|logic|string|real|realtime|shortint|longint|byte|chandle|event)?\s*(\w+)\s*(?:=\s*(.+))?', part)
            if match:
                params.append(Parameter(
                    name=match.group(1).strip(),
                    default_value=(match.group(2) or "").strip(),
                    line=base_line + 1,
                ))
        return params

    def _parse_port_list(self, port_str: str, base_line: int) -> List[Port]:
        ports = []
        for part in port_str.split(","):
            part = part.strip()
            if not part:
                continue
            match = re.match(r'(\w+)', part)
            if match:
                ports.append(Port(
                    name=match.group(1),
                    line=base_line + 1,
                ))
        return ports

    def _parse_module_content(self, module: DesignModule, lines: List[str],
                              base_line: int) -> None:
        content = "\n".join(lines)

        self._parse_ansi_ports(module, content, base_line)
        self._parse_internal_signals(module, content, base_line)
        self._parse_always_blocks(module, content, base_line)
        self._parse_assigns(module, content, base_line)
        self._parse_instances(module, content, base_line)
        self._parse_assertions(module, content, base_line)
        self._parse_functions(module, content, base_line)
        self._parse_tasks(module, content, base_line)

    def _parse_ansi_ports(self, module: DesignModule, content: str,
                          base_line: int) -> None:
        pattern = re.compile(
            r'\b(input|output|inout)\s+'
            r'(?:var\s+)?'
            r'(?:(?:logic|wire|reg|bit)\s+)?'
            r'(?:(?:signed|unsigned)\s+)?'
            r'(?:(\[[^\]]+\])\s+)?'
            r'(\w+)',
            re.MULTILINE
        )

        for match in pattern.finditer(content):
            direction_str = match.group(1)
            width = match.group(2) or ""
            name = match.group(3)

            direction = {
                "input": SignalDirection.INPUT,
                "output": SignalDirection.OUTPUT,
                "inout": SignalDirection.INOUT,
            }.get(direction_str, SignalDirection.INPUT)

            pos = match.start()
            line_num = content[:pos].count("\n") + base_line + 1

            existing = next((p for p in module.ports if p.name == name), None)
            if existing:
                existing.direction = direction
                existing.width = width.strip()
                existing.line = line_num
            else:
                module.ports.append(Port(
                    name=name,
                    direction=direction,
                    width=width.strip(),
                    line=line_num,
                ))

    def _parse_internal_signals(self, module: DesignModule, content: str,
                                base_line: int) -> None:
        pattern = re.compile(
            r'\b(logic|wire|reg|bit|integer|real|tri|wand|wor)\s+'
            r'(?:(?:signed|unsigned)\s+)?'
            r'(?:(\[[^\]]+\])\s+)?'
            r'(\w+)',
            re.MULTILINE
        )

        for match in pattern.finditer(content):
            type_str = match.group(1)
            width = match.group(2) or ""
            name = match.group(3)

            type_map = {
                "logic": SignalType.LOGIC,
                "wire": SignalType.WIRE,
                "reg": SignalType.REG,
                "bit": SignalType.BIT,
                "integer": SignalType.INTEGER,
                "real": SignalType.REAL,
                "tri": SignalType.TRI,
                "wand": SignalType.WAND,
                "wor": SignalType.WOR,
            }

            pos = match.start()
            line_num = content[:pos].count("\n") + base_line + 1

            if not any(p.name == name for p in module.ports):
                module.signals.append(Signal(
                    name=name,
                    signal_type=type_map.get(type_str, SignalType.UNKNOWN),
                    width=width.strip(),
                    line=line_num,
                ))

    def _parse_always_blocks(self, module: DesignModule, content: str,
                             base_line: int) -> None:
        pattern = re.compile(
            r'\b(always(?:_ff|_comb|_latch)?|always)\s*@\s*\(\s*([^)]*)\s*\)',
            re.MULTILINE
        )

        for match in pattern.finditer(content):
            sensitivity = match.group(2).strip()
            pos = match.start()
            line_num = content[:pos].count("\n") + base_line + 1

            clock = ""
            reset = ""
            reset_type = ""

            if "posedge" in sensitivity or "negedge" in sensitivity:
                edges = re.findall(r'(posedge|negedge)\s+(\w+)', sensitivity)
                if edges:
                    clock = edges[0][1]
                    if len(edges) > 1:
                        reset = edges[1][1]
                        reset_type = "async"
                block_start = match.end()
                block_text = content[block_start:block_start + 500]
                reset_match = re.search(
                    r'if\s*\(\s*(!?\s*(\w+))\s*\)', block_text
                )
                if reset_match and not reset:
                    reset = reset_match.group(2)
                    reset_type = "sync"
            else:
                sensitivity = "comb"

            module.always_blocks.append(AlwaysBlock(
                sensitivity=sensitivity,
                clock=clock,
                reset=reset,
                reset_type=reset_type,
                line=line_num,
            ))

    def _parse_assigns(self, module: DesignModule, content: str,
                       base_line: int) -> None:
        pattern = re.compile(r'\bassign\s+(\w+)\s*=', re.MULTILINE)
        for match in pattern.finditer(content):
            pos = match.start()
            line_num = content[:pos].count("\n") + base_line + 1
            module.assigns.append({
                "target": match.group(1),
                "line": line_num,
            })

    def _parse_instances(self, module: DesignModule, content: str,
                         base_line: int) -> None:
        pattern = re.compile(
            r'(\w+)\s*(?:#\s*\([^)]*\))?\s+(\w+)\s*\.\s*('
            r'\([^)]*\)|$)',
            re.MULTILINE
        )

        for match in pattern.finditer(content):
            mod_name = match.group(1)
            inst_name = match.group(2)

            if mod_name in ("if", "else", "for", "while", "case", "assign",
                          "always", "initial", "module", "function", "task",
                          "input", "output", "inout", "logic", "wire", "reg"):
                continue

            pos = match.start()
            line_num = content[:pos].count("\n") + base_line + 1

            connections = {}
            port_str = match.group(3)
            if port_str and port_str.startswith("("):
                connections = self._parse_port_connections(port_str)

            module.instances.append({
                "module_name": mod_name,
                "instance_name": inst_name,
                "connections": connections,
                "line": line_num,
            })

    def _parse_port_connections(self, port_str: str) -> Dict[str, str]:
        connections = {}
        inner = port_str.strip("()")
        for part in inner.split(","):
            part = part.strip()
            if "." in part:
                match = re.match(r'\.(\w+)\s*\(\s*(.*)\s*\)', part)
                if match:
                    connections[match.group(1)] = match.group(2).strip()
        return connections

    def _parse_assertions(self, module: DesignModule, content: str,
                          base_line: int) -> None:
        # Pattern 1: property <name>; or property <name> (...)
        prop_decl_pattern = re.compile(r'\bproperty\s+(\w+)', re.MULTILINE)
        # Pattern 2: assert property (<expr>); or label: assert property (<expr>);
        assert_prop_pattern = re.compile(r'(?:(\w+):\s*)?assert\s+property\s*\(', re.MULTILINE)
        # Pattern 3: assume property
        assume_prop_pattern = re.compile(r'\bassume\s+property\s*\(', re.MULTILINE)
        # Pattern 4: cover property
        cover_prop_pattern = re.compile(r'\bcover\s+property\s*\(', re.MULTILINE)
        # Pattern 5: immediate assert
        assert_imm_pattern = re.compile(r'\bassert\s+(\w+)', re.MULTILINE)

        # Parse property declarations
        for match in prop_decl_pattern.finditer(content):
            pos = match.start()
            line_num = content[:pos].count("\n") + base_line + 1
            name = match.group(1)
            # Extract full property code
            start = match.start()
            depth = 0
            end = start
            for j in range(start, min(start + 5000, len(content))):
                if content[j] == "(":
                    depth += 1
                elif content[j] == ")":
                    depth -= 1
                elif content[j] == ";" and depth == 0:
                    end = j + 1
                    break
                elif content[j:j+11] == "endproperty":
                    end = j + 11
                    break
            module.assertions.append({
                "name": name,
                "code": content[start:end].strip(),
                "type": "property",
                "line": line_num,
            })

        # Parse assert property
        for match in assert_prop_pattern.finditer(content):
            pos = match.start()
            line_num = content[:pos].count("\n") + base_line + 1
            label = match.group(1) if match.group(1) else f"assert_{line_num}"
            start = match.start()
            depth = 0
            end = start
            for j in range(start, min(start + 2000, len(content))):
                if content[j] == "(":
                    depth += 1
                elif content[j] == ")":
                    depth -= 1
                    if depth <= 0:
                        end = j + 1
                        break
            module.assertions.append({
                "name": label,
                "code": content[start:end].strip(),
                "type": "assert",
                "line": line_num,
            })

        # Parse assume property
        for match in assume_prop_pattern.finditer(content):
            pos = match.start()
            line_num = content[:pos].count("\n") + base_line + 1
            start = match.start()
            depth = 0
            end = start
            for j in range(start, min(start + 2000, len(content))):
                if content[j] == "(":
                    depth += 1
                elif content[j] == ")":
                    depth -= 1
                    if depth <= 0:
                        end = j + 1
                        break
            module.assertions.append({
                "name": f"assume_{line_num}",
                "code": content[start:end].strip(),
                "type": "assume",
                "line": line_num,
            })

        # Parse cover property
        for match in cover_prop_pattern.finditer(content):
            pos = match.start()
            line_num = content[:pos].count("\n") + base_line + 1
            start = match.start()
            depth = 0
            end = start
            for j in range(start, min(start + 2000, len(content))):
                if content[j] == "(":
                    depth += 1
                elif content[j] == ")":
                    depth -= 1
                    if depth <= 0:
                        end = j + 1
                        break
            module.assertions.append({
                "name": f"cover_{line_num}",
                "code": content[start:end].strip(),
                "type": "cover",
                "line": line_num,
            })

        # Parse immediate assertions
        for match in assert_imm_pattern.finditer(content):
            pos = match.start()
            line_num = content[:pos].count("\n") + base_line + 1
            # Skip if already captured as assert property
            if match.group(1) != "property":
                module.assertions.append({
                    "name": match.group(1),
                    "code": match.group(0).strip(),
                    "type": "assert_immediate",
                    "line": line_num,
                })

    def _parse_functions(self, module: DesignModule, content: str,
                         base_line: int) -> None:
        pattern = re.compile(
            r'\bfunction\s+(?:automatic\s+)?(\w+)\s+(\w+)\s*\(([^)]*)\)',
            re.MULTILINE
        )
        for match in pattern.finditer(content):
            pos = match.start()
            line_num = content[:pos].count("\n") + base_line + 1
            args = [a.strip() for a in match.group(3).split(",") if a.strip()]
            module.functions.append({
                "name": match.group(2),
                "return_type": match.group(1),
                "arguments": args,
                "line": line_num,
            })

    def _parse_tasks(self, module: DesignModule, content: str,
                     base_line: int) -> None:
        pattern = re.compile(
            r'\btask\s+(?:automatic\s+)?(\w+)\s*\(([^)]*)\)',
            re.MULTILINE
        )
        for match in pattern.finditer(content):
            pos = match.start()
            line_num = content[:pos].count("\n") + base_line + 1
            args = [a.strip() for a in match.group(2).split(",") if a.strip()]
            module.tasks.append({
                "name": match.group(1),
                "arguments": args,
                "line": line_num,
            })

    def _analyze_fsms(self) -> None:
        for module in self.modules:
            fsm_candidates = self._detect_fsm(module)
            module.fsm_info = fsm_candidates

    def _detect_fsm(self, module: DesignModule) -> List[FSMInfo]:
        fsms = []
        case_pattern = re.compile(r'\bcase\s*\(\s*(\w+)\s*\)', re.MULTILINE)
        module_content = "\n".join(self._lines[module.start_line-1:module.end_line])

        for ab in module.always_blocks:
            for match in case_pattern.finditer(module_content):
                state_var = match.group(1)
                pos = match.start()
                line_num = module.start_line + module_content[:pos].count("\n")

                states = self._extract_case_states(module_content, match.end())

                if states and self._looks_like_fsm(states):
                    transitions = self._extract_transitions(
                        module_content, match.end(), states, state_var
                    )
                    fsms.append(FSMInfo(
                        name=f"fsm_{state_var}",
                        current_signal=state_var,
                        states=states,
                        transitions=transitions,
                        state_variable=state_var,
                        line=line_num,
                    ))

        return fsms

    def _extract_case_states(self, content: str, start: int) -> List[str]:
        states = []
        depth = 0
        i = start
        while i < len(content) and i < start + 5000:
            ch = content[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            elif ch == ":" and depth == 0:
                j = i - 1
                while j >= 0 and content[j] in " \t\n\r":
                    j -= 1
                name_end = j + 1
                while j >= 0 and (content[j].isalnum() or content[j] == "_"):
                    j -= 1
                state_name = content[j+1:name_end].strip()
                if state_name and state_name not in ("endcase", "default", "endswitch"):
                    states.append(state_name)
            elif ch == "e" and content[i:i+8] == "endcase":
                break
            i += 1
        return states

    def _looks_like_fsm(self, states: List[str]) -> bool:
        if len(states) < 2:
            return False
        state_names = [s.upper() for s in states]
        fsm_keywords = ["IDLE", "WAIT", "START", "DONE", "ERROR", "RESET",
                       "ACTIVE", "BUSY", "READY", "VALID", "LOAD", "FETCH",
                       "EXEC", "WRITE", "READ", "INIT", "SETUP"]
        matches = sum(1 for s in state_names if any(kw in s for kw in fsm_keywords))
        return matches >= 1 or len(states) >= 3

    def _extract_transitions(self, content: str, start: int,
                             states: List[str], state_var: str) -> List[Dict[str, str]]:
        transitions = []
        pattern = re.compile(
            rf'{re.escape(state_var)}\s*<=?\s*(\w+)',
            re.MULTILINE
        )
        for match in pattern.finditer(content, start):
            next_state = match.group(1)
            if next_state in states:
                pos = match.start()
                preceding = content[max(0, pos-200):pos]
                source_state = None
                for s in reversed(states):
                    if s in preceding:
                        source_state = s
                        break
                if source_state:
                    transitions.append({
                        "from": source_state,
                        "to": next_state,
                    })
        return transitions

    def _analyze_protocols(self) -> None:
        for module in self.modules:
            content = "\n".join(self._lines[module.start_line-1:module.end_line])
            metadata = module.metadata

            signals = [s.name for s in module.signals] + [p.name for p in module.ports]
            has_valid = any("valid" in s.lower() for s in signals)
            has_ready = any("ready" in s.lower() for s in signals)
            has_enable = any("enable" in s.lower() or "en" == s.lower() for s in signals)

            if has_valid and has_ready:
                metadata["protocol"] = "valid_ready_handshake"
                module.metadata["valid_ready_interfaces"] = [
                    {"valid": v, "ready": r}
                    for v in signals if "valid" in v.lower()
                    for r in signals if "ready" in r.lower()
                ]
            elif has_enable:
                metadata["protocol"] = "enable_based"

            has_fifo = any("fifo" in s.lower() for s in signals)
            has_full = any("full" in s.lower() for s in signals)
            has_empty = any("empty" in s.lower() for s in signals)
            if has_fifo or (has_full and has_empty):
                metadata["is_fifo"] = True
                module.metadata["fifo_candidates"] = [
                    {"full": f, "empty": e}
                    for f in signals if "full" in f.lower()
                    for e in signals if "empty" in e.lower()
                ]

    def _identify_counters_and_pointers(self) -> None:
        for module in self.modules:
            all_names = [s.name for s in module.signals] + [p.name for p in module.ports]

            counters = [n for n in all_names if "count" in n.lower() or "cnt" == n.lower()]
            if counters:
                module.metadata["counters"] = counters

            pointers = [n for n in all_names if "ptr" in n.lower() or "pointer" in n.lower()]
            if pointers:
                module.metadata["pointers"] = pointers

    def get_summary(self) -> Dict[str, Any]:
        total_ports = sum(len(m.ports) for m in self.modules)
        total_signals = sum(len(m.signals) for m in self.modules)
        total_fsms = sum(len(m.fsm_info) for m in self.modules)
        total_assertions = sum(len(m.assertions) for m in self.modules)
        total_instances = sum(len(m.instances) for m in self.modules)
        total_always = sum(len(m.always_blocks) for m in self.modules)

        return {
            "num_modules": len(self.modules),
            "module_names": [m.name for m in self.modules],
            "total_ports": total_ports,
            "total_internal_signals": total_signals,
            "total_fsm_count": total_fsms,
            "total_assertions": total_assertions,
            "total_module_instances": total_instances,
            "total_always_blocks": total_always,
            "clock_signals": list(set(c for m in self.modules for c in m.clock_signals)),
            "reset_signals": list(set(r for m in self.modules for r in m.reset_signals)),
            "protocols_detected": list(set(
                m.metadata.get("protocol", "none")
                for m in self.modules
                if m.metadata.get("protocol")
            )),
            "modules_with_fsm": [m.name for m in self.modules if m.has_fsm],
            "modules_with_assertions": [m.name for m in self.modules if m.has_assertions],
            "fifo_candidates": [m.name for m in self.modules if m.metadata.get("is_fifo")],
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "modules": [
                {
                    "name": m.name,
                    "module_type": m.module_type.value,
                    "is_top": m.is_top,
                    "start_line": m.start_line,
                    "end_line": m.end_line,
                    "parameters": [
                        {"name": p.name, "default_value": p.default_value, "line": p.line}
                        for p in m.parameters
                    ],
                    "ports": [
                        {"name": p.name, "direction": p.direction.value, "width": p.width, "line": p.line}
                        for p in m.ports
                    ],
                    "signals": [
                        {"name": s.name, "type": s.signal_type.value, "width": s.width, "line": s.line}
                        for s in m.signals
                    ],
                    "fsm_info": [
                        {
                            "name": f.name,
                            "state_variable": f.state_variable,
                            "states": f.states,
                            "transitions": f.transitions,
                            "line": f.line,
                        }
                        for f in m.fsm_info
                    ],
                    "instances": m.instances,
                    "always_blocks": [
                        {
                            "sensitivity": a.sensitivity,
                            "clock": a.clock,
                            "reset": a.reset,
                            "reset_type": a.reset_type,
                            "line": a.line,
                        }
                        for a in m.always_blocks
                    ],
                    "assigns": m.assigns,
                    "assertions": m.assertions,
                    "functions": m.functions,
                    "tasks": m.tasks,
                    "metadata": m.metadata,
                }
                for m in self.modules
            ],
            "summary": self.get_summary(),
        }