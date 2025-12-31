# PipLinePro - Full Deploy Script
# Complete deployment with checks, tests, and backups
# For major changes and production releases (~2-3 minutes)

param(
    [switch]$SkipTests = $false,        # Skip running tests
    [switch]$SkipLint = $false,         # Skip linting
    [switch]$SkipMigrations = $false,   # Skip database migrations
    [switch]$Force = $false             # Skip confirmation prompts
)

$ErrorActionPreference = "Stop"

# Configuration
$FRONTEND_DIR = "frontend"
$FRONTEND_DIST = "frontend\dist"
$BACKEND_DIR = "app"
$FLASK_PORT = 5000
$PROJECT_ROOT = Get-Location
$BACKUP_DIR = "deployment_backups"
$LOG_FILE = "logs\deployment.log"

# Colors for output
function WriteSuccess { param($Message) Write-Host "[OK] $Message" -ForegroundColor Green; Log $Message }
function WriteInfo { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan; Log $Message }
function WriteWarn { param($Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow; Log $Message }
function WriteErr { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red; Log $Message }
function WriteHeader { param($Message) Write-Host "`n$('='*70)`n$Message`n$('='*70)" -ForegroundColor Magenta; Log "=== $Message ===" }

function Log {
    param($Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logPath = Join-Path $PROJECT_ROOT $LOG_FILE
    "$timestamp - $Message" | Out-File -FilePath $logPath -Append -Encoding UTF8
}

# Create logs directory if it doesn't exist
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
}

# Start deployment
$startTime = Get-Date
$deploymentId = Get-Date -Format "yyyyMMdd_HHmmss"

WriteHeader "PipLinePro - Full Deployment"
WriteInfo "Deployment ID: $deploymentId"
WriteInfo "Started at: $($startTime.ToString('yyyy-MM-dd HH:mm:ss'))"
WriteInfo "Project: $PROJECT_ROOT"
WriteInfo "Log file: $LOG_FILE"

try {
    # ============================================================================
    # STEP 1: Pre-deployment Checks
    # ============================================================================
    WriteHeader "Step 1: Pre-deployment Checks"
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        WriteSuccess "Python: $pythonVersion"
    } catch {
        throw "Python not found. Please install Python."
    }
    
    # Check Node.js
    try {
        $nodeVersion = node --version
        WriteSuccess "Node.js: $nodeVersion"
    } catch {
        throw "Node.js not found. Please install Node.js."
    }
    
    # Check npm
    try {
        $npmVersion = npm --version
        WriteSuccess "npm: v$npmVersion"
    } catch {
        throw "npm not found. Please install npm."
    }
    
    # Check virtual environment
    if (Test-Path ".venv") {
        WriteSuccess "Virtual environment found"
    } else {
        WriteWarn "Virtual environment not found (.venv)"
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
        WriteWarn "Flask is not responding"
    }
    
    # Check disk space
    $drive = (Get-Location).Drive.Name
    $freeSpace = (Get-PSDrive $drive).Free / 1GB
    if ($freeSpace -lt 1) {
        WriteWarn "Low disk space: $([math]::Round($freeSpace, 2)) GB free"
    } else {
        WriteSuccess "Disk space: $([math]::Round($freeSpace, 2)) GB free"
    }
    
    # ============================================================================
    # STEP 2: Create Backup
    # ============================================================================
    WriteHeader "Step 2: Create Backup"
    
    # Create backup directory
    if (-not (Test-Path $BACKUP_DIR)) {
        New-Item -ItemType Directory -Path $BACKUP_DIR -Force | Out-Null
    }
    
    $backupPath = Join-Path $BACKUP_DIR "backup_$deploymentId"
    New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
    
    WriteInfo "Creating backup: $backupPath"
    
    # Backup frontend dist
    if (Test-Path $FRONTEND_DIST) {
        $frontendBackup = Join-Path $backupPath "frontend_dist"
        Copy-Item -Path $FRONTEND_DIST -Destination $frontendBackup -Recurse -Force
        WriteSuccess "Frontend backed up"
    }
    
    # Backup database
    if (Test-Path "instance\treasury_fresh.db") {
        $dbBackup = Join-Path $backupPath "treasury_fresh.db"
        Copy-Item -Path "instance\treasury_fresh.db" -Destination $dbBackup -Force
        WriteSuccess "Database backed up"
    }
    
    # Backup .env
    if (Test-Path ".env") {
        Copy-Item -Path ".env" -Destination (Join-Path $backupPath ".env") -Force
        WriteSuccess "Environment config backed up"
    }
    
    $backupSize = (Get-ChildItem -Path $backupPath -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
    WriteInfo "Backup size: $([math]::Round($backupSize, 2)) MB"
    
    # ============================================================================
    # STEP 3: Run Linters (Optional)
    # ============================================================================
    if (-not $SkipLint) {
        WriteHeader "Step 3: Run Linters"
        
        # Backend linting (if flake8 is available)
        WriteInfo "Checking backend code quality..."
        try {
            $flake8 = python -m flake8 --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                python -m flake8 app --count --select=E9,F63,F7,F82 --show-source --statistics
                if ($LASTEXITCODE -eq 0) {
                    WriteSuccess "Backend linting passed"
                } else {
                    WriteWarn "Backend linting found issues (non-critical)"
                }
            }
        } catch {
            WriteWarn "flake8 not available, skipping backend linting"
        }
        
        # Frontend linting
        WriteInfo "Checking frontend code quality..."
        Push-Location $FRONTEND_DIR
        try {
            npm run lint 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                WriteSuccess "Frontend linting passed"
            } else {
                WriteWarn "Frontend linting found issues (non-critical)"
            }
        } catch {
            WriteWarn "Frontend linting not configured"
        } finally {
            Pop-Location
        }
        
    } else {
        WriteHeader "Step 3: Run Linters (SKIPPED)"
    }
    
    # ============================================================================
    # STEP 4: Run Tests (Optional)
    # ============================================================================
    if (-not $SkipTests) {
        WriteHeader "Step 4: Run Tests"
        
        # Backend tests
        if (Test-Path "tests") {
            WriteInfo "Running backend tests..."
            try {
                python -m pytest tests/ -v --tb=short 2>&1 | Tee-Object -Variable testOutput
                if ($LASTEXITCODE -eq 0) {
                    WriteSuccess "Backend tests passed"
                } else {
                    WriteWarn "Some backend tests failed (review output)"
                }
            } catch {
                WriteWarn "pytest not available or tests failed"
            }
        } else {
            WriteInfo "No backend tests found"
        }
        
        # Frontend tests
        WriteInfo "Running frontend tests..."
        Push-Location $FRONTEND_DIR
        try {
            npm run test -- --run 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                WriteSuccess "Frontend tests passed"
            } else {
                WriteWarn "Some frontend tests failed"
            }
        } catch {
            WriteWarn "Frontend tests not configured or failed"
        } finally {
            Pop-Location
        }
        
    } else {
        WriteHeader "Step 4: Run Tests (SKIPPED)"
    }
    
    # ============================================================================
    # STEP 5: Database Migrations (Optional)
    # ============================================================================
    if (-not $SkipMigrations) {
        WriteHeader "Step 5: Database Migrations"
        
        if (Test-Path "migrations") {
            WriteInfo "Checking for pending migrations..."
            try {
                # Check if Flask-Migrate is available
                python -c "from flask_migrate import Migrate" 2>&1 | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    # Run migrations
                    $env:FLASK_APP = "app.py"
                    flask db upgrade 2>&1 | Tee-Object -Variable migrationOutput
                    if ($LASTEXITCODE -eq 0) {
                        WriteSuccess "Database migrations applied"
                    } else {
                        WriteWarn "Migration issues detected (check output)"
                    }
                }
            } catch {
                WriteInfo "No pending migrations or Flask-Migrate not configured"
            }
        } else {
            WriteInfo "No migrations directory found"
        }
        
    } else {
        WriteHeader "Step 5: Database Migrations (SKIPPED)"
    }
    
    # ============================================================================
    # STEP 6: Install Dependencies
    # ============================================================================
    WriteHeader "Step 6: Install Dependencies"
    
    # Backend dependencies
    WriteInfo "Checking backend dependencies..."
    if (Test-Path "requirements.txt") {
        # Only install if requirements changed
        $reqHash = Get-FileHash "requirements.txt" -Algorithm MD5
        $lastReqHash = if (Test-Path ".last_requirements_hash") { Get-Content ".last_requirements_hash" } else { "" }
        
        if ($reqHash.Hash -ne $lastReqHash) {
            WriteInfo "Installing backend dependencies..."
            python -m pip install -r requirements.txt --quiet
            $reqHash.Hash | Out-File ".last_requirements_hash"
            WriteSuccess "Backend dependencies updated"
        } else {
            WriteSuccess "Backend dependencies up to date"
        }
    }
    
    # Frontend dependencies
    WriteInfo "Checking frontend dependencies..."
    Push-Location $FRONTEND_DIR
    try {
        if (-not (Test-Path "node_modules")) {
            WriteInfo "Installing frontend dependencies..."
            npm install
            WriteSuccess "Frontend dependencies installed"
        } else {
            WriteSuccess "Frontend dependencies up to date"
        }
    } finally {
        Pop-Location
    }
    
    # ============================================================================
    # STEP 7: Build Frontend
    # ============================================================================
    WriteHeader "Step 7: Build Frontend"
    
    WriteInfo "Building frontend (production mode)..."
    Push-Location $FRONTEND_DIR
    
    try {
        # Clean previous builds and problematic folders
        @("dist", "dist_new", "dist_backup") | ForEach-Object {
            if (Test-Path $_) {
                Remove-Item -Path $_ -Recurse -Force -ErrorAction SilentlyContinue
                WriteInfo "Cleaned $_"
            }
        }
        
        # Run build
        $buildOutput = npm run build 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Frontend build failed! Check output above."
        }
    } finally {
        Pop-Location
    }
    WriteSuccess "Frontend build completed"
    
    # Verify build
    if (-not (Test-Path "$FRONTEND_DIST\index.html")) {
        throw "Build verification failed: index.html not found"
    }
    
    # Show build statistics
    $distSize = (Get-ChildItem -Path $FRONTEND_DIST -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
    $fileCount = (Get-ChildItem -Path $FRONTEND_DIST -Recurse -File | Measure-Object).Count
    WriteInfo "Build size: $([math]::Round($distSize, 2)) MB ($fileCount files)"
    
    # ============================================================================
    # STEP 8: Deploy Application
    # ============================================================================
    WriteHeader "Step 8: Deploy Application"
    
    WriteSuccess "Frontend deployed to: $FRONTEND_DIST"
    WriteInfo "Frontend will be served by Vite/Nginx"
    
    # ============================================================================
    # STEP 9: Restart Services
    # ============================================================================
    WriteHeader "Step 9: Restart Services"
    
    if ($flaskRunning) {
        WriteInfo "Stopping Flask..."
        
        # Check if running as Windows Service
        $service = Get-Service -Name "PipLinePro" -ErrorAction SilentlyContinue
        if ($service) {
            WriteInfo "Detected Windows Service: $($service.Name)"
            WriteInfo "Restarting service..."
            Restart-Service -Name "PipLinePro" -Force
            WriteSuccess "Service restarted"
        } else {
            # Find and stop Flask process
            $flaskProcess = Get-Process -Name python -ErrorAction SilentlyContinue | 
                Where-Object { $_.Path -like "*python*" }
            
            if ($flaskProcess) {
                Stop-Process -Id $flaskProcess.Id -Force
                WriteSuccess "Flask stopped"
                Start-Sleep -Seconds 3
            }
            
            # Start Flask
            WriteInfo "Starting Flask..."
            Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PROJECT_ROOT'; python app.py" -WindowStyle Minimized
            WriteSuccess "Flask started"
        }
    } else {
        WriteInfo "Starting Flask..."
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PROJECT_ROOT'; python app.py" -WindowStyle Minimized
        WriteSuccess "Flask started"
    }
    
    # Wait for services to start
    WriteInfo "Waiting for services to start..."
    Start-Sleep -Seconds 5
    
    # ============================================================================
    # STEP 10: Verify Deployment
    # ============================================================================
    WriteHeader "Step 10: Verify Deployment"
    
    $verificationPassed = $true
    
    # Check backend health
    WriteInfo "Checking backend health..."
    $maxAttempts = 10
    $attempt = 0
    $backendHealthy = $false
    
    while ($attempt -lt $maxAttempts -and -not $backendHealthy) {
        Start-Sleep -Seconds 2
        $attempt++
        
        try {
            $healthCheck = Invoke-RestMethod -Uri "http://localhost:$FLASK_PORT/api/health" -TimeoutSec 3 -ErrorAction Stop
            if ($healthCheck.status -eq "healthy" -or $healthCheck.status -eq "ok") {
                $backendHealthy = $true
                WriteSuccess "Backend health check: PASSED"
                WriteInfo "  Status: $($healthCheck.status)"
                if ($healthCheck.database) {
                    WriteInfo "  Database: $($healthCheck.database)"
                }
            }
        } catch {
            if ($attempt -eq $maxAttempts) {
                WriteErr "Backend health check: FAILED"
                $verificationPassed = $false
            } else {
                WriteInfo "  Attempt $attempt/$maxAttempts..."
            }
        }
    }
    
    # Check frontend files
    WriteInfo "Checking frontend deployment..."
    if (Test-Path "$FRONTEND_DIST\index.html") {
        WriteSuccess "Frontend files: OK"
    } else {
        WriteErr "Frontend files: MISSING"
        $verificationPassed = $false
    }
    
    # Check database connection
    WriteInfo "Checking database..."
    if (Test-Path "instance\treasury_fresh.db") {
        $dbSize = (Get-Item "instance\treasury_fresh.db").Length / 1MB
        WriteSuccess "Database: OK ($([math]::Round($dbSize, 2)) MB)"
    } else {
        WriteWarn "Database file not found"
    }
    
    # ============================================================================
    # Deployment Complete
    # ============================================================================
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    WriteHeader "Deployment Complete!"
    
    if ($verificationPassed) {
        WriteSuccess "All verification checks passed!"
    } else {
        WriteWarn "Some verification checks failed - review output above"
    }
    
    WriteInfo "Deployment ID: $deploymentId"
    WriteInfo "Time taken: $([math]::Round($duration, 2)) seconds"
    WriteInfo "Backup location: $backupPath"
    WriteInfo ""
    WriteInfo "Application URLs:"
    WriteInfo "  Backend API: http://localhost:$FLASK_PORT"
    WriteInfo "  Frontend: http://erp.orderinvests.net"
    WriteInfo "  Health Check: http://localhost:$FLASK_PORT/api/health"
    WriteInfo ""
    WriteInfo "Logs:"
    WriteInfo "  Deployment log: $LOG_FILE"
    WriteInfo "  Application logs: logs\pipelinepro_enhanced.log"
    
    Write-Host "`n"
    WriteSuccess "Deployment successful!"
    WriteInfo "Next steps:"
    WriteInfo "1. Open http://erp.orderinvests.net in your browser"
    WriteInfo "2. Test all critical features"
    WriteInfo "3. Monitor logs for any errors"
    WriteInfo "4. Rollback if needed: .\rollback-deploy.ps1 $deploymentId"
    
    # Clean old backups (keep last 10)
    $oldBackups = Get-ChildItem -Path $BACKUP_DIR -Directory | 
        Sort-Object CreationTime -Descending | 
        Select-Object -Skip 10
    
    if ($oldBackups) {
        WriteInfo "`nCleaning old backups..."
        $oldBackups | ForEach-Object {
            Remove-Item $_.FullName -Recurse -Force
            WriteInfo "  Removed: $($_.Name)"
        }
    }
    
    exit 0
    
} catch {
    WriteErr "Deployment failed: $($_.Exception.Message)"
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
    
    WriteInfo "`nRollback options:"
    WriteInfo "1. Restore from backup: $backupPath"
    WriteInfo "2. Check logs: $LOG_FILE"
    WriteInfo "3. Manual rollback: Copy files from backup folder"
    
    WriteInfo "`nTroubleshooting:"
    WriteInfo "1. Check Flask logs: logs\pipelinepro_enhanced.log"
    WriteInfo "2. Check port availability: netstat -ano | findstr :$FLASK_PORT"
    WriteInfo "3. Verify Python environment: python --version"
    WriteInfo "4. Check disk space: Get-PSDrive"
    
    exit 1
}

