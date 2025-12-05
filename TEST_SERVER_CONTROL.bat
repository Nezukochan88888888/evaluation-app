@echo off
title Test Server Control System
color 0D

echo.
echo ========================================
echo      🧪 TESTING SERVER CONTROL SYSTEM 🧪
echo ========================================
echo.

echo [1/4] Testing server control scripts...
if exist "SERVER_CONTROL.bat" (
    echo ✅ SERVER_CONTROL.bat - Found
) else (
    echo ❌ SERVER_CONTROL.bat - Missing
)

if exist "QUICK_START.bat" (
    echo ✅ QUICK_START.bat - Found
) else (
    echo ❌ QUICK_START.bat - Missing
)

if exist "QUICK_STOP.bat" (
    echo ✅ QUICK_STOP.bat - Found
) else (
    echo ❌ QUICK_STOP.bat - Missing
)

if exist "SERVER_STATUS.bat" (
    echo ✅ SERVER_STATUS.bat - Found
) else (
    echo ❌ SERVER_STATUS.bat - Missing
)

echo.
echo [2/4] Testing PowerShell script...
if exist "server-control.ps1" (
    echo ✅ server-control.ps1 - Found
) else (
    echo ❌ server-control.ps1 - Missing
)

echo.
echo [3/4] Testing Python and dependencies...
py --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python - Not found
) else (
    echo ✅ Python - Available
)

py -c "from app import app; print('✅ Flask app - OK')" 2>nul
if errorlevel 1 (
    echo ❌ Flask app - Error
) else (
    echo ✅ Flask app - Ready
)

echo.
echo [4/4] Testing database...
if exist "app.db" (
    echo ✅ Database - Found
    py -c "import sqlite3; conn = sqlite3.connect('app.db'); cursor = conn.cursor(); cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"'); tables = cursor.fetchall(); print(f'✅ Tables: {len(tables)} found'); conn.close()" 2>nul
) else (
    echo ❌ Database - Not found
    echo 💡 Run SERVER_CONTROL.bat → Admin Controls → Reset Database
)

echo.
echo ========================================
echo            🎯 TEST RESULTS 🎯
echo ========================================
echo.

REM Get IP for access testing
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /R /C:"IPv4"') do set "IP=%%a"
for /f "tokens=1" %%a in ('echo %IP%') do set "CLEAN_IP=%%a"

echo 🌐 EXPECTED ACCESS URLS:
echo ========================
echo 👥 Students: http://%CLEAN_IP%:5000
echo 👨‍💼 Admin:    http://%CLEAN_IP%:5000/admin_dashboard
echo 📊 Analytics: http://%CLEAN_IP%:5000/admin/analytics
echo 💻 Local:     http://localhost:5000
echo.
echo 🚀 TO START TESTING:
echo ====================
echo 1. Run QUICK_START.bat
echo 2. Wait 10 seconds
echo 3. Open http://localhost:5000 in browser
echo 4. Test admin login: admin / admin123
echo 5. Run QUICK_STOP.bat when done
echo.
echo 💡 For full testing, use SERVER_CONTROL.bat
echo.
pause