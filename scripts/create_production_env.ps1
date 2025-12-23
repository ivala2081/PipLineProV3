# Script to create production .env file
# Run this script as Administrator to create the .env file

Write-Host "Creating production .env file..." -ForegroundColor Yellow

$envContent = @"
# PipLinePro Production Environment Configuration
# Generated automatically - DO NOT commit to version control

FLASK_ENV=production
DEBUG=False
FLASK_APP=app.py

# SECURITY: Production secret key (generated securely)
SECRET_KEY=XmKOEbUza2I1TP1ivDM0NakEJeqwVEDE9Itz6DXxsv6vMeNJdVAYgUNPe1obpwk6SFU2myYG0bc2_nDUNFr3tQ

# SECURITY: Bulk delete confirmation code
BULK_DELETE_CONFIRMATION_CODE=G8e2ne_G

# HTTPS Configuration (set to true when SSL certificates are configured)
HTTPS_ENABLED=false
SESSION_COOKIE_SECURE=false

# Database Configuration
DATABASE_TYPE=sqlite

# CORS Configuration - Production domain
CORS_ORIGINS=http://erp.orderinvests.net,https://erp.orderinvests.net

# Redis Configuration (disabled - enable when Redis is installed)
REDIS_ENABLED=false

# Logging Configuration
LOG_LEVEL=WARNING

# Database Migration - DO NOT enable in production
INIT_DB=false

# Backup Configuration
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=90
BACKUP_SCHEDULE_TIME=23:59
"@

try {
    # Check if file exists and remove read-only attribute
    if (Test-Path ".env") {
        $file = Get-Item ".env"
        if ($file.IsReadOnly) {
            Write-Host "Removing read-only attribute from existing .env file..." -ForegroundColor Yellow
            $file.IsReadOnly = $false
        }
        
        # Ask user if they want to overwrite
        $overwrite = Read-Host ".env file already exists. Overwrite? (y/N)"
        if ($overwrite -ne "y" -and $overwrite -ne "Y") {
            Write-Host "Skipping .env file creation. Existing file will be used." -ForegroundColor Yellow
            exit 0
        }
    }
    
    # Remove read-only attribute before writing
    if (Test-Path ".env") {
        (Get-Item ".env").IsReadOnly = $false
    }
    
    $envContent | Out-File -FilePath ".env" -Encoding utf8 -NoNewline -Force
    Write-Host "✅ Production .env file created successfully!" -ForegroundColor Green
    Write-Host "⚠️  IMPORTANT: Review and update SECRET_KEY and BULK_DELETE_CONFIRMATION_CODE if needed" -ForegroundColor Yellow
} catch {
    Write-Host "❌ Error creating .env file: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting steps:" -ForegroundColor Yellow
    Write-Host "1. Check if file is open in another program (close it)" -ForegroundColor White
    Write-Host "2. Try running PowerShell as Administrator" -ForegroundColor White
    Write-Host "3. Check file permissions: Get-Acl .env" -ForegroundColor White
    Write-Host ""
    Write-Host "Alternative: Create .env file manually with the content shown above" -ForegroundColor Cyan
    exit 1
}

