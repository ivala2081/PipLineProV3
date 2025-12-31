# PipLinePro - Rollback Deployment Script
# Quickly rollback to a previous deployment

param(
    [Parameter(Mandatory=$false)]
    [string]$BackupId = "",  # Specific backup ID to restore (e.g., 20251229_143022)
    [switch]$Latest = $false, # Restore the latest backup
    [switch]$List = $false    # List available backups
)

$ErrorActionPreference = "Stop"

# Configuration
$BACKUP_DIR = "deployment_backups"
$FRONTEND_DIST = "frontend\dist"
$FLASK_PORT = 5000

# Colors for output
function WriteSuccess { param($Message) Write-Host "[OK] $Message" -ForegroundColor Green }
function WriteInfo { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function WriteWarn { param($Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function WriteErr { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }
function WriteHeader { param($Message) Write-Host "`n$('='*70)`n$Message`n$('='*70)" -ForegroundColor Magenta }

WriteHeader "PipLinePro - Rollback Deployment"

# Check if backup directory exists
if (-not (Test-Path $BACKUP_DIR)) {
    WriteErr "Backup directory not found: $BACKUP_DIR"
    exit 1
}

# List backups if requested
if ($List) {
    WriteInfo "Available backups:"
    $backups = Get-ChildItem -Path $BACKUP_DIR -Directory | Sort-Object CreationTime -Descending
    
    if ($backups.Count -eq 0) {
        WriteWarn "No backups found"
        exit 0
    }
    
    $backups | ForEach-Object {
        $size = (Get-ChildItem -Path $_.FullName -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
        $timestamp = $_.CreationTime.ToString("yyyy-MM-dd HH:mm:ss")
        Write-Host "  $($_.Name) - $timestamp - $([math]::Round($size, 2)) MB" -ForegroundColor Cyan
    }
    
    WriteInfo "`nTo restore a backup, run:"
    WriteInfo "  .\rollback-deploy.ps1 -BackupId BACKUP_ID"
    WriteInfo "  .\rollback-deploy.ps1 -Latest"
    exit 0
}

# Determine which backup to restore
$backupToRestore = $null

if ($Latest) {
    $backupToRestore = Get-ChildItem -Path $BACKUP_DIR -Directory | 
        Sort-Object CreationTime -Descending | 
        Select-Object -First 1
    
    if (-not $backupToRestore) {
        WriteErr "No backups found"
        exit 1
    }
    
    WriteInfo "Selected latest backup: $($backupToRestore.Name)"
    
} elseif ($BackupId) {
    $backupPath = Join-Path $BACKUP_DIR "backup_$BackupId"
    if (Test-Path $backupPath) {
        $backupToRestore = Get-Item $backupPath
        WriteInfo "Selected backup: $($backupToRestore.Name)"
    } else {
        WriteErr "Backup not found: $backupPath"
        WriteInfo "Use -List to see available backups"
        exit 1
    }
    
} else {
    WriteErr "Please specify a backup to restore"
    WriteInfo "Options:"
    WriteInfo "  -Latest          Restore the most recent backup"
    WriteInfo "  -BackupId ID     Restore a specific backup"
    WriteInfo "  -List            List all available backups"
    exit 1
}

try {
    # Confirm rollback
    WriteWarn "This will restore the backup: $($backupToRestore.Name)"
    WriteWarn "Current deployment will be overwritten!"
    $confirm = Read-Host "Continue? (yes/no)"
    
    if ($confirm -ne "yes") {
        WriteInfo "Rollback cancelled"
        exit 0
    }
    
    WriteHeader "Starting Rollback"
    
    # Stop Flask
    WriteInfo "Stopping Flask..."
    $service = Get-Service -Name "PipLinePro" -ErrorAction SilentlyContinue
    if ($service) {
        Stop-Service -Name "PipLinePro" -Force
        WriteSuccess "Service stopped"
    } else {
        $flaskProcess = Get-Process -Name python -ErrorAction SilentlyContinue
        if ($flaskProcess) {
            Stop-Process -Id $flaskProcess.Id -Force
            WriteSuccess "Flask stopped"
        }
    }
    
    Start-Sleep -Seconds 2
    
    # Restore frontend
    $frontendBackup = Join-Path $backupToRestore.FullName "frontend_dist"
    if (Test-Path $frontendBackup) {
        WriteInfo "Restoring frontend..."
        
        # Backup current dist
        if (Test-Path $FRONTEND_DIST) {
            $tempBackup = "$FRONTEND_DIST`_before_rollback"
            if (Test-Path $tempBackup) {
                Remove-Item -Path $tempBackup -Recurse -Force
            }
            Move-Item -Path $FRONTEND_DIST -Destination $tempBackup
        }
        
        # Restore from backup
        Copy-Item -Path $frontendBackup -Destination $FRONTEND_DIST -Recurse -Force
        WriteSuccess "Frontend restored"
    }
    
    # Restore database
    $dbBackup = Join-Path $backupToRestore.FullName "treasury_fresh.db"
    if (Test-Path $dbBackup) {
        WriteInfo "Restoring database..."
        
        # Backup current database
        if (Test-Path "instance\treasury_fresh.db") {
            Copy-Item -Path "instance\treasury_fresh.db" -Destination "instance\treasury_fresh.db.before_rollback" -Force
        }
        
        # Restore from backup
        Copy-Item -Path $dbBackup -Destination "instance\treasury_fresh.db" -Force
        WriteSuccess "Database restored"
    }
    
    # Restore .env
    $envBackup = Join-Path $backupToRestore.FullName ".env"
    if (Test-Path $envBackup) {
        WriteInfo "Restoring environment config..."
        Copy-Item -Path $envBackup -Destination ".env" -Force
        WriteSuccess "Environment config restored"
    }
    
    # Restart Flask
    WriteInfo "Restarting Flask..."
    if ($service) {
        Start-Service -Name "PipLinePro"
        WriteSuccess "Service started"
    } else {
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; python app.py" -WindowStyle Minimized
        WriteSuccess "Flask started"
    }
    
    # Wait and verify
    WriteInfo "Waiting for services to start..."
    Start-Sleep -Seconds 5
    
    $maxAttempts = 10
    $attempt = 0
    $healthy = $false
    
    while ($attempt -lt $maxAttempts -and -not $healthy) {
        Start-Sleep -Seconds 2
        $attempt++
        
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$FLASK_PORT/api/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                $healthy = $true
            }
        } catch {
            WriteInfo "Attempt $attempt/$maxAttempts..."
        }
    }
    
    WriteHeader "Rollback Complete"
    
    if ($healthy) {
        WriteSuccess "Application is running and healthy"
    } else {
        WriteWarn "Application may not be fully started - check manually"
    }
    
    WriteInfo "Restored from: $($backupToRestore.Name)"
    WriteInfo "Backup timestamp: $($backupToRestore.CreationTime)"
    WriteInfo ""
    WriteInfo "Application URLs:"
    WriteInfo "  Backend: http://localhost:$FLASK_PORT"
    WriteInfo "  Frontend: http://erp.orderinvests.net"
    WriteInfo "  Health: http://localhost:$FLASK_PORT/api/health"
    
    exit 0
    
} catch {
    WriteErr "Rollback failed: $($_.Exception.Message)"
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
    exit 1
}

