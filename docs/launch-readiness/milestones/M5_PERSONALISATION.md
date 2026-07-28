# M5 — True personalisation

Status: **NOT STARTED**
Dependency: M2 role/profile schema, M3 authenticated services, M4 trustworthy data

## Objective

Provide separate, versioned, profile-specific contractor and job-seeker matching
with honest explanations.

## Baseline inputs

- Next.js currently ranks global `ai_score` and labels results “Recommended for
  you/business”.
- Dashboard ranking does not load the authenticated profile.
- Matching logic is duplicated across Python, TypeScript, Dart, and Edge code.

## Planned scope

- Temporarily rename all misleading recommendation/match labels.
- Implement separate server-side contractor and job-seeker engines.
- Use required role-specific profile inputs.
- Return score, eligibility state, reasons, missing data/requirements, risks,
  next action, and calculation version.
- Add different-profile tests, relevance feedback, and personalised alerts.

## Exit criteria

- Different profiles produce appropriately different rankings.
- Every result has reasons and missing-information disclosure.
- Correct role data drives the correct engine.
- No global/default score is marketed as a personal match or win probability.
