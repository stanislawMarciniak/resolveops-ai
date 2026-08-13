# Payment Matching Runbook

## Investigating an unmatched payment

Retrieve the customer record, invoice, and recent payments.

Verify that the customer identifiers correspond to the same billing customer.

Compare payment amount and currency with the invoice.

Compare invoice references after normalizing common separators such as hyphens and spaces.

## Reference normalization

Legacy billing stores invoice identifiers without separators.

For diagnostic comparison, INV8231, INV-8231, and INV 8231 represent the same canonical invoice identifier INV-8231.

Automatic matching failures caused only by separator differences may be corrected through manual payment matching.

## Manual resolution

When customer, invoice, payment amount, currency, and normalized invoice reference all match, the payment may be manually associated with the invoice.

After matching, retrieve the invoice again and verify that its status is PAID.

If an account hold exists, remove it only after the invoice verification succeeds.
