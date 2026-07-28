# M3 — Security and AI abuse protection

Status: **NOT STARTED**
Dependency: M2 ownership, RLS, and schema verification

## Objective

Protect accounts, private data, admin functions, AI quota, shared caches,
uploads, and server secrets.

## Baseline inputs

- Three Next.js AI routes are unauthenticated and accept browser-provided
  canonical content.
- Edge Function code has no explicit user/quota/size checks.
- Admin email has a hardcoded fallback.
- Historical secret exposure is unresolved and repository secret scanning is
  disabled.
- No CSP, AI usage table, rate limiter, or admin audit log.

## Planned scope

- Classify every route as public/auth/admin/webhook/internal.
- Require auth, canonical DB loads, schemas, size/time/rate limits, safe errors,
  and usage logging for AI.
- Add provider-neutral database/local rate limiting and optional managed adapter.
- Fail admin closed and audit actions.
- Harden headers, redirects, cookies, uploads, dependencies, secrets, and errors.
- Prove RLS/Storage isolation with two users and confirm no service-role key
  reaches client bundles.

## Exit criteria

- AI abuse and cache-poisoning controls pass.
- Admin fails closed and is auditable.
- RLS/Storage isolation passes.
- Secret scan passes and historical credentials are confirmed invalid.
- No unresolved high or critical security finding.
