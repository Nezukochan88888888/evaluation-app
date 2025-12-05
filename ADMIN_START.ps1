# PowerShell Admin Easy Start Script for Quiz Server
param(
    [switch]$NoAutoOpen
)

# Set console appearance
$Host.UI.RawUI.WindowTitle = "Quiz Server - Admin Easy Start"
Clear-Host

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "           📚 QUIZ SERVER - ADMIN EASY START 📚" -ForegroundColor Yellow  
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "🔧 Checking requirements..." -ForegroundColor Blue
try {
    $pythonVersion = py --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found! Please install Python 3.7+ first." -ForegroundColor Red
    Write-Host "📥 Download from: https://python.org/downloads" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Install packages
Write-Host ""
Write-Host "🔧 Installing required packages (one-time setup)..." -ForegroundColor Blue
try {
    py -m pip install flask flask-sqlalchemy flask-login flask-admin flask-wtf --quiet --upgrade | Out-Null
    Write-Host "✅ Packages ready!" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Package installation had issues, but continuing..." -ForegroundColor Yellow
}

# Setup database
Write-Host ""
Write-Host "🔧 Setting up database..." -ForegroundColor Blue

if (!(Test-Path "app.db")) {
    Write-Host "📊 Creating database..." -ForegroundColor Yellow
    py -c "from app import app, db; app.app_context().push(); db.create_all(); print('✅ Database created!')"
}

# Run migration
py -c @"
import sqlite3, os
if os.path.exists('app.db'):
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    try:
        cursor.execute('PRAGMA table_info(user)')
        columns = [col[1] for col in cursor.fetchall()]
        if 'session_token' not in columns:
            cursor.execute('ALTER TABLE user ADD COLUMN session_token VARCHAR(128)')
            conn.commit()
        print('✅ Database ready!')
    except Exception as e:
        print(f'⚠️ Database warning: {e}')
    finally:
        conn.close()
"@

# Get network IP
Write-Host ""
Write-Host "🌐 Getting network information..." -ForegroundColor Blue
$networkIP = try {
    (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Wi-Fi*","Ethernet*" | 
     Where-Object {$_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*" -or $_.IPAddress -like "172.*"})[0].IPAddress
} catch {
    "localhost"
}

if (!$networkIP -or $networkIP -eq "localhost") {
    $networkIP = "localhost"
    Write-Host "⚠️ Network IP detection failed. Using localhost only." -ForegroundColor Yellow
} else {
    Write-Host "✅ Network IP detected: $networkIP" -ForegroundColor Green
}

# Display startup info
Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "                  🚀 STARTING SERVER 🚀" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📊 ADMIN URLS (will open automatically):" -ForegroundColor Green
Write-Host "   Dashboard:    http://localhost:5000/admin_dashboard" -ForegroundColor White
Write-Host "   Students:     http://localhost:5000/admin_students" -ForegroundColor White  
Write-Host "   Questions:    http://localhost:5000/admin_questions" -ForegroundColor White
Write-Host ""

Write-Host "📱 STUDENT URL (share with students):" -ForegroundColor Green
Write-Host "   WiFi Access:  http://$networkIP:5000" -ForegroundColor Yellow
Write-Host ""

Write-Host "💡 ADMIN TIPS:" -ForegroundColor Green
Write-Host "   • Bookmark the admin URLs for quick access" -ForegroundColor White
Write-Host "   • Share the student URL with your class" -ForegroundColor White  
Write-Host "   • Reset student scores anytime from Students page" -ForegroundColor White
Write-Host "   • Add questions from Questions page or bulk upload" -ForegroundColor White
Write-Host ""

Write-Host "⚠️  Keep this window open while running quiz" -ForegroundColor Red
Write-Host "   Press Ctrl+C to stop the server" -ForegroundColor Red
Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# Auto-open admin dashboard
if (!$NoAutoOpen) {
    Write-Host "🌐 Opening admin dashboard in browser..." -ForegroundColor Blue
    Start-Sleep 2
    try {
        Start-Process "http://localhost:5000/admin_dashboard"
    } catch {
        Write-Host "⚠️ Could not auto-open browser. Please manually open: http://localhost:5000/admin_dashboard" -ForegroundColor Yellow
    }
}

Write-Host ""

# Start the server
try {
    py quick_start.py
} catch {
    Write-Host ""
    Write-Host "❌ Server error: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    Write-Host ""
    Write-Host "👋 Server stopped. Thanks for using Quiz Server!" -ForegroundColor Green
    Read-Host "Press Enter to exit"
}