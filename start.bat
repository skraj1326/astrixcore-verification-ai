@echo off
title AstrixCore Verification AI - Backend Server
echo ============================================
echo AstrixCore Verification AI V0.1
echo AI-assisted verification from RTL to coverage closure
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3.11+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Python found: 
python --version

REM Check if venv exists
if not exist backend\venv (
    echo.
    echo Creating virtual environment...
    python -m venv backend\venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate venv and install dependencies
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
echo.
echo Setting up storage...
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

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir backend