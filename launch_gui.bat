@echo off
:: WinMerge AI Review Exporter — GUI Launcher
:: Double-click this file to open the GUI.
:: Requires Python 3.10+ on PATH.

title WinMerge AI Review Exporter

python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found. Please install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)

:: Check package is installed
python -c "import winmerge_ai_exporter" >nul 2>&1
if errorlevel 1 (
    echo winmerge-ai-exporter not installed.
    echo Installing now...
    pip install winmerge-ai-exporter
    if errorlevel 1 (
        echo Installation failed. Please run: pip install winmerge-ai-exporter
        pause
        exit /b 1
    )
)

:: Launch GUI
python "%~dp0gui\launcher.py"
