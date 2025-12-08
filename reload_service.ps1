# Reload PipLinePro Service Script
# This script restarts the service to pick up code changes

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Reloading PipLinePro Service" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "WARNING: Not running as Administrator" -ForegroundColor Yellow
    Write-Host "Service restart may require admin privileges" -ForegroundColor Yellow
    Write-Host ""
}

# Get service status
$service = Get-Service -Name "PipLinePro" -ErrorAction SilentlyContinue
if (-not $service) {
    Write-Host "ERROR: PipLinePro service not found!" -ForegroundColor Red
    exit 1
}

Write-Host "Current service status: $($service.Status)" -ForegroundColor White
Write-Host ""

# Stop service
Write-Host "Stopping service..." -ForegroundColor Yellow
try {
    Stop-Service -Name "PipLinePro" -Force -ErrorAction Stop
    Start-Sleep -Seconds 3
    Write-Host "[OK] Service stopped" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to stop service: $_" -ForegroundColor Red
    Write-Host "You may need to run this script as Administrator" -ForegroundColor Yellow
    exit 1
}

# Start service
Write-Host "Starting service..." -ForegroundColor Yellow
try {
    Start-Service -Name "PipLinePro" -ErrorAction Stop
    Start-Sleep -Seconds 5
    Write-Host "[OK] Service started" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to start service: $_" -ForegroundColor Red
    exit 1
}

# Verify
$service = Get-Service -Name "PipLinePro" -ErrorAction SilentlyContinue
if ($service.Status -eq "Running") {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Service reloaded successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Service Status: $($service.Status)" -ForegroundColor Green
    Write-Host ""
    Write-Host "The application should now be accessible at:" -ForegroundColor Cyan
    Write-Host "  http://erp.orderinvests.net" -ForegroundColor White
    Write-Host "  http://127.0.0.1:5000" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "[ERROR] Service is not running!" -ForegroundColor Red
    Write-Host "Check logs: logs\service_error.log" -ForegroundColor Yellow
}

