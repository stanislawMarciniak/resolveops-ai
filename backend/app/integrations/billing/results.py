from pydantic import BaseModel

from app.models import Invoice, Payment


class InvoiceLookupResult(BaseModel):
    invoice: Invoice
    source_invoice_id: str


class PaymentLookupResult(BaseModel):
    payment: Payment

    source_invoice_reference: str | None = None
    source_matched_invoice_id: str | None = None