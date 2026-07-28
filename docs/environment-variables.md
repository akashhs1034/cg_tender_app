# Environment-variable inventory

Baseline inventory records names and purpose only. Never add values to this
document or commit `.env`, `opporta.env`, runner tokens, signing files, or
credentials.

## Primary frontend

| Name | Sensitivity | Required when | Consumer / behaviour |
|---|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Public configuration | Any live auth/data | Browser/server Supabase URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Public publishable key | Any live auth/data | Browser/server Supabase client; safety depends on grants/RLS |
| `SUPABASE_SERVICE_ROLE_KEY` | **Secret** | Server-side cache/admin/payment writes | Next.js admin client; must never be `NEXT_PUBLIC_` |
| `ADMIN_EMAILS` | Sensitive configuration | Admin routes | Comma-separated allowlist; current code improperly falls back to founder email |
| `GEMINI_API_KEY` | **Secret** | Next.js/Edge/Python Gemini features | AI generation/extraction |
| `GOOGLE_API_KEY` | **Secret** | Optional Next.js Gemini alias | Fallback alias in `frontend/lib/gemini.ts` |
| `GEMINI_MODEL` | Public configuration | Optional | Overrides Next.js Gemini model |
| `NEXT_PUBLIC_PAYMENTS_ENABLED` | Public feature flag | Payment UI/API activation | Must remain absent/false until M8 approval |
| `RAZORPAY_KEY_ID` | Public checkout identifier, sensitive operationally | Test payment activation | Create-order response |
| `RAZORPAY_KEY_SECRET` | **Secret** | Test payment activation | Razorpay Basic auth |
| `RAZORPAY_WEBHOOK_SECRET` | **Secret** | Webhook validation | HMAC verification |
| `NODE_ENV` | Runtime-managed | Next.js runtime | Framework behaviour/analytics |

`frontend/.env.example` currently lists only the Supabase URL/anon key,
`GEMINI_API_KEY`, and service-role key. Admin and payment variables are used but
not represented there.

## Python core, alerts, and AI

| Name | Sensitivity | Purpose / default |
|---|---|---|
| `SUPABASE_URL` | Sensitive configuration | Hosted project URL; cloud operations disabled if absent |
| `SUPABASE_SERVICE_KEY` | **Secret** | Preferred ingestion/admin write key |
| `SUPABASE_KEY` | Public or secret depending on key type | Legacy read/write fallback; should not replace service key for ingestion |
| `ANTHROPIC_API_KEY` | **Secret** | Optional Claude fallback |
| `GEMINI_API_KEY` | **Secret** | Optional Gemini extraction/evaluation |
| `RESEND_API_KEY` | **Secret** | Optional transactional email; alerts disabled/degraded if absent |
| `FROM_EMAIL` | Sensitive configuration | Sender; defaults to Resend development sender |
| `APP_URL` | Public configuration | Links/redirects; defaults differ by client but normally Vercel URL |
| `ALERT_SCORE_THRESHOLD` | Public configuration | Alert threshold, default 55 |
| `GEMINI_VISION_MAX_ATTEMPTS` | Public tuning | Vision retry attempts, default 4 |
| `GEMINI_VISION_PACE_SECONDS` | Public tuning | Vision pacing, default 5 seconds |
| `GENERIC_AI_PACE_SECONDS` | Public tuning | Generic AI pacing, default 10 seconds |

## Scraper tuning

All are optional public operational configuration.

| Source | Variables and defaults |
|---|---|
| CPPP state | `CPPP_STATE` (`Uttar Pradesh`), `CPPP_MAX_PAGES` (300), `CPPP_TIMEOUT_SECONDS` (15), `CPPP_DETAIL_TIMEOUT_SECONDS` (15), `CPPP_PROGRESS_EVERY` (50) |
| CPPP central/corrigendum | `CPPP_CENTRAL_MAX_PAGES` (80), `CORRIG_MAX_PAGES` (40) |
| CG eProc/Vyapam/jobs/WRD | `CG_EPROC_HEADLESS` (1), `CG_EPROC_MAX_ROWS` (0), `CG_VYAPAM_HEADLESS` (1), `CGPSC_MAX_AGE_DAYS` (180), `CGWRD_MAX_AGE_DAYS` (365) |
| CSPDCL/DPRCG | `CSPDCL_PARAMFLAGS` (1–12), `CSPDCL_MAX_PAGES_PER_FLAG` (20), `DPRCG_MAX_AGE_DAYS` (120) |
| GeM | `GEM_MAX_PAGES` (30), `GEM_PAGES_PER_TERM` (3), `GEM_USE_BROWSER` (1) |
| Newspapers | `HARIBHOOMI_MAX_CG_EDITIONS` (12), `HARIBHOOMI_MAX_PAGES_PER_EDITION` (20), `NEWSPAPER_OCR_RPM` (8), `NEWSPAPER_OCR_PACE_SECONDS` (0) |
| Samvad | `SAMVAD_MAX_ADS` (250), `SAMVAD_MAX_AGE_DAYS` (120) |
| UP eTender/jobs | `UP_ETENDER_HEADLESS` (1), `UP_ETENDER_TIMEOUT_MS` (15000), `UP_ETENDER_DETAIL_TIMEOUT_MS` (12000), `UP_ETENDER_MAX_DETAIL_LINKS` (12), `UP_JOBS_HEADLESS` (1), `UP_UPSSSC_HEADLESS` (1) |

## Discovery and approved-source scans

- `OPPORTA_DISCOVERY_MODE` (default `full`; workflow uses `basic`)
- `OPPORTA_DISCOVERY_MAX_SOURCES`
- `OPPORTA_DISCOVERY_MAX_LINKS`
- `OPPORTA_APPROVED_SCAN_MODE` (default `full`; workflow uses `basic`)
- `OPPORTA_APPROVED_MAX_SOURCES`
- `OPPORTA_APPROVED_MAX_FILES`
- `OPPORTA_APPROVED_MAX_PAGES_PER_SOURCE`

## GitHub Actions and runners

### Repository secrets

- Supabase/AI/email: `SUPABASE_URL`, `SUPABASE_KEY`,
  `SUPABASE_SERVICE_KEY`, `GEMINI_API_KEY`, `RESEND_API_KEY`, `FROM_EMAIL`,
  `APP_URL`.
- Network: `SCRAPER_HTTPS_PROXY`, `SCRAPER_NO_PROXY`.
- Android signing: `KEYSTORE_BASE64`, `KEYSTORE_PASSWORD`, `KEY_PASSWORD`,
  `KEY_ALIAS`.

### Repository variables

- `SCRAPER_RUNNER`
- `NEWSPAPER_OCR_RPM`
- `NEWSPAPER_OCR_PACE_SECONDS`
- `CPPP_MAX_PAGES`
- `GEM_PAGES_PER_TERM`

Workflow-local aliases include `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`,
`RUNNER_ENVIRONMENT`, and `HAS_RELEASE_SIGNING`.

### Self-host/VM setup

- GitHub runner: `RUNNER_TOKEN` (**secret**, short-lived), `REPO` or
  `RUNNER_REPO`, `RUNNER_LABELS`, `RUNNER_NAME`, `RUNNER_DIR`,
  `RUNNER_VERSION`.
- Linux standalone VM: `OPPORTA_BRANCH`, `OPPORTA_ENV_FILE`.

The Linux VM default branch is stale and must not be used unchanged.

## Configuration gaps

- No schema validates required variables by environment.
- No complete checked-in example spans frontend, ingestion, workflows, and
  runners.
- `CPPP_MAX_PAGES` tunes the state scraper, while central CPPP uses
  `CPPP_CENTRAL_MAX_PAGES`; workflow comments do not make this distinction
  sufficiently clear.
- Production configuration presence was not queried; absence/presence must not
  be inferred from local builds.
