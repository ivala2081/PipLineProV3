@echo off
echo ========================================
echo Starting PipLinePro Treasury System
echo ========================================
echo.

cd /d %~dp0

set FLASK_ENV=production
set DEBUG=False

if not exist .env (
    echo ERROR: .env file not found!
    echo Please create .env file first
    pause
    exit /b 1
)

if not exist logs mkdir logs

echo Starting application on port 5000...
echo Access at: http://62.84.189.9:5000
echo.
echo Press Ctrl+C to stop the server
echo.

python -m waitress --host=0.0.0.0 --port=5000 --threads=4 --call app:create_app

pause