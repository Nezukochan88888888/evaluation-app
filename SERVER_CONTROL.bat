@echo off
title Quiz Server Control Panel
color 0B
cls

:MAIN_MENU
echo.
echo ================================================================
echo                   🎯 QUIZ SERVER CONTROL PANEL 🎯
echo ================================================================
echo.
echo [1] 🚀 START SERVER (Quick Start)
echo [2] 🛠️  START SERVER (Development Mode)
echo [3] 🏭 START SERVER (Production Mode)
echo [4] ⛔ STOP SERVER
echo [5] 🔄 RESTART SERVER
echo [6] 📊 CHECK SERVER STATUS
echo [7] 🌐 SHOW ACCESS URLS
echo [8] 🛡️  ADMIN CONTROLS
echo [9] 🔧 MAINTENANCE
echo [0] 💾 EXIT
echo.
echo ================================================================
set /p choice="Enter your choice (0-9): "

if "%choice%"=="1" goto START_QUICK
if "%choice%"=="2" goto START_DEV
if "%choice%"=="3" goto START_PROD
if "%choice%"=="4" goto STOP_SERVER
if "%choice%"=="5" goto RESTART_SERVER
if "%choice%"=="6" goto CHECK_STATUS
if "%choice%"=="7" goto SHOW_URLS
if "%choice%"=="8" goto ADMIN_MENU
if "%choice%"=="9" goto MAINTENANCE_MENU
if "%choice%"=="0" goto EXIT
goto MAIN_MENU

:START_QUICK
cls
echo.
echo 🚀 STARTING QUIZ SERVER - QUICK MODE
echo ===================================
echo.
echo This will start the server using the fastest method...
echo.
start "Quiz Server" cmd /c "start_quiz_server.bat"
timeout /t 3 >nul
goto CHECK_STATUS

:START_DEV
cls
echo.
echo 🛠️ STARTING SERVER - DEVELOPMENT MODE
echo ====================================
echo.
echo Starting with auto-reload and debug features...
echo.
start "Quiz Server DEV" cmd /c "run_local.bat"
timeout /t 3 >nul
goto MAIN_MENU

:START_PROD
cls
echo.
echo 🏭 STARTING SERVER - PRODUCTION MODE
echo ===================================
echo.
echo Starting optimized production server (Waitress)...
echo.
start "Quiz Server PROD" cmd /c "start_production_server.bat"
timeout /t 3 >nul
goto CHECK_STATUS

:STOP_SERVER
cls
echo.
echo ⛔ STOPPING QUIZ SERVER
echo ======================
echo.
echo Terminating all Python processes (Flask/Waitress servers)...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM py.exe >nul 2>&1
echo.
echo ✅ Server stopped successfully!
echo.
pause
goto MAIN_MENU

:RESTART_SERVER
cls
echo.
echo 🔄 RESTARTING QUIZ SERVER
echo ========================
echo.
echo Step 1: Stopping current server...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM py.exe >nul 2>&1
echo ✅ Server stopped.
echo.
echo Step 2: Starting server in 3 seconds...
timeout /t 3 >nul
start "Quiz Server" cmd /c "start_quiz_server.bat"
echo ✅ Server restarted!
echo.
timeout /t 2 >nul
goto CHECK_STATUS

:CHECK_STATUS
cls
echo.
echo 📊 SERVER STATUS CHECK
echo =====================
echo.

REM --- Check Port 5000 ---
netstat -an | findstr /R /C:":5000.*LISTENING" >nul
if %ERRORLEVEL% EQU 0 goto STATUS_RUNNING
goto STATUS_STOPPED

:STATUS_RUNNING
echo ✅ SERVER STATUS: RUNNING (Port 5000 Active)
echo 📡 Server is listening for connections.

REM Check for python processes (informational)
tasklist /FI "IMAGENAME eq python.exe" 2>NUL | find /I /N "python.exe" >NUL
if %ERRORLEVEL% EQU 0 goto FOUND_PYTHON_EXE
tasklist /FI "IMAGENAME eq py.exe" 2>NUL | find /I /N "py.exe" >NUL
if %ERRORLEVEL% EQU 0 goto FOUND_PY_EXE

echo ❗ Note: No obvious Python process found, but port 5000 is active.
goto STATUS_RUNNING_DONE

:FOUND_PYTHON_EXE
echo 🐍 Python process detected (python.exe).
goto STATUS_RUNNING_DONE

:FOUND_PY_EXE
echo 🐍 Python process detected (py.exe).
goto STATUS_RUNNING_DONE

:STATUS_RUNNING_DONE
echo.
pause
goto MAIN_MENU

:STATUS_STOPPED
echo ❌ SERVER STATUS: STOPPED (Port 5000 Not Active)
echo 🔌 Server is not listening on port 5000.

REM Check for lingering processes
tasklist /FI "IMAGENAME eq python.exe" 2>NUL | find /I /N "python.exe" >NUL
if %ERRORLEVEL% EQU 0 goto PROCESS_FOUND_NO_PORT
tasklist /FI "IMAGENAME eq py.exe" 2>NUL | find /I /N "py.exe" >NUL
if %ERRORLEVEL% EQU 0 goto PROCESS_FOUND_NO_PORT

echo 💤 No Python processes found.
echo.
pause
goto MAIN_MENU

:PROCESS_FOUND_NO_PORT
echo 🐍 Python process detected, but not listening on 5000.
echo    It might be stuck, starting up, or on another port.
echo.
pause
goto MAIN_MENU

:SHOW_URLS
echo.
echo 🌐 ACCESS INFORMATION
echo ====================

REM Get IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /R /C:"IPv4"') do set "IP=%%a"
for /f "tokens=1" %%a in ('echo %IP%') do set "CLEAN_IP=%%a"

echo.
echo 👥 STUDENT ACCESS:
echo    http://localhost:5000
echo    http://%CLEAN_IP%:5000
echo.
echo 👨‍💼 ADMIN ACCESS:
echo    http://localhost:5000/admin_dashboard
echo    http://%CLEAN_IP%:5000/admin_dashboard
echo.
echo 📊 ANALYTICS:
echo    http://localhost:5000/admin/analytics
echo    http://%CLEAN_IP%:5000/admin/analytics
echo.
echo 📋 Login: admin / admin123
echo.
pause
goto MAIN_MENU

:ADMIN_MENU
cls
echo.
echo 🛡️ ADMIN CONTROLS
echo ================
echo.
echo [1] 🔄 Reset Database
echo [2] 👤 Create Admin User  
echo [3] 📊 Show Database Stats
echo [4] 🗂️ Backup Database
echo [5] 🔙 Back to Main Menu
echo.
set /p admin_choice="Enter choice (1-5): "

if "%admin_choice%"=="1" goto RESET_DB
if "%admin_choice%"=="2" goto CREATE_ADMIN
if "%admin_choice%"=="3" goto DB_STATS
if "%admin_choice%"=="4" goto BACKUP_DB
if "%admin_choice%"=="5" goto MAIN_MENU
goto ADMIN_MENU

:RESET_DB
echo.
echo 🔄 RESETTING DATABASE
echo ====================
echo.
echo ⚠️  WARNING: This will delete all data!
set /p confirm="Type YES to confirm: "
if not "%confirm%"=="YES" goto ADMIN_MENU

echo.
echo Creating backup before reset...
copy app.db app_backup_before_reset.db >nul 2>&1
echo.
echo Running database reset...
py reset_database.py
echo.
echo ✅ Database reset complete!
pause
goto ADMIN_MENU

:CREATE_ADMIN
echo.
echo 👤 CREATE ADMIN USER
echo ===================
echo.
py -c "
from app import app, db
from app.models import User
with app.app_context():
    username = input('Enter admin username: ')
    password = input('Enter admin password: ')
    
    admin = User(username=username, email=f'{username}@quiz.local', is_admin=True)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    print(f'✅ Admin user {username} created successfully!')
"
pause
goto ADMIN_MENU

:DB_STATS
echo.
echo 📊 DATABASE STATISTICS
echo =====================
echo.
py -c "
from app import app, db
from app.models import User, Questions, QuizScore, StudentResponse
with app.app_context():
    print(f'👥 Total Users: {User.query.count()}')
    print(f'👨‍💼 Admin Users: {User.query.filter_by(is_admin=True).count()}')
    print(f'📝 Total Questions: {Questions.query.count()}')
    print(f'🎯 Quiz Scores: {QuizScore.query.count()}')
    print(f'📊 Student Responses: {StudentResponse.query.count()}')
"
pause
goto ADMIN_MENU

:BACKUP_DB
echo.
echo 🗂️ BACKING UP DATABASE
echo =====================
echo.
set backup_name=app_backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.db
set backup_name=%backup_name: =0%
copy app.db "%backup_name%" >nul
echo ✅ Database backed up as: %backup_name%
pause
goto ADMIN_MENU

:MAINTENANCE_MENU
cls
echo.
echo 🔧 MAINTENANCE OPTIONS
echo =====================
echo.
echo [1] 🧹 Clean Log Files
echo [2] 🔍 Check Dependencies
echo [3] 📦 Update Packages
echo [4] 🛠️ Repair Installation
echo [5] 🔙 Back to Main Menu
echo.
set /p maint_choice="Enter choice (1-5): "

if "%maint_choice%"=="1" goto CLEAN_LOGS
if "%maint_choice%"=="2" goto CHECK_DEPS
if "%maint_choice%"=="3" goto UPDATE_PACKAGES
if "%maint_choice%"=="4" goto REPAIR_INSTALL
if "%maint_choice%"=="5" goto MAIN_MENU
goto MAINTENANCE_MENU

:CLEAN_LOGS
echo.
echo 🧹 CLEANING LOG FILES
echo ====================
echo.
del server_*.txt >nul 2>&1
del *.log >nul 2>&1
echo ✅ Log files cleaned!
pause
goto MAINTENANCE_MENU

:CHECK_DEPS
echo.
echo 🔍 CHECKING DEPENDENCIES
echo =======================
echo.
py -m pip check
pause
goto MAINTENANCE_MENU

:UPDATE_PACKAGES
echo.
echo 📦 UPDATING PACKAGES
echo ===================
echo.
py -m pip install --upgrade flask flask-sqlalchemy flask-login flask-admin flask-wtf werkzeug wtforms waitress
echo ✅ Packages updated!
pause
goto MAINTENANCE_MENU

:REPAIR_INSTALL
echo.
echo 🛠️ REPAIR INSTALLATION
echo ======================
echo.
call install_and_run.bat
pause
goto MAIN_MENU

:EXIT
cls
echo.
echo 💾 EXITING SERVER CONTROL PANEL
echo ===============================
echo.
echo Thank you for using the Quiz Server Control Panel!
echo.
echo ⚠️  Note: Server will continue running in background.
echo    Use option 4 (STOP SERVER) if you want to stop it.
echo.
pause
exit

REM Error handling
:ERROR
echo.
echo ❌ An error occurred. Please try again.
pause
goto MAIN_MENU