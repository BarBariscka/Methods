# Start the unified GUI for labs 1-4
# Usage: right-click -> Run with PowerShell, or: .\start.ps1

Set-Location $PSScriptRoot

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  GUI for Labs 1-4" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$hasUv = Get-Command uv -ErrorAction SilentlyContinue
if ($hasUv) {
    Write-Host "Using uv..." -ForegroundColor Green
    uv run python run.py
} else {
    Write-Host "Using python directly..." -ForegroundColor Yellow
    python run.py
}
