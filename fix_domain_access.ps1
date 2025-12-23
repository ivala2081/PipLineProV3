# Fix Domain Access - Ensure Nginx is running and configured correctly
# This ensures your domain works without port numbers

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Fixing Domain Access (Remove Port from URL)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$NginxDir = "C:\nginx"
$NginxExe = "$NginxDir\nginx.exe"

# Step 1: Check if Nginx is running
Write-Host "[1/3] Checking Nginx status..." -ForegroundColor Yellow
$nginxProcess = Get-Process -Name "nginx" -ErrorAction SilentlyContinue
if ($nginxProcess) {
    Write-Host "[OK] Nginx is running (PID: $($nginxProcess.Id))" -ForegroundColor Green
} else {
    Write-Host "[X] Nginx is not running - starting it..." -ForegroundColor Yellow
    Push-Location $NginxDir
    Start-Process -FilePath $NginxExe -WindowStyle Hidden
    Pop-Location
    Start-Sleep -Seconds 2
    $nginxProcess = Get-Process -Name "nginx" -ErrorAction SilentlyContinue
    if ($nginxProcess) {
        Write-Host "[OK] Nginx started successfully" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Failed to start Nginx" -ForegroundColor Red
        Write-Host "Check: C:\nginx\logs\error.log" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""

# Step 2: Test Nginx configuration
Write-Host "[2/3] Testing Nginx configuration..." -ForegroundColor Yellow
Push-Location $NginxDir
$testResult = & $NginxExe -t 2>&1
Pop-Location

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Configuration is valid" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Configuration test failed:" -ForegroundColor Red
    Write-Host $testResult -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 3: Reload Nginx
Write-Host "[3/3] Reloading Nginx..." -ForegroundColor Yellow
Push-Location $NginxDir
& $NginxExe -s reload
Pop-Location

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Nginx reloaded successfully" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Reload had issues, but Nginx may still work" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your domain should now work WITHOUT port numbers:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  ✓ http://erp.orderinvests.net/login" -ForegroundColor Green
Write-Host "  ✗ http://erp.orderinvests.net:5000/login  (don't use this)" -ForegroundColor Red
Write-Host ""
Write-Host "Nginx is routing:" -ForegroundColor Cyan
Write-Host "  Port 80 (HTTP) → Port 5000 (Flask)" -ForegroundColor White
Write-Host ""
Write-Host "If you still see port 5000 in your browser:" -ForegroundColor Yellow
Write-Host "  1. Clear browser cache" -ForegroundColor White
Write-Host "  2. Use http://erp.orderinvests.net (without :5000)" -ForegroundColor White
Write-Host "  3. Check if cloud firewall allows port 80" -ForegroundColor White
Write-Host ""

