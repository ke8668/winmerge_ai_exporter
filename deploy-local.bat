@echo off
setlocal enabledelayedexpansion

set "BUMP_ARG=%~1"
if "%BUMP_ARG%"=="" set "BUMP_ARG=patch"

echo ================================================================================
echo   Local CI-CD Pipeline
echo ================================================================================
echo.

where git >nul 2>&1
if errorlevel 1 (
    echo X git not found
    exit /b 1
)

if not exist VERSION (
    echo 1.3.2> VERSION
)

set /p CURRENT_VERSION=<VERSION
set "CURRENT_VERSION=%CURRENT_VERSION: =%"
echo Current version: %CURRENT_VERSION%
echo.

echo ================================================================================
echo   STAGE 1-4: CI - Running tests
echo ================================================================================
echo.

set "CI_STATUS=PASSED"

call .\run-ci-locally.bat NOPAUSE
if errorlevel 1 (
    echo.
    echo X CI FAILED
    echo.
    set /p "CI_OVERRIDE=Deploy anyway? [y/N]: "
    if /i not "!CI_OVERRIDE!"=="y" (
        echo Aborted.
        exit /b 1
    )
    set "CI_STATUS=OVERRIDDEN"
    echo.
) else (
    echo OK: CI passed
    echo.
)

echo ================================================================================
echo   STAGE 2-4: Checking git status
echo ================================================================================
echo.

git diff --quiet
if errorlevel 1 (
    echo Warning: Uncommitted changes.
    git status --short
    echo.
    set /p "CONTINUE=Continue anyway? [y/N]: "
    if /i not "!CONTINUE!"=="y" (
        echo Aborted.
        exit /b 1
    )
)

echo OK: Git checked
echo.

echo ================================================================================
echo   STAGE 3-4: Version bump
echo ================================================================================
echo.

set "NEW_VERSION="
for /f "delims=" %%i in ('python -c "v = '%CURRENT_VERSION%'.split('.'); maj, mn, p = int(v[0]), int(v[1]), int(v[2]); arg = '%BUMP_ARG%'; print(arg) if arg.count('.') == 2 else print(f'{maj+1}.0.0') if arg == 'major' else print(f'{maj}.{mn+1}.0') if arg == 'minor' else print(f'{maj}.{mn}.{p+1}')"') do (
    set "NEW_VERSION=%%i"
)

echo New version: %CURRENT_VERSION% to %NEW_VERSION%
echo.

set /p "CONFIRM=Proceed with build and tag v%NEW_VERSION%? [y/N]: "
if /i not "!CONFIRM!"=="y" (
    echo Aborted.
    exit /b 0
)

echo %NEW_VERSION%> VERSION
echo.

echo ================================================================================
echo   STAGE 4-4: CD - Building and tagging release
echo ================================================================================
echo.

if exist build-release.bat (
    call .\build-release.bat
) else (
    echo Info: build-release.bat not found, skipping.
)

echo.
echo OK: Build complete
echo.

git add VERSION
git commit -m "chore: bump version to v%NEW_VERSION% STATUS: %CI_STATUS%"
git tag -a "v%NEW_VERSION%" -m "Release v%NEW_VERSION% STATUS: %CI_STATUS%"

echo OK: Tagged v%NEW_VERSION% locally
echo.

set /p "PUSH_CONFIRM=Push to GitHub now? [y/N]: "
if /i "!PUSH_CONFIRM!"=="y" (
    git push
    git push origin "v%NEW_VERSION%"
)

echo Done.
exit /b 0