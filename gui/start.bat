@echo off
REM Start the unified GUI for labs 1-4
REM Usage: double-click this file or run from command line

cd /d "%~dp0"

echo ============================================================
echo   GUI for Labs 1-4
echo ============================================================
echo.

where uv >nul 2>&1
if %errorlevel% == 0 (
    echo Using uv...
    uv run python run.py
) else (
    echo Using python directly...
    python run.py
)

pause
