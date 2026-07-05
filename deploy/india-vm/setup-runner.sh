#!/usr/bin/env bash
###############################################################################
# Opporta — register this India VM as a GitHub Actions self-hosted runner.
#
# Why: GitHub's US runners are geo-blocked by many NIC/gov.in portals. Running
# the SAME "Daily Tender Ingestion" workflow on a runner with a real Indian IP
# unblocks them — fully automated, using your GitHub Actions secrets, visible
# in the Actions UI. No separate VM cron, no secrets copied onto the box.
#
# Tested on: Oracle Cloud "Always Free" (Mumbai / Hyderabad), Ubuntu 22.04,
# both ARM (Ampere A1) and x86 shapes.
#
# ── One-time steps ──────────────────────────────────────────────────────────
# 1) On GitHub:  repo → Settings → Actions → Runners → "New self-hosted runner".
#    Copy the REGISTRATION TOKEN it shows (starts with "A...", valid ~1 hour).
# 2) On the VM (as the non-root 'ubuntu' user):
#      curl -fsSL https://raw.githubusercontent.com/akashhs1034/cg_tender_app/main/deploy/india-vm/setup-runner.sh -o setup-runner.sh
#      RUNNER_TOKEN=<paste-token> bash setup-runner.sh
# 3) On GitHub:  repo → Settings → Secrets and variables → Actions → Variables →
#    New repository variable:  name SCRAPER_RUNNER,  value  india
#    (that label points the workflow at this runner; until then it stays on
#     ubuntu-latest, so nothing breaks).
#
# Idempotent — safe to re-run (uses --replace). Env overrides:
#   RUNNER_TOKEN   (required)  registration token from step 1
#   REPO           owner/repo  (default akashhs1034/cg_tender_app)
#   RUNNER_LABELS  (default: india)   must match the SCRAPER_RUNNER variable
#   RUNNER_NAME    (default: opporta-india-<host>)
#   RUNNER_VERSION (default: latest release)
###############################################################################
set -euo pipefail

REPO="${REPO:-akashhs1034/cg_tender_app}"
REPO_URL="https://github.com/${REPO}"
RUNNER_LABELS="${RUNNER_LABELS:-india}"
RUNNER_NAME="${RUNNER_NAME:-opporta-india-$(hostname -s 2>/dev/null || echo vm)}"
RUNNER_DIR="${RUNNER_DIR:-$HOME/actions-runner}"
RUN_USER="$(whoami)"

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
die() { printf '\n\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

[ "$(id -u)" -ne 0 ] || die "Run as a NORMAL user (e.g. ubuntu), not root. The runner refuses to configure as root."
[ -n "${RUNNER_TOKEN:-}" ] || die "RUNNER_TOKEN is required. Get it from GitHub → Settings → Actions → Runners → New self-hosted runner."

# ---------------------------------------------------------------------------
# 0. Architecture → GitHub runner package
# ---------------------------------------------------------------------------
case "$(uname -m)" in
  x86_64|amd64)   RUNNER_ARCH="x64"   ;;
  aarch64|arm64)  RUNNER_ARCH="arm64" ;;
  *)              die "Unsupported CPU arch: $(uname -m)" ;;
esac

# ---------------------------------------------------------------------------
# 1. System prerequisites + Playwright OS deps (so the workflow's plain
#    'playwright install chromium' works without needing sudo at run time)
# ---------------------------------------------------------------------------
say "Installing system packages (python, git, curl, tar)…"
sudo apt-get update -y
sudo apt-get install -y python3 python3-venv python3-pip git curl ca-certificates tar jq

say "Pre-installing Playwright Chromium OS libraries (one-time, needs sudo)…"
PW_VENV="$(mktemp -d)/pw"
python3 -m venv "$PW_VENV"
"$PW_VENV/bin/pip" install -q --upgrade pip playwright
sudo "$PW_VENV/bin/python" -m playwright install-deps chromium || \
  say "playwright install-deps returned non-zero — continuing (deps may already be present)."

# ---------------------------------------------------------------------------
# 2. Download the Actions runner
# ---------------------------------------------------------------------------
RUNNER_VERSION="${RUNNER_VERSION:-}"
if [ -z "$RUNNER_VERSION" ]; then
  say "Resolving latest runner version…"
  RUNNER_VERSION="$(curl -fsSL https://api.github.com/repos/actions/runner/releases/latest \
    | jq -r '.tag_name' | sed 's/^v//')"
fi
[ -n "$RUNNER_VERSION" ] && [ "$RUNNER_VERSION" != "null" ] || RUNNER_VERSION="2.319.1"
say "Using runner v${RUNNER_VERSION} (${RUNNER_ARCH})."

mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"
PKG="actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz"
if [ ! -f "config.sh" ]; then
  curl -fsSL -o "$PKG" \
    "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${PKG}"
  tar xzf "$PKG"
  rm -f "$PKG"
fi

# ---------------------------------------------------------------------------
# 3. Register with the repo and install as a service
# ---------------------------------------------------------------------------
# If a previous service exists, stop + remove so --replace re-registers cleanly.
if [ -f "./svc.sh" ] && sudo ./svc.sh status >/dev/null 2>&1; then
  say "Existing runner service found — stopping it before re-config…"
  sudo ./svc.sh stop  || true
  sudo ./svc.sh uninstall || true
fi

say "Registering runner '${RUNNER_NAME}' with ${REPO} (labels: ${RUNNER_LABELS})…"
./config.sh \
  --url "$REPO_URL" \
  --token "$RUNNER_TOKEN" \
  --name "$RUNNER_NAME" \
  --labels "$RUNNER_LABELS" \
  --work "_work" \
  --unattended \
  --replace

say "Installing + starting the runner as a systemd service (auto-starts on boot)…"
sudo ./svc.sh install "$RUN_USER"
sudo ./svc.sh start

# ---------------------------------------------------------------------------
# 4. Done
# ---------------------------------------------------------------------------
echo
say "DONE. Runner '${RUNNER_NAME}' is online with label(s): ${RUNNER_LABELS}"
echo "   • Verify:   GitHub → Settings → Actions → Runners  (should show 'Idle')"
echo "   • FINAL STEP → set repo variable SCRAPER_RUNNER = ${RUNNER_LABELS}"
echo "     (Settings → Secrets and variables → Actions → Variables → New variable)"
echo "   • Then the daily workflow (and the 'Run workflow' button) executes here."
echo "   • Service logs:   sudo journalctl -u 'actions.runner.*' -f"
echo "   • Manage:         cd $RUNNER_DIR && sudo ./svc.sh {status|stop|start}"
