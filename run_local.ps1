param(
  [switch]$Lan,
  [int]$Port = 5000,
  [switch]$AddFirewall
)

$ErrorActionPreference = 'Stop'

# 0) Ensure we're in the repo root (script may be double-clicked)
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host "[1/8] Checking virtual environment..."
if (-not (Test-Path .\.venv\Scripts\Activate.ps1)) {
  Write-Host "Creating venv with py..."
  py -m venv .venv
}
. .\.venv\Scripts\Activate.ps1

Write-Host "[2/8] Installing/Updating dependencies..."
py -m pip install --upgrade pip
py -m pip install -r requirements.txt

Write-Host "[3/8] Setting environment variables for this session..."
$env:FLASK_APP = "main.py"
$env:FLASK_ENV = "development"
if (-not $env:SECRET_KEY) { $env:SECRET_KEY = "dev-secret" }

Write-Host "[4/8] Preparing database (migrate if possible, else initdb)..."
try {
  py -m flask db upgrade
} catch {
  Write-Warning "flask db upgrade failed. Falling back to flask initdb..."
  py -m flask initdb
}

Write-Host "[5/8] Seeding sample questions (safe to re-run)..."
try {
  py -m flask seed
} catch {
  Write-Warning "Seeding failed: $($_.Exception.Message)"
}

# 6) Decide host binding
$hostBind = if ($Lan) { '0.0.0.0' } else { '127.0.0.1' }

# 7) Ensure port is free or pick an alternative
$preferredPorts = @($Port, 5050, 5080, 7000) | Select-Object -Unique
$chosen = $null
foreach ($p in $preferredPorts) {
  $inUse = (netstat -ano | findstr ":$p" | findstr LISTENING)
  if (-not $inUse) { $chosen = $p; break }
}
if (-not $chosen) { $chosen = $Port }

# 7b) Optionally add firewall rule (requires admin)
if ($Lan -or $AddFirewall) {
  try {
    Write-Host "[6/8] Adding firewall allow rule for TCP $chosen (requires admin)..."
    netsh advfirewall firewall add rule name="Flask $chosen" dir=in action=allow protocol=TCP localport=$chosen | Out-Null
  } catch {
    Write-Warning "Could not add firewall rule automatically. If students cannot connect, run PowerShell as Administrator and execute: netsh advfirewall firewall add rule name=\"Flask $chosen\" dir=in action=allow protocol=TCP localport=$chosen"
  }
}

# 7c) Determine LAN URL if needed
function Get-LanIPv4 {
  try {
    $ip = Get-NetIPAddress -AddressFamily IPv4 -PrefixOrigin Dhcp -SuffixOrigin Dhcp | Where-Object { $_.IPAddress -ne '127.0.0.1' } | Select-Object -First 1 -ExpandProperty IPAddress
    if (-not $ip) {
      $ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.InterfaceOperationalStatus -eq 'Up' } | Select-Object -First 1 -ExpandProperty IPAddress)
    }
    return $ip
  } catch {
    return $null
  }
}

$lanIp = if ($Lan) { Get-LanIPv4 } else { $null }

Write-Host "[7/8] Starting Flask..." -ForegroundColor Green
if ($Lan -and $lanIp) {
  Write-Host "Teacher URL (this PC): http://127.0.0.1:${chosen}" -ForegroundColor Cyan
  Write-Host ("Student URL (same LAN): http://{0}:{1}" -f $lanIp, $chosen) -ForegroundColor Cyan
  Write-Host "If students cannot reach it, ensure firewall rule exists and that you started PowerShell as Administrator for the rule to apply."
} else {
  Write-Host ("Local URL: http://127.0.0.1:{0}" -f $chosen) -ForegroundColor Cyan
}

Write-Host ("[8/8] Binding {0}:{1} ..." -f $hostBind, $chosen) -ForegroundColor Green
Write-Host "If Windows prompts for firewall access, click Allow."
py -m flask run --host=$hostBind --port=$chosen
