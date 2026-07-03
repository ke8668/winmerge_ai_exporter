@echo off
REM ============================================================================
REM run-ci-locally.bat
REM
REM Runs the same CI checks as GitHub Actions, but locally.
REM Uses an isolated virtual environment (.venv) so results are reproducible
REM regardless of what is installed globally on the host machine.
REM
REM Usage:
REM   .\run-ci-locally.bat            (interactive ??pauses at end)
REM   .\run-ci-locally.bat NOPAUSE    (for use inside deploy-local.bat)
REM ============================================================================
setlocal enabledelayedexpansion

set PAUSE_MODE=1
if /i "%~1"=="NOPAUSE" set PAUSE_MODE=0

echo.
echo ================================================================================
echo   Running local CI checks (isolated venv)...
echo ================================================================================
echo.

REM ----------------------------------------------------------------------------
REM Step 1: Create / reuse isolated virtual environment
REM ----------------------------------------------------------------------------
echo Step 1: Preparing isolated virtual environment (.venv)...
echo.

if not exist .venv (
    python -m venv .venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment. Is Python installed?
        if "%PAUSE_MODE%"=="1" pause
        exit /b 1
    )
    echo Created new .venv
) else (
    echo Reusing existing .venv
)

REM Activate venv ??all subsequent python/pip/pytest calls use the venv
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo Error: Failed to activate .venv
    if "%PAUSE_MODE%"=="1" pause
    exit /b 1
)

echo.

REM ----------------------------------------------------------------------------
REM Step 2: Install pinned dependencies into the venv
REM ----------------------------------------------------------------------------
echo Step 2: Installing pinned dependencies from requirements-dev.txt...
echo.

pip install -r requirements-dev.txt -q
if errorlevel 1 (
    echo Error: Failed to install dependencies
    if "%PAUSE_MODE%"=="1" pause
    exit /b 1
)

echo Dependencies installed.
echo.

REM ----------------------------------------------------------------------------
REM Step 3: Syntax check (Using Python's built-in compileall - standard way)
REM ----------------------------------------------------------------------------
echo Step 3: Syntax check (compileall)...
echo.

python -m compileall -q -x "\.git|__pycache__|\.pytest_cache|build|dist|\.venv" .

if errorlevel 1 (
    echo.
    echo Syntax check FAILED: One or more Python files have syntax errors.
    if "%PAUSE_MODE%"=="1" pause
    exit /b 1
)

echo All .py files OK.
echo.

REM ----------------------------------------------------------------------------
REM Step 4: Run tests inside the venv
REM ----------------------------------------------------------------------------
echo Step 4: Running pytest...
echo.

pytest tests/ -v --tb=short --cov=winmerge_ai_exporter --cov-report=term-missing

if errorlevel 1 (
    echo.
    echo Tests FAILED
    if "%PAUSE_MODE%"=="1" pause
    exit /b 1
)

echo.
echo All tests passed.
echo.

echo ================================================================================
echo   Local CI checks PASSED - safe to push
echo ================================================================================
echo.
if "%PAUSE_MODE%"=="1" pause
exit /b 0
