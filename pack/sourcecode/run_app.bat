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
    echo ❌ Python không được tìm thấy!
    echo    Vui lòng cài đặt Python 3.10+ từ: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if virtual environment exists
if exist "env\Scripts\activate.bat" (
    echo ✅ Phát hiện virtual environment
    call env\Scripts\activate.bat
) else (
    echo ⚠️  Virtual environment chưa tồn tại
    echo    Đang sử dụng Python global...
)

REM Check if dependencies are installed
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo ❌ Dependencies chưa được cài đặt!
    echo    Đang cài đặt requirements...
    python -m pip install -r requirements.txt
)

REM Run the launcher
python launcher.py

echo.
pause
