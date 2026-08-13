from datetime import datetime
from decimal import Decimal

from pydantic import Field

from .base import DomainModel
from .enums import Currency, InvoiceStatus, PaymentStatus


class Invoice(DomainModel):
    invoice_id: str = Field(min_length=1, max_length=64)
    customer_id: str = Field(min_length=1, max_length=64)

    amount: Decimal = Field(gt=0)
    currency: Currency

    status: InvoiceStatus

    issued_at: datetime | None = None
    due_at: datetime | None = None


class Payment(DomainModel):
    payment_id: str = Field(min_length=1, max_length=64)
    customer_id: str = Field(min_length=1, max_length=64)

    amount: Decimal = Field(gt=0)
    currency: Currency

    status: PaymentStatus

    invoice_reference: str | None = Field(
        default=None,
        max_length=64,
    )

    matched_invoice_id: str | None = Field(
        default=None,
        max_length=64,
    )

    received_at: datetime

class AccountHold(DomainModel):
    customer_id: str = Field(
        min_length=1,
        max_length=64,
    )

    hold_code: str = Field(
        min_length=1,
        max_length=100,
    )

    active: bool