# PipLinePro Maintenance Script
# Run this weekly/monthly for system maintenance
# Usage: .\maintenance.ps1

$ProjectPath = "C:\PipLinePro"
$LogPath = "$ProjectPath\logs"
$BackupPath = "$ProjectPath\backups"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PipLinePro Maintenance Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Ensure directories exist
if (-not (Test-Path $LogPath)) {
    New-Item -ItemType Directory -Path $LogPath -Force | Out-Null
    Write-Host "Created logs directory" -ForegroundColor Green
}

if (-not (Test-Path $BackupPath)) {
    New-Item -ItemType Directory -Path $BackupPath -Force | Out-Null
    Write-Host "Created backups directory" -ForegroundColor Green
}

# Clean old logs (keep last 30 days)
Write-Host "Cleaning old log files (older than 30 days)..." -ForegroundColor Yellow
$oldLogs = Get-ChildItem "$LogPath\*.log" -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) }
if ($oldLogs) {
    $oldLogs | Remove-Item -Force
    Write-Host "Removed $($oldLogs.Count) old log file(s)" -ForegroundColor Green
} else {
    Write-Host "No old log files to remove" -ForegroundColor Gray
}

# Clean old backups (keep last 90 days)
Write-Host "Cleaning old backup files (older than 90 days)..." -ForegroundColor Yellow
$oldBackups = Get-ChildItem "$BackupPath\*.db" -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-90) }
if ($oldBackups) {
    $oldBackups | Remove-Item -Force
    Write-Host "Removed $($oldBackups.Count) old backup file(s)" -ForegroundColor Green
} else {
    Write-Host "No old backup files to remove" -ForegroundColor Gray
}

# Check disk space
Write-Host ""
Write-Host "Disk Space Check:" -ForegroundColor Cyan
$disk = Get-PSDrive C
$freeGB = [math]::Round($disk.Free / 1GB, 2)
$usedGB = [math]::Round(($disk.Used / 1GB), 2)
$totalGB = [math]::Round(($disk.Free + $disk.Used) / 1GB, 2)
$percentFree = [math]::Round(($disk.Free / ($disk.Free + $disk.Used)) * 100, 2)

Write-Host "  Total: $totalGB GB" -ForegroundColor White
Write-Host "  Used: $usedGB GB" -ForegroundColor White
Write-Host "  Free: $freeGB GB ($percentFree%)" -ForegroundColor $(if ($percentFree -lt 10) { "Red" } elseif ($percentFree -lt 20) { "Yellow" } else { "Green" })

if ($percentFree -lt 10) {
    Write-Host "  WARNING: Low disk space!" -ForegroundColor Red
}

# Check service status
Write-Host ""
Write-Host "Service Status:" -ForegroundColor Cyan
$service = Get-Service -Name "PipLinePro" -ErrorAction SilentlyContinue
if ($service) {
    $statusColor = if ($service.Status -eq "Running") { "Green" } else { "Red" }
    Write-Host "  Status: $($service.Status)" -ForegroundColor $statusColor
    Write-Host "  Startup Type: $($service.StartType)" -ForegroundColor White
} else {
    Write-Host "  Service 'PipLinePro' not found!" -ForegroundColor Red
    Write-Host "  Run the deployment checklist to install the service." -ForegroundColor Yellow
}

# Check database file
Write-Host ""
Write-Host "Database Check:" -ForegroundColor Cyan
$dbPath = "$ProjectPath\instance\treasury_fresh.db"
if (Test-Path $dbPath) {
    $dbSize = [math]::Round((Get-Item $dbPath).Length / 1MB, 2)
    $dbLastModified = (Get-Item $dbPath).LastWriteTime
    Write-Host "  Database: treasury_fresh.db" -ForegroundColor Green
    Write-Host "  Size: $dbSize MB" -ForegroundColor White
    Write-Host "  Last Modified: $dbLastModified" -ForegroundColor White
} else {
    Write-Host "  Database file not found!" -ForegroundColor Red
}

# Check log file sizes
Write-Host ""
Write-Host "Log File Sizes:" -ForegroundColor Cyan
$logFiles = Get-ChildItem "$LogPath\*.log" -ErrorAction SilentlyContinue
if ($logFiles) {
    foreach ($log in $logFiles) {
        $sizeMB = [math]::Round($log.Length / 1MB, 2)
        $sizeColor = if ($sizeMB -gt 100) { "Yellow" } else { "White" }
        Write-Host "  $($log.Name): $sizeMB MB" -ForegroundColor $sizeColor
    }
} else {
    Write-Host "  No log files found" -ForegroundColor Gray
}

# Check backup count
Write-Host ""
Write-Host "Backup Files:" -ForegroundColor Cyan
$backupFiles = Get-ChildItem "$BackupPath\*.db" -ErrorAction SilentlyContinue
if ($backupFiles) {
    Write-Host "  Total backups: $($backupFiles.Count)" -ForegroundColor White
    $latestBackup = $backupFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    Write-Host "  Latest backup: $($latestBackup.Name) ($($latestBackup.LastWriteTime))" -ForegroundColor White
} else {
    Write-Host "  No backup files found" -ForegroundColor Yellow
    Write-Host "  Consider running a backup: python scripts\backup_database.py" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Maintenance completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

