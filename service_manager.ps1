# PipLinePro Service Manager
# Quick commands to manage the PipLinePro Windows Service
# Usage: .\service_manager.ps1 [start|stop|restart|status|logs]

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "restart", "status", "logs", "install", "uninstall")]
    [string]$Action = "status"
)

$ServiceName = "PipLinePro"
$LogPath = "C:\PipLinePro\logs"

function Show-Status {
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service) {
        $statusColor = if ($service.Status -eq "Running") { "Green" } else { "Red" }
        Write-Host "Service: $ServiceName" -ForegroundColor Cyan
        Write-Host "  Status: $($service.Status)" -ForegroundColor $statusColor
        Write-Host "  Startup Type: $($service.StartType)" -ForegroundColor White
        
        # Check if port is listening
        $port = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
        if ($port) {
            Write-Host "  Port 5000: Listening" -ForegroundColor Green
        } else {
            Write-Host "  Port 5000: Not listening" -ForegroundColor Yellow
        }
    } else {
        Write-Host "Service '$ServiceName' not found!" -ForegroundColor Red
        Write-Host "Run '.\service_manager.ps1 install' to install the service." -ForegroundColor Yellow
    }
}

function Show-Logs {
    Write-Host "Recent service logs:" -ForegroundColor Cyan
    Write-Host ""
    
    $outputLog = "$LogPath\service_output.log"
    $errorLog = "$LogPath\service_error.log"
    
    if (Test-Path $outputLog) {
        Write-Host "=== Service Output (last 20 lines) ===" -ForegroundColor Yellow
        Get-Content $outputLog -Tail 20 -ErrorAction SilentlyContinue
        Write-Host ""
    }
    
    if (Test-Path $errorLog) {
        Write-Host "=== Service Errors (last 20 lines) ===" -ForegroundColor Red
        Get-Content $errorLog -Tail 20 -ErrorAction SilentlyContinue
        Write-Host ""
    }
    
    $appLog = "$LogPath\pipelinepro_enhanced.log"
    if (Test-Path $appLog) {
        Write-Host "=== Application Log (last 10 lines) ===" -ForegroundColor Cyan
        Get-Content $appLog -Tail 10 -ErrorAction SilentlyContinue
    }
}

function Install-Service {
    Write-Host "Installing PipLinePro Windows Service..." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "You need to run NSSM commands manually:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "cd C:\nssm\win64" -ForegroundColor White
    Write-Host ".\nssm.exe install PipLinePro `"C:\Python314\python.exe`" `"-m waitress --host=0.0.0.0 --port=5000 --threads=4 --call app:create_app`"" -ForegroundColor White
    Write-Host ".\nssm.exe set PipLinePro AppDirectory `"C:\PipLinePro`"" -ForegroundColor White
    Write-Host ".\nssm.exe set PipLinePro AppEnvironmentExtra `"FLASK_ENV=production`" `"DEBUG=False`"" -ForegroundColor White
    Write-Host ".\nssm.exe set PipLinePro AppRestartDelay 5000" -ForegroundColor White
    Write-Host ".\nssm.exe set PipLinePro AppStdout `"C:\PipLinePro\logs\service_output.log`"" -ForegroundColor White
    Write-Host ".\nssm.exe set PipLinePro AppStderr `"C:\PipLinePro\logs\service_error.log`"" -ForegroundColor White
    Write-Host ".\nssm.exe start PipLinePro" -ForegroundColor White
    Write-Host ""
    Write-Host "See DEPLOYMENT_CHECKLIST.md for full instructions." -ForegroundColor Yellow
}

function Uninstall-Service {
    Write-Host "Uninstalling PipLinePro Windows Service..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Run this command as Administrator:" -ForegroundColor Yellow
    Write-Host "cd C:\nssm\win64" -ForegroundColor White
    Write-Host ".\nssm.exe stop PipLinePro" -ForegroundColor White
    Write-Host ".\nssm.exe remove PipLinePro confirm" -ForegroundColor White
}

switch ($Action.ToLower()) {
    "start" {
        Write-Host "Starting $ServiceName..." -ForegroundColor Cyan
        Start-Service -Name $ServiceName -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        Show-Status
    }
    "stop" {
        Write-Host "Stopping $ServiceName..." -ForegroundColor Yellow
        Stop-Service -Name $ServiceName -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        Show-Status
    }
    "restart" {
        Write-Host "Restarting $ServiceName..." -ForegroundColor Cyan
        Restart-Service -Name $ServiceName -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
        Show-Status
    }
    "status" {
        Show-Status
    }
    "logs" {
        Show-Logs
    }
    "install" {
        Install-Service
    }
    "uninstall" {
        Uninstall-Service
    }
}

