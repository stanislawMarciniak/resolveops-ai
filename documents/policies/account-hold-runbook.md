# Account Hold Runbook

## Stale PAYMENT_OVERDUE holds

A PAYMENT_OVERDUE hold may become stale when all relevant
invoices have already been settled but the hold remains
active.

If the relevant invoice is already PAID and no outstanding
balance responsible for the hold remains, the obsolete hold
may be removed.

## Minimal remediation

ResolveOps should always choose the minimum sufficient
remediation.

If an invoice is already PAID, ResolveOps must not create an
unnecessary payment matching operation.

Example:

Invoice: PAID
Payment: MATCHED
Hold: ACTIVE

Correct remediation:

1. remove_account_hold

Incorrect remediation:

1. match_payment
2. remove_account_hold
