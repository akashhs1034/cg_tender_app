# M0.1 — Launch Engineering Gates

Status: **COMPLETE — draft PR open; review required; not deployed.**

Branch: `agent/m0-launch-gates`

## Objective

Turn the failed M0 engineering checks into repeatable pull-request gates without
changing ingestion, database, payments, or product behaviour beyond the
build/type/lint repairs required for those gates.

## Scope

- Secret-safe historical credential classification and owner actions.
- Gitleaks policy, current-tree/history checks, and pull-request secret scan.
- Working Next.js 16 ESLint, independent TypeScript, and production build gates.
- Patched production frontend dependency graph with no high or critical audit
  findings.
- Python compile, unit, Streamlit smoke, dependency, workflow, inventory, and
  documentation-link checks.
- Pull-request CI and solo-founder-safe `main` protection after exact check
  names have run.

## Explicit exclusions

- No ingestion architecture or Milestone 1 work.
- No database mutation or destructive test.
- No paid API invocation, paid-service activation, or payment activation.
- No credential values, rotation, history rewrite, force push, or automatic
  merge.
- No claim of deployment or production functional validation.

## Implemented controls

- Historical response ledger:
  [HISTORICAL_CREDENTIAL_RESPONSE.md](../../security/HISTORICAL_CREDENTIAL_RESPONSE.md)
- Developer secret checks:
  [SECRET_SCANNING.md](../../security/SECRET_SCANNING.md)
- Pull-request workflow: `.github/workflows/launch_gates.yml`
- Frontend flat ESLint config: `frontend/eslint.config.mjs`
- Workflow parser: `scripts/validate_workflows.py`
- Launch-document link validator: `scripts/validate_launch_docs.py`
- GitHub native secret scanning: enabled on 2026-07-28; push protection was not
  changed.

## Local result

| Gate | Result |
|---|---|
| ESLint | PASS — zero errors and warnings |
| TypeScript | PASS — independent `tsc --noEmit` |
| Production build | PASS — Next.js 16.2.12 ran TypeScript and generated 16 static pages |
| Production npm audit | PASS — zero findings at all severities |
| Python | PASS — compileall, 25 unit tests, two card smokes, `pip check`, and resolved-set `pip-audit` |
| Audit tooling | PASS — baseline inventory/tests, five workflow YAML files, ten required docs, and 22 local links |
| Current-tree Gitleaks | PASS — zero findings with narrow public-client allowances |
| Full-history Gitleaks | EXPECTED NON-ZERO — three private historical records remain; all output redacted |

`npm ci` also reports nine high findings limited to dev-only legacy
`brace-expansion` paths used by ESLint plugins. They are absent from
`npm audit --omit=dev`, not shipped in the production graph, and documented in
the validation log. An attempted incompatible global override was rejected
because it broke ESLint; no unsafe suppression or forced upgrade remains.

## Exit criteria

- [x] M0 PR #51 is merged and verified on `origin/main`.
- [x] ESLint runs successfully.
- [x] Independent TypeScript check passes.
- [x] Next.js build runs TypeScript and passes.
- [x] Production npm audit has zero high and zero critical findings.
- [x] Historical credential types and locations are documented without values.
- [x] Secret-scanning CI has run and passed.
- [x] All pull-request launch jobs have run automatically.
- [x] `main` protection is configured with the four verified check names.
- [x] Draft M0.1 pull request is open.
- [x] Milestone 1 has not started.

## Validation evidence

See [VALIDATION_LOG.md](../VALIDATION_LOG.md).

- Draft PR: `https://github.com/akashhs1034/cg_tender_app/pull/52`
- First `Launch gates` run:
  `https://github.com/akashhs1034/cg_tender_app/actions/runs/30376707271`
- Verified successful checks: `Frontend gates`, `Python gates`, `Secret scan`,
  and `Audit tooling`.
- Vercel preview: passed; this is not a production deployment or production
  functional validation.
- PR remains draft, mergeable, and has no auto-merge request.
- `main` remains at the M0 merge commit; M0.1 was not merged.
