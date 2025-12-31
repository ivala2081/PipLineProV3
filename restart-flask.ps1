# Quick Flask Restart Script for Production
# Use this after deploying backend code changes

$ErrorActionPreference = "Stop"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Restarting Flask Application" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if running as Windows Service
$service = Get-Service -Name "PipLinePro" -ErrorAction SilentlyContinue
if ($service) {
    Write-Host "[INFO] Detected Windows Service: $($service.Name)" -ForegroundColor Yellow
    Write-Host "[INFO] Restarting service..." -ForegroundColor Yellow
    Restart-Service -Name "PipLinePro" -Force
    Write-Host "[OK] Service restarted successfully" -ForegroundColor Green
} else {
    Write-Host "[INFO] Flask is running as a process" -ForegroundColor Yellow
    
    # Find Flask process on port 5000
    $process = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | 
               Select-Object -ExpandProperty OwningProcess -First 1
    
    if ($process) {
        Write-Host "[INFO] Stopping Flask process (PID: $process)..." -ForegroundColor Yellow
        Stop-Process -Id $process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        Write-Host "[OK] Flask stopped" -ForegroundColor Green
    } else {
        Write-Host "[WARN] No Flask process found on port 5000" -ForegroundColor Yellow
    }
    
    # Start Flask
    Write-Host "[INFO] Starting Flask..." -ForegroundColor Yellow
    $projectRoot = Get-Location
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot'; python app.py" -WindowStyle Minimized
    Write-Host "[OK] Flask started in background" -ForegroundColor Green
}

# Wait and verify
Write-Host "`n[INFO] Waiting for Flask to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

$attempts = 0
$maxAttempts = 10
$healthy = $false

while ($attempts -lt $maxAttempts -and -not $healthy) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/api/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $healthy = $true
        }
    } catch {
        $attempts++
        if ($attempts -lt $maxAttempts) {
            Start-Sleep -Seconds 2
        }
    }
}

if ($healthy) {
    Write-Host "[OK] Flask is healthy and running!" -ForegroundColor Green
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "  Restart Complete!" -ForegroundColor Green
    Write-Host "========================================`n" -ForegroundColor Green
} else {
    Write-Host "[WARN] Flask may still be starting. Check manually." -ForegroundColor Yellow
    Write-Host "[INFO] Check logs: logs\pipelinepro_errors_enhanced.log" -ForegroundColor Cyan
}

