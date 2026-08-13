import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Final

from app.integrations.billing.results import (
    InvoiceLookupResult,
    PaymentLookupResult,
)
from app.integrations.billing.schemas import (
    LegacyAccountHold,
    LegacyInvoice,
    LegacyPayment,
)
from app.models import (
    AccountHold,
    Currency,
    Invoice,
    InvoiceStatus,
    Payment,
    PaymentStatus,
)

LEGACY_INVOICE_STATUSES: Final[
    dict[str, InvoiceStatus]
] = {
    "OPEN": InvoiceStatus.OPEN,
    "OVD": InvoiceStatus.OVERDUE,
    "PAID": InvoiceStatus.PAID,
    "CANC": InvoiceStatus.CANCELLED,
}


LEGACY_PAYMENT_STATUSES: Final[
    dict[str, PaymentStatus]
] = {
    "RCVD": PaymentStatus.RECEIVED,
    "MATCH": PaymentStatus.MATCHED,
    "REV": PaymentStatus.REVERSED,
}


LEGACY_TIMESTAMP_FORMAT: Final[str] = (
    "%Y/%m/%d %H:%M:%S"
)


class LegacyBillingError(ValueError):
    """Raised when legacy billing data cannot be normalized."""


def normalize_invoice_id(
    invoice_id: str,
) -> str:
    compact = re.sub(
        r"[^A-Za-z0-9]",
        "",
        invoice_id,
    ).upper()

    match = re.fullmatch(
        r"INV(\d+)",
        compact,
    )

    if match is None:
        raise LegacyBillingError(
            f"Unsupported invoice ID: {invoice_id!r}"
        )

    number = match.group(1)

    return f"INV-{number}"


def to_legacy_invoice_id(
    invoice_id: str,
) -> str:
    canonical = normalize_invoice_id(
        invoice_id
    )

    return canonical.replace("-", "")


def normalize_customer_id(
    customer_id: str,
) -> str:
    normalized = customer_id.strip()

    if not normalized:
        raise LegacyBillingError(
            "Customer ID cannot be empty."
        )

    return normalized


def parse_amount(
    amount: str,
) -> Decimal:
    try:
        parsed = Decimal(amount)

    except InvalidOperation as exc:
        raise LegacyBillingError(
            f"Invalid monetary amount: {amount!r}"
        ) from exc

    if parsed <= 0:
        raise LegacyBillingError(
            "Monetary amount must be positive."
        )

    return parsed


def parse_currency(
    currency: str,
) -> Currency:
    try:
        return Currency(
            currency.strip().upper()
        )

    except ValueError as exc:
        raise LegacyBillingError(
            f"Unsupported currency: {currency!r}"
        ) from exc


def parse_invoice_status(
    status: str,
) -> InvoiceStatus:
    normalized = status.strip().upper()

    try:
        return LEGACY_INVOICE_STATUSES[
            normalized
        ]

    except KeyError as exc:
        raise LegacyBillingError(
            f"Unsupported invoice status: {status!r}"
        ) from exc


def parse_payment_status(
    status: str,
) -> PaymentStatus:
    normalized = status.strip().upper()

    try:
        return LEGACY_PAYMENT_STATUSES[
            normalized
        ]

    except KeyError as exc:
        raise LegacyBillingError(
            f"Unsupported payment status: {status!r}"
        ) from exc


def parse_legacy_timestamp(
    timestamp: str,
) -> datetime:
    try:
        return datetime.strptime(
            timestamp,
            LEGACY_TIMESTAMP_FORMAT,
        )

    except ValueError as exc:
        raise LegacyBillingError(
            f"Invalid legacy timestamp: {timestamp!r}"
        ) from exc


def parse_legacy_invoice(
    raw: LegacyInvoice,
) -> Invoice:
    return Invoice(
        invoice_id=normalize_invoice_id(
            raw.INV_NO
        ),
        customer_id=normalize_customer_id(
            raw.CUST_NO
        ),
        amount=parse_amount(
            raw.AMT
        ),
        currency=parse_currency(
            raw.CURR
        ),
        status=parse_invoice_status(
            raw.STAT_CD
        ),
    )


def parse_legacy_invoice_lookup(
    raw: LegacyInvoice,
) -> InvoiceLookupResult:
    return InvoiceLookupResult(
        invoice=parse_legacy_invoice(
            raw
        ),
        source_invoice_id=(
            raw.INV_NO.strip()
        ),
    )


def parse_legacy_payment(
    raw: LegacyPayment,
) -> Payment:
    invoice_reference: str | None = None

    if raw.INV_REF is not None:
        invoice_reference = normalize_invoice_id(
            raw.INV_REF
        )

    matched_invoice_id: str | None = None

    if raw.MATCHED_INV_NO is not None:
        matched_invoice_id = normalize_invoice_id(
            raw.MATCHED_INV_NO
        )

    return Payment(
        payment_id=raw.PAY_ID.strip(),
        customer_id=normalize_customer_id(
            raw.CUST_NO
        ),
        amount=parse_amount(
            raw.AMT
        ),
        currency=parse_currency(
            raw.CURR
        ),
        status=parse_payment_status(
            raw.STAT_CD
        ),
        invoice_reference=invoice_reference,
        matched_invoice_id=matched_invoice_id,
        received_at=parse_legacy_timestamp(
            raw.RECEIVED_TS
        ),
    )


def parse_legacy_payment_lookup(
    raw: LegacyPayment,
) -> PaymentLookupResult:
    return PaymentLookupResult(
        payment=parse_legacy_payment(
            raw
        ),
        source_invoice_reference=(
            raw.INV_REF.strip()
            if raw.INV_REF is not None
            else None
        ),
        source_matched_invoice_id=(
            raw.MATCHED_INV_NO.strip()
            if raw.MATCHED_INV_NO is not None
            else None
        ),
    )


def parse_legacy_account_hold(
    raw: LegacyAccountHold,
) -> AccountHold:
    flag = raw.ACTIVE_FLG.strip().upper()

    if flag not in {"Y", "N"}:
        raise LegacyBillingError(
            "Unsupported account hold flag: "
            f"{raw.ACTIVE_FLG!r}"
        )

    return AccountHold(
        customer_id=normalize_customer_id(
            raw.CUST_NO
        ),
        hold_code=raw.HOLD_CD.strip(),
        active=flag == "Y",
    )