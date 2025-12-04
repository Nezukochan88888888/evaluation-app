@echo off
title Flask Quiz App - Auto Installer & Launcher
color 0A
echo.
echo ========================================================
echo          FLASK QUIZ APP - AUTO SETUP
echo ========================================================
echo.
echo This will automatically install everything needed and
echo start your quiz server!
echo.
pause

echo [STEP 1/4] Checking Python...
py --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! 
    echo Please install Python from: https://python.org
    echo Make sure to check "Add to PATH" during installation
    pause
    exit /b 1
)
echo [SUCCESS] Python is ready!

echo.
echo [STEP 2/4] Installing required packages...
echo This may take a minute...
py -m pip install --upgrade pip
py -m pip install flask flask-sqlalchemy flask-login flask-admin flask-wtf werkzeug wtforms
if errorlevel 1 (
    echo [ERROR] Package installation failed!
    echo Please check your internet connection and try again
    pause
    exit /b 1
)
echo [SUCCESS] All packages installed!

echo.
echo [STEP 3/4] Setting up database...
py -c "from app import app, db; app.app_context().push(); db.create_all(); print('[SUCCESS] Database ready!')" 2>nul
py -c "import sqlite3, os; conn = sqlite3.connect('app.db'); cursor = conn.cursor(); cursor.execute('PRAGMA table_info(user)'); columns = [column[1] for column in cursor.fetchall()]; cursor.execute('ALTER TABLE user ADD COLUMN session_token VARCHAR(128)') if 'session_token' not in columns else None; conn.commit(); conn.close(); print('[SUCCESS] Migration complete!')" 2>nul

echo.
echo [STEP 4/4] Starting server...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /R /C:"IPv4"') do set "IP=%%a"
for /f "tokens=1" %%a in ('echo %IP%') do set "CLEAN_IP=%%a"

echo.
echo ========================================================
echo          🚀 SERVER IS STARTING! 🚀
echo ========================================================
echo.
echo 📱 STUDENT ACCESS: http://%CLEAN_IP%:5000
echo 👨‍💼 ADMIN ACCESS:   http://%CLEAN_IP%:5000/admin_dashboard
echo 💻 LOCAL ACCESS:   http://localhost:5000
echo.
echo 📋 QUICK INSTRUCTIONS:
echo 1. Share the STUDENT ACCESS link with your students
echo 2. Students register and take the quiz
echo 3. Use ADMIN ACCESS to manage questions and scores
echo.
echo ⚠️  Press Ctrl+C to stop the server
echo ========================================================
echo.

py main.py
pause