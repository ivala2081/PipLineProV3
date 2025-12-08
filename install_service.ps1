# PipLinePro Service Installation Script
# MUST RUN AS ADMINISTRATOR
# Right-click PowerShell and select "Run as Administrator"

param(
    [switch]$Uninstall
)

# Check for administrator privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

$ServiceName = "PipLinePro"
$ProjectPath = "C:\PipLinePro"
$PythonPath = "C:\Python314\python.exe"
$NSSMPath = "C:\nssm\nssm-2.24\win64\nssm.exe"

# Check if NSSM exists
if (-not (Test-Path $NSSMPath)) {
    Write-Host "NSSM not found at: $NSSMPath" -ForegroundColor Red
    Write-Host "Downloading NSSM..." -ForegroundColor Yellow
    
    $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
    $zipFile = "$env:TEMP\nssm.zip"
    $nssmDir = "C:\nssm"
    
    try {
        Invoke-WebRequest -Uri $nssmUrl -OutFile $zipFile -UseBasicParsing
        Expand-Archive -Path $zipFile -DestinationPath $nssmDir -Force
        Remove-Item $zipFile
        Write-Host "NSSM downloaded and extracted successfully" -ForegroundColor Green
    } catch {
        Write-Host "Failed to download NSSM: $_" -ForegroundColor Red
        exit 1
    }
}

# Check if Python exists
if (-not (Test-Path $PythonPath)) {
    Write-Host "ERROR: Python not found at: $PythonPath" -ForegroundColor Red
    Write-Host "Please update PythonPath in this script" -ForegroundColor Yellow
    exit 1
}

# Check if project directory exists
if (-not (Test-Path $ProjectPath)) {
    Write-Host "ERROR: Project directory not found: $ProjectPath" -ForegroundColor Red
    exit 1
}

# Ensure log directory exists
$LogPath = "$ProjectPath\logs"
if (-not (Test-Path $LogPath)) {
    New-Item -ItemType Directory -Path $LogPath -Force | Out-Null
    Write-Host "Created logs directory" -ForegroundColor Green
}

if ($Uninstall) {
    Write-Host "Uninstalling $ServiceName service..." -ForegroundColor Yellow
    & $NSSMPath stop $ServiceName
    Start-Sleep -Seconds 2
    & $NSSMPath remove $ServiceName confirm
    Write-Host "Service uninstalled" -ForegroundColor Green
    exit 0
}

# Check if service already exists
$existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "Service '$ServiceName' already exists!" -ForegroundColor Yellow
    Write-Host "Stopping existing service..." -ForegroundColor Yellow
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "Removing existing service..." -ForegroundColor Yellow
    & $NSSMPath remove $ServiceName confirm
    Start-Sleep -Seconds 2
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installing PipLinePro Windows Service" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Install the service
Write-Host "Step 1: Installing service..." -ForegroundColor Yellow
& $NSSMPath install $ServiceName $PythonPath "-m waitress --host=0.0.0.0 --port=5000 --threads=4 --call app:create_app"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install service!" -ForegroundColor Red
    exit 1
}

# Configure service
Write-Host "Step 2: Configuring service..." -ForegroundColor Yellow
& $NSSMPath set $ServiceName AppDirectory $ProjectPath
& $NSSMPath set $ServiceName AppEnvironmentExtra "FLASK_ENV=production" "DEBUG=False"
& $NSSMPath set $ServiceName AppRestartDelay 5000
& $NSSMPath set $ServiceName AppThrottle 1500
& $NSSMPath set $ServiceName AppExit Default Restart
& $NSSMPath set $ServiceName AppStdout "$LogPath\service_output.log"
& $NSSMPath set $ServiceName AppStderr "$LogPath\service_error.log"
& $NSSMPath set $ServiceName Start SERVICE_AUTO_START
& $NSSMPath set $ServiceName Description "PipLinePro Treasury Management System - Production Server"

Write-Host "Step 3: Starting service..." -ForegroundColor Yellow
& $NSSMPath start $ServiceName

Start-Sleep -Seconds 3

# Verify service
Write-Host ""
Write-Host "Step 4: Verifying service..." -ForegroundColor Yellow
$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($service) {
    $statusColor = if ($service.Status -eq "Running") { "Green" } else { "Red" }
    Write-Host "Service Status: $($service.Status)" -ForegroundColor $statusColor
    Write-Host "Startup Type: $($service.StartType)" -ForegroundColor White
    
    if ($service.Status -eq "Running") {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "Service installed and running!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Access your application at:" -ForegroundColor Cyan
        Write-Host "  http://62.84.189.9:5000" -ForegroundColor White
        Write-Host ""
        Write-Host "Service management:" -ForegroundColor Cyan
        Write-Host "  Start:   Start-Service PipLinePro" -ForegroundColor White
        Write-Host "  Stop:    Stop-Service PipLinePro" -ForegroundColor White
        Write-Host "  Restart: Restart-Service PipLinePro" -ForegroundColor White
        Write-Host "  Status:  Get-Service PipLinePro" -ForegroundColor White
    } else {
        Write-Host ""
        Write-Host "Service installed but not running. Check logs:" -ForegroundColor Yellow
        Write-Host "  $LogPath\service_error.log" -ForegroundColor White
    }
} else {
    Write-Host "ERROR: Service not found after installation!" -ForegroundColor Red
    exit 1
}

