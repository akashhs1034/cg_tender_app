#!/usr/bin/env bash
###############################################################################
# Opporta — India VM scraper setup
#
# Runs the daily ingestion pipeline (ingest.py) from an India-based server so
# NIC/gov.in portals that geo-block GitHub's US runners become reachable.
#
# Tested on: Oracle Cloud "Always Free" (Mumbai / Hyderabad), Ubuntu 22.04.
# Works on both ARM (Ampere A1) and x86 shapes.
#
# Usage (as the default 'ubuntu' user):
#   1) create the secrets file  ~/opporta.env   (see README.md)
#   2) curl -fsSL https://raw.githubusercontent.com/akashhs1034/cg_tender_app/main/deploy/india-vm/setup.sh | bash
#      (or: bash setup.sh   after cloning the repo)
#
# Idempotent — safe to re-run. It will:
#   • install Python + system libs + Playwright Chromium
#   • clone/refresh the repo into /opt/opporta/app
#   • create a venv and install requirements
#   • install a systemd service + daily timer (07:30 IST)
#   • do one test run and print the SCRAPER SUMMARY
###############################################################################
set -euo pipefail

REPO_URL="https://github.com/akashhs1034/cg_tender_app.git"
# Branch carrying the scraper fixes (UPPCL legacy-TLS, resilient jobs upsert,
# Playwright headless-shell). Switch to 'main' after you merge it.
BRANCH="${OPPORTA_BRANCH:-claude/project-review-optimize-9x3z45}"
APP_DIR="/opt/opporta/app"
VENV_DIR="/opt/opporta/venv"
ENV_SRC="${OPPORTA_ENV_FILE:-$HOME/opporta.env}"
ENV_DST="/opt/opporta/opporta.env"
RUN_USER="$(whoami)"

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
die() { printf '\n\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

# ---------------------------------------------------------------------------
# 0. Preconditions
# ---------------------------------------------------------------------------
[ -f "$ENV_SRC" ] || die "Secrets file not found at $ENV_SRC .
   Create it first (see deploy/india-vm/README.md). It must contain at least:
   SUPABASE_URL=...  SUPABASE_KEY=...  SUPABASE_SERVICE_KEY=...  GEMINI_API_KEY=..."

grep -q '^SUPABASE_URL=' "$ENV_SRC" || die "$ENV_SRC is missing SUPABASE_URL"
grep -q '^SUPABASE_KEY=' "$ENV_SRC" || die "$ENV_SRC is missing SUPABASE_KEY"

# ---------------------------------------------------------------------------
# 1. System packages
# ---------------------------------------------------------------------------
say "Installing system packages (python, git, build libs)…"
sudo apt-get update -y
sudo apt-get install -y python3 python3-venv python3-pip git curl ca-certificates

# ---------------------------------------------------------------------------
# 2. Fetch / refresh the repo
# ---------------------------------------------------------------------------
say "Fetching the repository ($BRANCH)…"
sudo mkdir -p /opt/opporta
sudo chown -R "$RUN_USER":"$RUN_USER" /opt/opporta
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" fetch --depth 1 origin "$BRANCH"
  git -C "$APP_DIR" checkout -B "$BRANCH" "origin/$BRANCH"
else
  git clone --depth 1 -b "$BRANCH" "$REPO_URL" "$APP_DIR"
fi

# ---------------------------------------------------------------------------
# 3. Python venv + dependencies
# ---------------------------------------------------------------------------
say "Creating virtualenv and installing Python dependencies…"
python3 -m venv "$VENV_DIR"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$APP_DIR/requirements.txt"

say "Installing Playwright Chromium + OS deps (needed by several scrapers)…"
python -m playwright install --with-deps chromium

# ---------------------------------------------------------------------------
# 4. Install secrets file (root-only readable)
# ---------------------------------------------------------------------------
say "Installing secrets file…"
cp "$ENV_SRC" "$ENV_DST"
chmod 600 "$ENV_DST"

# ---------------------------------------------------------------------------
# 5. systemd service + daily timer
# ---------------------------------------------------------------------------
say "Installing systemd service + daily timer…"
sudo tee /etc/systemd/system/opporta-scraper.service >/dev/null <<UNIT
[Unit]
Description=Opporta daily tender/job ingestion
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=$RUN_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$ENV_DST
# Refresh code before each run so fixes land automatically:
ExecStartPre=/usr/bin/git -C $APP_DIR pull --ff-only origin $BRANCH
ExecStart=$VENV_DIR/bin/python $APP_DIR/ingest.py
TimeoutStartSec=2400
UNIT

sudo tee /etc/systemd/system/opporta-scraper.timer >/dev/null <<'UNIT'
[Unit]
Description=Run Opporta ingestion daily at 07:30 IST

[Timer]
# 02:00 UTC == 07:30 IST
OnCalendar=*-*-* 02:00:00 UTC
Persistent=true

[Install]
WantedBy=timers.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now opporta-scraper.timer

# ---------------------------------------------------------------------------
# 6. Test run now
# ---------------------------------------------------------------------------
say "Doing a one-off test run (this takes ~15–25 min)…"
say "Watch the SCRAPER SUMMARY at the end — India-only portals should now return records."
set +e
sudo systemctl start opporta-scraper.service
STATUS=$?
set -e

echo
say "Recent log output:"
sudo journalctl -u opporta-scraper.service --no-pager -n 60 || true

echo
if [ "$STATUS" -eq 0 ]; then
  say "DONE. Daily timer is active. Next runs happen automatically at 07:30 IST."
  echo "   • See live logs:   sudo journalctl -u opporta-scraper.service -f"
  echo "   • Run on demand:   sudo systemctl start opporta-scraper.service"
  echo "   • Timer status:    systemctl list-timers opporta-scraper.timer"
else
  die "Test run exited non-zero. Check the log above (usually a missing secret in $ENV_DST)."
fi
