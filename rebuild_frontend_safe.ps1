# Safe Frontend Rebuild - Works around locked dist directory
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Safe Frontend Rebuild" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Stop Flask server if running
Write-Host "[1/4] Stopping Flask server..." -ForegroundColor Yellow
$pythonProcesses = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.Path -notlike "*Cursor*" }
if ($pythonProcesses) {
    Write-Host "Found $($pythonProcesses.Count) Python process(es) - stopping..." -ForegroundColor Yellow
    $pythonProcesses | ForEach-Object {
        Write-Host "  Stopping PID: $($_.Id)" -ForegroundColor Gray
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 3
    Write-Host "OK - Flask server stopped" -ForegroundColor Green
} else {
    Write-Host "OK - No Flask server running" -ForegroundColor Green
}

# Step 2: Build to temporary directory
Write-Host ""
Write-Host "[2/4] Building to temporary directory..." -ForegroundColor Yellow
Set-Location frontend

# Backup original config
Copy-Item "vite.config.ts" "vite.config.ts.backup" -Force

# Modify vite config to build to dist_new and disable emptyOutDir
$viteConfig = Get-Content "vite.config.ts" -Raw
$tempConfig = $viteConfig -replace "outDir: process\.env\.VITE_BUILD_OUTDIR \|\| 'dist'", "outDir: 'dist_new'"
$tempConfig = $tempConfig -replace "outDir: 'dist'", "outDir: 'dist_new'"
$tempConfig = $tempConfig -replace "emptyOutDir: true", "emptyOutDir: false"

# Write modified config
$tempConfig | Set-Content "vite.config.ts" -NoNewline -Encoding UTF8

# Build
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR - Build failed!" -ForegroundColor Red
    Set-Location ..
    exit 1
}

# Step 3: Replace old dist with new one
Write-Host ""
Write-Host "[3/4] Replacing old build..." -ForegroundColor Yellow

# Remove old dist_old if it exists
if (Test-Path "dist_old") {
    Remove-Item "dist_old" -Recurse -Force -ErrorAction SilentlyContinue
}

# Rename old dist to dist_old (if it exists and is locked, try to remove it)
if (Test-Path "dist") {
    Write-Host "Removing old dist directory..." -ForegroundColor Yellow
    try {
        # Try to remove it directly first
        Remove-Item "dist" -Recurse -Force -ErrorAction Stop
        Write-Host "OK - Old dist removed" -ForegroundColor Green
    } catch {
        # If removal fails, try renaming it
        Write-Host "Old dist is locked, renaming to dist_old..." -ForegroundColor Yellow
        try {
            Rename-Item "dist" "dist_old" -ErrorAction Stop
            Write-Host "OK - Old dist renamed" -ForegroundColor Green
        } catch {
            Write-Host "WARNING - Could not remove or rename old dist, will try to overwrite" -ForegroundColor Yellow
        }
    }
}

# Rename new build to dist
if (Test-Path "dist_new") {
    try {
        Rename-Item "dist_new" "dist" -ErrorAction Stop
        Write-Host "OK - New build installed" -ForegroundColor Green
    } catch {
        # If rename fails because dist exists, remove dist first
        Write-Host "dist still exists, removing it first..." -ForegroundColor Yellow
        Remove-Item "dist" -Recurse -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
        Rename-Item "dist_new" "dist" -ErrorAction Stop
        Write-Host "OK - New build installed" -ForegroundColor Green
    }
    
    # Clean up old build after a delay
    Start-Sleep -Seconds 2
    if (Test-Path "dist_old") {
        Remove-Item "dist_old" -Recurse -Force -ErrorAction SilentlyContinue
    }
} else {
    Write-Host "ERROR - New build directory not found!" -ForegroundColor Red
    Set-Location ..
    exit 1
}

# Step 4: Restore original config
if (Test-Path "vite.config.ts.backup") {
    Move-Item "vite.config.ts.backup" "vite.config.ts" -Force
    Write-Host "OK - Config restored" -ForegroundColor Green
}

Set-Location ..

Write-Host ""
Write-Host "[4/4] Build complete!" -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "OK - Frontend rebuilt successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now start the Flask server:" -ForegroundColor Yellow
Write-Host "  python app.py" -ForegroundColor White
Write-Host ""

