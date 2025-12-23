# Simple One-Command Deployment Script
# Deploys both frontend and backend updates to production
# Usage: .\deploy.ps1

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deploying Updates to Production" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Use the existing comprehensive deployment script
& ".\deploy_production.ps1"
