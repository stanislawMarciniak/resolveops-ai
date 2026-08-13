# Currency Matching Policy

## Currency equality

A payment may only be directly matched to an invoice when
the payment currency equals the invoice currency.

Examples:

- PLN payment -> PLN invoice: potentially valid.
- EUR payment -> EUR invoice: potentially valid.
- USD payment -> EUR invoice: invalid for direct matching.

## Cross-currency settlement

ResolveOps must not perform currency conversion.

Cross-currency payments require Finance Operations review
even when the numerical payment amount equals the invoice
amount.

## Account holds

A PAYMENT_OVERDUE hold must not be removed on the basis of
a payment that cannot be safely matched because of a
currency mismatch.
