# PipLinePro Complete Installation Script
# MUST RUN AS ADMINISTRATOR
# This script installs everything needed for production deployment

# Check for administrator privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "ERROR: This script requires Administrator privileges!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "To run this script:" -ForegroundColor Yellow
    Write-Host "1. Right-click on PowerShell" -ForegroundColor White
    Write-Host "2. Select 'Run as Administrator'" -ForegroundColor White
    Write-Host "3. Navigate to: C:\PipLinePro" -ForegroundColor White
    Write-Host "4. Run: .\INSTALL_ALL.ps1" -ForegroundColor White
    Write-Host ""
    exit 1
}

$ProjectPath = "C:\PipLinePro"
Set-Location $ProjectPath

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PipLinePro Complete Installation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Install Windows Service
Write-Host "Step 1/3: Installing Windows Service..." -ForegroundColor Yellow
Write-Host ""
& "$ProjectPath\install_service.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Service installation failed!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 2: Configure Firewall
Write-Host "Step 2/3: Configuring Firewall..." -ForegroundColor Yellow
Write-Host ""
& "$ProjectPath\install_firewall.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Firewall configuration failed!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 3: Install Backup Task
Write-Host "Step 3/3: Installing Backup Task..." -ForegroundColor Yellow
Write-Host ""
& "$ProjectPath\install_backup_task.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Backup task installation failed!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Final verification
Write-Host "========================================" -ForegroundColor Green
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Verify service
$service = Get-Service -Name "PipLinePro" -ErrorAction SilentlyContinue
if ($service) {
    $statusColor = if ($service.Status -eq "Running") { "Green" } else { "Yellow" }
    Write-Host "Service Status: $($service.Status)" -ForegroundColor $statusColor
} else {
    Write-Host "Service Status: Not Found" -ForegroundColor Red
}

# Verify firewall
$firewall = Get-NetFirewallRule -DisplayName "PipLinePro HTTP" -ErrorAction SilentlyContinue
if ($firewall) {
    Write-Host "Firewall Rule: Installed" -ForegroundColor Green
} else {
    Write-Host "Firewall Rule: Not Found" -ForegroundColor Red
}

# Verify backup task
$backupTask = Get-ScheduledTask -TaskName "PipLinePro Daily Backup" -ErrorAction SilentlyContinue
if ($backupTask) {
    Write-Host "Backup Task: Installed" -ForegroundColor Green
} else {
    Write-Host "Backup Task: Not Found" -ForegroundColor Red
}

Write-Host ""
Write-Host "Your application should now be accessible at:" -ForegroundColor Cyan
Write-Host "  http://62.84.189.9:5000" -ForegroundColor White
Write-Host ""
Write-Host "The service will:" -ForegroundColor Cyan
Write-Host "  [OK] Start automatically on server boot" -ForegroundColor Green
Write-Host "  [OK] Restart automatically if it crashes" -ForegroundColor Green
Write-Host "  [OK] Create daily backups at 2:00 AM" -ForegroundColor Green
Write-Host ""

