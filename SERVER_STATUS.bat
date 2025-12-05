@echo off
title Quiz Server Status Check
color 0E

echo.
echo ========================================
echo      📊 QUIZ SERVER STATUS CHECK 📊
echo ========================================
echo.

REM Check Python processes
tasklist /FI "IMAGENAME eq python.exe" 2>NUL | find /I /N "python.exe" >NUL
if "%ERRORLEVEL%"=="0" (
    echo ✅ SERVER: RUNNING ^(python.exe^)
    echo 🐍 Python processes found:
    tasklist /FI "IMAGENAME eq python.exe" | findstr python.exe
) else (
    tasklist /FI "IMAGENAME eq py.exe" 2>NUL | find /I /N "py.exe" >NUL
    if "%ERRORLEVEL%"=="0" (
        echo ✅ SERVER: RUNNING ^(py.exe^)
        echo 🐍 Python processes found:
        tasklist /FI "IMAGENAME eq py.exe" | findstr py.exe
    ) else (
        echo ❌ SERVER: STOPPED
        echo 💤 No Python processes detected
        goto NO_SERVER
    )
)

echo.
echo 🌐 Checking port 5000...
netstat -an | findstr :5000 >nul
if "%ERRORLEVEL%"=="0" (
    echo ✅ PORT 5000: ACTIVE
    echo 📡 Server is accepting connections
    netstat -an | findstr :5000
) else (
    echo ❌ PORT 5000: NOT LISTENING
    echo 🔌 Server may be starting or stopped
)

REM Get IP for access info
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /R /C:"IPv4"') do set "IP=%%a"
for /f "tokens=1" %%a in ('echo %IP%') do set "CLEAN_IP=%%a"

echo.
echo 🌐 ACCESS LINKS:
echo ================
echo 👥 Students: http://%CLEAN_IP%:5000
echo 👨‍💼 Admin:    http://%CLEAN_IP%:5000/admin_dashboard
echo 📊 Analytics: http://%CLEAN_IP%:5000/admin/analytics
echo 💻 Local:     http://localhost:5000
echo.
echo 📋 Admin Login: admin / admin123
goto END

:NO_SERVER
echo.
echo 🚀 TO START SERVER:
echo ===================
echo • QUICK_START.bat     (Simple start)
echo • SERVER_CONTROL.bat  (Full control panel)
echo • server-control.ps1  (PowerShell version)

:END
echo.
echo ========================================
pause