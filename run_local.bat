@echo off
setlocal ENABLEDELAYEDEXPANSION

REM 1) Ensure we run from the script's directory
cd /d "%~dp0"

echo [1/6] Checking virtual environment...
if not exist .venv\Scripts\activate.bat (
  echo Creating venv with py...
  py -m venv .venv
)
call .venv\Scripts\activate.bat

echo [2/6] Installing/Updating dependencies...
py -m pip install --upgrade pip
py -m pip install -r requirements.txt

echo [3/6] Setting environment variables for this session...
set FLASK_APP=main.py
set FLASK_ENV=development
if "%SECRET_KEY%"=="" set SECRET_KEY=dev-secret

echo [4/6] Preparing database (migrate if possible, else initdb)...
py -m flask db upgrade || py -m flask initdb

echo [5/6] Seeding sample questions (safe to re-run)...
flask seed

echo [6/6] Starting Flask on a free port...
set PORT=5000
for %%P in (5000 5050 5080 7000) do (
  for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%%P ^| findstr LISTENING') do set INUSE=1
  if not defined INUSE (
    set PORT=%%P
    goto :START
  )
  set INUSE=
)
:START
echo Starting Flask on http://127.0.0.1:%PORT% ...
flask run --host=127.0.0.1 --port=%PORT%
