@echo off
echo 🚀 Setting up Agentic AI OS Control System on Windows...
echo.

REM Check if uv is available
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ UV not found. Installing with pip instead...
    pip install -r requirements.txt
) else (
    echo ✅ UV found. Installing with UV...
    uv sync --no-dev --extra windows --extra production
)

echo.
echo 🎯 Setup complete!
echo.
echo To run the application:
echo python run_app.py
echo.
pause