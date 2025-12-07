@echo off
title Building Quiz App Executable
echo.
echo ========================================================
echo          BUILDING STANDALONE EXECUTABLE
echo ========================================================
echo.
echo This script will compile the Python code into a standalone
echo .exe file that can run on any Windows computer without
echo needing Python installed.
echo.

echo [STEP 1/4] Installing PyInstaller...
py -m pip install pyinstaller --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install PyInstaller.
    pause
    exit /b 1
)
echo [SUCCESS] PyInstaller ready.

echo.

echo [STEP 2/4] Cleaning previous builds...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del /q *.spec 2>nul
echo [SUCCESS] Cleaned.

echo.

echo [STEP 3/4] Compiling application...
echo This may take 1-2 minutes. Please wait...
echo.

py -m PyInstaller ^
    --noconfirm ^
    --onedir ^
    --console ^
    --name "QuizServer" ^
    --add-data "app/templates;app/templates" ^
    --add-data "app/static;app/static" ^
    --add-data "migrations;migrations" ^
    --hidden-import "waitress" ^
    --hidden-import "engineio.async_drivers.threading" ^
    --hidden-import "flask_migrate" ^
    production_server.py

if errorlevel 1 (
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.

echo [STEP 4/4] Finalizing distribution package...

REM Copy the database if it exists (optional, or let it be created)
if exist app.db (
    echo Copying existing database...
    copy app.db "dist\QuizServer\" >nul
)

REM Create a simple runner script for the users
echo @echo off > "dist\QuizServer\START_QUIZ.bat"
echo echo Starting Quiz Server... >> "dist\QuizServer\START_QUIZ.bat"
echo echo Open your browser to the URL shown below. >> "dist\QuizServer\START_QUIZ.bat"
echo echo Close this window to stop the server. >> "dist\QuizServer\START_QUIZ.bat"
echo echo. >> "dist\QuizServer\START_QUIZ.bat"
echo QuizServer.exe >> "dist\QuizServer\START_QUIZ.bat"
echo pause >> "dist\QuizServer\START_QUIZ.bat"

echo.

echo ========================================================
echo          BUILD COMPLETE! 
echo ========================================================
echo.

echo The standalone application is ready in:

echo    %CD%\dist\QuizServer\

echo WHAT TO DO NOW:

echo 1. Go to the 'dist' folder.

echo 2. Zip the 'QuizServer' folder.

echo 3. Send that ZIP file to other users.

echo.


echo They just need to extract it and run 'START_QUIZ.bat'.

echo.
pause
