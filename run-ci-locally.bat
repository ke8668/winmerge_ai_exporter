@echo off
setlocal enabledelayedexpansion

set PAUSE_MODE=1
if /i "%~1"=="NOPAUSE" set PAUSE_MODE=0

echo.
echo ================================================================================
echo   Running local CI checks...
echo ================================================================================
echo.

echo Step 1: Syntax check (python -m py_compile)...
echo.
set FAILED=0

for /r %%f in (*.py) do (
    echo %%f | findstr /i "\.git\\" >nul
    if errorlevel 1 (
        echo %%f | findstr /i "__pycache__" >nul
        if errorlevel 1 (
            python -m py_compile "%%f" 2>nul
            if errorlevel 1 (
                echo Syntax error in: %%f
                python -m py_compile "%%f"
                set FAILED=1
            )
        )
    )
)

if "%FAILED%"=="1" (
    echo.
    echo Syntax check FAILED
    if "%PAUSE_MODE%"=="1" pause
    exit /b 1
)

echo All files compile OK
echo.

echo Step 2: Checking test dependencies...
echo.
python -c "import pytest, pytest_cov" >nul 2>&1
if errorlevel 1 (
    echo Installing pytest and pytest-cov...
    pip install pytest pytest-cov -q
    if errorlevel 1 (
        echo Failed to install dependencies
        if "%PAUSE_MODE%"=="1" pause
        exit /b 1
    )
)

echo Dependencies ready
echo.

echo Step 3: Running pytest...
echo.
pytest tests/ -v --tb=short --cov=winmerge_ai_exporter --cov-report=term-missing

if errorlevel 1 (
    echo.
    echo Tests FAILED
    if "%PAUSE_MODE%"=="1" pause
    exit /b 1
)

echo.
echo All tests passed
echo.

echo ================================================================================
echo   Local CI checks PASSED - safe to push
echo ================================================================================
echo.
if "%PAUSE_MODE%"=="1" pause
exit /b 0