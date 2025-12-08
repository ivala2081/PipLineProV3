# PipLinePro Firewall Configuration Script
# MUST RUN AS ADMINISTRATOR

# Check for administrator privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Configuring Firewall for PipLinePro" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if rule already exists
$existingRule = Get-NetFirewallRule -DisplayName "PipLinePro HTTP" -ErrorAction SilentlyContinue
if ($existingRule) {
    Write-Host "Firewall rule already exists. Removing old rule..." -ForegroundColor Yellow
    Remove-NetFirewallRule -DisplayName "PipLinePro HTTP" -ErrorAction SilentlyContinue
}

# Create firewall rule
Write-Host "Creating firewall rule for port 5000..." -ForegroundColor Yellow
try {
    New-NetFirewallRule -DisplayName "PipLinePro HTTP" `
        -Direction Inbound `
        -LocalPort 5000 `
        -Protocol TCP `
        -Action Allow `
        -Description "Allow inbound HTTP traffic for PipLinePro Treasury System" | Out-Null
    
    Write-Host "Firewall rule created successfully!" -ForegroundColor Green
    Write-Host ""
    
    # Verify rule
    $rule = Get-NetFirewallRule -DisplayName "PipLinePro HTTP" -ErrorAction SilentlyContinue
    if ($rule) {
        Write-Host "Firewall Rule Details:" -ForegroundColor Cyan
        Write-Host "  Name: $($rule.DisplayName)" -ForegroundColor White
        Write-Host "  Enabled: $($rule.Enabled)" -ForegroundColor White
        Write-Host "  Direction: $($rule.Direction)" -ForegroundColor White
        Write-Host "  Action: $($rule.Action)" -ForegroundColor White
        Write-Host ""
        Write-Host "Port 5000 is now open for inbound connections!" -ForegroundColor Green
    }
} catch {
    Write-Host "ERROR: Failed to create firewall rule: $_" -ForegroundColor Red
    exit 1
}

