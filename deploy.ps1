# PipLinePro Production Deployment Script for Windows Server
# Run this script on the Windows Server as Administrator

param(
    [string]$ServerIP = "62.84.189.9",
    [string]$AppPath = "C:\PipLinePro",
    [int]$Port = 5000
)

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "PipLinePro Production Deployment Script" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Please right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

Write-Host "[1/10] Checking Python installation..." -ForegroundColor Green
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python is not installed!" -ForegroundColor Red
    Write-Host "Please install Python 3.11 from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    exit 1
}
Write-Host "Python installed: $pythonVersion" -ForegroundColor Cyan

Write-Host ""
Write-Host "[2/10] Checking Node.js installation..." -ForegroundColor Green
$nodeVersion = node --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Node.js is not installed!" -ForegroundColor Red
    Write-Host "Please install Node.js 20 LTS from: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}
Write-Host "Node.js installed: $nodeVersion" -ForegroundColor Cyan

Write-Host ""
Write-Host "[3/10] Creating application directory..." -ForegroundColor Green
if (-not (Test-Path $AppPath)) {
    New-Item -ItemType Directory -Path $AppPath -Force | Out-Null
    Write-Host "Created directory: $AppPath" -ForegroundColor Cyan
} else {
    Write-Host "Directory already exists: $AppPath" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "[4/10] Creating required directories..." -ForegroundColor Green
$directories = @("logs", "instance", "static\uploads", "backups", "instance\sessions")
foreach ($dir in $directories) {
    $fullPath = Join-Path $AppPath $dir
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        Write-Host "Created: $fullPath" -ForegroundColor Cyan
    }
}

Write-Host ""
Write-Host "[5/10] Installing Python dependencies..." -ForegroundColor Green
Set-Location $AppPath
if (Test-Path "requirements.txt") {
    Write-Host "Installing from requirements.txt..." -ForegroundColor Cyan
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install Python dependencies!" -ForegroundColor Red
        exit 1
    }
    Write-Host "Python dependencies installed successfully" -ForegroundColor Cyan
} else {
    Write-Host "WARNING: requirements.txt not found!" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[6/10] Building React frontend..." -ForegroundColor Green
$frontendPath = Join-Path $AppPath "frontend"
if (Test-Path $frontendPath) {
    Set-Location $frontendPath
    Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install frontend dependencies!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Building frontend for production..." -ForegroundColor Cyan
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to build frontend!" -ForegroundColor Red
        exit 1
    }
    Write-Host "Frontend built successfully" -ForegroundColor Cyan
    Set-Location $AppPath
} else {
    Write-Host "WARNING: Frontend directory not found, skipping frontend build" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[7/10] Creating production .env file..." -ForegroundColor Green
$envContent = @"
# Production Environment Configuration
FLASK_ENV=production
DEBUG=False

# Security - IMPORTANT: Change these values!
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(64))")

# Database Configuration (SQLite default)
DATABASE_TYPE=sqlite

# Admin Configuration
ADMIN_USERNAME=admin
ADMIN_PASSWORD=ChangeThisPassword123!
ADMIN_EMAIL=admin@pipeline.com

# Redis (optional - set to true if Redis is installed)
REDIS_ENABLED=false

# Logging
LOG_LEVEL=INFO

# Database Initialization (set to false after first run)
INIT_DB=true

# CORS Configuration - Update with your domain
CORS_ORIGINS=http://${ServerIP}:${Port},http://localhost:${Port}

# Backup Configuration
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=90
"@

$envPath = Join-Path $AppPath ".env"
if (-not (Test-Path $envPath)) {
    $envContent | Out-File -FilePath $envPath -Encoding UTF8
    Write-Host "Created .env file at: $envPath" -ForegroundColor Cyan
    Write-Host "IMPORTANT: Edit .env and change SECRET_KEY and ADMIN_PASSWORD!" -ForegroundColor Yellow
} else {
    Write-Host ".env file already exists, skipping..." -ForegroundColor Cyan
}

Write-Host ""
Write-Host "[8/10] Initializing database..." -ForegroundColor Green
Set-Location $AppPath
$env:FLASK_ENV = "production"
$env:INIT_DB = "true"
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('Database initialized')"
if ($LASTEXITCODE -eq 0) {
    Write-Host "Database initialized successfully" -ForegroundColor Cyan
} else {
    Write-Host "WARNING: Database initialization may have failed" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[9/10] Configuring Windows Firewall..." -ForegroundColor Green
$ruleName = "PipLinePro-Port-$Port"
$existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
if ($existingRule) {
    Write-Host "Firewall rule already exists: $ruleName" -ForegroundColor Cyan
} else {
    New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -LocalPort $Port -Protocol TCP -Action Allow | Out-Null
    Write-Host "Firewall rule created: Allow TCP port $Port" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "[10/10] Creating startup script..." -ForegroundColor Green
$startupScript = @"
@echo off
cd /d $AppPath
echo Starting PipLinePro...
python -m gunicorn --bind 0.0.0.0:$Port --workers 4 --threads 2 --timeout 120 --access-logfile logs/access.log --error-logfile logs/error.log "app:create_app()"
"@

$startupPath = Join-Path $AppPath "start_production.bat"
$startupScript | Out-File -FilePath $startupPath -Encoding ASCII
Write-Host "Created startup script: $startupPath" -ForegroundColor Cyan

Write-Host ""
Write-Host "==================================================================" -ForegroundColor Green
Write-Host "Deployment completed successfully!" -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit $AppPath\.env and update SECRET_KEY and ADMIN_PASSWORD" -ForegroundColor White
Write-Host "2. Run the application:" -ForegroundColor White
Write-Host "   cd $AppPath" -ForegroundColor Cyan
Write-Host "   .\start_production.bat" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Access the application at:" -ForegroundColor White
Write-Host "   http://${ServerIP}:${Port}" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. To run as Windows Service, use NSSM:" -ForegroundColor White
Write-Host "   Download NSSM: https://nssm.cc/download" -ForegroundColor Cyan
Write-Host "   nssm install PipLinePro $AppPath\start_production.bat" -ForegroundColor Cyan
Write-Host ""
Write-Host "Default admin credentials (CHANGE IMMEDIATELY):" -ForegroundColor Yellow
Write-Host "   Username: admin" -ForegroundColor White
Write-Host "   Password: (check .env file)" -ForegroundColor White
Write-Host ""

