# Production checklist

This is a human approval checklist. An unchecked critical item blocks public
launch. Evidence must link to a commit, run, migration, incident exercise, or
production validation record.

## Release identity and rollback

- [ ] Release commit reviewed and present in `main`.
- [ ] All required checks pass on that exact commit.
- [ ] Database migrations reviewed, backed up, and applied in order.
- [ ] Application and database rollback procedures tested.
- [ ] Feature flags and kill switches verified.
- [ ] Human launch owner records go/no-go approval.

## Security and privacy

- [ ] Historically exposed credentials confirmed revoked/rotated.
- [ ] Secret scanning passes for current tree and reachable history.
- [ ] No service-role/secret key is present in a public bundle.
- [ ] AI routes require auth, validation, quotas, size/time limits, and logging.
- [ ] Admin access fails closed and produces audit events.
- [ ] Two-user RLS and Storage-isolation tests pass.
- [ ] CSP/security headers, redirect safety, uploads, and error sanitisation pass.
- [ ] Privacy, deletion, export, retention, and grievance flows are reviewed.

## Database and data safety

- [ ] Fresh Supabase project can be recreated from migrations and fixtures.
- [ ] Production upgrade has verified backup, restore, and rollback evidence.
- [ ] Every code-referenced table/bucket is version-controlled.
- [ ] No expired opportunity is permanently removed by routine ingestion.
- [ ] Lifecycle and history transitions are auditable.
- [ ] Official-source URL, provenance, verification, and last-checked fields exist.

## Ingestion and data quality

- [ ] Strict health thresholds are tuned and enabled in scheduled ingestion.
- [ ] Each run/source/failure is recorded and queryable.
- [ ] Partial source success persists; retry is idempotent.
- [ ] Freshness and stale-source alerts are actionable.
- [ ] Duplicate, missing deadline, invalid link, expired leakage, classification,
  and verification metrics meet approved thresholds.
- [ ] No protected full newspaper content is republished unnecessarily.

## Product truthfulness and UX

- [ ] Global scores are not labelled as personal recommendations.
- [ ] Contractor and job-seeker matching use their authenticated profiles.
- [ ] Explanations, missing information, requirements, and risk flags are shown.
- [ ] AI is clearly advisory and official sources are authoritative.
- [ ] Core journeys pass on supported mobile and desktop browsers.
- [ ] English/Hindi core journeys and accessibility checks pass.
- [ ] No critical dead action, placeholder button, or role-irrelevant navigation.

## CI, observability, and incidents

- [ ] Frontend install/lint/typecheck/build/unit/API/E2E checks block merge.
- [ ] Python compile/unit/parser/health/data-quality checks block merge.
- [ ] Migration/schema/RLS tests block merge.
- [ ] Dependency, secret, and static scans block high/critical findings.
- [ ] Frontend/API/auth/Supabase/AI/ingestion/payment telemetry is monitored.
- [ ] Alert ownership, severity, escalation, and status communication are tested.
- [ ] Database, Storage, and deployment restore rehearsal completed.

## Payments and legal

- [ ] Production payments remain disabled until explicit written activation.
- [ ] Razorpay test-mode order/webhook/reconciliation/idempotency tests pass.
- [ ] Wrong amount/order/user cannot grant entitlement.
- [ ] Expiry/refund/cancellation/failed-payment handling passes.
- [ ] Terms, privacy, refund, AI, accuracy, deletion, export, and grievance
  documents are reviewed by qualified counsel.

## Controlled launch

- [ ] Beta/invite controls and support process work.
- [ ] Metrics definitions are implemented without fabricated outcomes.
- [ ] Traffic/AI caps and daily health report are active.
- [ ] Stage scope is approved: invite-only → CG contractors → CG job seekers →
  Uttar Pradesh → paid plans.
- [ ] Production smoke passes after deployment.
- [ ] Rollback window closes only after human approval.
