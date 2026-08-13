# Billing Policy

## Payment recognition

A payment is considered confirmed when the billing system contains a received transaction with a matching customer, amount, and currency.

A received payment may remain unmatched when the invoice reference cannot be resolved automatically. An unmatched payment must not be treated as missing if the underlying transaction has been confirmed.

## Manual payment matching

Support operators may manually associate a confirmed payment with an invoice when the customer, amount, currency, and intended invoice can be verified.

Manual payment matching is considered a write operation and requires operator approval before execution.

## Invoice status

After a confirmed payment is successfully matched to an overdue invoice, the invoice status must be updated to PAID before any billing-related account hold is removed.
