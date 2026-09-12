@echo off
title AstrixCore Verification AI Launcher
color 0B
echo ============================================
echo  AstrixCore Verification AI V0.1
echo  AI-assisted verification from RTL to coverage
echo ============================================
echo.

REM ============================================
REM Check for compatible Python (3.10, 3.11, 3.12)
REM ============================================
set PY_EXE=
for %%v in (3.12 3.11 3.10) do (
    where python%%v >nul 2>&1
    if not errorlevel 1 (
        set PY_EXE=python%%v
        goto :found_python
    )
)

REM Fallback to system python
where python >nul 2>&1
if not errorlevel 1 (
    python --version 2>&1 | findstr /r "3\.(10|11|12)" >nul
    if not errorlevel 1 (
        set PY_EXE=python
        goto :found_python
    )
)

:found_python
if defined PY_EXE (
    echo Found compatible Python: %PY_EXE%
    %PY_EXE% --version
    goto :run_native
)

REM ============================================
REM No compatible Python - check for Docker
REM ============================================
echo.
echo No compatible Python found (need 3.10, 3.11, or 3.12)
echo Checking for Docker...
where docker >nul 2>&1
if not errorlevel 1 (
    docker --version
    echo.
    echo Docker found! Starting with Docker Compose...
    echo.
    docker compose up --build
    goto :eof
)

REM ============================================
REM Neither Python nor Docker available
REM ============================================
echo.
echo ============================================
echo  SETUP REQUIRED
echo ============================================
echo.
echo AstrixCore requires Python 3.10, 3.11, or 3.12
echo (Python 3.14 is NOT compatible with FastAPI/pydantic)
echo.
echo OPTION 1: Install Python 3.11 (Recommended)
echo   1. Download from: https://www.python.org/downloads/release/python-3119/
echo   2. Run installer, CHECK "Add Python to PATH"
echo   3. Restart this launcher
echo.
echo OPTION 2: Install Docker Desktop
echo   1. Download from: https://www.docker.com/products/docker-desktop/
echo   2. Install and start Docker
echo   3. Run: docker compose up --build
echo.
echo OPTION 3: Use Windows Subsystem for Linux (WSL)
echo   1. Run: wsl --install
echo   2. In WSL: sudo apt update && sudo apt install python3.11 python3.11-venv
echo   3. Run this launcher from WSL terminal
echo.
echo ============================================
pause
exit /b 1

:run_native
echo.
echo Setting up virtual environment...
if not exist backend\venv (
    echo Creating venv with %PY_EXE%...
    %PY_EXE% -m venv backend\venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo.
echo Installing/updating dependencies...
call backend\venv\Scripts\activate.bat
pip install -q -r backend\requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Create storage directories
if not exist storage mkdir storage
if not exist storage\rtl mkdir storage\rtl
if not exist storage\tests mkdir storage\tests
if not exist storage\logs mkdir storage\logs
if not exist storage\coverage mkdir storage\coverage

REM Copy .env if not exists
if not exist backend\.env (
    copy backend\.env.example backend\.env >nul 2>&1
)

echo.
echo ============================================
echo Starting AstrixCore Verification AI Backend
echo ============================================
echo.
echo Backend API:  http://localhost:8000
echo API Docs:     http://localhost:8000/docs
echo Health Check: http://localhost:8000/health
echo FIFO Example: http://localhost:8000/api/v1/rtl/examples/fifo
echo.
echo Press Ctrl+C to stop the server
echo.

cd backend
..\..\backend\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

if errorlevel 1 (
    echo.
    echo An error occurred. Press any key to exit...
    pause >nul
)