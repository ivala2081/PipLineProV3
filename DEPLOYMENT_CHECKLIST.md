# PipLinePro Production Deployment Checklist
## Server: 62.84.189.9 (Microsoft Server)

### ✅ PHASE 1: Environment Setup

#### 1.1 Verify Python Environment
- [ ] Python 3.14 installed at `C:\Python314\python.exe`
- [ ] Virtual environment activated (if using): `.venv\Scripts\Activate.ps1`
- [ ] All dependencies installed: `pip install -r requirements.txt`
- [ ] Waitress installed: `pip install waitress`

#### 1.2 Environment Variables
- [ ] Create `.env` file in `C:\PipLinePro\` (copy from `env.example`)
- [ ] Set `FLASK_ENV=production`
- [ ] Set `DEBUG=False`
- [ ] Set `SECRET_KEY` (generate new secure key)
- [ ] Set `DATABASE_TYPE=sqlite`
- [ ] Verify database path: `instance/treasury_fresh.db`
- [ ] Set `CORS_ORIGINS=http://62.84.189.9:5000,http://62.84.189.9`
- [ ] Set `REDIS_ENABLED=false` (if not using Redis)

#### 1.3 Frontend Build
- [ ] Navigate to `frontend` directory
- [ ] Run `npm install` (if not done)
- [ ] Run `npm run build` (builds to `dist_prod`)
- [ ] Verify `dist_prod` folder contains:
  - `index.html`
  - `js/` folder with all JS files
  - `css/` folder with CSS files
  - `plogo.png`, `manifest.json`, `sw.js`

---

### ✅ PHASE 2: Windows Service Setup (Auto-Start & Auto-Restart)

#### 2.1 Install NSSM (Non-Sucking Service Manager)
- [ ] Download NSSM from: https://nssm.cc/download
- [ ] Extract to `C:\nssm\` or `C:\Program Files\nssm\`
- [ ] Add NSSM to PATH (optional but recommended)

#### 2.2 Create Windows Service
Run PowerShell **as Administrator**:

```powershell
# Navigate to NSSM directory
cd C:\nssm\win64  # or wherever you extracted NSSM

# Install the service
.\nssm.exe install PipLinePro "C:\Python314\python.exe" "-m waitress --host=0.0.0.0 --port=5000 --threads=4 --call app:create_app"

# Set working directory
.\nssm.exe set PipLinePro AppDirectory "C:\PipLinePro"

# Set environment variables
.\nssm.exe set PipLinePro AppEnvironmentExtra "FLASK_ENV=production" "DEBUG=False"

# Configure auto-restart on failure
.\nssm.exe set PipLinePro AppRestartDelay 5000
.\nssm.exe set PipLinePro AppThrottle 1500
.\nssm.exe set PipLinePro AppExit Default Restart
.\nssm.exe set PipLinePro AppStdout "C:\PipLinePro\logs\service_output.log"
.\nssm.exe set PipLinePro AppStderr "C:\PipLinePro\logs\service_error.log"

# Set service to start automatically
.\nssm.exe set PipLinePro Start SERVICE_AUTO_START

# Set service description
.\nssm.exe set PipLinePro Description "PipLinePro Treasury Management System - Production Server"

# Start the service
.\nssm.exe start PipLinePro
```

#### 2.3 Verify Service
- [ ] Open Services (`services.msc`)
- [ ] Find "PipLinePro" service
- [ ] Verify status is "Running"
- [ ] Set "Startup type" to "Automatic"
- [ ] Test restart: Right-click → Restart

---

### ✅ PHASE 3: Firewall Configuration

#### 3.1 Open Port 5000
Run PowerShell **as Administrator**:

```powershell
# Allow inbound traffic on port 5000
New-NetFirewallRule -DisplayName "PipLinePro HTTP" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow

# Verify rule exists
Get-NetFirewallRule -DisplayName "PipLinePro HTTP"
```

---

### ✅ PHASE 4: Database Backup Automation

#### 4.1 Create Scheduled Backup Task
Run PowerShell **as Administrator**:

```powershell
# Create scheduled task for daily backups
$action = New-ScheduledTaskAction -Execute "C:\Python314\python.exe" -Argument "C:\PipLinePro\scripts\backup_database.py" -WorkingDirectory "C:\PipLinePro"
$trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "PipLinePro Daily Backup" -Action $action -Trigger $trigger -Settings $settings -Description "Daily backup of PipLinePro database"
```

#### 4.2 Verify Backup Script
- [ ] Check `scripts\backup_database.py` exists
- [ ] Test backup manually: `python scripts\backup_database.py`
- [ ] Verify backup created in `backups\` folder
- [ ] Set backup retention (e.g., keep last 30 days)

---

### ✅ PHASE 5: Logging & Monitoring

#### 5.1 Log Directory Setup
- [ ] Ensure `logs\` directory exists
- [ ] Verify log files are being created:
  - `pipelinepro_enhanced.log`
  - `pipelinepro_errors_enhanced.log`
  - `service_output.log`
  - `service_error.log`

#### 5.2 Log Rotation
- [ ] Set up log rotation (keep last 30 days)
- [ ] Configure log size limits (e.g., max 100MB per file)

#### 5.3 Health Check Monitoring
- [ ] Test health endpoint: `http://62.84.189.9:5000/api/v1/health/`
- [ ] Set up external monitoring (optional):
  - UptimeRobot
  - Pingdom
  - Custom monitoring script

---

### ✅ PHASE 6: Security Hardening

#### 6.1 File Permissions
- [ ] Restrict access to `.env` file (only Administrator)
- [ ] Restrict access to `instance\treasury_fresh.db` (only Administrator)
- [ ] Restrict access to `logs\` directory (only Administrator)

#### 6.2 SSL/HTTPS (Optional but Recommended)
- [ ] Obtain SSL certificate (Let's Encrypt, or commercial)
- [ ] Configure reverse proxy (IIS, Nginx, or Apache)
- [ ] Redirect HTTP to HTTPS
- [ ] Update `CORS_ORIGINS` to include HTTPS URL

#### 6.3 Update SECRET_KEY
- [ ] Generate new secure SECRET_KEY:
  ```python
  import secrets
  print(secrets.token_urlsafe(32))
  ```
- [ ] Update `.env` file with new SECRET_KEY
- [ ] Restart service after updating

---

### ✅ PHASE 7: Maintenance Scripts

#### 7.1 Create Maintenance Script
Create `C:\PipLinePro\maintenance.ps1`:

```powershell
# PipLinePro Maintenance Script
# Run this weekly/monthly

$ProjectPath = "C:\PipLinePro"
$LogPath = "$ProjectPath\logs"
$BackupPath = "$ProjectPath\backups"

# Clean old logs (keep last 30 days)
Get-ChildItem "$LogPath\*.log" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } | Remove-Item

# Clean old backups (keep last 90 days)
Get-ChildItem "$BackupPath\*.db" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-90) } | Remove-Item

# Check disk space
$disk = Get-PSDrive C
Write-Host "Disk space: $([math]::Round($disk.Free / 1GB, 2)) GB free"

# Check service status
$service = Get-Service -Name "PipLinePro" -ErrorAction SilentlyContinue
if ($service) {
    Write-Host "Service status: $($service.Status)"
} else {
    Write-Host "Service not found!"
}
```

#### 7.2 Schedule Maintenance
- [ ] Create scheduled task to run `maintenance.ps1` weekly
- [ ] Test maintenance script manually

---

### ✅ PHASE 8: Testing & Verification

#### 8.1 Service Tests
- [ ] Restart server: `Restart-Service PipLinePro`
- [ ] Stop server: `Stop-Service PipLinePro`
- [ ] Start server: `Start-Service PipLinePro`
- [ ] Verify service auto-starts after server reboot

#### 8.2 Application Tests
- [ ] Access: `http://62.84.189.9:5000`
- [ ] Test login functionality
- [ ] Test API endpoints: `http://62.84.189.9:5000/api/v1/health/`
- [ ] Test database operations
- [ ] Test file uploads (if applicable)

#### 8.3 Performance Tests
- [ ] Check response times
- [ ] Monitor memory usage
- [ ] Monitor CPU usage
- [ ] Check database query performance

---

### ✅ PHASE 9: Documentation & Access

#### 9.1 Document Access Information
- [ ] Server IP: `62.84.189.9`
- [ ] Port: `5000`
- [ ] Admin credentials: (store securely, not in code)
- [ ] Database location: `C:\PipLinePro\instance\treasury_fresh.db`
- [ ] Log location: `C:\PipLinePro\logs\`

#### 9.2 Create Quick Reference Card
- [ ] Service name: `PipLinePro`
- [ ] Service control commands
- [ ] Log file locations
- [ ] Backup locations
- [ ] Emergency contact information

---

### ✅ PHASE 10: Disaster Recovery

#### 10.1 Backup Verification
- [ ] Test database restore from backup
- [ ] Document restore procedure
- [ ] Store backups in multiple locations (local + cloud)

#### 10.2 Recovery Procedures
- [ ] Document how to restore from backup
- [ ] Document how to reinstall service
- [ ] Document how to recover from database corruption

---

## Quick Commands Reference

### Service Management
```powershell
# Start service
Start-Service PipLinePro

# Stop service
Stop-Service PipLinePro

# Restart service
Restart-Service PipLinePro

# Check status
Get-Service PipLinePro

# View service logs
Get-Content C:\PipLinePro\logs\service_output.log -Tail 50
```

### Manual Server Start (for testing)
```powershell
cd C:\PipLinePro
$env:FLASK_ENV = "production"
python -m waitress --host=0.0.0.0 --port=5000 --threads=4 --call app:create_app
```

### Check Running Processes
```powershell
Get-Process python | Where-Object { $_.Path -like "*Python314*" }
```

### View Recent Logs
```powershell
Get-Content C:\PipLinePro\logs\pipelinepro_enhanced.log -Tail 100
```

---

## Troubleshooting

### Service Won't Start
1. Check logs: `C:\PipLinePro\logs\service_error.log`
2. Verify Python path is correct
3. Verify `.env` file exists
4. Check port 5000 is not in use: `netstat -ano | findstr :5000`

### Application Not Accessible
1. Check firewall rules
2. Verify service is running: `Get-Service PipLinePro`
3. Check application logs
4. Test locally: `http://localhost:5000`

### Database Issues
1. Check database file permissions
2. Verify database path in `.env`
3. Check database file size (not corrupted)
4. Restore from backup if needed

---

## Maintenance Schedule

- **Daily**: Automatic database backup (2:00 AM)
- **Weekly**: Log cleanup, disk space check
- **Monthly**: Full system backup, security updates
- **Quarterly**: Performance review, optimization

---

## Support & Updates

- Keep Python packages updated: `pip list --outdated`
- Keep frontend dependencies updated: `npm outdated`
- Monitor for security vulnerabilities
- Review logs regularly for errors

---

**Last Updated**: 2025-12-01
**Server**: 62.84.189.9
**Status**: Production Ready ✅

