# Run the Opporta scraper on your Windows PC (free, no card)

Several Indian government portals (CG e-Proc, SECL, PWD-CG, DPR-CG, Samvad,
CG PSC, Vyapam, UPSSSC, …) **block foreign IP addresses**, so they return 0
when the scraper runs on GitHub's US servers. Running the **same pipeline on
your own Windows PC** — which has an Indian home-internet IP — fixes this for
**every source except GeM** (GeM needs its seller API separately).

Cost: **₹0**. No credit card. Your PC just needs to be on around the scheduled
time each day (it catches up at next power-on if it was off).

> This does not change your website, domain, Vercel, or Supabase. The scraper
> writes to the same Supabase database as before — just from your PC.

---

## Step 1 — Install Python (one time, ~3 min)
1. Download from **https://www.python.org/downloads/windows/** (get the latest 3.11+).
2. Run the installer. **On the first screen, TICK “Add python.exe to PATH.”** Then click *Install Now*.

## Step 2 — Get the project onto your PC (~2 min)
**Easiest (no Git):**
1. Go to **https://github.com/akashhs1034/cg_tender_app**
2. Branch selector → pick **`claude/project-review-optimize-9x3z45`**
3. Green **Code** button → **Download ZIP**.
4. Right-click the ZIP → **Extract All…** → extract to somewhere simple like `C:\opporta`.
   You should end up with a folder like `C:\opporta\cg_tender_app` containing `ingest.py`.

## Step 3 — Add your secrets (~3 min)
1. Open the extracted folder, go into `deploy\windows\`, and copy **`opporta.env.example`** into the **repo root** (the folder that has `ingest.py`), renaming it to **`opporta.env`**.
2. Open `opporta.env` in Notepad and paste your values after each `=`:
   ```
   SUPABASE_URL=...
   SUPABASE_KEY=...
   SUPABASE_SERVICE_KEY=...
   GEMINI_API_KEY=...
   ```
   (These are the same values you set as GitHub Actions secrets. RESEND/FROM_EMAIL/APP_URL are optional.)
3. Save and close.

## Step 4 — Run the setup (~15–25 min for the first run)
1. Open the repo folder in File Explorer.
2. Click the address bar, type `powershell`, press Enter — a PowerShell window opens in that folder.
3. Paste this and press Enter:
   ```powershell
   powershell -ExecutionPolicy Bypass -File deploy\windows\setup.ps1
   ```
It installs everything, schedules a **daily 07:30** run, and does one test run.
At the end you’ll see the **SCRAPER SUMMARY** — the India-blocked sources should now show record counts instead of `0 RESULTS`.

---

## Everyday use
- **It runs automatically every day at 07:30** (Windows Task Scheduler, task name `OpportaScraper`). Just leave the PC on around then.
- **Run it right now, any time:**
  ```powershell
  powershell -ExecutionPolicy Bypass -File deploy\windows\run.ps1
  ```
- **See/adjust the schedule:** open **Task Scheduler** → *Task Scheduler Library* → **OpportaScraper**.

## Troubleshooting
| Problem | Fix |
|---|---|
| `Python not found on PATH` | Reinstall Python and tick “Add python.exe to PATH”. |
| `opporta.env is missing SUPABASE_URL` | You didn’t fill in the secrets file. Redo Step 3. |
| `running scripts is disabled` | Use the exact command with `-ExecutionPolicy Bypass` as shown. |
| Some portals still show 0 | A few change their page layout over time — send me the SCRAPER SUMMARY and I’ll patch them. GeM stays 0 until its seller API is wired. |

Once it’s confirmed working here, the GitHub daily cron can stay on as a backup
(the reachable sources) or be turned off — your call.
