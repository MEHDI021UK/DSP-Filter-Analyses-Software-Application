@echo off
setlocal enabledelayedexpansion

echo ################################################
echo #   Advanced DSP Studio Pro - EXE Builder      #
echo ################################################
echo.

:: Check for PyInstaller
python -m PyInstaller --version >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller not found.
    echo Attempting to install PyInstaller...
    python -m pip install pyinstaller
    if !errorlevel! neq 0 (
        echo [FATAL] Failed to install PyInstaller. Please install it manually: pip install pyinstaller
        pause
        exit /b 1
    )
)

echo [1/3] Cleaning up old build artifacts...
if exist build rd /s /q build
if exist dist rd /s /q dist
echo.

echo [2/3] Building Standalone Executable...
echo This may take a minute...
:: Using the existing .spec file if available, otherwise creating from scratch
if exist advanced_dsp_studio.spec (
    echo Using existing advanced_dsp_studio.spec file...
    python -m PyInstaller --noconfirm advanced_dsp_studio.spec
) else (
    echo Creating new build configuration...
    echo [ERROR] No spec file found. Attempting to build from parent folder...
    if exist "..\advanced_dsp_studio.py" (
        python -m PyInstaller --noconfirm --onefile --windowed --name "Advanced_DSP_Studio_Pro" --collect-all customtkinter --add-data "../*.py;." "..\advanced_dsp_studio.py"
    ) else (
        echo [FATAL] Could not find advanced_dsp_studio.py in parent folder.
        pause
        exit /b 1
    )
)

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed! Check the console output above for details.
    pause
    exit /b 1
)

echo.
echo [3/3] Build Successful!
echo ################################################
echo # Your EXE is located in the 'dist' folder.      #
echo ################################################
echo.
pause
