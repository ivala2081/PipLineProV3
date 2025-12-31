# ============================================================================
# Deploy Frontend Changes Script
# ============================================================================
# This script ensures frontend changes are properly deployed and active
# Usage: .\deploy_frontend.ps1
# ============================================================================

param(
    [switch]$SkipBuild,
    [switch]$Force
)

# Colors and formatting functions
function Write-Success { 
    param([string]$msg) 
    Write-Host "[OK] $msg" -ForegroundColor Green 
}

function Write-Fail { 
    param([string]$msg) 
    Write-Host "[ERROR] $msg" -ForegroundColor Red 
}

function Write-Info { 
    param([string]$msg) 
    Write-Host "[INFO] $msg" -ForegroundColor Cyan 
}

function Write-Step { 
    param([string]$msg) 
    Write-Host "[STEP] $msg" -ForegroundColor Yellow 
}

# Set error action preference after functions are defined
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Frontend Deployment Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Update Service Worker Version
Write-Step "STEP 1: Updating Service Worker Cache Version"

$swPath = "frontend\public\sw.js"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$newVersion = $timestamp

Write-Info "Updating cache version to: $newVersion"

$swContent = Get-Content $swPath -Raw
$swContent = $swContent -replace "const CACHE_VERSION = '[^']+';", "const CACHE_VERSION = '$newVersion';"

Set-Content $swPath -Value $swContent -NoNewline

Write-Success "Service worker cache version updated to: $newVersion"

# Step 2: Build Frontend
if (-not $SkipBuild) {
    Write-Step "STEP 2: Building Frontend"
    
    Push-Location "frontend"
    
    try {
        Write-Info "Running npm run build..."
        $buildOutput = npm run build 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            Write-Fail "Build failed!"
            Write-Host $buildOutput -ForegroundColor Red
            Pop-Location
            exit 1
        }
        
        Write-Success "Frontend built successfully"
    }
    finally {
        Pop-Location
    }
} else {
    Write-Info "Skipping build (using existing dist_new)"
}

# Step 3: Stop the service
Write-Step "STEP 3: Stopping PipLinePro Service"

$service = Get-Service -Name "PipLinePro" -ErrorAction SilentlyContinue
if ($service -and $service.Status -eq "Running") {
    Stop-Service -Name "PipLinePro" -Force
    Start-Sleep -Seconds 3
    Write-Success "Service stopped"
} else {
    Write-Info "Service was not running"
}

# Step 4: Backup current dist (if exists)
Write-Step "STEP 4: Backing up current deployment"

$distPath = "frontend\dist"
$backupPath = "frontend\dist_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"

if (Test-Path $distPath) {
    Write-Info "Creating backup at: $backupPath"
    Rename-Item -Path $distPath -NewName (Split-Path $backupPath -Leaf)
    Write-Success "Backup created"
} else {
    Write-Info "No existing dist folder to backup"
}

# Step 5: Deploy new build
Write-Step "STEP 5: Deploying new build"

$distNewPath = "frontend\dist_new"

if (-not (Test-Path $distNewPath)) {
    Write-Fail "dist_new folder not found! Build may have failed."
    if (Test-Path $backupPath) {
        Write-Info "Restoring backup..."
        Rename-Item -Path $backupPath -NewName "dist"
    }
    Start-Service -Name "PipLinePro" -ErrorAction SilentlyContinue
    exit 1
}

# Create new dist directory
New-Item -ItemType Directory -Path $distPath -Force | Out-Null

# Copy all files from dist_new to dist
Write-Info "Copying files from dist_new to dist..."
Copy-Item -Path "$distNewPath\*" -Destination $distPath -Recurse -Force

# Verify critical files
$criticalFiles = @("index.html", "sw.js", "js")
$allFilesExist = $true

foreach ($file in $criticalFiles) {
    $filePath = Join-Path $distPath $file
    if (-not (Test-Path $filePath)) {
        Write-Fail "Critical file/folder missing: $file"
        $allFilesExist = $false
    }
}

if (-not $allFilesExist) {
    Write-Fail "Deployment failed - critical files missing!"
    if (Test-Path $backupPath) {
        Write-Info "Restoring backup..."
        Remove-Item -Path $distPath -Recurse -Force
        Rename-Item -Path $backupPath -NewName "dist"
    }
    Start-Service -Name "PipLinePro" -ErrorAction SilentlyContinue
    exit 1
}

Write-Success "Files deployed successfully"

# Verify service worker version in deployed files
$deployedSW = Get-Content "$distPath\sw.js" | Select-String "CACHE_VERSION"
Write-Info "Deployed service worker version: $deployedSW"

# Step 6: Clean up old backups (keep last 3)
Write-Step "STEP 6: Cleaning up old backups"

$backups = Get-ChildItem "frontend" -Directory | Where-Object { $_.Name -like "dist_backup_*" } | Sort-Object LastWriteTime -Descending
if ($backups.Count -gt 3) {
    $backups | Select-Object -Skip 3 | ForEach-Object {
        Write-Info "Removing old backup: $($_.Name)"
        Remove-Item $_.FullName -Recurse -Force
    }
}

Write-Success "Old backups cleaned"

# Step 7: Start the service
Write-Step "STEP 7: Starting PipLinePro Service"

Start-Service -Name "PipLinePro"
Start-Sleep -Seconds 5

$service = Get-Service -Name "PipLinePro"
if ($service.Status -eq "Running") {
    Write-Success "Service started successfully"
} else {
    Write-Fail "Service failed to start!"
    Write-Info "Check logs: .\Server.ps1 -Logs"
    exit 1
}

# Step 8: Verify deployment
Write-Step "STEP 8: Verifying deployment"

Start-Sleep -Seconds 3

try {
    $response = Invoke-WebRequest -Uri "http://erp.orderinvests.net" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Success "Website is accessible"
    }
} catch {
    Write-Fail "Website is not accessible: $_"
}

# Verify service worker
try {
    $swResponse = Invoke-WebRequest -Uri "http://erp.orderinvests.net/sw.js" -UseBasicParsing -TimeoutSec 10
    if ($swResponse.Content -match $newVersion) {
        Write-Success "Service worker version verified: $newVersion"
    } else {
        Write-Fail "Service worker version mismatch!"
    }
} catch {
    Write-Fail "Could not verify service worker: $_"
}

# Step 9: Create cache-busting instructions
Write-Step "STEP 9: Cache Busting Instructions"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " ✅ DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "New Service Worker Version: $newVersion" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  IMPORTANT: Users need to clear their browser cache!" -ForegroundColor Yellow
Write-Host ""
Write-Host "📋 Instructions for users:" -ForegroundColor Cyan
Write-Host "   1. Visit: http://erp.orderinvests.net/test.html" -ForegroundColor White
Write-Host "   2. Click 'Clear All Caches' button" -ForegroundColor White
Write-Host "   OR" -ForegroundColor Yellow
Write-Host "   Press Ctrl+Shift+R (hard refresh)" -ForegroundColor White
Write-Host ""
Write-Host "🔍 Verification:" -ForegroundColor Cyan
Write-Host "   Test page: http://erp.orderinvests.net/test.html" -ForegroundColor White
Write-Host "   Should show version: $newVersion" -ForegroundColor White
Write-Host ""
Write-Host "📊 Check status: .\Server.ps1 -Status" -ForegroundColor Cyan
Write-Host "📜 View logs: .\Server.ps1 -Logs" -ForegroundColor Cyan
Write-Host ""

# Optional: Open test page in browser
$openBrowser = Read-Host "Open test page in browser? (Y/N)"
if ($openBrowser -eq "Y" -or $openBrowser -eq "y") {
    Start-Process "http://erp.orderinvests.net/test.html"
}

Write-Host "Deployment completed at: $(Get-Date)" -ForegroundColor Green
Write-Host ""

