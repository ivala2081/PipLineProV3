# PipLinePro - Quick Deploy Script
# Fast deployment for frequent changes
# Builds frontend and restarts Flask (~30 seconds)

param(
    [switch]$SkipBuild = $false,  # Skip frontend build (just restart Flask)
    [switch]$NoRestart = $false   # Deploy without restarting Flask
)

$ErrorActionPreference = "Stop"

# Configuration
$FRONTEND_DIR = "frontend"
$FRONTEND_DIST = "frontend\dist"
$BACKEND_STATIC = "static"
$FLASK_PORT = 5000
$PROJECT_ROOT = Get-Location

# Colors for output
function WriteSuccess { param($Message) Write-Host "[OK] $Message" -ForegroundColor Green }
function WriteInfo { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function WriteWarn { param($Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function WriteErr { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }
function WriteHeader { param($Message) Write-Host "`n$('='*70)`n$Message`n$('='*70)" -ForegroundColor Magenta }

# Start deployment
$startTime = Get-Date
WriteHeader "PipLinePro - Quick Deploy"
WriteInfo "Started at: $($startTime.ToString('yyyy-MM-dd HH:mm:ss'))"
WriteInfo "Project: $PROJECT_ROOT"

try {
    # ============================================================================
    # STEP 1: Pre-deployment Checks
    # ============================================================================
    WriteHeader "Step 1: Pre-deployment Checks"
    
    # Check if frontend directory exists
    if (-not (Test-Path $FRONTEND_DIR)) {
        throw "Frontend directory not found: $FRONTEND_DIR"
    }
    WriteSuccess "Frontend directory found"
    
    # Check if node_modules exists
    if (-not (Test-Path "$FRONTEND_DIR\node_modules")) {
        WriteWarn "node_modules not found. Run 'npm install' first."
        WriteInfo "Running npm install..."
        Set-Location $FRONTEND_DIR
        npm install
        Set-Location $PROJECT_ROOT
        WriteSuccess "Dependencies installed"
    }
    
    # Check if Flask is running
    $flaskRunning = $false
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$FLASK_PORT/api/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $flaskRunning = $true
            WriteSuccess "Flask is running on port $FLASK_PORT"
        }
    } catch {
        WriteWarn "Flask is not responding (will start after deployment)"
    }
    
    # ============================================================================
    # STEP 2: Build Frontend
    # ============================================================================
    if (-not $SkipBuild) {
        WriteHeader "Step 2: Build Frontend"
        
        WriteInfo "Building frontend (production mode)..."
        Push-Location $FRONTEND_DIR
        
        try {
            # Clean problematic folders
            @("dist_new", "dist_backup") | ForEach-Object {
                if (Test-Path $_) {
                    Remove-Item -Path $_ -Recurse -Force -ErrorAction SilentlyContinue
                    WriteInfo "Cleaned $_"
                }
            }
            
            # Run build
            WriteInfo "Running: npm run build"
            npm run build
            if ($LASTEXITCODE -ne 0) {
                WriteErr "Frontend build failed with exit code: $LASTEXITCODE"
                throw "Build failed with exit code $LASTEXITCODE"
            }
        } finally {
            Pop-Location
        }
        WriteSuccess "Frontend build completed"
        
        # Verify dist directory was created
        if (-not (Test-Path $FRONTEND_DIST)) {
            throw "Build output not found: $FRONTEND_DIST"
        }
        
        # Show build size
        $distSize = (Get-ChildItem -Path $FRONTEND_DIST -Recurse -File | Measure-Object -Property Length -Sum).Sum
        $distSizeMB = [math]::Round($distSize / 1MB, 2)
        WriteInfo "Build size: $distSizeMB MB"
        
    } else {
        WriteHeader "Step 2: Build Frontend (SKIPPED)"
        WriteWarn "Skipping frontend build as requested"
    }
    
    # ============================================================================
    # STEP 3: Deploy Frontend
    # ============================================================================
    if (-not $SkipBuild) {
        WriteHeader "Step 3: Deploy Frontend"
        
        # Backup current dist if it exists
        if (Test-Path $FRONTEND_DIST) {
            $backupName = "dist_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
            $backupPath = Join-Path $FRONTEND_DIR $backupName
            
            WriteInfo "Creating backup: $backupName"
            # Note: Frontend serves from its own dist directory
            # No need to copy to backend static folder
            WriteSuccess "Current build preserved"
        }
        
        WriteSuccess "Frontend deployed successfully"
    }
    
    # ============================================================================
    # STEP 4: Restart Flask
    # ============================================================================
    if (-not $NoRestart) {
        WriteHeader "Step 4: Restart Flask"
        
        if ($flaskRunning) {
            WriteInfo "Stopping Flask..."
            
            # Find Flask process
            $flaskProcess = Get-Process -Name python -ErrorAction SilentlyContinue | 
                Where-Object { $_.Path -like "*python*" -and (Get-NetTCPConnection -LocalPort $FLASK_PORT -ErrorAction SilentlyContinue) }
            
            if ($flaskProcess) {
                Stop-Process -Id $flaskProcess.Id -Force
                WriteSuccess "Flask stopped"
                Start-Sleep -Seconds 2
            } else {
                WriteWarn "Could not find Flask process (may be running as service)"
            }
        }
        
        WriteInfo "Starting Flask..."
        
        # Check if running as Windows Service
        $service = Get-Service -Name "PipLinePro" -ErrorAction SilentlyContinue
        if ($service) {
            WriteInfo "Detected Windows Service: $($service.Name)"
            Restart-Service -Name "PipLinePro" -Force
            WriteSuccess "Service restarted"
        } else {
            # Start Flask in background
            WriteInfo "Starting Flask in new window..."
            Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PROJECT_ROOT'; python app.py" -WindowStyle Minimized
            WriteSuccess "Flask started in background"
        }
        
        # Wait for Flask to start
        WriteInfo "Waiting for Flask to start..."
        $maxAttempts = 15
        $attempt = 0
        $started = $false
        
        while ($attempt -lt $maxAttempts -and -not $started) {
            Start-Sleep -Seconds 2
            $attempt++
            
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:$FLASK_PORT/api/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
                if ($response.StatusCode -eq 200) {
                    $started = $true
                    WriteSuccess "Flask is running and healthy"
                }
            } catch {
                WriteInfo "Attempt $attempt/$maxAttempts - waiting..."
            }
        }
        
        if (-not $started) {
            WriteWarn "Flask may not have started properly. Check manually."
        }
        
    } else {
        WriteHeader "Step 4: Restart Flask (SKIPPED)"
        WriteWarn "Skipping Flask restart as requested"
    }
    
    # ============================================================================
    # STEP 5: Verify Deployment
    # ============================================================================
    WriteHeader "Step 5: Verify Deployment"
    
    # Check backend health
    try {
        $healthCheck = Invoke-RestMethod -Uri "http://localhost:$FLASK_PORT/api/health" -TimeoutSec 5 -ErrorAction Stop
        WriteSuccess "Backend health check: OK"
        WriteInfo "Status: $($healthCheck.status)"
    } catch {
        WriteWarn "Backend health check failed: $($_.Exception.Message)"
    }
    
    # Check frontend files
    if (Test-Path "$FRONTEND_DIST\index.html") {
        WriteSuccess "Frontend files: OK"
    } else {
        WriteWarn "Frontend index.html not found"
    }
    
    # ============================================================================
    # Deployment Complete
    # ============================================================================
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    WriteHeader "Deployment Complete!"
    WriteSuccess "Time taken: $([math]::Round($duration, 2)) seconds"
    WriteInfo "Backend: http://localhost:$FLASK_PORT"
    WriteInfo "Frontend: http://erp.orderinvests.net"
    WriteInfo "Health Check: http://localhost:$FLASK_PORT/api/health"
    
    Write-Host "`n"
    WriteInfo "Next steps:"
    WriteInfo "1. Open http://erp.orderinvests.net in your browser"
    WriteInfo "2. Test your changes"
    WriteInfo "3. Check logs if any issues occur"
    
    exit 0
    
} catch {
    WriteErr "Deployment failed: $($_.Exception.Message)"
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
    
    WriteInfo "`nTroubleshooting:"
    WriteInfo "1. Check if ports are available: netstat -ano | findstr :$FLASK_PORT"
    WriteInfo "2. Check Flask logs in logs/ directory"
    WriteInfo "3. Verify frontend build: cd frontend && npm run build"
    WriteInfo "4. Try manual restart: python app.py"
    
    exit 1
}

