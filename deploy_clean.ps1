Write-Host "Stopping service..."
Stop-Service PipLinePro -Force
Start-Sleep -Seconds 5

Write-Host "Removing old dist..."
Remove-Item -Path "C:\PipLinePro\frontend\dist" -Recurse -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

Write-Host "Creating new dist..."
New-Item -ItemType Directory -Path "C:\PipLinePro\frontend\dist" -Force | Out-Null
New-Item -ItemType Directory -Path "C:\PipLinePro\frontend\dist\js" -Force | Out-Null
New-Item -ItemType Directory -Path "C:\PipLinePro\frontend\dist\css" -Force | Out-Null

Write-Host "Copying files..."
Copy-Item -Path "C:\PipLinePro\frontend\dist_new\*" -Destination "C:\PipLinePro\frontend\dist\" -Recurse -Force

Write-Host "Starting service..."
Start-Service PipLinePro
Start-Sleep -Seconds 3

Write-Host "Verifying..."
$count = (Get-ChildItem "C:\PipLinePro\frontend\dist\js").Count
Write-Host "JS files in dist: $count"

$status = (Get-Service PipLinePro).Status
Write-Host "Service status: $status"

Write-Host "Deploy completed!"
