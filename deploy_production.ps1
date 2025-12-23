# PipLinePro Production Deployment Script
# Builds frontend, restarts backend, and deploys to production
# Run this script after making updates to automatically deploy changes

param(
    [switch]$SkipFrontend,
    [switch]$SkipBackend,
    [switch]$Quick,
    [switch]$Help
)

$ErrorActionPreference = "Continue"
$ProjectPath = "C:\PipLinePro"
$PythonPath = "C:\Python314\python.exe"
$FrontendPath = "$ProjectPath\frontend"
$LogPath = "$ProjectPath\logs"

function Write-Step {
    param([string]$Message, [string]$Color = "Cyan")
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor $Color
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
    Write-Host "  [INFO] $Message" -ForegroundColor Yellow
}

if ($Help) {
    Write-Host "PipLinePro Production Deployment Script" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\deploy_production.ps1              # Full deployment (frontend + backend)" -ForegroundColor White
    Write-Host "  .\deploy_production.ps1 -Quick        # Quick deployment (skip checks)" -ForegroundColor White
    Write-Host "  .\deploy_production.ps1 -SkipFrontend # Deploy backend only" -ForegroundColor White
    Write-Host "  .\deploy_production.ps1 -SkipBackend  # Deploy frontend only" -ForegroundColor White
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PipLinePro Production Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Change to project directory
Set-Location $ProjectPath

# Step 1: Build Frontend
if (-not $SkipFrontend) {
    Write-Step "Step 1/4: Building Frontend" "Cyan"
    
    if (-not (Test-Path $FrontendPath)) {
        Write-Error "Frontend directory not found!"
        exit 1
    }
    
    # Use the safe rebuild script
    Write-Info "Running safe frontend build..."
    & "$ProjectPath\rebuild_frontend_safe.ps1"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Frontend build failed!"
        exit 1
    }
    
    Write-Success "Frontend built successfully"
    Write-Host ""
} else {
    Write-Step "Step 1/4: Building Frontend" "Gray"
    Write-Info "Skipped (use -SkipFrontend to hide this)"
    Write-Host ""
}

# Step 2: Check Backend Dependencies
if (-not $SkipBackend) {
    Write-Step "Step 2/4: Checking Backend" "Cyan"
    
    if (-not $Quick) {
        Write-Info "Checking Python installation..."
        $pythonCheck = & $PythonPath --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Python not found at $PythonPath"
            exit 1
        }
        Write-Success "Python: $pythonCheck"
        
        Write-Info "Checking required packages..."
        $missingPackages = @()
        $requiredPackages = @("flask", "sqlalchemy", "flask-cors")
        
        foreach ($package in $requiredPackages) {
            # Handle packages with hyphens (like flask-cors -> flask_cors)
            $importName = $package -replace '-', '_'
            $check = & $PythonPath -c "import $importName" 2>&1
            if ($LASTEXITCODE -ne 0) {
                $missingPackages += $package
            }
        }
        
        if ($missingPackages.Count -gt 0) {
            Write-Info "Missing packages: $($missingPackages -join ', ')"
            Write-Info "Installing missing packages (using --user flag for permissions)..."
            & $PythonPath -m pip install --user -r requirements.txt --no-warn-script-location
            if ($LASTEXITCODE -ne 0) {
                Write-Info "Package installation had issues, but continuing..."
                Write-Info "Critical packages may need manual installation"
            } else {
                Write-Success "Packages installed"
            }
        } else {
            Write-Success "All packages installed"
        }
    } else {
        Write-Info "Quick mode: Skipping dependency checks"
    }
    
    Write-Host ""
} else {
    Write-Step "Step 2/4: Checking Backend" "Gray"
    Write-Info "Skipped (use -SkipBackend to hide this)"
    Write-Host ""
}

# Step 3: Stop Current Server
if (-not $SkipBackend) {
    Write-Step "Step 3/4: Restarting Backend Server" "Cyan"
    
    Write-Info "Stopping current server processes..."
    
    # Stop Python processes (Flask/Gunicorn)
    $stopped = $false
    Get-Process -Name "python" -ErrorAction SilentlyContinue | ForEach-Object {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)" -ErrorAction SilentlyContinue).CommandLine
        if ($cmdLine -like "*app.py*" -or $cmdLine -like "*gunicorn*" -or $cmdLine -like "*waitress*") {
            Write-Info "Stopping Python process: $($_.Id)"
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
            $stopped = $true
        }
    }
    
    if ($stopped) {
        Start-Sleep -Seconds 3
        Write-Success "Server stopped"
    } else {
        Write-Info "No server process found (may not be running)"
    }
    
    Write-Host ""
} else {
    Write-Step "Step 3/4: Restarting Backend Server" "Gray"
    Write-Info "Skipped (use -SkipBackend to hide this)"
    Write-Host ""
}

# Step 4: Start Production Server
if (-not $SkipBackend) {
    Write-Step "Step 4/4: Starting Production Server" "Cyan"
    
    # Check for production environment file
    if (Test-Path "$ProjectPath\.env.production") {
        Write-Info "Using production environment configuration..."
        try {
            # Remove read-only attribute if set
            if (Test-Path "$ProjectPath\.env") {
                $file = Get-Item "$ProjectPath\.env" -Force
                $file.IsReadOnly = $false
            }
            Copy-Item "$ProjectPath\.env.production" "$ProjectPath\.env" -Force -ErrorAction Stop
            Write-Success "Production config loaded"
        } catch {
            Write-Info "Could not copy .env.production to .env (may be locked), using existing .env if available"
            if (-not (Test-Path "$ProjectPath\.env")) {
                Write-Error ".env file not found and could not be created!"
                exit 1
            }
        }
    } elseif (Test-Path "$ProjectPath\.env") {
        Write-Info "Using existing .env file"
    } else {
        Write-Error ".env file not found! Please create one."
        exit 1
    }
    
    # Check if database exists
    if (-not (Test-Path "$ProjectPath\instance\treasury_fresh.db")) {
        Write-Info "Database not found - will be created on first run"
    }
    
    # Start server using the production script
    Write-Info "Starting production server..."
    
    # Check for Gunicorn
    $gunicornCheck = & $PythonPath -c "import gunicorn" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Info "Starting with Gunicorn (production WSGI server)..."
        Start-Process -FilePath $PythonPath -ArgumentList "-m", "gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app:create_app()" -WorkingDirectory $ProjectPath -WindowStyle Hidden
    } else {
        # Check for Waitress (Windows-friendly)
        $waitressCheck = & $PythonPath -c "import waitress" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Info "Starting with Waitress (Windows WSGI server)..."
            Start-Process -FilePath $PythonPath -ArgumentList "-m", "waitress", "--host=0.0.0.0", "--port=5000", "--threads=4", "--call", "app:create_app" -WorkingDirectory $ProjectPath -WindowStyle Hidden
        } else {
            Write-Info "Starting with Flask development server (not recommended for production)..."
            Start-Process -FilePath $PythonPath -ArgumentList "app.py" -WorkingDirectory $ProjectPath -WindowStyle Hidden
        }
    }
    
    # Wait for server to start
    Write-Info "Waiting for server to start..."
    Start-Sleep -Seconds 5
    
    # Verify server is running
    $maxRetries = 6
    $retryCount = 0
    $serverStarted = $false
    
    while ($retryCount -lt $maxRetries -and -not $serverStarted) {
        try {
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:5000/api/v1/health/" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                $serverStarted = $true
                Write-Success "Backend server is running and healthy!"
            }
        } catch {
            $retryCount++
            if ($retryCount -lt $maxRetries) {
                Write-Info "Waiting for server... ($retryCount/$maxRetries)"
                Start-Sleep -Seconds 2
            }
        }
    }
    
    if (-not $serverStarted) {
        Write-Error "Server may not have started properly. Check logs: $LogPath"
        Write-Info "You can check status with: .\start_production_server.ps1 -Status"
    }
    
    Write-Host ""
} else {
    Write-Step "Step 4/4: Starting Production Server" "Gray"
    Write-Info "Skipped (use -SkipBackend to hide this)"
    Write-Host ""
}

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Application URLs:" -ForegroundColor Yellow
Write-Host "  Frontend: http://62.84.189.9:5000" -ForegroundColor White
Write-Host "  API: http://62.84.189.9:5000/api/v1/" -ForegroundColor White
Write-Host "  Health: http://62.84.189.9:5000/api/v1/health/" -ForegroundColor White
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Yellow
Write-Host "  .\start_production_server.ps1 -Status   # Check server status" -ForegroundColor White
Write-Host "  .\start_production_server.ps1 -Stop     # Stop server" -ForegroundColor White
Write-Host "  .\start_production_server.ps1 -Restart # Restart server" -ForegroundColor White
Write-Host ""
Write-Host "Logs location: $LogPath" -ForegroundColor Gray
Write-Host ""

