# PipLinePro Production Service Management Script
# Provides commands to start, stop, restart, and monitor the Flask application

param(
    [Parameter(Position=0)]
    [ValidateSet('start', 'stop', 'restart', 'status', 'logs', 'health')]
    [string]$Action = 'status'
)

$ProjectPath = "C:\PipLinePro"
$PythonPath = "C:\Python314\python.exe"
$AppPath = "$ProjectPath\app.py"
$LogPath = "$ProjectPath\logs"

function Write-Status {
    param([string]$Message, [string]$Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor $Color
}

function Get-FlaskProcess {
    """Get Flask/PipLinePro Python process"""
    $processes = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
        $cmdLine -like "*app.py*" -or $cmdLine -like "*gunicorn*" -or $cmdLine -like "*PipLinePro*"
    }
    return $processes
}

function Get-Port5000Process {
    """Get process using port 5000"""
    $connections = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
    if ($connections) {
        $pid = $connections[0].OwningProcess
        return Get-Process -Id $pid -ErrorAction SilentlyContinue
    }
    return $null
}

function Start-PipelineService {
    Write-Status "Starting PipLinePro service..." "Yellow"
    
    # Check if already running
    $existing = Get-FlaskProcess
    if ($existing) {
        Write-Status "Service is already running (PID: $($existing.Id))" "Yellow"
        return
    }
    
    # Change to project directory
    Set-Location $ProjectPath
    
    # Check if .env exists
    if (-not (Test-Path ".env")) {
        Write-Status "WARNING: .env file not found. Run scripts\create_production_env.ps1 first" "Yellow"
    }
    
    # Start Flask application
    Write-Status "Starting Flask application..." "Cyan"
    Start-Process -FilePath $PythonPath -ArgumentList $AppPath -WorkingDirectory $ProjectPath -WindowStyle Hidden
    
    # Wait for startup
    Start-Sleep -Seconds 5
    
    # Verify it's running
    $process = Get-Port5000Process
    if ($process) {
        Write-Status "Service started successfully (PID: $($process.Id))" "Green"
    } else {
        Write-Status "WARNING: Service may not have started. Check logs for errors." "Yellow"
    }
}

function Stop-PipelineService {
    Write-Status "Stopping PipLinePro service..." "Yellow"
    
    # Find Flask processes
    $processes = Get-FlaskProcess
    if (-not $processes) {
        # Try to find process on port 5000
        $process = Get-Port5000Process
        if ($process) {
            $processes = @($process)
        }
    }
    
    if ($processes) {
        foreach ($proc in $processes) {
            Write-Status "Stopping process PID: $($proc.Id)" "Yellow"
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 2
        Write-Status "Service stopped" "Green"
    } else {
        Write-Status "No running service found" "Yellow"
    }
}

function Get-ServiceStatus {
    Write-Status "=== PipLinePro Service Status ===" "Cyan"
    
    # Check Flask process
    $process = Get-FlaskProcess
    if (-not $process) {
        $process = Get-Port5000Process
    }
    
    if ($process) {
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($process.Id)").CommandLine
        } catch {
            $cmdLine = "N/A"
        }
        $memoryMB = [math]::Round($process.WorkingSet64 / 1MB, 2)
        
        $uptimeInfo = ""
        $startTimeInfo = ""
        if ($process.StartTime) {
            try {
                $uptime = (Get-Date) - $process.StartTime
                $uptimeInfo = "$($uptime.Days) days, $($uptime.Hours) hours, $($uptime.Minutes) minutes"
                $startTimeInfo = $process.StartTime.ToString()
            } catch {
                $uptimeInfo = "N/A"
                $startTimeInfo = "N/A"
            }
        } else {
            $uptimeInfo = "N/A"
            $startTimeInfo = "N/A"
        }
        
        Write-Status "Status: RUNNING" "Green"
        Write-Host "  Process ID: $($process.Id)" -ForegroundColor White
        if ($cmdLine -and $cmdLine -ne "N/A") {
            Write-Host "  Command: $($cmdLine -replace '.*python.exe', 'python.exe')" -ForegroundColor White
        }
        Write-Host "  Memory: $memoryMB MB" -ForegroundColor White
        if ($uptimeInfo -ne "N/A") {
            Write-Host "  Uptime: $uptimeInfo" -ForegroundColor White
            Write-Host "  Started: $startTimeInfo" -ForegroundColor White
        }
    } else {
        Write-Status "Status: STOPPED" "Red"
    }
    
    # Check port 5000
    $port5000 = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
    if ($port5000) {
        Write-Status "Port 5000: IN USE" "Green"
    } else {
        Write-Status "Port 5000: FREE" "Yellow"
    }
    
    # Check database
    $dbPath = "$ProjectPath\instance\treasury_fresh.db"
    if (Test-Path $dbPath) {
        $dbSize = (Get-Item $dbPath).Length / 1MB
        Write-Status "Database: OK ($([math]::Round($dbSize, 2)) MB)" "Green"
    } else {
        Write-Status "Database: NOT FOUND" "Red"
    }
    
    # Check health endpoint
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:5000/api/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Status "Health Check: OK" "Green"
        } else {
            Write-Status "Health Check: FAILED (Status: $($response.StatusCode))" "Yellow"
        }
    } catch {
        Write-Status "Health Check: FAILED ($($_.Exception.Message))" "Red"
    }
}

function Show-Logs {
    param([int]$Lines = 50)
    
    Write-Status "=== Recent Logs (last $Lines lines) ===" "Cyan"
    
    $logFile = "$LogPath\pipelinepro_enhanced.log"
    if (Test-Path $logFile) {
        Get-Content $logFile -Tail $Lines | Write-Host
    } else {
        Write-Status "Log file not found: $logFile" "Yellow"
    }
}

function Test-HealthEndpoint {
    Write-Status "Testing health endpoint..." "Yellow"
    
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/health" -Method Get -TimeoutSec 5
        Write-Status "Health Check Response:" "Green"
        $response | ConvertTo-Json -Depth 3 | Write-Host
    } catch {
        Write-Status "Health check failed: $($_.Exception.Message)" "Red"
    }
}

# Main execution
Set-Location $ProjectPath

switch ($Action) {
    'start' {
        Start-PipelineService
    }
    'stop' {
        Stop-PipelineService
    }
    'restart' {
        Stop-PipelineService
        Start-Sleep -Seconds 3
        Start-PipelineService
    }
    'status' {
        Get-ServiceStatus
    }
    'logs' {
        Show-Logs
    }
    'health' {
        Test-HealthEndpoint
    }
}

