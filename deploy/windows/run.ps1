# Opporta scraper — daily run (Windows)
# Loads secrets from opporta.env, then runs ingest.py in the repo's venv.
# Called by the "OpportaScraper" scheduled task and can be run by hand.

$ErrorActionPreference = "Stop"

# Repo root = two levels up from deploy\windows\
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$EnvFile  = Join-Path $RepoRoot "opporta.env"
$VenvPy   = Join-Path $RepoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $EnvFile)) {
    Write-Error "Secrets file not found: $EnvFile  (copy deploy\windows\opporta.env.example there and fill it in)"
}
if (-not (Test-Path $VenvPy)) {
    Write-Error "Virtualenv not found. Run deploy\windows\setup.ps1 first."
}

# Load KEY=VALUE lines from opporta.env into this process's environment.
Get-Content $EnvFile | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
        $idx = $line.IndexOf("=")
        $key = $line.Substring(0, $idx).Trim()
        $val = $line.Substring($idx + 1).Trim()
        if ($key) { [Environment]::SetEnvironmentVariable($key, $val, "Process") }
    }
}

# Refresh code if this is a git checkout (optional; ignored for a ZIP download).
if (Test-Path (Join-Path $RepoRoot ".git")) {
    try { git -C $RepoRoot pull --ff-only 2>$null } catch { }
}

Set-Location $RepoRoot
Write-Host "Running Opporta ingestion from $RepoRoot ..."
& $VenvPy (Join-Path $RepoRoot "ingest.py")
exit $LASTEXITCODE
