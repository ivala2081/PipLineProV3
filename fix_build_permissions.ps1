# Fix Build Permissions - Unlock and Clean dist Directory
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Fixing Build Permissions" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Stop Python processes
Write-Host "[1/3] Stopping Python processes..." -ForegroundColor Yellow
$pythonProcesses = Get-Process -Name python -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    Write-Host "Found $($pythonProcesses.Count) Python process(es)" -ForegroundColor Yellow
    $pythonProcesses | ForEach-Object {
        Write-Host "  Stopping process ID: $($_.Id)" -ForegroundColor Gray
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
    Write-Host "OK - Python processes stopped" -ForegroundColor Green
} else {
    Write-Host "OK - No Python processes found" -ForegroundColor Green
}

# Step 2: Stop Node processes
Write-Host ""
Write-Host "[2/3] Checking for Node processes..." -ForegroundColor Yellow
$nodeProcesses = Get-Process -Name node -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*PipLinePro*" }
if ($nodeProcesses) {
    Write-Host "Found $($nodeProcesses.Count) Node process(es)" -ForegroundColor Yellow
    $nodeProcesses | ForEach-Object {
        Write-Host "  Stopping process ID: $($_.Id)" -ForegroundColor Gray
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
    Write-Host "OK - Node processes stopped" -ForegroundColor Green
} else {
    Write-Host "OK - No relevant Node processes found" -ForegroundColor Green
}

# Step 3: Remove locked dist directory
Write-Host ""
Write-Host "[3/3] Removing locked dist directory..." -ForegroundColor Yellow
$distPath = Join-Path $PSScriptRoot "frontend\dist"

if (Test-Path $distPath) {
    $maxRetries = 3
    $retryCount = 0
    $removed = $false
    
    while ($retryCount -lt $maxRetries -and -not $removed) {
        try {
            Remove-Item $distPath -Recurse -Force -ErrorAction Stop
            Write-Host "OK - Successfully removed dist directory" -ForegroundColor Green
            $removed = $true
        } catch {
            $retryCount++
            if ($retryCount -lt $maxRetries) {
                Write-Host "  Retry $retryCount/$maxRetries - Waiting 2 seconds..." -ForegroundColor Yellow
                Start-Sleep -Seconds 2
            } else {
                Write-Host "ERROR - Failed to remove dist directory" -ForegroundColor Red
                Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
                Write-Host ""
                Write-Host "Manual fix:" -ForegroundColor Yellow
                Write-Host "  1. Close file explorer windows showing dist folder" -ForegroundColor Yellow
                Write-Host "  2. Stop web servers" -ForegroundColor Yellow
                Write-Host "  3. Run: Remove-Item '$distPath' -Recurse -Force" -ForegroundColor Yellow
                exit 1
            }
        }
    }
} else {
    Write-Host "OK - dist directory doesn't exist" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "OK - Build permissions fixed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Rebuild frontend with:" -ForegroundColor Yellow
Write-Host "  cd frontend" -ForegroundColor White
Write-Host "  npm run build" -ForegroundColor White
Write-Host ""
