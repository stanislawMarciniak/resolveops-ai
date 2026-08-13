from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.models import (
    Currency,
    Evidence,
    EvidenceSource,
    Invoice,
    InvoiceStatus,
    Payment,
    PaymentStatus,
)
from pydantic import ValidationError


def test_invoice_accepts_valid_data() -> None:
    invoice = Invoice(
        invoice_id="INV-8231",
        customer_id="ACME",
        amount=Decimal("4999.00"),
        currency=Currency.PLN,
        status=InvoiceStatus.OVERDUE,
    )

    assert invoice.invoice_id == "INV-8231"
    assert invoice.amount == Decimal("4999.00")


def test_invoice_rejects_negative_amount() -> None:
    with pytest.raises(ValidationError):
        Invoice(
            invoice_id="INV-8231",
            customer_id="ACME",
            amount=Decimal("-100.00"),
            currency=Currency.PLN,
            status=InvoiceStatus.OVERDUE,
        )


def test_payment_model() -> None:
    payment = Payment(
        payment_id="TX-9912",
        customer_id="ACME",
        amount=Decimal("4999.00"),
        currency=Currency.PLN,
        status=PaymentStatus.RECEIVED,
        invoice_reference="INV-8231",
        received_at=datetime.now(UTC),
    )

    assert payment.invoice_reference == "INV-8231"
    assert payment.matched_invoice_id is None


def test_models_reject_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        Invoice(
            invoice_id="INV-8231",
            customer_id="ACME",
            amount=Decimal("4999.00"),
            currency=Currency.PLN,
            status=InvoiceStatus.OVERDUE,
            malicious_instruction="drop database",
        )


def test_hypothetical_evidence_payload() -> None:
    evidence = Evidence(
        evidence_id="EV-001",
        source=EvidenceSource.BILLING,
        description="Invoice remains overdue despite payment.",
        details={
            "invoice_id": "INV8231",
            "payment_reference": "INV-8231",
            "amount": 4999.0,
        },
    )

    assert evidence.source == EvidenceSource.BILLING
    assert evidence.details["invoice_id"] == "INV8231"