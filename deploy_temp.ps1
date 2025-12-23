Stop-Service PipLinePro -Force
Start-Sleep -Seconds 5
Remove-Item -Path "C:\PipLinePro\frontend\dist" -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path "C:\PipLinePro\frontend\dist" -Force
Copy-Item -Path "C:\PipLinePro\frontend\dist_new\*" -Destination "C:\PipLinePro\frontend\dist\" -Recurse -Force
Start-Service PipLinePro
Write-Host "Deploy completed!"
