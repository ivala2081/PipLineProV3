# Verify fix_template_data_dates import fix
# This script checks if the import is working correctly

Write-Host "=== Verifying fix_template_data_dates Import ===" -ForegroundColor Cyan
Write-Host ""

# Check if import exists in transactions.py
Write-Host "1. Checking import in app/routes/transactions.py..." -ForegroundColor Yellow
$importLine = Select-String -Path "app\routes\transactions.py" -Pattern "from app.services.datetime_fix_service import fix_template_data_dates"
if ($importLine) {
    Write-Host "   [OK] Import found on line $($importLine.LineNumber)" -ForegroundColor Green
} else {
    Write-Host "   [ERROR] Import not found!" -ForegroundColor Red
    exit 1
}

# Test if import works
Write-Host ""
Write-Host "2. Testing Python import..." -ForegroundColor Yellow
try {
    $result = python -c "from app.services.datetime_fix_service import fix_template_data_dates; print('SUCCESS')" 2>&1
    if ($result -match "SUCCESS") {
        Write-Host "   [OK] Import works correctly" -ForegroundColor Green
    } else {
        Write-Host "   [ERROR] Import failed: $result" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   [ERROR] Failed to test import: $_" -ForegroundColor Red
    exit 1
}

# Check service status
Write-Host ""
Write-Host "3. Checking service status..." -ForegroundColor Yellow
$service = Get-Service -Name PipLinePro -ErrorAction SilentlyContinue
if ($service) {
    if ($service.Status -eq "Running") {
        Write-Host "   [OK] Service is running" -ForegroundColor Green
    } else {
        Write-Host "   [WARNING] Service is not running (Status: $($service.Status))" -ForegroundColor Yellow
    }
} else {
    Write-Host "   [ERROR] Service not found!" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "The code fix is in place. To apply it:" -ForegroundColor Yellow
Write-Host ""
Write-Host "Run PowerShell AS ADMINISTRATOR and execute:" -ForegroundColor White
Write-Host "  Restart-Service PipLinePro" -ForegroundColor Cyan
Write-Host ""
Write-Host "Or use the service manager:" -ForegroundColor White
Write-Host "  .\service_manager.ps1 restart" -ForegroundColor Cyan
Write-Host ""
Write-Host "After restarting, test: http://62.84.189.9:5000/clients" -ForegroundColor White

