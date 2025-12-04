# PipLinePro Backup Task Installation Script
# MUST RUN AS ADMINISTRATOR

# Check for administrator privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

$TaskName = "PipLinePro Daily Backup"
$PythonPath = "C:\Python314\python.exe"
$ScriptPath = "C:\PipLinePro\scripts\backup_database.py"
$WorkingDir = "C:\PipLinePro"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installing Daily Backup Task" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python exists
if (-not (Test-Path $PythonPath)) {
    Write-Host "ERROR: Python not found at: $PythonPath" -ForegroundColor Red
    exit 1
}

# Check if backup script exists
if (-not (Test-Path $ScriptPath)) {
    Write-Host "WARNING: Backup script not found at: $ScriptPath" -ForegroundColor Yellow
    Write-Host "Creating basic backup script..." -ForegroundColor Yellow
    
    # Create basic backup script
    $backupScript = @"
import os
import shutil
from datetime import datetime

# Backup configuration
db_path = r'C:\PipLinePro\instance\treasury_fresh.db'
backup_dir = r'C:\PipLinePro\backups'

# Ensure backup directory exists
os.makedirs(backup_dir, exist_ok=True)

# Create backup filename with timestamp
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_filename = f'treasury_fresh_backup_{timestamp}.db'
backup_path = os.path.join(backup_dir, backup_filename)

# Copy database file
if os.path.exists(db_path):
    shutil.copy2(db_path, backup_path)
    print(f'Backup created: {backup_path}')
else:
    print(f'ERROR: Database file not found at {db_path}')
"@
    
    # Ensure scripts directory exists
    $scriptsDir = "C:\PipLinePro\scripts"
    if (-not (Test-Path $scriptsDir)) {
        New-Item -ItemType Directory -Path $scriptsDir -Force | Out-Null
    }
    
    $backupScript | Out-File -FilePath $ScriptPath -Encoding UTF8
    Write-Host "Backup script created" -ForegroundColor Green
}

# Remove existing task if it exists
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
}

# Create scheduled task action
Write-Host "Creating scheduled task..." -ForegroundColor Yellow
$action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "`"$ScriptPath`"" `
    -WorkingDirectory $WorkingDir

# Create trigger (daily at 2:00 AM)
$trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM

# Create task settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false

# Create principal (run as SYSTEM)
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

# Register the task
try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Daily backup of PipLinePro database (treasury_fresh.db)" | Out-Null
    
    Write-Host "Scheduled task created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Name: $TaskName" -ForegroundColor White
    Write-Host "  Schedule: Daily at 2:00 AM" -ForegroundColor White
    Write-Host "  Script: $ScriptPath" -ForegroundColor White
    Write-Host ""
    Write-Host "To test the backup manually:" -ForegroundColor Yellow
    Write-Host "  python `"$ScriptPath`"" -ForegroundColor White
    Write-Host ""
    Write-Host "To view scheduled tasks:" -ForegroundColor Yellow
    Write-Host "  Get-ScheduledTask -TaskName `"$TaskName`"" -ForegroundColor White
} catch {
    Write-Host "ERROR: Failed to create scheduled task: $_" -ForegroundColor Red
    exit 1
}

