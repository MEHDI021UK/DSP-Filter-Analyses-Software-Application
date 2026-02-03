@echo off
setlocal
title DSP Studio Launcher

echo ==========================================
echo    ADVANCED DSP STUDIO PRO - LAUNCHER
echo ==========================================
echo.

:: 1. Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed.
    echo Please install Python from python.org and add it to your PATH.
    pause
    exit /b
)

:: 2. Check and Install Dependencies
echo [STEP 1/2] Checking system dependencies...
python -c "import numpy, matplotlib, scipy, customtkinter" >nul 2>&1

if %errorlevel% neq 0 (
    echo [INFO] Missing libraries detected. Installing required packages...
    pip install numpy matplotlib scipy customtkinter
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install libraries automatically. 
        echo Please run: pip install numpy matplotlib scipy customtkinter
        pause
        exit /b
    )
) else (
    echo [OK] All dependencies are ready.
)

:: 3. Launch the Application
echo [STEP 2/2] Launching Advanced DSP Studio...
echo.
start "" python advanced_dsp_studio.py

echo [SUCCESS] Studio is starting in a separate window.
timeout /t 3 >nul
exit
