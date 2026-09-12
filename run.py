#!/usr/bin/env python3
"""
AstrixCore Verification AI - One-Click Launcher
Run this file directly to start the backend server.
"""

import os
import sys
import subprocess
import venv
import time
from pathlib import Path

ROOT = Path(__file__).parent
BACKEND = ROOT / "backend"
VENV = BACKEND / "venv"
REQUIREMENTS = BACKEND / "requirements.txt"

def print_banner():
    print("=" * 60)
    print("  AstrixCore Verification AI V0.1")
    print("  AI-assisted verification from RTL to coverage closure")
    print("=" * 60)
    print()

def check_python():
    print(f"Python: {sys.version.split()[0]}")
    if sys.version_info < (3, 11):
        print("ERROR: Python 3.11+ required")
        input("Press Enter to exit...")
        sys.exit(1)
    print("OK")

def setup_venv():
    print("\nSetting up virtual environment...")
    if not VENV.exists():
        print("Creating venv...")
        venv.create(VENV, with_pip=True)
    else:
        print("Venv exists")
    
    # Get pip executable
    if sys.platform == "win32":
        pip = VENV / "Scripts" / "pip.exe"
        python = VENV / "Scripts" / "python.exe"
    else:
        pip = VENV / "bin" / "pip"
        python = VENV / "bin" / "python"
    
    print(f"Venv Python: {python}")
    print(f"Venv Pip: {pip}")
    print(f"Python exists: {python.exists()}")
    
    return str(pip), str(python)

def install_deps(pip):
    print("\nInstalling dependencies...")
    try:
        subprocess.run([pip, "install", "-q", "-r", str(REQUIREMENTS)], check=True)
        print("Dependencies installed")
    except subprocess.CalledProcessError:
        print("ERROR: Failed to install dependencies")
        sys.exit(1)

def setup_dirs():
    dirs = ["storage", "storage/rtl", "storage/tests", "storage/logs", "storage/coverage"]
    for d in dirs:
        (ROOT / d).mkdir(parents=True, exist_ok=True)

def start_server(python):
    print("\n" + "=" * 60)
    print("Starting AstrixCore Verification AI Backend")
    print("=" * 60)
    print("\nBackend API:  http://localhost:8000")
    print("API Docs:     http://localhost:8000/docs")
    print("Health:       http://localhost:8000/health")
    print("FIFO Demo:    http://localhost:8000/api/v1/rtl/examples/fifo")
    print("\nPress Ctrl+C to stop\n")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND)
    # Ensure the venv's Python is used for subprocesses
    venv_bin = str(VENV / "Scripts")
    env["PATH"] = venv_bin + os.pathsep + env.get("PATH", "")
    
    try:
        # Use the venv's python explicitly with -m uvicorn
        subprocess.run([
            python, "-m", "uvicorn", "app.main:app",
            "--host", "0.0.0.0", "--port", "8000"
        ], cwd=BACKEND, env=env)
    except KeyboardInterrupt:
        print("\n\nServer stopped")

def main():
    print_banner()
    check_python()
    pip, python = setup_venv()
    install_deps(pip)
    setup_dirs()
    start_server(python)

if __name__ == "__main__":
    main()