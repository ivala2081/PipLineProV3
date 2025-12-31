# PipLinePro - Super Fast Deploy
# Minimal deployment - just build and restart (~15-20 seconds)

$ErrorActionPreference = "Stop"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  PipLinePro - Fast Deploy" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$startTime = Get-Date

try {
    # Build Frontend
    Write-Host "[1/3] Building frontend..." -ForegroundColor Yellow
    Push-Location frontend
    
    # Clean old builds
    Remove-Item -Path "dist", "dist_new", "dist_backup" -Recurse -Force -ErrorAction SilentlyContinue
    
    # Build
    npm run build --silent
    
    if ($LASTEXITCODE -ne 0) {
        Pop-Location
        throw "Build failed"
    }
    
    Pop-Location
    Write-Host "      Frontend built successfully" -ForegroundColor Green
    
    # Stop Flask
    Write-Host "[2/3] Restarting Flask..." -ForegroundColor Yellow
    
    # Try Windows Service first
    $service = Get-Service -Name "PipLinePro" -ErrorAction SilentlyContinue
    if ($service) {
        Restart-Service -Name "PipLinePro" -Force
        Write-Host "      Service restarted" -ForegroundColor Green
    } else {
        # Stop any running Python processes on port 5000
        $process = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | 
                   Select-Object -ExpandProperty OwningProcess -First 1
        
        if ($process) {
            Stop-Process -Id $process -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
        }
        
        # Start Flask in background
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; python app.py" -WindowStyle Minimized
        Write-Host "      Flask restarted" -ForegroundColor Green
    }
    
    # Wait for Flask
    Write-Host "[3/3] Waiting for Flask..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    
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
                Start-Sleep -Seconds 1
            }
        }
    }
    
    if ($healthy) {
        Write-Host "      Flask is healthy" -ForegroundColor Green
    } else {
        Write-Host "      Flask may still be starting..." -ForegroundColor Yellow
    }
    
    # Done
    $duration = [math]::Round(((Get-Date) - $startTime).TotalSeconds, 1)
    
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "  Deployment Complete! ($duration seconds)" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "`nOpen: " -NoNewline
    Write-Host "http://erp.orderinvests.net" -ForegroundColor Cyan
    Write-Host ""
    
} catch {
    Write-Host "`n[ERROR] Deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`nTry:" -ForegroundColor Yellow
    Write-Host "  cd frontend && npm run build" -ForegroundColor Gray
    exit 1
}

