# Start Nginx Reverse Proxy
# Run this script to start Nginx and route domain to Flask app

$NginxDir = "C:\nginx"
$NginxExe = "$NginxDir\nginx.exe"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Nginx Reverse Proxy" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Nginx is already running
$nginxProcess = Get-Process -Name "nginx" -ErrorAction SilentlyContinue
if ($nginxProcess) {
    Write-Host "Nginx is already running (PID: $($nginxProcess.Id))" -ForegroundColor Yellow
    Write-Host "Reloading configuration..." -ForegroundColor Yellow
    Push-Location $NginxDir
    & $NginxExe -s reload
    Pop-Location
    Write-Host "[OK] Configuration reloaded" -ForegroundColor Green
} else {
    # Test configuration first
    Write-Host "Testing Nginx configuration..." -ForegroundColor Yellow
    Push-Location $NginxDir
    $testResult = & $NginxExe -t 2>&1
    Pop-Location
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Configuration is valid" -ForegroundColor Green
        
        # Start Nginx
        Write-Host "Starting Nginx..." -ForegroundColor Yellow
        Push-Location $NginxDir
        Start-Process -FilePath $NginxExe -WindowStyle Hidden
        Pop-Location
        
        Start-Sleep -Seconds 2
        
        # Verify it started
        $nginxProcess = Get-Process -Name "nginx" -ErrorAction SilentlyContinue
        if ($nginxProcess) {
            Write-Host "[OK] Nginx started successfully (PID: $($nginxProcess.Id))" -ForegroundColor Green
        } else {
            Write-Host "[ERROR] Failed to start Nginx" -ForegroundColor Red
            Write-Host "Check error log: $NginxDir\logs\error.log" -ForegroundColor Yellow
            exit 1
        }
    } else {
        Write-Host "[ERROR] Nginx configuration test failed:" -ForegroundColor Red
        Write-Host $testResult -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Nginx is running!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your application should be accessible at:" -ForegroundColor Yellow
Write-Host "  http://erp.orderinvests.net" -ForegroundColor White
Write-Host "  http://62.84.189.9" -ForegroundColor White
Write-Host ""
Write-Host "Nginx is forwarding port 80 -> port 5000" -ForegroundColor Gray
Write-Host ""
Write-Host "To stop Nginx:" -ForegroundColor Cyan
Write-Host "  cd C:\nginx && .\nginx.exe -s stop" -ForegroundColor White
Write-Host ""
Write-Host "To reload configuration:" -ForegroundColor Cyan
Write-Host "  cd C:\nginx && .\nginx.exe -s reload" -ForegroundColor White
Write-Host ""

