# PowerShell Script to Start Flask Production Server for 60+ Students
param(
    [switch]$NoAutoOpen
)

# Set console title and colors
$Host.UI.RawUI.WindowTitle = "Flask Quiz Production Server"
Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "      FLASK QUIZ PRODUCTION SERVER" -ForegroundColor Yellow
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
Write-Host "[INFO] Checking Python installation..." -ForegroundColor Blue
try {
    $pythonVersion = py --version 2>&1
    Write-Host "[SUCCESS] $pythonVersion found!" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.7+ and try again" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install/check production packages
Write-Host ""
Write-Host "[INFO] Installing production server requirements..." -ForegroundColor Blue
try {
    py -m pip install flask flask-sqlalchemy flask-login flask-admin flask-wtf werkzeug wtforms waitress --quiet --upgrade
    Write-Host "[SUCCESS] Production packages ready!" -ForegroundColor Green
} catch {
    Write-Host "[WARNING] Package installation had issues, but continuing..." -ForegroundColor Yellow
}

# Check and create database
Write-Host ""
Write-Host "[INFO] Checking database..." -ForegroundColor Blue
if (!(Test-Path "app.db")) {
    Write-Host "[INFO] Database not found. Creating initial database..." -ForegroundColor Yellow
    py -c "from app import app, db; app.app_context().push(); db.create_all(); print('[SUCCESS] Database created!')"
}

# Run migration
Write-Host ""
Write-Host "[INFO] Running database migration (if needed)..." -ForegroundColor Blue
py -c @"
import sqlite3, os
if os.path.exists('app.db'):
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    try:
        cursor.execute('PRAGMA table_info(user)')
        columns = [column[1] for column in cursor.fetchall()]
        if 'session_token' not in columns:
            cursor.execute('ALTER TABLE user ADD COLUMN session_token VARCHAR(128)')
            conn.commit()
            print('[SUCCESS] Database updated!')
        else:
            print('[INFO] Database already up to date!')
    except Exception as e:
        print(f'[WARNING] Migration error: {e}')
    finally:
        conn.close()
"@

# Get network IP
Write-Host ""
Write-Host "[INFO] Getting network information..." -ForegroundColor Blue
$networkIP = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Wi-Fi*","Ethernet*" | Where-Object {$_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*" -or $_.IPAddress -like "172.*"})[0].IPAddress
if (!$networkIP) {
    $networkIP = "localhost"
    Write-Host "[WARNING] Could not detect network IP. Using localhost only." -ForegroundColor Yellow
}

# Display server information
Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "      PRODUCTION SERVER STARTING..." -ForegroundColor Yellow
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[SERVER INFO]" -ForegroundColor Green
Write-Host "Server Type:      Waitress (Production Grade)" -ForegroundColor White
Write-Host "Capacity:         60+ Students" -ForegroundColor White
Write-Host "Threads:          6 (Concurrent Handling)" -ForegroundColor White
Write-Host "Host Binding:     0.0.0.0 (Network Access)" -ForegroundColor White
Write-Host "Port:             5000" -ForegroundColor White
Write-Host ""
Write-Host "[ACCESS INFO]" -ForegroundColor Green
Write-Host "Local Access:     http://localhost:5000" -ForegroundColor White
Write-Host "Network Access:   http://$networkIP`:5000" -ForegroundColor White
Write-Host ""
Write-Host "[STUDENT INSTRUCTIONS]" -ForegroundColor Green
Write-Host "Students can access the quiz at:" -ForegroundColor White
Write-Host "http://$networkIP`:5000" -ForegroundColor Yellow
Write-Host ""
Write-Host "[ADMIN ACCESS]" -ForegroundColor Green
Write-Host "Admin Dashboard: http://$networkIP`:5000/admin_dashboard" -ForegroundColor White
Write-Host "Advanced Admin:  http://$networkIP`:5000/admin" -ForegroundColor White
Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "Production server optimized for 60+ students" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Red
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Auto-open browser unless disabled
if (!$NoAutoOpen) {
    Write-Host "[INFO] Opening admin dashboard in browser..." -ForegroundColor Blue
    Start-Sleep 3
    Start-Process "http://localhost:5000/admin_dashboard"
}

# Start the production server
try {
    py production_server.py
} catch {
    Write-Host ""
    Write-Host "[ERROR] Failed to start production server: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}