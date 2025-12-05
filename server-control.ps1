# Quiz Server Control Panel - PowerShell Edition
# Enhanced server management with better error handling

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "restart", "status", "help")]
    [string]$Action = "menu"
)

# Configuration
$ServerScript = "main.py"
$ProcessName = @("python", "py")
$Port = 5000

function Write-Banner {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "                   🎯 QUIZ SERVER CONTROL (PS) 🎯" -ForegroundColor Yellow
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Get-ServerStatus {
    $pythonProcesses = Get-Process | Where-Object { $_.ProcessName -in $ProcessName } 
    $portInUse = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    
    return @{
        ProcessRunning = ($pythonProcesses.Count -gt 0)
        PortActive = ($portInUse -ne $null)
        ProcessCount = $pythonProcesses.Count
        Processes = $pythonProcesses
    }
}

function Show-ServerStatus {
    Write-Host "📊 SERVER STATUS CHECK" -ForegroundColor Yellow
    Write-Host "=====================" -ForegroundColor Yellow
    Write-Host ""
    
    $status = Get-ServerStatus
    
    if ($status.ProcessRunning) {
        Write-Host "✅ SERVER STATUS: RUNNING" -ForegroundColor Green
        Write-Host "🐍 Python processes: $($status.ProcessCount)" -ForegroundColor Green
        
        # Show process details
        $status.Processes | ForEach-Object {
            Write-Host "   PID: $($_.Id) | CPU: $($_.CPU) | Memory: $([math]::Round($_.WorkingSet64 / 1MB, 2))MB" -ForegroundColor Gray
        }
    } else {
        Write-Host "❌ SERVER STATUS: STOPPED" -ForegroundColor Red
        Write-Host "💤 No Python processes found" -ForegroundColor Red
    }
    
    Write-Host ""
    if ($status.PortActive) {
        Write-Host "✅ PORT $Port: ACTIVE" -ForegroundColor Green
        Write-Host "📡 Server is listening for connections" -ForegroundColor Green
    } else {
        Write-Host "❌ PORT $Port: NOT ACTIVE" -ForegroundColor Red
        Write-Host "🔌 Server is not listening" -ForegroundColor Red
    }
    
    Show-AccessInfo
}

function Show-AccessInfo {
    Write-Host ""
    Write-Host "🌐 ACCESS INFORMATION" -ForegroundColor Cyan
    Write-Host "====================" -ForegroundColor Cyan
    
    # Get local IP
    $localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -match "^192\.168\." -or $_.IPAddress -match "^10\." -or $_.IPAddress -match "^172\." } | Select-Object -First 1).IPAddress
    
    Write-Host ""
    Write-Host "👥 STUDENT ACCESS:" -ForegroundColor Green
    Write-Host "   http://localhost:$Port"
    if ($localIP) {
        Write-Host "   http://$localIP`:$Port"
    }
    
    Write-Host ""
    Write-Host "👨‍💼 ADMIN ACCESS:" -ForegroundColor Yellow
    Write-Host "   http://localhost:$Port/admin_dashboard"
    if ($localIP) {
        Write-Host "   http://$localIP`:$Port/admin_dashboard"
    }
    
    Write-Host ""
    Write-Host "📊 ANALYTICS:" -ForegroundColor Magenta
    Write-Host "   http://localhost:$Port/admin/analytics"
    if ($localIP) {
        Write-Host "   http://$localIP`:$Port/admin/analytics"
    }
    
    Write-Host ""
    Write-Host "📋 Admin Login: admin / admin123" -ForegroundColor Gray
}

function Start-QuizServer {
    param([string]$Mode = "production")
    
    Write-Host "🚀 STARTING QUIZ SERVER" -ForegroundColor Yellow
    Write-Host "======================" -ForegroundColor Yellow
    Write-Host ""
    
    # Check if already running
    $status = Get-ServerStatus
    if ($status.ProcessRunning) {
        Write-Host "⚠️  Server is already running!" -ForegroundColor Yellow
        Write-Host "Use 'restart' to restart the server." -ForegroundColor Yellow
        return
    }
    
    try {
        Write-Host "📦 Checking dependencies..." -ForegroundColor Gray
        
        switch ($Mode) {
            "dev" {
                Write-Host "🛠️  Starting in DEVELOPMENT mode..." -ForegroundColor Cyan
                Start-Process -FilePath "cmd" -ArgumentList "/c", "run_local.bat" -WindowStyle Normal
            }
            "quick" {
                Write-Host "⚡ Starting QUICK mode..." -ForegroundColor Green
                Start-Process -FilePath "cmd" -ArgumentList "/c", "start_quiz_server.bat" -WindowStyle Normal
            }
            default {
                Write-Host "🏭 Starting PRODUCTION mode (Waitress)..." -ForegroundColor Blue
                Start-Process -FilePath "python" -ArgumentList $ServerScript -WindowStyle Normal
            }
        }
        
        Write-Host ""
        Write-Host "✅ Server start command issued!" -ForegroundColor Green
        Write-Host "🕐 Waiting 3 seconds for startup..." -ForegroundColor Gray
        Start-Sleep -Seconds 3
        
        Show-ServerStatus
        
    } catch {
        Write-Host "❌ Error starting server: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Stop-QuizServer {
    Write-Host "⛔ STOPPING QUIZ SERVER" -ForegroundColor Red
    Write-Host "======================" -ForegroundColor Red
    Write-Host ""
    
    $status = Get-ServerStatus
    if (-not $status.ProcessRunning) {
        Write-Host "💤 Server is already stopped." -ForegroundColor Gray
        return
    }
    
    try {
        Write-Host "🛑 Terminating Python processes..." -ForegroundColor Yellow
        
        # Graceful shutdown attempt
        $pythonProcesses = Get-Process | Where-Object { $_.ProcessName -in $ProcessName }
        foreach ($process in $pythonProcesses) {
            Write-Host "   Stopping PID: $($process.Id)" -ForegroundColor Gray
            try {
                $process | Stop-Process -Force -ErrorAction Stop
            } catch {
                Write-Host "   ⚠️  Could not stop PID: $($process.Id)" -ForegroundColor Yellow
            }
        }
        
        Start-Sleep -Seconds 2
        
        # Verify shutdown
        $newStatus = Get-ServerStatus
        if ($newStatus.ProcessRunning) {
            Write-Host "⚠️  Some processes may still be running" -ForegroundColor Yellow
        } else {
            Write-Host "✅ Server stopped successfully!" -ForegroundColor Green
        }
        
    } catch {
        Write-Host "❌ Error stopping server: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Restart-QuizServer {
    Write-Host "🔄 RESTARTING QUIZ SERVER" -ForegroundColor Yellow
    Write-Host "========================" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "Step 1: Stopping current server..." -ForegroundColor Cyan
    Stop-QuizServer
    
    Write-Host ""
    Write-Host "Step 2: Starting server..." -ForegroundColor Cyan
    Start-Sleep -Seconds 2
    Start-QuizServer
}

function Show-Menu {
    Write-Banner
    
    Write-Host "[1] 🚀 Start Server (Production)" -ForegroundColor Green
    Write-Host "[2] 🛠️  Start Server (Development)" -ForegroundColor Cyan  
    Write-Host "[3] ⚡ Start Server (Quick)" -ForegroundColor Yellow
    Write-Host "[4] ⛔ Stop Server" -ForegroundColor Red
    Write-Host "[5] 🔄 Restart Server" -ForegroundColor Blue
    Write-Host "[6] 📊 Check Status" -ForegroundColor Magenta
    Write-Host "[7] 🌐 Show Access URLs" -ForegroundColor White
    Write-Host "[8] 🛡️  Admin Tools" -ForegroundColor DarkYellow
    Write-Host "[0] 💾 Exit" -ForegroundColor Gray
    Write-Host ""
    
    $choice = Read-Host "Enter your choice (0-8)"
    
    switch ($choice) {
        "1" { Start-QuizServer -Mode "production" }
        "2" { Start-QuizServer -Mode "dev" }
        "3" { Start-QuizServer -Mode "quick" }
        "4" { Stop-QuizServer }
        "5" { Restart-QuizServer }
        "6" { Show-ServerStatus }
        "7" { Show-AccessInfo }
        "8" { Show-AdminMenu }
        "0" { Write-Host "👋 Goodbye!" -ForegroundColor Green; return }
        default { Write-Host "❌ Invalid choice" -ForegroundColor Red }
    }
    
    Write-Host ""
    Read-Host "Press Enter to continue"
    Show-Menu
}

function Show-AdminMenu {
    Write-Host ""
    Write-Host "🛡️ ADMIN TOOLS" -ForegroundColor DarkYellow
    Write-Host "==============" -ForegroundColor DarkYellow
    Write-Host ""
    
    Write-Host "[1] 🔄 Reset Database"
    Write-Host "[2] 📊 Database Stats"  
    Write-Host "[3] 🗂️ Backup Database"
    Write-Host "[4] 👤 Create Admin User"
    Write-Host "[0] 🔙 Back to Main Menu"
    Write-Host ""
    
    $choice = Read-Host "Enter choice (0-4)"
    
    switch ($choice) {
        "1" { 
            $confirm = Read-Host "⚠️  Reset database? This will delete all data! Type YES to confirm"
            if ($confirm -eq "YES") {
                python reset_database.py
            }
        }
        "2" { 
            python -c "from app import app, db; from app.models import User, Questions, QuizScore, StudentResponse; app.app_context().push(); print(f'👥 Users: {User.query.count()}'); print(f'📝 Questions: {Questions.query.count()}'); print(f'🎯 Scores: {QuizScore.query.count()}'); print(f'📊 Responses: {StudentResponse.query.count()}')"
        }
        "3" {
            $backupName = "app_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').db"
            Copy-Item "app.db" $backupName
            Write-Host "✅ Backup created: $backupName" -ForegroundColor Green
        }
        "4" {
            python -c "from app import app, db; from app.models import User; app.app_context().push(); username=input('Username: '); password=input('Password: '); admin=User(username=username, email=f'{username}@quiz.local', is_admin=True); admin.set_password(password); db.session.add(admin); db.session.commit(); print(f'✅ Admin {username} created!')"
        }
        "0" { return }
    }
}

function Show-Help {
    Write-Host ""
    Write-Host "🎯 QUIZ SERVER CONTROL - PowerShell Edition" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "USAGE:" -ForegroundColor Yellow
    Write-Host "  .\server-control.ps1 [action]"
    Write-Host ""
    Write-Host "ACTIONS:" -ForegroundColor Yellow
    Write-Host "  start    - Start the server (production mode)"
    Write-Host "  stop     - Stop the server"  
    Write-Host "  restart  - Restart the server"
    Write-Host "  status   - Show server status"
    Write-Host "  help     - Show this help"
    Write-Host "  (no action) - Show interactive menu"
    Write-Host ""
    Write-Host "EXAMPLES:" -ForegroundColor Green
    Write-Host "  .\server-control.ps1 start"
    Write-Host "  .\server-control.ps1 status"
    Write-Host "  .\server-control.ps1"
}

# Main execution
Clear-Host

switch ($Action) {
    "start" { Start-QuizServer }
    "stop" { Stop-QuizServer }
    "restart" { Restart-QuizServer }
    "status" { Show-ServerStatus }
    "help" { Show-Help }
    default { Show-Menu }
}