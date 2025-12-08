# Setup Firewall Rule for Port 80
$rule = Get-NetFirewallRule -DisplayName "PipLinePro HTTP Port 80" -ErrorAction SilentlyContinue
if (-not $rule) {
    New-NetFirewallRule -DisplayName "PipLinePro HTTP Port 80" `
        -Direction Inbound `
        -LocalPort 80 `
        -Protocol TCP `
        -Action Allow `
        -Description "Allow inbound HTTP traffic for PipLinePro (Nginx)" | Out-Null
    Write-Host "[OK] Firewall rule created for port 80" -ForegroundColor Green
} else {
    Write-Host "[OK] Firewall rule already exists" -ForegroundColor Green
    if (-not $rule.Enabled) {
        Enable-NetFirewallRule -DisplayName "PipLinePro HTTP Port 80"
        Write-Host "[OK] Firewall rule enabled" -ForegroundColor Green
    }
}

