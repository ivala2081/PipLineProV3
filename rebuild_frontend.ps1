# Rebuild Frontend Script
# This script rebuilds the frontend with the fixed configuration

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Rebuilding Frontend" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$frontendDir = "frontend"
if (-not (Test-Path $frontendDir)) {
    Write-Host "ERROR: Frontend directory not found!" -ForegroundColor Red
    exit 1
}

Push-Location $frontendDir

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: npm install failed!" -ForegroundColor Red
        Pop-Location
        exit 1
    }
}

# Build the frontend
Write-Host "Building frontend..." -ForegroundColor Yellow
npm run build

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Frontend build completed successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "The build is now in: frontend/dist" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Restart the Flask service to serve the new build" -ForegroundColor White
    Write-Host "2. Clear browser cache (Ctrl+Shift+Delete)" -ForegroundColor White
    Write-Host "3. Reload the page (Ctrl+F5)" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Frontend build FAILED!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Check the error messages above" -ForegroundColor Yellow
}

Pop-Location

