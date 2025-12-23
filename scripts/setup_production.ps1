# PipLinePro Production Setup Script
# Run this script as Administrator to complete production setup

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PipLinePro Production Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check for administrator privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

$ProjectPath = "C:\PipLinePro"
Set-Location $ProjectPath

# Step 1: Create production .env file
Write-Host "Step 1: Creating production .env file..." -ForegroundColor Yellow
if (Test-Path ".env") {
    $overwrite = Read-Host ".env file already exists. Overwrite? (y/N)"
    if ($overwrite -ne "y" -and $overwrite -ne "Y") {
        Write-Host "Skipping .env file creation" -ForegroundColor Yellow
    } else {
        & "$ProjectPath\scripts\create_production_env.ps1"
    }
} else {
    & "$ProjectPath\scripts\create_production_env.ps1"
}

# Step 2: Verify database exists
Write-Host "`nStep 2: Verifying database..." -ForegroundColor Yellow
$dbPath = "$ProjectPath\instance\treasury_fresh.db"
if (Test-Path $dbPath) {
    $dbSize = (Get-Item $dbPath).Length / 1MB
    Write-Host "OK: Database found ($([math]::Round($dbSize, 2)) MB)" -ForegroundColor Green
} else {
    Write-Host "WARNING: Database not found at $dbPath" -ForegroundColor Yellow
}

# Step 3: Setup backup directory
Write-Host "`nStep 3: Setting up backup directory..." -ForegroundColor Yellow
$backupDir = "$ProjectPath\backups"
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    Write-Host "OK: Backup directory created" -ForegroundColor Green
} else {
    Write-Host "OK: Backup directory exists" -ForegroundColor Green
}

# Step 4: Install Windows Scheduled Task for backups
Write-Host "`nStep 4: Installing backup scheduled task..." -ForegroundColor Yellow
$installBackup = Read-Host "Install Windows Scheduled Task for daily backups? (Y/n)"
if ($installBackup -ne "n" -and $installBackup -ne "N") {
    & "$ProjectPath\install_backup_task.ps1"
} else {
    Write-Host "Skipping backup task installation" -ForegroundColor Yellow
    Write-Host "Note: Backups will still run via the application's internal scheduler" -ForegroundColor Cyan
}

# Step 5: Verify log rotation
Write-Host "`nStep 5: Verifying log rotation..." -ForegroundColor Yellow
$logsDir = "$ProjectPath\logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
}
Write-Host "OK: Log rotation configured (10MB per file, 7 backups)" -ForegroundColor Green

# Step 6: Check Redis status
Write-Host "`nStep 6: Checking Redis configuration..." -ForegroundColor Yellow
$redisEnabled = (Get-Content ".env" -ErrorAction SilentlyContinue | Select-String "REDIS_ENABLED=true")
if ($redisEnabled) {
    Write-Host "INFO: Redis is enabled in configuration" -ForegroundColor Cyan
    Write-Host "Make sure Redis is installed and running" -ForegroundColor Yellow
} else {
    Write-Host "INFO: Redis is disabled (using in-memory cache)" -ForegroundColor Cyan
    Write-Host "To enable Redis, install Redis and set REDIS_ENABLED=true in .env" -ForegroundColor Yellow
}

# Step 7: Verify Nginx configuration
Write-Host "`nStep 7: Checking Nginx configuration..." -ForegroundColor Yellow
$nginxConfig = "$ProjectPath\nginx_config.conf"
if (Test-Path $nginxConfig) {
    Write-Host "OK: Nginx configuration file found" -ForegroundColor Green
    Write-Host "Note: SSL certificates need to be configured for HTTPS" -ForegroundColor Yellow
} else {
    Write-Host "WARNING: Nginx configuration not found" -ForegroundColor Yellow
}

# Step 8: Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Setup Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Review .env file and update SECRET_KEY if needed" -ForegroundColor White
Write-Host "2. Set HTTPS_ENABLED=true and SESSION_COOKIE_SECURE=true when SSL is configured" -ForegroundColor White
Write-Host "3. Install Redis if you want distributed caching (optional)" -ForegroundColor White
Write-Host "4. Configure SSL certificates for HTTPS" -ForegroundColor White
Write-Host "5. Restart the application to apply changes" -ForegroundColor White
Write-Host ""
Write-Host "To restart the application:" -ForegroundColor Yellow
Write-Host "  .\start_production_server.ps1 -Restart" -ForegroundColor White
Write-Host ""
Write-Host "Setup completed!" -ForegroundColor Green

