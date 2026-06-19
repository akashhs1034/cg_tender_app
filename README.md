# Opporta

Hyper-local government **tenders & jobs** intelligence for Chhattisgarh & Uttar Pradesh.
This is the refactored foundation: one schema, one pipeline, one app — runnable today.

## ⚠️ Security first (do this before anything else)
The original project committed live secrets (Supabase service key in
`scraper_entry.py`, Google key in `client_secret.json`, `.env`). If those ever
touched GitHub, **rotate them now** (Supabase → Settings → API; Google Cloud →
Service Accounts) and keep secrets only in `.env` (gitignored) or GitHub Secrets.

## What's here
```
core.py        # single schema + value/date parsing + transparent fit score
ingest.py      # THE pipeline: seed CSVs + scrapers -> dedup -> local CSV + Supabase
app.py         # Streamlit dashboard (DB or local fallback; real filters/search/sort)
schema.sql     # run once in Supabase
scrapers/      # add one real portal scraper at a time (template inside)
seed/          # your existing CSVs, used as starter data
data/          # generated normalized CSVs (gitignored) — lets the app run with no DB
```

## Run it in 3 steps
```bash
pip install -r requirements.txt
python ingest.py        # builds data/tenders.csv + data/jobs.csv from seed data
streamlit run app.py    # works immediately, no database needed
```
To use the cloud DB: paste `schema.sql` into the Supabase SQL editor, copy
`.env.example` to `.env`, fill in your (rotated) keys, then re-run `ingest.py`.

## The one rule that fixes the old mess
The original had four scrapers writing four different column sets to differently
named tables, while the app read columns nobody produced. Now **everything goes
through `core.tender_record()` / `core.job_record()`**, so the pipeline, scrapers,
schema, and app can never drift apart again.

## Roadmap (suggested order)
1. **Secure & deploy** the working app (Streamlit Community Cloud is free).
2. **One real scraper.** Pick the single most reliable portal, make it produce
   real rows end-to-end. Don't attempt all 64 at once.
3. **Replace the rule-based score** with a learned model once you have real
   bid/win outcomes to train on.
4. **Notifications** (email/WhatsApp on new high-fit tenders) — this is the
   feature people actually pay for.

---

## SaaS model (per-contractor product, CG + UP)

Opporta now scores one shared feed against **each contractor's own profile**, so it
serves many customers from the same data.

- `core.score_tender_for_user(tender, profile)` — personal fit score + a hard
  **eligibility verdict** (class / turnover / experience). This is the wedge the
  big aggregators are weakest on.
- `accounts.py` — per-user profile + saved-tender pipeline (Supabase or local).
- `app.py` — sign in → set firm profile → personalized "My matches" → save to
  pipeline. Jobs are a state/district/category browse.

### MVP shortcut to fix before charging money
Sign-in is **email-only** (no password). It's fine for demos and first design
partners, but before you take payment, replace it with **Supabase Auth**
(magic-link or password) and switch the RLS policies in `schema.sql` to
per-user (`auth.jwt()->>'email' = email`) so customers can't read each other's
data. Then add billing (Razorpay is the common India choice).

### Suggested pricing tiers
- **Free** — browse state-level tenders + jobs (acquisition).
- **Pro** — district-level alerts, personal fit scoring, saved pipeline.
- **Premium** — eligibility extraction from tender PDFs, tender *results* data
  (who won, at what price), team seats.

### Why you can win a crowded market
Tender247, BidAssist and TenderTiger compete on national breadth. Your edge is
depth where they're thin — municipal/panchayat tenders in CG + UP — plus a
per-firm eligibility verdict that turns a list into a decision. Keep the moat in
**hyper-local coverage + a fit model that improves as customers log real wins.**

---

## AI document evaluator (`evaluator.py` + the "🧮 AI evaluator" tab)
A contractor picks a tender/job, uploads their documents, and gets an
**eligibility-readiness %** — which mandatory requirements they meet and which
they're missing. Deterministic by default; set `ANTHROPIC_API_KEY` to let Claude
extract requirements/facts from messy document text.

**Honesty rule baked in:** it reports *readiness against stated criteria*, never
a fabricated "win probability." A true win-likelihood needs tender *results* data
(who won, at what price) — start collecting that, and it becomes a real model later.

## Roadmap for your three asks
1. **Document evaluator — built.** Upgrade path: turn on the API key, then OCR
   for scanned certs (add `pytesseract`).
2. **Do the documentation for the user — next build.** Do this *safely*: a
   per-tender required-document checklist + a reusable document vault (store
   certs once, reuse across bids) + auto-fill of repetitive fields, with AI
   *drafting* the technical/cover narrative for human review. Never auto-submit.
3. **All CG + UP portal data, up to date — an ops problem, not a one-off.**
   Don't scrape 64 sites blindly. Start with the central **CPPP / eProcure**
   feed filtered to CG+UP plus the two state eProc portals
   (`eproc.cgstate.gov.in`, `etender.up.nic.in`) — most municipal/panchayat
   tenders above threshold publish there anyway. Add per-portal health
   monitoring and show data freshness. Consider a paid structured tender API to
   skip the scraping-maintenance treadmill entirely.
