@echo off
title Flask Quiz Server
echo.
echo ===============================================
echo          FLASK QUIZ APP SERVER
echo ===============================================
echo.

REM Get current IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /R /C:"IPv4"') do set "IP=%%a"
for /f "tokens=1" %%a in ('echo %IP%') do set "CLEAN_IP=%%a"

echo [INFO] Checking Python installation...
py --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)
echo [SUCCESS] Python found!

echo.
echo [INFO] Skipping package check (Offline Mode)...
REM py -m pip install flask flask-sqlalchemy flask-login flask-admin flask-wtf werkzeug wtforms --quiet --upgrade
echo [SUCCESS] Required packages assumed ready!

echo.
echo [INFO] Checking database...
if not exist app.db (
    echo [INFO] Database not found. Creating initial database...
    py -c "from app import app, db; app.app_context().push(); db.create_all(); print('[SUCCESS] Database created!')"
)

echo.
echo [INFO] Running database migration (if needed)...
py -c "
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
"

echo.
echo ===============================================
echo          SERVER STARTING...
echo ===============================================
echo.
echo [ACCESS INFO]
echo Local Access:     http://localhost:5000
echo Network Access:   http://%CLEAN_IP%:5000
echo.
echo [STUDENT INSTRUCTIONS]
echo Students can access the quiz at:
echo http://%CLEAN_IP%:5000
echo.
echo [ADMIN ACCESS]
echo Admin Dashboard: http://%CLEAN_IP%:5000/admin_dashboard
echo.
echo ===============================================
echo Press Ctrl+C to stop the server
echo ===============================================
echo.

py main.py
pause