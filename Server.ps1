# ============================================================================
# PipLinePro Production Server Deployment Script
# ============================================================================
# This script applies all updates to the production website
# MUST RUN AS ADMINISTRATOR
#
# Usage:
#   .\Server.ps1              - Full deployment (build + deploy)
#   .\Server.ps1 -Quick       - Quick deploy (skip build, just copy files)
#   .\Server.ps1 -Restart     - Just restart the service
#   .\Server.ps1 -Status      - Check service status
#   .\Server.ps1 -Logs        - View recent logs
# ============================================================================

param(
    [switch]$Quick,
    [switch]$Restart,
    [switch]$Status,
    [switch]$Logs,
    [switch]$Help
)

# Configuration
$ServiceName = "PipLinePro"
$ProjectPath = "C:\PipLinePro"
$FrontendPath = "$ProjectPath\frontend"
$DistPath = "$FrontendPath\dist"
$DistNewPath = "$FrontendPath\dist_new"
$LogPath = "$ProjectPath\logs"
$WebsiteURL = "http://erp.orderinvests.net"

# Colors and formatting
function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host " $Message" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([string]$Step, [string]$Message)
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] [$Step] $Message" -ForegroundColor Yellow
}

function Write-Success {
    param([string]$Message)
    Write-Host "  [OK] $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "  [ERROR] $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "  [INFO] $Message" -ForegroundColor Gray
}

# Show help
if ($Help) {
    Write-Header "PipLinePro Server Deployment"
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\Server.ps1              Full deployment (build frontend + deploy + restart)" -ForegroundColor White
    Write-Host "  .\Server.ps1 -Quick       Quick deploy (skip build, use existing dist_new)" -ForegroundColor White
    Write-Host "  .\Server.ps1 -Restart     Just restart the service" -ForegroundColor White
    Write-Host "  .\Server.ps1 -Status      Check service and website status" -ForegroundColor White
    Write-Host "  .\Server.ps1 -Logs        View recent application logs" -ForegroundColor White
    Write-Host "  .\Server.ps1 -Help        Show this help message" -ForegroundColor White
    Write-Host ""
    Write-Host "Website: $WebsiteURL" -ForegroundColor Cyan
    Write-Host ""
    exit 0
}

# Check for administrator privileges
function Test-Administrator {
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    return $isAdmin
}

# Elevate to admin if needed
if (-not (Test-Administrator)) {
    Write-Host "Requesting administrator privileges..." -ForegroundColor Yellow
    $scriptPath = $MyInvocation.MyCommand.Path
    $arguments = "-ExecutionPolicy Bypass -File `"$scriptPath`""
    if ($Quick) { $arguments += " -Quick" }
    if ($Restart) { $arguments += " -Restart" }
    if ($Status) { $arguments += " -Status" }
    if ($Logs) { $arguments += " -Logs" }
    
    Start-Process powershell -Verb RunAs -ArgumentList $arguments -Wait
    exit
}

# Show status
if ($Status) {
    Write-Header "PipLinePro Status"
    
    # Service status
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service) {
        $statusColor = if ($service.Status -eq "Running") { "Green" } else { "Red" }
        Write-Host "Service: $ServiceName" -ForegroundColor Cyan
        Write-Host "  Status: $($service.Status)" -ForegroundColor $statusColor
        Write-Host "  Startup Type: $($service.StartType)" -ForegroundColor White
    } else {
        Write-Host "Service: $ServiceName - NOT FOUND" -ForegroundColor Red
    }
    
    # Port check
    Write-Host ""
    $port = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
    if ($port) {
        Write-Host "Port 5000: Listening" -ForegroundColor Green
    } else {
        Write-Host "Port 5000: Not listening" -ForegroundColor Red
    }
    
    # Website check
    Write-Host ""
    Write-Host "Website Check:" -ForegroundColor Cyan
    try {
        $response = Invoke-WebRequest -Uri $WebsiteURL -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
        Write-Host "  $WebsiteURL - OK ($($response.StatusCode))" -ForegroundColor Green
    } catch {
        Write-Host "  $WebsiteURL - FAILED" -ForegroundColor Red
    }
    
    # Disk space
    Write-Host ""
    $disk = Get-PSDrive C
    $freeGB = [math]::Round($disk.Free / 1GB, 2)
    Write-Host "Disk Space (C:): $freeGB GB free" -ForegroundColor $(if ($freeGB -gt 10) { "Green" } else { "Yellow" })
    
    Write-Host ""
    exit 0
}

# Show logs
if ($Logs) {
    Write-Header "Recent Logs"
    
    $appLog = "$LogPath\pipelinepro_enhanced.log"
    $errorLog = "$LogPath\pipelinepro_errors_enhanced.log"
    $serviceLog = "$LogPath\service_output.log"
    
    if (Test-Path $appLog) {
        Write-Host "=== Application Log (last 20 lines) ===" -ForegroundColor Yellow
        Get-Content $appLog -Tail 20 -ErrorAction SilentlyContinue
        Write-Host ""
    }
    
    if (Test-Path $errorLog) {
        Write-Host "=== Error Log (last 10 lines) ===" -ForegroundColor Red
        Get-Content $errorLog -Tail 10 -ErrorAction SilentlyContinue
        Write-Host ""
    }
    
    exit 0
}

# Just restart
if ($Restart) {
    Write-Header "Restarting PipLinePro Service"
    
    Write-Step "1/2" "Stopping service..."
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3
    Write-Success "Service stopped"
    
    Write-Step "2/2" "Starting service..."
    Start-Service -Name $ServiceName -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 5
    
    $service = Get-Service -Name $ServiceName
    if ($service.Status -eq "Running") {
        Write-Success "Service is running"
        Write-Host ""
        Write-Host "Website: $WebsiteURL" -ForegroundColor Green
    } else {
        Write-Error "Service failed to start. Check logs with: .\Server.ps1 -Logs"
    }
    
    Write-Host ""
    exit 0
}

# ============================================================================
# FULL DEPLOYMENT
# ============================================================================

Write-Header "PipLinePro Production Deployment"
Write-Host "Website: $WebsiteURL" -ForegroundColor Cyan
Write-Host ""

$totalSteps = if ($Quick) { 4 } else { 5 }
$currentStep = 0

# Step 1: Stop service
$currentStep++
Write-Step "$currentStep/$totalSteps" "Stopping service..."

$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($service -and $service.Status -eq "Running") {
    Stop-Service -Name $ServiceName -Force
    Start-Sleep -Seconds 5
    
    # Verify stopped
    $service = Get-Service -Name $ServiceName
    if ($service.Status -eq "Stopped") {
        Write-Success "Service stopped"
    } else {
        Write-Info "Service may still be stopping..."
        Start-Sleep -Seconds 5
    }
} else {
    Write-Info "Service was not running"
}

# Step 2: Build frontend (unless -Quick)
if (-not $Quick) {
    $currentStep++
    Write-Step "$currentStep/$totalSteps" "Building frontend..."
    
    Set-Location $FrontendPath
    
    # Remove old dist_new if exists
    if (Test-Path $DistNewPath) {
        Remove-Item -Path $DistNewPath -Recurse -Force -ErrorAction SilentlyContinue
    }
    
    # Run npm build
    $buildOutput = npm run build 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Frontend built successfully"
    } else {
        Write-Error "Frontend build failed!"
        Write-Host $buildOutput -ForegroundColor Red
        Start-Service -Name $ServiceName -ErrorAction SilentlyContinue
        exit 1
    }
    
    Set-Location $ProjectPath
}

# Step 3: Remove old dist
$currentStep++
Write-Step "$currentStep/$totalSteps" "Removing old build..."

if (Test-Path $DistPath) {
    try {
        Remove-Item -Path $DistPath -Recurse -Force -ErrorAction Stop
        Write-Success "Old build removed"
    } catch {
        Write-Info "Some files could not be removed (may be cached), continuing..."
        # Try to remove individual files
        Get-ChildItem $DistPath -Recurse -File | ForEach-Object {
            Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
        }
    }
}

# Step 4: Copy new build
$currentStep++
Write-Step "$currentStep/$totalSteps" "Deploying new build..."

if (Test-Path $DistNewPath) {
    # Create dist directory if it doesn't exist
    if (-not (Test-Path $DistPath)) {
        New-Item -ItemType Directory -Path $DistPath -Force | Out-Null
    }
    
    # Copy all files
    Copy-Item -Path "$DistNewPath\*" -Destination $DistPath -Recurse -Force
    
    # Verify copy
    $newFiles = (Get-ChildItem "$DistPath\js" -ErrorAction SilentlyContinue).Count
    if ($newFiles -gt 0) {
        Write-Success "New build deployed ($newFiles JS files)"
    } else {
        Write-Error "Deploy may have failed - no JS files found"
    }
} else {
    Write-Error "dist_new directory not found! Run without -Quick flag to build first."
    Start-Service -Name $ServiceName -ErrorAction SilentlyContinue
    exit 1
}

# Step 5: Start service
$currentStep++
Write-Step "$currentStep/$totalSteps" "Starting service..."

Start-Service -Name $ServiceName -ErrorAction SilentlyContinue
Start-Sleep -Seconds 5

# Verify service is running
$service = Get-Service -Name $ServiceName
if ($service.Status -eq "Running") {
    Write-Success "Service started"
} else {
    Write-Error "Service failed to start!"
    Write-Info "Check logs with: .\Server.ps1 -Logs"
}

# Final verification
Write-Host ""
Write-Step "Verify" "Testing website..."
Start-Sleep -Seconds 3

try {
    $response = Invoke-WebRequest -Uri $WebsiteURL -UseBasicParsing -TimeoutSec 15 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Success "Website is accessible"
    }
} catch {
    Write-Info "Website may take a moment to start. Try refreshing in a few seconds."
}

# Summary
Write-Header "Deployment Complete!"
Write-Host "Website URL: $WebsiteURL" -ForegroundColor Green
Write-Host ""
Write-Host "Quick Commands:" -ForegroundColor Yellow
Write-Host "  .\Server.ps1 -Status    Check status" -ForegroundColor White
Write-Host "  .\Server.ps1 -Restart   Restart service" -ForegroundColor White
Write-Host "  .\Server.ps1 -Logs      View logs" -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANT: Clear browser cache (Ctrl+Shift+R) to see updates!" -ForegroundColor Cyan
Write-Host ""

