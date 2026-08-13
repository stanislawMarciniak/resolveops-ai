# Multi-Invoice Suspension Policy

## Multiple outstanding invoices

A PAYMENT_OVERDUE account hold may be associated with more
than one outstanding invoice.

ResolveOps must evaluate all known invoices relevant to the
reported suspension before removing the hold.

## Partial remediation

A valid payment may still be matched to the invoice it
settles.

However, matching one payment does not justify removing the
account hold when another relevant invoice remains overdue.

Example:

INV-1001: OVERDUE
INV-1002: OVERDUE
Payment settles INV-1002

Allowed:

1. match payment to INV-1002

Not allowed:

2. remove account hold

The remaining overdue invoice must be resolved separately.
