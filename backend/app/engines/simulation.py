"""Simulation Engine - Manages simulation execution with Verilator adapter."""

import subprocess
import tempfile
import os
import time
import shutil
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class SimulationConfig:
    simulator: str = "verilator"
    top_module: str = ""
    clock_signal: str = "clk"
    reset_signal: str = "rst"
    timeout: int = 300
    extra_flags: List[str] = None
    include_dirs: List[str] = None

    def __post_init__(self):
        if self.extra_flags is None:
            self.extra_flags = []
        if self.include_dirs is None:
            self.include_dirs = []


@dataclass
class SimulationResult:
    success: bool = False
    exit_code: int = -1
    stdout: str = ""
    stderr: str = ""
    compilation_log: str = ""
    simulation_log: str = ""
    coverage_report: str = ""
    runtime_seconds: float = 0.0
    error_message: str = ""
    command: str = ""
    artifacts: dict = None

    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = {}


class SimulationEngine:
    """Manages simulation across Verilator and other simulators."""

    def __init__(self):
        self.verilator_path = shutil.which("verilator")
        self.icarus_path = shutil.which("iverilog")

    def is_verilator_available(self) -> bool:
        return self.verilator_path is not None

    def is_icarus_available(self) -> bool:
        return self.icarus_path is not None

    def compile(self, rtl_files: List[str], config: SimulationConfig,
                testbench_file: str = "") -> SimulationResult:
        """Compile RTL and testbench with Verilator."""
        result = SimulationResult()
        start_time = time.time()

        if not self.verilator_path:
            result.error_message = "Verilator executable was not found."
            result.status = "UNAVAILABLE"
            result.tool = "verilator"
            return result

        # Create temp directory for compilation
        with tempfile.TemporaryDirectory() as tmpdir:
            # Copy RTL files to temp directory
            rtl_copies = []
            for rtl_file in rtl_files:
                if os.path.exists(rtl_file):
                    dest = os.path.join(tmpdir, os.path.basename(rtl_file))
                    shutil.copy2(rtl_file, dest)
                    rtl_copies.append(dest)
                else:
                    # Assume it's content, write it
                    dest = os.path.join(tmpdir, f"rtl_{len(rtl_copies)}.sv")
                    with open(dest, "w") as f:
                        f.write(rtl_file)
                    rtl_copies.append(dest)

            # Write testbench
            tb_path = ""
            if testbench_file:
                if os.path.exists(testbench_file):
                    tb_path = os.path.join(tmpdir, "tb.sv")
                    shutil.copy2(testbench_file, tb_path)
                else:
                    tb_path = os.path.join(tmpdir, "tb.sv")
                    with open(tb_path, "w") as f:
                        f.write(testbench_file)

            cmd = [
                self.verilator_path,
                "--binary",
                "--top-module", config.top_module,
                "-Wall",
                "--trace",
                "--cc",
            ]

            for inc_dir in config.include_dirs:
                cmd.extend(["-I", inc_dir])

            cmd.extend(config.extra_flags)
            cmd.extend(rtl_copies)

            if tb_path:
                cmd.append(tb_path)

            result.command = " ".join(cmd)

            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=config.timeout,
                    cwd=tmpdir,
                )
                result.exit_code = proc.returncode
                result.stdout = proc.stdout
                result.stderr = proc.stderr
                result.compilation_log = proc.stdout + proc.stderr
                result.success = proc.returncode == 0

                if result.success:
                    # Find the compiled binary
                    exe_path = os.path.join(tmpdir, f"V{config.top_module}")
                    if not os.path.exists(exe_path):
                        exe_path = os.path.join(tmpdir, "obj_dir", f"V{config.top_module}")
                    if os.path.exists(exe_path):
                        result.artifacts["executable"] = exe_path
                        result.artifacts["build_dir"] = tmpdir
            except subprocess.TimeoutExpired:
                result.error_message = f"Compilation timed out after {config.timeout}s"
            except Exception as e:
                result.error_message = f"Compilation error: {str(e)}"

        result.runtime_seconds = time.time() - start_time
        return result

    def simulate(self, compiled_dir: str, config: SimulationConfig,
                 test_name: str = "") -> SimulationResult:
        """Run simulation on compiled design."""
        result = SimulationResult()
        start_time = time.time()

        exe_path = os.path.join(compiled_dir, f"V{config.top_module}")
        if not os.path.exists(exe_path):
            exe_path = os.path.join(compiled_dir, "obj_dir", f"V{config.top_module}")

        if not os.path.exists(exe_path):
            result.error_message = f"Compiled executable not found: {exe_path}"
            result.runtime_seconds = time.time() - start_time
            return result

        try:
            proc = subprocess.run(
                [exe_path],
                capture_output=True,
                text=True,
                timeout=config.timeout,
                cwd=compiled_dir,
            )
            result.exit_code = proc.returncode
            result.stdout = proc.stdout
            result.stderr = proc.stderr
            result.simulation_log = proc.stdout + proc.stderr
            result.success = proc.returncode == 0
        except subprocess.TimeoutExpired:
            result.error_message = f"Simulation timed out after {config.timeout}s"
        except Exception as e:
            result.error_message = f"Simulation error: {str(e)}"

        result.runtime_seconds = time.time() - start_time
        return result

    def run_test(self, rtl_files: List[str], test_code: str,
                 config: SimulationConfig) -> SimulationResult:
        """Complete flow: compile and run a single test."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write testbench
            tb_path = os.path.join(tmpdir, "tb.sv")
            with open(tb_path, "w") as f:
                f.write(test_code)

            # Compile
            compile_result = self.compile(rtl_files, config, tb_path)
            if not compile_result.success:
                return compile_result

            # Simulate
            build_dir = compile_result.artifacts.get("build_dir", tmpdir)
            sim_result = self.simulate(build_dir, config)
            sim_result.compilation_log = compile_result.compilation_log
            return sim_result


class VerilatorAdapter:
    """Adapter for Verilator simulator."""

    def __init__(self):
        self.path = shutil.which("verilator")

    def is_available(self) -> bool:
        return self.path is not None

    def get_version(self) -> str:
        if not self.path:
            return "NOT AVAILABLE"
        try:
            result = subprocess.run([self.path, "--version"], capture_output=True, text=True)
            return result.stdout.strip()
        except Exception:
            return "UNKNOWN"