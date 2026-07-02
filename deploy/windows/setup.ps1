# Opporta scraper — one-time setup (Windows)
#
# Creates a Python virtualenv, installs dependencies + Playwright Chromium,
# registers a daily scheduled task ("OpportaScraper", 07:30 local), and does
# one test run.
#
# HOW TO RUN:
#   1) Install Python 3.11+ from https://www.python.org/downloads/windows/
#      -> during install, TICK "Add python.exe to PATH".
#   2) Put your secrets in  <repo>\opporta.env  (copy from
#      deploy\windows\opporta.env.example and fill in the values).
#   3) Open PowerShell in the repo folder and run:
#         powershell -ExecutionPolicy Bypass -File deploy\windows\setup.ps1

$ErrorActionPreference = "Stop"
function Say($m) { Write-Host "`n==> $m" -ForegroundColor Cyan }

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$EnvFile  = Join-Path $RepoRoot "opporta.env"
$Example  = Join-Path $PSScriptRoot "opporta.env.example"
$VenvDir  = Join-Path $RepoRoot ".venv"
$VenvPy   = Join-Path $VenvDir "Scripts\python.exe"
$RunPs1   = Join-Path $PSScriptRoot "run.ps1"

# --- 0. Python present? ---
Say "Checking for Python..."
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
if (-not $py) {
    Write-Error "Python not found on PATH. Install it from https://www.python.org/downloads/windows/ (tick 'Add python.exe to PATH'), then re-run this script."
}
$pyExe = $py.Source

# --- 1. Secrets file present? ---
if (-not (Test-Path $EnvFile)) {
    if (Test-Path $Example) { Copy-Item $Example $EnvFile }
    Write-Error "Created $EnvFile from the template. Open it, paste your Supabase/Gemini values, save, then re-run this script."
}
if (-not (Select-String -Path $EnvFile -Pattern '^\s*SUPABASE_URL=\S' -Quiet)) {
    Write-Error "$EnvFile is missing SUPABASE_URL (or it's blank). Fill it in and re-run."
}

# --- 2. Virtualenv + deps ---
Say "Creating virtualenv..."
if (-not (Test-Path $VenvPy)) { & $pyExe -m venv $VenvDir }

Say "Installing Python dependencies (a few minutes)..."
& $VenvPy -m pip install --upgrade pip
& $VenvPy -m pip install -r (Join-Path $RepoRoot "requirements.txt")

Say "Installing Playwright Chromium (needed by several scrapers)..."
& $VenvPy -m playwright install chromium

# --- 3. Scheduled task (daily 07:30 local) ---
Say "Registering daily scheduled task 'OpportaScraper' (07:30 every day)..."
$action  = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$RunPs1`""
$trigger = New-ScheduledTaskTrigger -Daily -At 7:30am
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
    -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Hours 1)
Register-ScheduledTask -TaskName "OpportaScraper" -Action $action -Trigger $trigger `
    -Settings $settings -Description "Opporta daily tender/job ingestion" -Force | Out-Null
Write-Host "   Scheduled. It runs daily at 07:30; if the PC is off then, it runs at next power-on."

# --- 4. Test run now ---
Say "Doing a test run now (~15-25 min). Watch the SCRAPER SUMMARY at the end..."
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $RunPs1
$code = $LASTEXITCODE

if ($code -eq 0) {
    Say "DONE. The India-blocked portals should now show record counts."
    Write-Host "   Run on demand:  powershell -ExecutionPolicy Bypass -File deploy\windows\run.ps1"
    Write-Host "   See the task:   open 'Task Scheduler' -> Task Scheduler Library -> OpportaScraper"
} else {
    Write-Error "Test run exited with code $code. Usually a missing/blank value in opporta.env."
}
