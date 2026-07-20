@echo off
REM ⚛ AML AI Copilot - Launcher Script
REM SEA Quantathon 2026 · QCFinOp Team

echo.
echo ========================================
echo   AML AI Copilot - Quick Launcher
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found!
    echo    Please install Python 3.10+ from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if virtual environment exists
if exist "env\Scripts\activate.bat" (
    echo ✅ Virtual environment detected
    call env\Scripts\activate.bat
) else (
    echo ⚠️  Virtual environment does not exist
    echo    Using global Python...
)

REM Check if dependencies are installed
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo ❌ Dependencies not installed!
    echo    Installing requirements...
    python -m pip install -r requirements.txt
)

REM Run the launcher
python launcher.py

echo.
pause
