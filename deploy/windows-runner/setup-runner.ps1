<#
  Opporta — one-command GitHub Actions self-hosted runner setup for Windows.

  Registers THIS Windows PC as the runner for the daily scraper so it runs from
  your Indian home IP (unblocks NIC/gov.in portals). Downloads the runner,
  registers it with the label "india", and installs it as an auto-starting
  background service — no interactive prompts.

  HOW TO RUN (once):
    1) GitHub -> repo Settings -> Actions -> Runners -> "New self-hosted runner"
       -> copy the token it shows (valid ~1 hour).
    2) Open PowerShell AS ADMINISTRATOR and paste ONE line (token pasted in):

         $env:RUNNER_TOKEN="PASTE_TOKEN_HERE"; iwr -useb https://raw.githubusercontent.com/akashhs1034/cg_tender_app/main/deploy/windows-runner/setup-runner.ps1 | iex

    3) GitHub -> Settings -> Secrets and variables -> Actions -> Variables ->
       add repository variable  SCRAPER_RUNNER = india

  Re-runnable: it re-registers cleanly with --replace.

  Optional env overrides: RUNNER_TOKEN (required), RUNNER_REPO
  (default akashhs1034/cg_tender_app), RUNNER_LABELS (default india),
  RUNNER_DIR (default C:\actions-runner).
#>

$ErrorActionPreference = 'Stop'

function Fail($m) { Write-Host "`nERROR: $m" -ForegroundColor Red; exit 1 }
function Say($m)  { Write-Host "`n==> $m" -ForegroundColor Cyan }

# --- must be Administrator (needed to install the service) --------------------
$admin = ([Security.Principal.WindowsPrincipal] `
          [Security.Principal.WindowsIdentity]::GetCurrent() `
         ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) { Fail "Open PowerShell as Administrator, then run this again." }

$Repo    = if ($env:RUNNER_REPO)   { $env:RUNNER_REPO }   else { 'akashhs1034/cg_tender_app' }
$Label   = if ($env:RUNNER_LABELS) { $env:RUNNER_LABELS } else { 'india' }
$Dir     = if ($env:RUNNER_DIR)    { $env:RUNNER_DIR }    else { 'C:\actions-runner' }
$Token   = $env:RUNNER_TOKEN
$RepoUrl = "https://github.com/$Repo"

if ([string]::IsNullOrWhiteSpace($Token)) {
  Fail "RUNNER_TOKEN is not set. First run:  `$env:RUNNER_TOKEN='paste-token'`  (get it from GitHub -> Settings -> Actions -> Runners -> New self-hosted runner)."
}

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

New-Item -ItemType Directory -Force -Path $Dir | Out-Null
Set-Location $Dir

# --- download the runner (latest release, win-x64) ---------------------------
if (-not (Test-Path (Join-Path $Dir 'config.cmd'))) {
  Say "Finding the latest runner version..."
  $rel = Invoke-RestMethod -Uri 'https://api.github.com/repos/actions/runner/releases/latest' `
                           -Headers @{ 'User-Agent' = 'opporta-setup' }
  $ver = $rel.tag_name.TrimStart('v')
  if ([string]::IsNullOrWhiteSpace($ver)) { $ver = '2.328.0' }   # fallback
  $pkg = "actions-runner-win-x64-$ver.zip"
  Say "Downloading runner v$ver ..."
  Invoke-WebRequest -Uri "https://github.com/actions/runner/releases/download/v$ver/$pkg" -OutFile $pkg
  Say "Extracting..."
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  [System.IO.Compression.ZipFile]::ExtractToDirectory((Join-Path $Dir $pkg), $Dir)
  Remove-Item $pkg -Force
} else {
  Say "Runner already downloaded in $Dir — reusing."
}

# --- clean any previous registration, then register + install service --------
Say "Registering '$env:COMPUTERNAME' with $Repo (label: $Label) and installing the service..."
& "$Dir\config.cmd" remove --token $Token 2>$null | Out-Null

& "$Dir\config.cmd" --url $RepoUrl --token $Token `
    --name "opporta-india-$env:COMPUTERNAME" `
    --labels $Label --work "_work" --unattended --replace --runasservice
if ($LASTEXITCODE -ne 0) { Fail "Runner configuration failed (exit $LASTEXITCODE). Common cause: an expired token — grab a fresh one and retry." }

Say "DONE. Runner is installed as a service and starts automatically with Windows."
Write-Host "   * Verify:  GitHub -> Settings -> Actions -> Runners  (should show 'Idle')" -ForegroundColor Green
Write-Host "   * FINAL STEP -> add repo Variable  SCRAPER_RUNNER = $Label" -ForegroundColor Yellow
Write-Host "     (Settings -> Secrets and variables -> Actions -> Variables -> New repository variable)"
Write-Host "   * Then test:  Actions -> Daily Tender Ingestion -> Run workflow  (PC must be on)."
