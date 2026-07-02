# Run the Opporta scraper from a free India server

The daily scraper runs on GitHub's US servers, and several Indian government
portals (CG e-Proc, SECL, PWD-CG, DPR-CG, Samvad, CG PSC, Vyapam, UPSSSC, …)
**block foreign IP addresses**. Running the exact same pipeline from an
India-based server fixes this for **every source except GeM** (GeM also has
anti-bot/CAPTCHA and needs its seller API separately).

**Oracle Cloud "Always Free"** gives a permanent, $0/month VM in the Mumbai or
Hyderabad region — a real Indian IP. This guide gets it running in ~30–40 min.

> This does **not** change your website, domain, Vercel, or Supabase. It's just
> a second place the scraper runs from. You can keep or disable the GitHub cron.

---

## Part A — Create the free Oracle VM (~15 min)

1. **Sign up:** https://www.oracle.com/cloud/free/ → *Start for free*.
   - Requires an email + a card for identity verification. **Always Free
     resources are never charged**; the card is only for verification.
   - **Home Region: choose `India South (Hyderabad)` or `India West (Mumbai)`.**
     ⚠️ You cannot change region later, and it must be India for this to work.

2. After the account is ready, open the **Cloud Console** →
   ☰ menu → **Compute → Instances → Create instance**.

3. Configure the instance:
   - **Name:** `opporta-scraper`
   - **Image:** *Canonical Ubuntu 22.04*
   - **Shape:** click *Change shape* →
     - Best: **Ampere (Arm) — VM.Standard.A1.Flex**, 1 OCPU / 6 GB RAM (Always Free).
     - If Ampere shows "out of capacity", pick **VM.Standard.E2.1.Micro** (x86, Always Free). Both work.
   - **SSH keys:** choose *Generate a key pair for me* → **Download the private key**
     (keep it safe — you need it to log in).
   - Leave networking default → **Create**.

4. Wait ~1 min until the instance is **Running**. Copy its **Public IP address**.

---

## Part B — Log in and open a terminal (~5 min)

**On Windows:** install [Git for Windows](https://git-scm.com/download/win) (gives
"Git Bash"), or use PowerShell — both have `ssh`.
**On Mac/Linux:** Terminal already has `ssh`.

```bash
# move the downloaded key somewhere sensible and lock its permissions
chmod 600 /path/to/your-private-key.key

# log in (user is 'ubuntu'); replace with your VM's public IP
ssh -i /path/to/your-private-key.key ubuntu@YOUR_PUBLIC_IP
```
Type `yes` if asked to trust the host. You're now on the Indian server.

---

## Part C — Add your secrets (~5 min)

Create the secrets file in your home folder. These are the **same values** you
set as GitHub Actions secrets.

```bash
cat > ~/opporta.env <<'EOF'
SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_SERVICE_KEY=
GEMINI_API_KEY=
RESEND_API_KEY=
FROM_EMAIL=
APP_URL=
EOF

nano ~/opporta.env      # paste the real values after each =, then Ctrl-O, Enter, Ctrl-X
chmod 600 ~/opporta.env
```

Where to find them: GitHub → your repo → **Settings → Secrets and variables →
Actions**. (Secret *values* can't be re-read there; use the originals from your
Supabase/Gemini dashboards if needed.)

---

## Part D — Run the installer (~15 min)

One command. It installs everything, schedules the daily run, and does a test:

```bash
curl -fsSL https://raw.githubusercontent.com/akashhs1034/cg_tender_app/claude/project-review-optimize-9x3z45/deploy/india-vm/setup.sh | bash
```

At the end you'll see the **SCRAPER SUMMARY**. The India-blocked sources should
now show record counts instead of `[WARN] 0 RESULTS`.

The scraper is now scheduled **daily at 07:30 IST** automatically. Useful commands:

```bash
sudo systemctl start opporta-scraper.service          # run right now
sudo journalctl -u opporta-scraper.service -f         # watch live logs
systemctl list-timers opporta-scraper.timer           # confirm the schedule
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Secrets file not found` | You didn't create `~/opporta.env`. Redo Part C. |
| `is missing SUPABASE_URL` | A required line in `~/opporta.env` is blank. |
| Ampere shape "out of capacity" | Use `VM.Standard.E2.1.Micro`, or retry later. |
| Can't SSH (timeout) | In Oracle console → instance → *Subnet → Security List* → add an ingress rule for TCP 22 (usually there by default). |
| Test run shows some portals still 0 | A few portals change layout over time; report the summary and we'll patch selectors. GeM stays 0 until its seller API is wired. |

Once it's confirmed working here, you can (optionally) disable the GitHub
Actions cron so the pipeline runs only from India.
