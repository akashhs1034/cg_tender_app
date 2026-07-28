# M8 — Payments and legal readiness

Status: **NOT STARTED — production payments must remain disabled**
Dependency: M2/M3/M7 controls and qualified legal review

## Objective

Prepare safe paid access and reviewable legal documents without activating live
payments.

## Planned scope

- Central plans/entitlements with server enforcement.
- Validate user, order, plan, amount, currency, status, and provider event.
- Idempotent event log, reconciliation, expiry, refunds, cancellations, and
  failed payments.
- Razorpay test mode only and explicit production kill switch.
- Draft Terms, Privacy, Refund, AI/accuracy disclaimers, deletion/export, and
  grievance pages marked for legal review.

## Exit criteria

- Test payment and duplicate webhook tests pass.
- Wrong amount/order/user cannot grant access.
- Entitlement expiry/refund/cancellation works.
- Production payments remain disabled pending explicit human approval.
- Legal drafts exist and are clearly not professional legal advice.
