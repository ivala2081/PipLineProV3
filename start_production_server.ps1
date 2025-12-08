# PipLinePro Production Server Startup Script
# Server: 62.84.189.9 (Microsoft Server)
# Run this script as Administrator

param(
    [switch]$Stop,
    [switch]$Restart,
    [switch]$Status
)

$ErrorActionPreference = "Continue"
$ProjectPath = "C:\PipLinePro"
$PythonPath = "C:\Python314\python.exe"
$FrontendPath = "$ProjectPath\frontend"
$LogPath = "$ProjectPath\logs"

# Ensure log directory exists
if (-not (Test-Path $LogPath)) {
    New-Item -ItemType Directory -Path $LogPath -Force | Out-Null
}

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor $Color
}

function Stop-PipelineServers {
    Write-Log "Stopping PipLinePro servers..." "Yellow"
    
    # Stop Python processes
    Get-Process -Name "python" -ErrorAction SilentlyContinue | ForEach-Object {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
        if ($cmdLine -like "*app.py*" -or $cmdLine -like "*gunicorn*") {
            Write-Log "Stopping Python process: $($_.Id)" "Yellow"
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        }
    }
    
    # Stop Node processes (frontend dev server)
    Get-Process -Name "node" -ErrorAction SilentlyContinue | ForEach-Object {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
        if ($cmdLine -like "*vite*" -or $cmdLine -like "*npm*") {
            Write-Log "Stopping Node process: $($_.Id)" "Yellow"
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        }
    }
    
    Start-Sleep -Seconds 2
    
    # Clear lock files
    Get-ChildItem "$LogPath\*.lock" -Force -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
    
    Write-Log "Servers stopped" "Green"
}

function Get-ServerStatus {
    Write-Log "=== PipLinePro Server Status ===" "Cyan"
    
    # Check Flask backend
    $flaskRunning = $false
    Get-Process -Name "python" -ErrorAction SilentlyContinue | ForEach-Object {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
        if ($cmdLine -like "*app.py*") {
            Write-Log "Flask Backend: RUNNING (PID: $($_.Id))" "Green"
            $flaskRunning = $true
        }
    }
    if (-not $flaskRunning) {
        Write-Log "Flask Backend: STOPPED" "Red"
    }
    
    # Check if port 5000 is in use
    $port5000 = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
    if ($port5000) {
        Write-Log "Port 5000: IN USE" "Green"
    } else {
        Write-Log "Port 5000: FREE" "Yellow"
    }
    
    # Check database
    if (Test-Path "$ProjectPath\instance\treasury_fresh.db") {
        $dbSize = (Get-Item "$ProjectPath\instance\treasury_fresh.db").Length / 1MB
        Write-Log "Database: OK (Size: $([math]::Round($dbSize, 2)) MB)" "Green"
    } else {
        Write-Log "Database: NOT FOUND" "Red"
    }
    
    # Check frontend build
    if (Test-Path "$FrontendPath\dist_prod\index.html") {
        Write-Log "Frontend Build: OK (dist_prod)" "Green"
    } elseif (Test-Path "$FrontendPath\dist\index.html") {
        Write-Log "Frontend Build: OK (dist)" "Green"
    } else {
        Write-Log "Frontend Build: NOT FOUND" "Red"
    }
}

function Start-ProductionServer {
    Write-Log "=== Starting PipLinePro Production Server ===" "Cyan"
    Write-Log "Server IP: 62.84.189.9" "White"
    Write-Log "Project Path: $ProjectPath" "White"
    
    # Change to project directory
    Set-Location $ProjectPath
    
    # Check if .env.production exists and copy to .env
    if (Test-Path "$ProjectPath\.env.production") {
        Write-Log "Using production environment configuration..." "Yellow"
        Copy-Item "$ProjectPath\.env.production" "$ProjectPath\.env" -Force
    }
    
    # Verify database exists
    if (-not (Test-Path "$ProjectPath\instance\treasury_fresh.db")) {
        Write-Log "ERROR: Database not found at instance\treasury_fresh.db" "Red"
        exit 1
    }
    
    # Clear old log files
    Get-ChildItem "$LogPath\*.lock" -Force -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
    
    Write-Log "Starting Flask backend on port 5000..." "Yellow"
    
    # Start Flask with Gunicorn (production WSGI server)
    # If Gunicorn is not available, fall back to Flask development server
    $gunicornAvailable = & $PythonPath -c "import gunicorn" 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Using Gunicorn WSGI server..." "Green"
        Start-Process -FilePath $PythonPath -ArgumentList "-m", "gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--timeout", "120", "app:create_app()" -WorkingDirectory $ProjectPath -WindowStyle Hidden
    } else {
        Write-Log "Gunicorn not available, using Flask development server..." "Yellow"
        Write-Log "Note: For production, install Gunicorn: pip install gunicorn" "Yellow"
        Start-Process -FilePath $PythonPath -ArgumentList "app.py" -WorkingDirectory $ProjectPath -WindowStyle Hidden
    }
    
    # Wait for server to start
    Write-Log "Waiting for server to start..." "Yellow"
    Start-Sleep -Seconds 5
    
    # Verify server is running
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:5000/api/v1/health/" -UseBasicParsing -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Log "Backend server started successfully!" "Green"
        }
    } catch {
        Write-Log "Warning: Could not verify backend health endpoint" "Yellow"
    }
    
    Write-Log "" "White"
    Write-Log "=== PipLinePro Production Server Started ===" "Green"
    Write-Log "Backend URL: http://62.84.189.9:5000" "Cyan"
    Write-Log "API Docs: http://62.84.189.9:5000/api/v1/docs/" "Cyan"
    Write-Log "" "White"
    Write-Log "To check status: .\start_production_server.ps1 -Status" "White"
    Write-Log "To stop: .\start_production_server.ps1 -Stop" "White"
    Write-Log "To restart: .\start_production_server.ps1 -Restart" "White"
}

# Main execution
if ($Stop) {
    Stop-PipelineServers
} elseif ($Restart) {
    Stop-PipelineServers
    Start-Sleep -Seconds 3
    Start-ProductionServer
} elseif ($Status) {
    Get-ServerStatus
} else {
    # Check if already running
    $alreadyRunning = $false
    Get-Process -Name "python" -ErrorAction SilentlyContinue | ForEach-Object {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
        if ($cmdLine -like "*app.py*") {
            $alreadyRunning = $true
        }
    }
    
    if ($alreadyRunning) {
        Write-Log "Server is already running. Use -Restart to restart or -Stop to stop." "Yellow"
        Get-ServerStatus
    } else {
        Start-ProductionServer
    }
}

