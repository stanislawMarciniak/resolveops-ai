# Split Payment Policy

## Purpose

This policy governs payment-to-invoice matching when the
received payment does not independently settle the full
outstanding invoice amount.

## Full settlement requirement

A payment may be manually matched to an invoice only when
the individual payment amount fully settles the outstanding
invoice balance.

A payment that is lower than the outstanding invoice amount
must not be manually matched as full settlement.

## Multiple partial payments

Multiple partial payments must not be combined automatically
by ResolveOps in order to simulate a single full payment.

Cases requiring aggregation of multiple partial payments
must be escalated to Finance Operations.

## Account holds

A PAYMENT_OVERDUE hold must remain active while an invoice
still has an outstanding unpaid balance.

ResolveOps must not remove the hold merely because one or
more partial payments have been received.
