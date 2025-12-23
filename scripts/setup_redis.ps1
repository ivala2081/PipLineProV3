# Redis Setup Script for PipLinePro
# This script helps set up Redis for production caching

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Redis Setup for PipLinePro" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ProjectPath = "C:\PipLinePro"

# Check if Redis is already installed
Write-Host "Checking Redis installation..." -ForegroundColor Yellow

$redisInstalled = $false
$redisPath = ""

# Check common Redis installation paths
$possiblePaths = @(
    "C:\Redis\redis-server.exe",
    "C:\Program Files\Redis\redis-server.exe",
    "C:\Program Files (x86)\Redis\redis-server.exe",
    "$env:ProgramFiles\Redis\redis-server.exe"
)

foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $redisInstalled = $true
        $redisPath = $path
        Write-Host "OK: Redis found at: $path" -ForegroundColor Green
        break
    }
}

if (-not $redisInstalled) {
    Write-Host "Redis is not installed." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To install Redis on Windows:" -ForegroundColor Cyan
    Write-Host "1. Download from: https://github.com/microsoftarchive/redis/releases" -ForegroundColor White
    Write-Host "2. Or use Chocolatey: choco install redis-64" -ForegroundColor White
    Write-Host "3. Or use WSL: wsl --install then apt-get install redis-server" -ForegroundColor White
    Write-Host ""
    
    $installNow = Read-Host "Would you like to download Redis installer? (y/N)"
    if ($installNow -eq "y" -or $installNow -eq "Y") {
        Write-Host "Opening Redis download page..." -ForegroundColor Yellow
        Start-Process "https://github.com/microsoftarchive/redis/releases"
    }
    
    Write-Host ""
    Write-Host "After installing Redis, run this script again to configure it." -ForegroundColor Yellow
    exit 0
}

# Check if Redis is running
Write-Host ""
Write-Host "Checking if Redis is running..." -ForegroundColor Yellow

$redisRunning = $false
try {
    $redisProcess = Get-Process -Name "redis-server" -ErrorAction SilentlyContinue
    if ($redisProcess) {
        $redisRunning = $true
        Write-Host "OK: Redis is running (PID: $($redisProcess.Id))" -ForegroundColor Green
    }
} catch {
    # Redis not running
}

if (-not $redisRunning) {
    Write-Host "Redis is not running." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To start Redis:" -ForegroundColor Cyan
    Write-Host "1. Run: redis-server" -ForegroundColor White
    Write-Host "2. Or install as Windows Service:" -ForegroundColor White
    Write-Host "   redis-server --service-install redis.windows.conf" -ForegroundColor White
    Write-Host "   redis-server --service-start" -ForegroundColor White
    Write-Host ""
    
    $startNow = Read-Host "Would you like to start Redis now? (y/N)"
    if ($startNow -eq "y" -or $startNow -eq "Y") {
        Write-Host "Starting Redis..." -ForegroundColor Yellow
        Start-Process -FilePath $redisPath -WindowStyle Hidden
        Start-Sleep -Seconds 2
        
        $redisProcess = Get-Process -Name "redis-server" -ErrorAction SilentlyContinue
        if ($redisProcess) {
            Write-Host "OK: Redis started successfully" -ForegroundColor Green
            $redisRunning = $true
        } else {
            Write-Host "ERROR: Failed to start Redis" -ForegroundColor Red
        }
    }
}

# Test Redis connection
if ($redisRunning) {
    Write-Host ""
    Write-Host "Testing Redis connection..." -ForegroundColor Yellow
    
    try {
        # Try to connect using Python
        $testScript = @"
import redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    r.ping()
    print('OK: Redis connection successful')
    print(f'Redis version: {r.info()[\"redis_version\"]}')
except Exception as e:
    print(f'ERROR: Redis connection failed: {e}')
"@
        
        $testScript | python
    } catch {
        Write-Host "WARNING: Could not test Redis connection" -ForegroundColor Yellow
    }
}

# Update .env file
Write-Host ""
Write-Host "Updating .env file..." -ForegroundColor Yellow

$envFile = "$ProjectPath\.env"
if (Test-Path $envFile) {
    $envContent = Get-Content $envFile -Raw
    
    # Update REDIS_ENABLED
    if ($envContent -match "REDIS_ENABLED=(true|false)") {
        $envContent = $envContent -replace "REDIS_ENABLED=(true|false)", "REDIS_ENABLED=true"
        Write-Host "Updated REDIS_ENABLED=true" -ForegroundColor Green
    } else {
        $envContent += "`nREDIS_ENABLED=true`n"
        Write-Host "Added REDIS_ENABLED=true" -ForegroundColor Green
    }
    
    # Add Redis configuration if not present
    if (-not ($envContent -match "REDIS_HOST")) {
        $envContent += "REDIS_HOST=localhost`nREDIS_PORT=6379`nREDIS_DB=0`n"
        Write-Host "Added Redis configuration" -ForegroundColor Green
    }
    
    $envContent | Set-Content $envFile -NoNewline
    Write-Host "OK: .env file updated" -ForegroundColor Green
} else {
    Write-Host "WARNING: .env file not found. Create it first using scripts\create_production_env.ps1" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($redisInstalled) {
    Write-Host "Redis Installation: OK" -ForegroundColor Green
} else {
    Write-Host "Redis Installation: NOT INSTALLED" -ForegroundColor Red
}

if ($redisRunning) {
    Write-Host "Redis Status: RUNNING" -ForegroundColor Green
} else {
    Write-Host "Redis Status: NOT RUNNING" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Restart PipLinePro application to use Redis" -ForegroundColor White
Write-Host "2. Monitor Redis: redis-cli monitor" -ForegroundColor White
Write-Host "3. Check Redis info: redis-cli info" -ForegroundColor White
Write-Host ""
Write-Host "To restart PipLinePro:" -ForegroundColor Cyan
Write-Host "  .\scripts\manage_production_service.ps1 restart" -ForegroundColor White

