from decimal import Decimal

import pytest
from app.integrations.billing import (
    LegacyBillingError,
    LegacyInvoice,
    LegacyPayment,
    normalize_invoice_id,
    parse_legacy_invoice,
    parse_legacy_payment,
)
from app.integrations.billing.adapter import (
    parse_legacy_account_hold,
    parse_legacy_invoice_lookup,
    parse_legacy_payment_lookup,
)
from app.integrations.billing.schemas import (
    LegacyAccountHold,
)
from app.models import (
    Currency,
    InvoiceStatus,
    PaymentStatus,
)


def test_normalize_invoice_id() -> None:
    assert (
        normalize_invoice_id("INV8231")
        == "INV-8231"
    )

    assert (
        normalize_invoice_id("inv-8231")
        == "INV-8231"
    )

    assert (
        normalize_invoice_id("INV 8231")
        == "INV-8231"
    )


def test_invalid_invoice_id_is_rejected() -> None:
    with pytest.raises(
        LegacyBillingError
    ):
        normalize_invoice_id(
            "something-random"
        )


def test_parse_legacy_invoice() -> None:
    raw = LegacyInvoice(
        CUST_NO="000018392",
        INV_NO="INV8231",
        STAT_CD="OVD",
        AMT="4999.00",
        CURR="PLN",
    )

    invoice = parse_legacy_invoice(raw)

    assert invoice.invoice_id == "INV-8231"

    assert (
        invoice.customer_id
        == "000018392"
    )

    assert (
        invoice.amount
        == Decimal("4999.00")
    )

    assert invoice.currency is Currency.PLN

    assert (
        invoice.status
        is InvoiceStatus.OVERDUE
    )


def test_parse_legacy_payment() -> None:
    raw = LegacyPayment(
        PAY_ID="TX-9912",
        CUST_NO="000018392",
        AMT="4999.00",
        CURR="PLN",
        STAT_CD="RCVD",
        INV_REF="INV-8231",
        MATCHED_INV_NO=None,
        RECEIVED_TS=(
            "2026/08/08 14:31:22"
        ),
    )

    payment = parse_legacy_payment(raw)

    assert payment.payment_id == "TX-9912"

    assert (
        payment.invoice_reference
        == "INV-8231"
    )

    assert payment.matched_invoice_id is None

    assert (
        payment.status
        is PaymentStatus.RECEIVED
    )


def test_invalid_amount_is_rejected() -> None:
    raw = LegacyInvoice(
        CUST_NO="000018392",
        INV_NO="INV8231",
        STAT_CD="OVD",
        AMT="not-a-number",
        CURR="PLN",
    )

    with pytest.raises(
        LegacyBillingError
    ):
        parse_legacy_invoice(raw)

def test_unknown_status_is_rejected() -> None:
    raw = LegacyInvoice(
        CUST_NO="000018392",
        INV_NO="INV8231",
        STAT_CD="WHAT",
        AMT="4999.00",
        CURR="PLN",
    )

    with pytest.raises(
        LegacyBillingError
    ):
        parse_legacy_invoice(raw)

def test_parse_legacy_account_hold() -> None:
    raw = LegacyAccountHold(
        CUST_NO="000018392",
        HOLD_CD="PAYMENT_OVERDUE",
        ACTIVE_FLG="Y",
    )

    hold = parse_legacy_account_hold(
        raw
    )

    assert (
        hold.customer_id
        == "000018392"
    )

    assert (
        hold.hold_code
        == "PAYMENT_OVERDUE"
    )

    assert hold.active is True

def test_invoice_lookup_preserves_source_id() -> None:
    raw = LegacyInvoice(
        CUST_NO="000018392",
        INV_NO="INV8231",
        STAT_CD="OVD",
        AMT="4999.00",
        CURR="PLN",
    )

    result = parse_legacy_invoice_lookup(
        raw
    )

    assert (
        result.invoice.invoice_id
        == "INV-8231"
    )

    assert (
        result.source_invoice_id
        == "INV8231"
    )


def test_payment_lookup_preserves_source_reference() -> None:
    raw = LegacyPayment(
        PAY_ID="TX-9912",
        CUST_NO="000018392",
        AMT="4999.00",
        CURR="PLN",
        STAT_CD="RCVD",
        INV_REF="INV-8231",
        MATCHED_INV_NO=None,
        RECEIVED_TS=(
            "2026/08/08 14:31:22"
        ),
    )

    result = parse_legacy_payment_lookup(
        raw
    )

    assert (
        result.payment.invoice_reference
        == "INV-8231"
    )

    assert (
        result.source_invoice_reference
        == "INV-8231"
    )

    assert (
        result.source_matched_invoice_id
        is None
    )