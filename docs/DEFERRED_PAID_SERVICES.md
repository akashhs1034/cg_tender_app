# Deferred paid services

No paid service is required or activated by the M0 work. These integrations may
become operationally necessary at scale; software should remain provider-neutral
and safely disabled when credentials are absent.

## India-hosted runner or proxy

- Service purpose: reliable access to geo-restricted NIC/government portals.
- Why it may be needed: GitHub-hosted US IPs are blocked or degraded for several
  sources; home runners are not always available.
- Free/current fallback: GitHub-hosted runner with partial coverage, local
  Windows runner, or free-tier India VM where available.
- Environment variables: `SCRAPER_RUNNER`, `SCRAPER_HTTPS_PROXY`,
  `SCRAPER_NO_PROXY`, runner registration/configuration names.
- Activation: provision a hardened India host/proxy, validate egress/IP,
  register the runner or proxy secret, run a strict-health canary, then enable
  the repository variable.
- Operational impact: higher coverage and schedule reliability; new host
  patching, uptime, capacity, and cost ownership.
- Security considerations: runner sees production secrets and executes workflow
  code; use least privilege, isolation, updates, egress controls, and short-lived
  registration tokens.

## Higher AI quota (Gemini/Anthropic or future provider)

- Service purpose: extraction, advisory analysis, and drafting.
- Why it may be needed: free quotas are rate-limited and not a production SLA.
- Free/current fallback: deterministic/rule-based output, disabled AI actions,
  paced free-tier calls, and manual review.
- Environment variables: `GEMINI_API_KEY`, `GOOGLE_API_KEY`,
  `ANTHROPIC_API_KEY`, `GEMINI_MODEL`, pacing/quota variables.
- Activation: only after M3 authentication, canonical-data loading, per-user/IP
  quotas, usage logging, cost caps, timeouts, and kill switch.
- Operational impact: higher throughput and predictable latency, plus variable
  cost and provider incidents.
- Security considerations: never expose keys client-side; minimise prompt data,
  prevent cache poisoning, redact logs, and retain advisory disclaimers.

## Transactional email provider capacity

- Service purpose: verified alerts, account notifications, and support email.
- Why it may be needed: development/free sender limits and deliverability are
  insufficient for a public launch.
- Free/current fallback: Resend development/free tier when permitted, local log
  provider, in-app alerts, and safely skipped email.
- Environment variables: `RESEND_API_KEY`, `FROM_EMAIL`, `APP_URL`.
- Activation: verify a sending domain, configure DKIM/SPF/DMARC, implement
  unsubscribe/preferences/bounces, canary delivery, and provider abstraction.
- Operational impact: deliverability, suppression handling, and recurring/usage
  cost.
- Security considerations: protect API key, prevent recipient leakage, rate
  limit, minimise personal data, and audit sends.

## Managed rate limiting and cache

- Service purpose: distributed AI/API abuse protection and shared quota state.
- Why it may be needed: local memory is not consistent across serverless
  instances; database limiting can add latency/contention at scale.
- Free/current fallback: database-backed atomic limits and local development
  limiter behind a provider interface.
- Environment variables: provider URL/token/prefix names to be defined in M3;
  feature disabled when absent.
- Activation: dual-run against database limiter, test fail-closed behaviour,
  configure TTL/quotas, then switch provider flag.
- Operational impact: lower abuse risk and cross-instance consistency; network
  dependency and cost.
- Security considerations: hash/minimise identifiers, protect token, bound
  cardinality, and avoid storing request content.

## Error monitoring, log retention, and status page

- Service purpose: actionable frontend/API/ingestion alerts, durable logs, and
  public incident communication.
- Why it may be needed: GitHub logs and local/provider logs have limited
  retention, correlation, alerting, and user communication.
- Free/current fallback: structured stdout, GitHub summaries/issues/artifacts,
  provider dashboards, and a static status-page template.
- Environment variables: provider-neutral DSN/token/environment/release names
  to be defined in M7.
- Activation: implement adapters and redaction first, canary non-sensitive
  errors, verify alerts/runbooks, then enable production sampling.
- Operational impact: faster detection/response; ongoing alert tuning and cost.
- Security considerations: never send secrets, document contents, resumes, or
  unnecessary user data; define retention and access control.

## Supabase capacity, point-in-time recovery, and Storage growth

- Service purpose: production database/Auth/Storage capacity, stronger backup
  objectives, and recovery.
- Why it may be needed: free-tier quotas/backup guarantees may not meet public
  launch RPO/RTO and document growth.
- Free/current fallback: free project, versioned migrations, scheduled logical
  exports where permitted, local restore rehearsal, retention limits.
- Environment variables: existing Supabase URL/public/service credentials;
  backup destination credentials only if later approved.
- Activation: finish M2/M7 migrations and restore rehearsal, define RPO/RTO,
  verify encryption/region/retention, then approve plan change.
- Operational impact: improved resilience/capacity with recurring cost.
- Security considerations: India/user-data requirements, encrypted backups,
  least-privilege backup credentials, RLS, and deletion/retention compliance.

## Vercel production capacity

- Service purpose: Next.js hosting, serverless functions, build/deployment, and
  rollback capacity.
- Why it may be needed: free limits may not support traffic, logs, function
  duration, team controls, or SLA needs.
- Free/current fallback: current Vercel deployment and local Next.js build;
  provider-neutral application code.
- Environment variables: existing frontend/server configuration; provider
  project/team identifiers should not be hardcoded into business logic.
- Activation: measure real beta traffic/limits, verify rollback and region,
  approve only the capacity required.
- Operational impact: higher quotas/support with recurring cost.
- Security considerations: protect deployment access, isolate preview/prod
  secrets, require reviewed releases, and audit team membership.

## Payment provider transaction activation

- Service purpose: paid plan checkout and settlement.
- Why it may be needed: monetisation after controlled launch gates.
- Free/current fallback: free plans only; Razorpay test mode; feature flag off.
- Environment variables: `NEXT_PUBLIC_PAYMENTS_ENABLED`, `RAZORPAY_KEY_ID`,
  `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`.
- Activation: complete M8 test-mode reconciliation/idempotency/entitlement and
  legal review, then require explicit human production activation.
- Operational impact: transaction fees, reconciliation, refunds, support, and
  tax/accounting operations.
- Security considerations: never trust client amount/status, verify signatures
  and event identity, store no card data, and keep production keys isolated.
