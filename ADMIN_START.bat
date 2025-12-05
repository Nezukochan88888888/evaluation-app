@echo off
title Quiz Server - Admin Easy Start
color 0A
echo.
echo ========================================================
echo           📚 QUIZ SERVER - ADMIN EASY START 📚
echo ========================================================
echo.
echo 🔧 Checking requirements...

REM Check if Python is available
py --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.7+ first.
    echo 📥 Download from: https://python.org/downloads
    pause
    exit /b 1
)

echo ✅ Python found!
echo.
echo 🔧 Installing required packages (one-time setup)...

REM Install packages silently
py -m pip install flask flask-sqlalchemy flask-login flask-admin flask-wtf --quiet --upgrade

echo ✅ Packages ready!
echo.
echo 🔧 Setting up database...

REM Check for database and create if needed
if not exist app.db (
    echo 📊 Creating database...
    py -c "from app import app, db; app.app_context().push(); db.create_all(); print('✅ Database created!')"
)

REM Run migration
py -c "import sqlite3, os; conn = sqlite3.connect('app.db') if os.path.exists('app.db') else None; cursor = conn.cursor() if conn else None; cursor.execute('PRAGMA table_info(user)') if cursor else None; columns = [col[1] for col in cursor.fetchall()] if cursor else []; cursor.execute('ALTER TABLE user ADD COLUMN session_token VARCHAR(128)') if cursor and 'session_token' not in columns else None; conn.commit() if conn else None; conn.close() if conn else None; print('✅ Database ready!')"

echo.
echo 🌐 Getting network information...

REM Get IP address for network access
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /R /C:"IPv4"') do set "IP=%%a"
for /f "tokens=1" %%a in ('echo %IP%') do set "CLEAN_IP=%%a"

echo ✅ Network IP: %CLEAN_IP%
echo.
echo ========================================================
echo                  🚀 STARTING SERVER 🚀
echo ========================================================
echo.
echo 📊 ADMIN URLS (will open automatically):
echo    Dashboard:    http://localhost:5000/admin_dashboard
echo    Students:     http://localhost:5000/admin_students  
echo    Questions:    http://localhost:5000/admin_questions
echo.
echo 📱 STUDENT URL (share with students):
echo    WiFi Access:  http://%CLEAN_IP%:5000
echo.
echo 💡 ADMIN TIP: Bookmark these URLs for quick access!
echo.
echo ⚠️  Keep this window open while running quiz
echo    Press Ctrl+C to stop the server
echo.
echo ========================================================
echo.

REM Wait 2 seconds then auto-open admin dashboard
timeout /t 2 /nobreak >nul
start "" "http://localhost:5000/admin_dashboard"

echo 🌐 Admin dashboard opening in browser...
echo.

REM Start the server
py quick_start.py

echo.
echo 👋 Server stopped. Thanks for using Quiz Server!
pause