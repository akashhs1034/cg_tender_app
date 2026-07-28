# M1 — Reliable ingestion

Status: **NOT STARTED**
Dependency: M0 review and approved handling of historical-secret risk

## Objective

Make collection dependable, observable, recoverable, idempotent, and independent
of one long all-or-nothing run while preserving opportunity history.

## Baseline inputs

- Scheduled workflow omits `--strict-health`.
- Routine ingestion permanently deletes expired tenders/jobs/corrigendums.
- Failed row upserts can be silently skipped.
- No `ingestion_runs`, dead-letter queue, checkpoint, or durable source-freshness
  migration exists.
- Recent ingestion history includes failures, cancellations, and a long-running
  job.

## Planned scope

- Tune strict-health thresholds with quiet-day fixtures, then enable the flag.
- Add additive lifecycle states and history; archive rather than delete.
- Add run, source checkpoint, failure/dead-letter, freshness, and alert models.
- Persist validated source batches incrementally.
- Add structured errors and retry limits without hiding failed rows.
- Test multi-anchor outage, legitimate zero, partial failure, duplicate run,
  failed row, archive transition, and recovery.

## Exit criteria

- Strict health is active and tested.
- Every run and failed record is traceable.
- Partial success persists and retries remain idempotent.
- Expired records are archived, not destroyed.
- Source freshness and operational alerts are visible.
- Existing public data is not damaged.

Stop and report if backup, additive migration, or quiet-day evidence is missing.
