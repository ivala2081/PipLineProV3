# Rebuild Frontend - Simple script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Rebuilding Frontend" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Change to frontend directory
Set-Location frontend

# Clean and rebuild
Write-Host "[1/2] Cleaning old build..." -ForegroundColor Yellow
if (Test-Path "dist") {
    try {
        Remove-Item "dist" -Recurse -Force -ErrorAction Stop
        Write-Host "OK - Old build removed" -ForegroundColor Green
    } catch {
        Write-Host "WARNING - Could not remove dist directory: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "You may need to close file explorer or stop the web server first" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Trying to build anyway..." -ForegroundColor Yellow
    }
} else {
    Write-Host "OK - No old build to clean" -ForegroundColor Green
}

Write-Host ""
Write-Host "[2/2] Building frontend (this may take 2-5 minutes)..." -ForegroundColor Yellow
npm run build

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "OK - Frontend build completed!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "ERROR - Frontend build failed!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "If you see permission errors, try:" -ForegroundColor Yellow
    Write-Host "  1. Close file explorer windows" -ForegroundColor White
    Write-Host "  2. Stop the web server (python app.py)" -ForegroundColor White
    Write-Host "  3. Run: .\fix_build_permissions.ps1" -ForegroundColor White
    exit 1
}

# Return to root
Set-Location ..

