@echo off
echo 🎨 ComfyUI Prompt Generator - Setup Script
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8+ first.
    pause
    exit /b 1
)

echo ✓ Python found
python --version

REM Check if Ollama is installed
ollama --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ⚠️  Ollama is not installed.
    echo    Download from: https://ollama.ai
    echo    After installing Ollama, run: ollama pull qwen3:latest
    echo.
)

REM Create virtual environment
echo.
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
echo.
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo ✅ Setup complete!
echo.
echo To start the application:
echo 1. Make sure Ollama is running: ollama serve
echo 2. Activate virtual environment: venv\Scripts\activate
echo 3. Run the app: python prompt_generator.py
echo 4. Open browser to: http://localhost:5000
echo.
pause
